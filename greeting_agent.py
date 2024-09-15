from groq import Groq
from utils import fetch_api_data,fetch_all_data




import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv('GROQ_API_KEY')
client = Groq(api_key=GROQ_API_KEY)


import json

# Load the JSON data from file
# Accessing different parts of the data



greeting=0


model_name = ""



def fetch_general(query,Chat_bot_name,Chat_bot_company,model):

    # last_query = string_to_list(query)[-1]
   # print("\n\n\n\n",last_query,"\n\n\n\n")
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": f"you are a expert greeting assistant for the company {Chat_bot_company} and your usage is for eccommerce customer support your name is {Chat_bot_name}."
            },
            {
                "role": "user",
                "content": f"This is {query} given by customer respond to this  and act formally as such you are from customer support  just give the reply and nothing else",
            }
        ],

        model=model,
        temperature=0.5,
    )
    return chat_completion.choices[0].message.content

def greeting_data_retrieve(state):
    global greeting
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

    user_data = fetch_api_data(data,api_key)
    bot_name = user_data["botName"]
    company_name = user_data["companyName"]
    selected_features = user_data["selectedFeatures"]

    if("Greeting" in selected_features):
        greeting = 1

    if(user_data["selectedModel"] =="Llama 3"):
        model_name = "llama3-8b-8192"
    elif(user_data["selectedModel"] =="Llama 3.1"):
        model_name = "llama-3.1-70b-versatile"
    else:
        model_name = "mixtral-8x7b-32768"




    # Retrieval
    if(greeting==0):
        return {"answer": "Subscriber hasn't purchased this feature yet", "question": question}
    answer = fetch_general(question,bot_name,company_name,model_name)
    return {"answer": answer, "question": question}


import ast

def string_to_list(conversation_str):
    try:
        # Convert the string representation back to a list
        conversation_list = ast.literal_eval(conversation_str)
        print(conversation_list[-1])
        return conversation_list
    except Exception as e:
        print(e)
        return str(e)
    

# print(fetch_general("who are you"))