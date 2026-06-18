from flask import Flask,render_template,jsonify,request
from dotenv import load_dotenv
import os 

from flipkart.retrieval_generation import generation
from langchain_groq import ChatGroq

os.environ['GROQ_API_KEY'] = os.getenv("groq_api")
model = ChatGroq( model = "llama-3.3-70b-versatile")

chain = generation()

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("chat.html")

@app.route("/get" , methods = ['POST' , 'GET'])
def chat():
    if request.method == "POST":
        msg = request.form['msg']
        input = msg

        result = chain.invoke(
            {'input' : input},
            config={'configurable' : {'session_id' : 'Paras'}}
        )['answer']

        return str(result)

if __name__ == "__main__":
    app.run(host = "0.0.0.0" , port = 5000 , debug = True)