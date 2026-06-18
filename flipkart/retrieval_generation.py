#------------------------------------------------------------------------
# Import Statements
#------------------------------------------------------------------------

from dotenv import load_dotenv 
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_astradb import AstraDBVectorStore
import os
from langchain_groq import ChatGroq

load_dotenv()

chat_history = []
store = {}

#------------------------------------------------------------------------
# Getting new Vector Store and also get secret keys with model
#------------------------------------------------------------------------

embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-base-en-v1.5")
astra_db_end_point = os.getenv("astra_db_end_point")
astra_db_app_token = os.getenv("astra_db_token")
namespace_astra_db = os.getenv("astra_db_keyspace")


vector_store = AstraDBVectorStore(
    embedding=embeddings,
    api_endpoint=astra_db_end_point,
    token=astra_db_app_token,
    collection_name="flipkart",
    namespace=namespace_astra_db
)

# ----------------------------
# GLOBAL MEMORY STORE (IMPORTANT)
# ----------------------------
store = {}


def generation(vector_store = vector_store):
    """
    Returns a history-aware RAG chain with memory.
    Store is kept global outside so memory persists across calls.
    """
    groq_api = os.getenv("groq_api")
    print("----"*30)
    print(groq_api)
    model = ChatGroq(api_key=groq_api , model = "llama-3.3-70b-versatile")
    # --- Prompts ---
    retriever_prompt = (
        "Given a chat history and the latest user question which might reference context in the chat history, "
        "formulate a standalone question which can be understood without the chat history. "
        "Do NOT answer the question, just reformulate it if needed and otherwise return it as is."
    )

    contexulized_q_prompt = ChatPromptTemplate.from_messages([
        ("system", retriever_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}")
    ])

    PRODUCT_BOT_TEMPLATE = """
    Your ecommercebot bot is an expert in product recommendations and customer queries.
    It analyzes product titles and reviews to provide accurate and helpful responses.
    Ensure your answers are relevant to the product context and refrain from straying off-topic.
    Your responses should be concise and informative.

    CONTEXT:
    {context}

    QUESTION: {input}

    YOUR ANSWER:
    """

    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", PRODUCT_BOT_TEMPLATE),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}")
    ])

    retriever = vector_store.as_retriever(search_kwargs={"k": 3})

    # --- Condense question chain ---
    condense_question_chain = contexulized_q_prompt | model | StrOutputParser()

    def retrieve_documents(inputs):
        if inputs.get("chat_history"):
            standalone_question = condense_question_chain.invoke({
                "chat_history": inputs["chat_history"],
                "input": inputs["input"]
            })
        else:
            standalone_question = inputs["input"]

        return retriever.invoke(standalone_question)

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    # --- RAG Chain ---
    rag_chain = (
        RunnablePassthrough.assign(
            context=RunnableLambda(retrieve_documents) | format_docs
        )
        | RunnablePassthrough.assign(
            answer=qa_prompt | model | StrOutputParser()
        )
    )

    # --- Session history ---
    def get_session_history(session_id: str) -> BaseChatMessageHistory:
        if session_id not in store:
            store[session_id] = ChatMessageHistory()
        return store[session_id]

    chain_with_memory = RunnableWithMessageHistory(
        rag_chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key="answer",
    )

    return chain_with_memory

# if __name__ == "__main__":
#     chain_with_memory = generation()

#     print("+"*60)
#     print(store)

#     ans = chain_with_memory.invoke({
#         "input": "can you tell me the best bluetooth buds?"},
#         config={
#             "configurable": {"session_id": "Paras"}
#         }
#     )["answer"]

#     print(ans)
#     print("+"*60)
#     print(store)
    
#     print("*"*100)

#     ans = chain_with_memory.invoke({
#         "input": "what is my previous question?"},
#         config={
#             "configurable": {"session_id": "Paras"}
#         }
#     )["answer"]
#     print(ans)
#     print("+"*60)
#     print(store)