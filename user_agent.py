from groq import Groq
from utils import fetch_api_data,fetch_all_data
from  utils import execute_query,rephrase_ans

import json

user = 0

# Load the JSON data from file
import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv('GROQ_API_KEY')

client = Groq(api_key=GROQ_API_KEY)

client = Groq(api_key=GROQ_API_KEY)
table_name = "customers"



def fetch_user(query,url):
    columns =execute_query(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table_name}';",url)
    array = []
    for i in columns:
        array.append(i[0])

    column_name = str(array)
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "you are text to sql bot which given sql command should mandotarly be in single line just give sql query and nothing else"
            },
            {
                "role": "user",
                "content": f"Write a SQL Query given the table name {table_name} and columns as a list {column_name} for the given last question in this chat_history: {query}",
            }
        ],

        model="llama-3.1-8b-instant",
        temperature=0.5,
    )
    return chat_completion.choices[0].message.content

def user_data_retrieve(state):
    global user  # Reference the global variable 'user'
    
    print("sUt")
    """
    Retrieve documents

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, documents, that contains retrieved documents
    """
    print("---RETRIEVE---")
    question = state["question"]
    api_key = state["api_key"]
    data = fetch_all_data()

    user_data = fetch_api_data(data, api_key)

    # Accessing different parts of the data
    selected_features = user_data["selectedFeatures"]
    
    postgresUrl = user_data["postgresUrl"]

    if ("User data" in selected_features):
        user = 1  # Set the global 'user' variable

    if user == 0:
        return {"answer": "Subscriber hasn't purchased this feature yet", "question": question}
    
    # Retrieval
    ans = fetch_user(question,postgresUrl)
    answer = rephrase_ans(question, execute_query(ans,postgresUrl) + "this is response from the database",api_key)
    
    return {"answer": answer, "question": question}
# print(fetch_user("Change name to vansh khaneja for user id 104"))