import os
from groq import Groq
import firebase_admin
from firebase_admin import credentials, firestore
cred = credentials.Certificate('openchat-c8c21-firebase-adminsdk-bigc7-8a378609ab.json')

import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv('GROQ_API_KEY')

client = Groq(api_key=GROQ_API_KEY)
firebase_admin.initialize_app(cred)
db = firestore.client()


import psycopg2
import os

# Retrieve credentials from environment variables or directly input them
def fetch_all_data():
    data = []
    users_ref = db.collection('users')
    docs = users_ref.stream()
    for doc in docs:
        doc_data = doc.to_dict()
        data.append(doc_data)
    return data


def fetch_api_data(data,api_key):
    for doc in data:
        if 'api_key' in doc and doc['api_key'] == api_key:
            return doc
    return None




model_name = ""




def execute_query(query,url):
    conn = psycopg2.connect(
        url
    )

    # Create a cursor
    cursor = conn.cursor()

    try:
        # Execute the query
        cursor.execute(query)

        # Commit the changes for non-SELECT queries (like UPDATE)
        conn.commit()

        # Check if the query is SELECT and fetch rows
        if query.strip().lower().startswith('select'):
            rows = cursor.fetchall()
            return rows if rows else "No data found."
        else:
            return "Command executed successfully."

    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        cursor.close()
        conn.close()


def rephrase_ans(question,response,api_key):
    data = fetch_all_data()

    user_data = fetch_api_data(data,api_key)
    print("user",user_data)
    company_name = user_data["companyName"]
    selected_features = user_data["selectedFeatures"]


    if(user_data["selectedModel"] =="Llama 3"):
        model_name = "llama3-8b-8192"
    elif(user_data["selectedModel"] =="Llama 3.1"):
        model_name = "llama-3.1-70b-versatile"
    else:
        model_name = "mixtral-8x7b-32768"
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": f"you are text to ecommerce customer support assisant for {company_name}"
            },
            {
                "role": "user",
                "content": f"This is the question {question} given by customer and this the database response {response} for the given question rephrase the answer based on the question.",
            }
        ],

        model=model_name,
        temperature=0.5,
    )
    return chat_completion.choices[0].message.content

import re
def find_order_id(text):
    # Regular expression to find an order ID (a sequence of digits)
    match = re.search(r'\b\d{4}\b', text)
    if match:
        return 0
    else:
        return 1




