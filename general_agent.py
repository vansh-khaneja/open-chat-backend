from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Qdrant
from langchain_community.embeddings.huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
import numpy as np
from scipy.spatial.distance import cosine
from utils import rephrase_ans,fetch_api_data,fetch_all_data
from sentence_transformers import CrossEncoder
rankmodel = CrossEncoder("jinaai/jina-reranker-v1-tiny-en")
large_model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
small_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
import os
from dotenv import load_dotenv

load_dotenv()

QDRANT_API_KEY = os.getenv('QDRANT_API_KEY')
QDRANT_URL = os.getenv('QDRANT_URL')

general = 0

import os




client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
)




def general_data_retrieve(state):
    global general
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
    print(api_key)

    data = fetch_all_data()

    user_data = fetch_api_data(data,api_key)
    print(data)
    print("+++this ss",user_data)
    selected_features = user_data["selectedFeatures"]
    db_name = user_data["db_name"]
    advance_features = user_data["selectedAdvancedFeatures"]

    if("General" in selected_features):
        general = 1


    if("Reranking" in advance_features):
        reranking = 1
    else:
        reranking = 0


    if("Hybrid search" in advance_features):
        hybrid_search = 1
    else:
        hybrid_search=0


    # # Retrieval
    # ques_vector = small_model.encode(question)

    # result = client.search(
    # collection_name="bac",
    # query_vector = ques_vector,
    # limit=4
    # )
    answer_list_unranked = []
    if(general==0):
        return {"answer": "Subscriber hasn't purchased this feature yet", "question": question}
    
    if(hybrid_search==0):
        answer_list_unranked = normal_search(question,db_name)

        finanl_list = []

        if (reranking==0):
            finanl_list =answer_list_unranked
        else:
            answer_list_reranked = rerank(answer_list_unranked,question)
            finanl_list = answer_list_reranked
    
    else:
        answer_list_unranked = multi_stage(question,db_name)
        if (reranking==0):
            finanl_list = answer_list_unranked
        else:
            answer_list_reranked = rerank(answer_list_unranked,question)
            finanl_list = answer_list_reranked

    
    rephrased_ans = rephrase_ans(question,str(finanl_list),api_key)
    return {"question":question,"answer":rephrased_ans}



 
    



def rerank (unranked_array,question):
    print("===RERANKING===")

    results = rankmodel.rank(question, unranked_array, return_documents=True, top_k=4)
    reranked_list = []
    reranked_list = []
    for i in range(0,4):
        reranked_list.append(results[i]['text'])

    

    return reranked_list



def multi_stage(question,db_name):
    
    print("===HYBRID SEARCH ===")
    small_ques_vector = small_model.encode(question)
    large_ques_vector = large_model.encode(question)


    result = client.search(
    collection_name=db_name,
    query_vector = small_ques_vector,
    limit=10
    )

    texts = []
    large_emb = []
    for r in result:
        texts.append(r.payload["text"])
        large_emb.append(large_model.encode(r.payload["text"]))


    cosine_similarities = []
    for embedding in large_emb:
        similarity = 1 - cosine(large_ques_vector, embedding)  # cosine() returns distance, so subtract from 1
        cosine_similarities.append(similarity)

    top_4_indices = np.argsort(cosine_similarities)[-4:][::-1]

    final_list = []
    for i in top_4_indices:
        final_list.append(texts[i])

    return final_list

    


def normal_search(question,db_name):
    print("===NORMAL SEARCH===")
    ques_vector = small_model.encode(question)

    result = client.search(
    collection_name=db_name,
    query_vector = ques_vector,
    limit=4
    )

    final_list = []
    for r in result:
        final_list.append(r.payload["text"])

    return final_list


    



# print(refund_data_retrieve({"question":"what items are not refundable"}))