# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
from utils import execute_query, rephrase_ans, find_order_id
from langchain_groq import ChatGroq
from langchain_community.utilities import ArxivAPIWrapper, WikipediaAPIWrapper
from langchain_community.tools import ArxivQueryRun, WikipediaQueryRun
# from fastapi import FastAPI
from langgraph.graph import END, StateGraph, START
from flask import Flask, request, jsonify
from flask_cors import CORS
# import order_agent
# import product_agent
import user_agent
import greeting_agent
import general_agent

import greeting_agent

from typing import Literal

import train_data
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field

import issue_redirect


import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv('GROQ_API_KEY')

greeting = 0
user = 0
issue = 0
app = Flask(__name__)


CORS(app)
class RouteQuery(BaseModel):
    """Route a user query to the most relevant datasource."""
    datasource: Literal[
        "greeting_query",
        "general_query",
        "user_query",
        "issue_query"
    ] = Field(
        ...,
        description="Given a user question, choose to route it to greeting_query, general_query, user_query, or issue_query."
    )

# app = FastAPI()

# # Add CORS Middleware
# origins = [
#     "http://127.0.0.1:5500"
# ]

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,  # Allow your frontend to access the backend
#     allow_credentials=True,
#     allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
#     allow_headers=["*"],  # Allow all headers
# )

llm = ChatGroq(groq_api_key=GROQ_API_KEY, model_name="llama-3.1-70b-versatile")
structured_llm_router = llm.with_structured_output(RouteQuery)

# Prompt
system = """You are an expert at routing a user question to a product_query, order_status, refund_query, or wikipedia.
The greeting_query is for greetings like hi, hello, thanks, bye, who are you etc.
The general_query is for any queries related to the company, companies work company policies and all the general information staff related refund related and all other like this is basically the major data etc.
The issue_query is for any query related to unresolved issues or when users say pass this to the support team or say this issue is not yet resolver or not clear.
The user_query is for issues related to account management like username, password,email etc etc.
Use the greeting_query,user_query,general_query,issue_query . Otherwise general_query."""
route_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "{question}"),
    ]
)

question_router = route_prompt | structured_llm_router
print("\nAGENTS INITIATED ...")


api_wrapper = WikipediaAPIWrapper(top_k_results=1, doc_content_chars_max=200)
wiki = WikipediaQueryRun(api_wrapper=api_wrapper)

print("\nWIKI WRAPPER CREATED ...")

from typing_extensions import TypedDict

class GraphState(TypedDict):
    question: str
    api_key:str
    generation: str
    answer: str

def route_question(state):
    print("AGENT NEEDED FINIDING AGENT...")
    question = state["question"]
    source = question_router.invoke({"question": question})

    if source.datasource == "greeting_query":
        print("---ROUTE QUESTION TO GREETING AGENT---")
        return "greeting_query"
    
    elif source.datasource == "general_query":
        print("---ROUTE QUESTION TO GENERAL AGENT---")
        return "general_query"
    
    elif source.datasource == "user_query":
        print("\nROUTing QUESTION TO USER AGENT...")
        return "user_query"
    
    elif source.datasource == "issue_query":
        print("---ROUTE QUESTION TO ISSUE AGENT---")
        return "issue_query"
    

workflow = StateGraph(GraphState)

workflow.add_node("user_data_retrieve", user_agent.user_data_retrieve)
workflow.add_node("greeting_data_retrieve", greeting_agent.greeting_data_retrieve)
workflow.add_node("general_data_retrieve", general_agent.general_data_retrieve)
workflow.add_node("issue_data_retrieve", issue_redirect.issue_data_retrieve)

workflow.add_conditional_edges(
    START,
    route_question,
    {
        "greeting_query": "greeting_data_retrieve",
        "general_query": "general_data_retrieve",
        "user_query": "user_data_retrieve",
        "issue_query": "issue_data_retrieve",
    },
)

workflow.add_edge("greeting_data_retrieve", END)
workflow.add_edge("general_data_retrieve", END)
workflow.add_edge("user_data_retrieve", END)
workflow.add_edge("issue_data_retrieve", END)

appi = workflow.compile()

def generate_ans(question,api_key):
    inputs = {"question": question,"api_key":api_key}
    for output in appi.stream(inputs):
        for key, value in output.items():
            print(f"\nUsing Node '{key}'...")
    return value["answer"]




class TextInput(BaseModel):
    query: str
    api_key: str


@app.route("/query/", methods=["POST"])
def echo_text():
    input_text = request.json.get("query")
    api_key = request.json.get("api_key")
    ans = generate_ans(input_text, api_key)  # Ensure generate_ans is not async in Flask
    return jsonify({"query": input_text, "response": ans})


@app.route("/query", methods=["OPTIONS"])
def handle_options():
    return jsonify({'status': 'OK'}), 200

@app.route("/text", methods=["POST"])
def echo():
    input_text = request.json.get("text")
    db_name = train_data.db_gen(input_text)
    return {"db_name": db_name}



# Run Flask Application
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)



# chat_history = []

# print("Ready to launch")

# @app.get("/")
# def read_root():
#     return {"Hello": "World"}

# @app.post("/submit/")
# async def submit_data(ques: dict):
#     ques = str(ques)
#     print("Data received:", ques)
#     chat_history.append("User: " + ques)

#     if question_router.invoke({"question": ques}).datasource in ["order_query", "product_query", "user_query", "issue_query"]:
#         sql_or_doc = generate_ans(str(chat_history))
#         ans = execute_query(sql_or_doc)
#         rephrase_answer = rephrase_ans(ques, ans)
#         chat_history.append("Bot: " + rephrase_answer)
#         print(rephrase_answer)
#         return {"message": "Data received successfully!", "data": rephrase_answer}
#     elif question_router.invoke({"question": ques}).datasource in ["greet_query"]:
#         sql_or_doc = generate_ans(str(chat_history))
#         chat_history.append("Bot: " + sql_or_doc)
#         print(sql_or_doc)
#         return {"message": "Data received successfully!", "data": sql_or_doc}
#     else:
#         sql_or_doc = generate_ans(str(chat_history))
#         rephrase_answer = rephrase_ans(ques, sql_or_doc)
#         chat_history.append("Bot: " + rephrase_answer)
#         print(rephrase_answer)
#         return {"message": "Data received successfully!", "data": rephrase_answer}

# ques = "BUT the issue is MY NAME IS NOT UPDATED YET"
# print(question_router.invoke({"question": ques}).datasource)