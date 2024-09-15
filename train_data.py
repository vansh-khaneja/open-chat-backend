
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from langchain.schema import Document # import Document class
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import string
import random


import os
from dotenv import load_dotenv

load_dotenv()

QDRANT_API_KEY = os.getenv('QDRANT_API_KEY')
QDRANT_URL = os.getenv('QDRANT_URL')


# app = FastAPI()

# Add CORS middleware to allow requests from specific origins
# origins = [
#     "http://localhost:3000",  # Add your frontend URL here
#     "http://example.com",   
#     "https://open-chatt.vercel.app",   # You can add multiple URLs
# ]

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,  # List of allowed origins
#     allow_credentials=True,
#     allow_methods=["*"],  # Allow all HTTP methods (POST, GET, etc.)
#     allow_headers=["*"],  # Allow all headers
# )
small_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

class TextInput(BaseModel):
    text: str

def generate_alphanumeric(length=7):
    characters = string.ascii_letters + string.digits  # A-Z, a-z, 0-9
    return ''.join(random.choices(characters, k=length))


# @app.post("/text/")
def db_gen(input_text):
    alphanumeric_number = generate_alphanumeric()
    
    docs = [Document(page_content=input_text)]

    chunk_size = 150
    chunk_overlap = 50

    r_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )

# Split the input text into chunks
    refund_splits = r_splitter.split_documents(docs)

# Extract page content from the splits
    chunks = [doc.page_content for doc in refund_splits]
    vectors = small_model.encode(chunks)

    client = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
    )

    # Recreate the collection if it already exists
    client.create_collection(
        collection_name=alphanumeric_number,
        vectors_config=VectorParams(size=len(vectors[0]), distance=Distance.COSINE),
    )

    # Prepare payload
    payload = [{"text": i} for i in chunks]

    # Upload the collection
    client.upload_collection(
        collection_name=alphanumeric_number,
        ids=[i for i in range(len(chunks))],
        vectors=vectors,
        payload=payload  
    )

    print("DATA UPLOADED !!!!")
    return alphanumeric_number
