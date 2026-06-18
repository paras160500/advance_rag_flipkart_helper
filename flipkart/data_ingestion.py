# This will ingest the data into the Astra DB.

#------------------------------------------------------------------------
# Import Statements
#------------------------------------------------------------------------

import os
from dotenv import load_dotenv
load_dotenv()
from langchain_community.embeddings import HuggingFaceEmbeddings
from astrapy import DataAPIClient
from langchain_astradb import AstraDBVectorStore


#------------------------------------------------------------------------
# Secerets of Database and the embedding variable
#------------------------------------------------------------------------

embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-base-en-v1.5")
astra_db_end_point = os.getenv("astra_db_end_point")
astra_db_app_token = os.getenv("astra_db_token")
namespace_astra_db = os.getenv("astra_db_keyspace")


#------------------------------------------------------------------------
# Main logic of 
#------------------------------------------------------------------------

def ingest_data_to_database(docs):
    client = DataAPIClient(astra_db_app_token)
    db = client.get_database_by_api_endpoint(astra_db_end_point)

    collection_name = "flipkart"

    # Collection doesn't exist -> create it and ingest
    if collection_name not in db.list_collection_names():

        print("Collection not found. Creating collection and ingesting data...")
        try:
            AstraDBVectorStore.from_documents(
                documents=docs,
                embedding=embeddings,
                api_endpoint=astra_db_end_point,
                token=astra_db_app_token,
                collection_name=collection_name,
                namespace=namespace_astra_db
            )

            print("Data ingestion completed.")
            return
        except Exception as e:
            print("Data Ingestion Issue :- " , str(e))

    # Collection exists
    collection = db.get_collection(collection_name)

    if collection.find_one({}):
        print("Data already exists.")
        return
    else:
        print("Collection exists but is empty. Ingesting data...")
        try:
            AstraDBVectorStore.from_documents(
                documents=docs,
                embedding=embeddings,
                api_endpoint=astra_db_end_point,
                token=astra_db_app_token,
                collection_name=collection_name,
                namespace=namespace_astra_db
            )
            print("Data ingestion completed.")
        except Exception as e:
            print("Collection is there but the issue is about pushing data into that collection :- " , str(e))
