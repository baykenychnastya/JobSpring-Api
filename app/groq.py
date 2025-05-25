import os
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_community.vectorstores import FAISS
from langchain_groq import ChatGroq
from langchain.chains import RetrievalQA

from app.get_embedding_function import get_embedding_function

CUSTOM_PROMPT_TEMPLATE = """
Use the following pieces of context to answer the user question. If you
don't know the answer, just say that you don't know, don't try to make up an
answer.

{context}

Question: {question}

Please provide your answer in the following JSON format: 
{{
    "answer": "Your detailed answer here",
    "sources": "Direct sentences or paragraphs from the context that support 
        your answers. ONLY RELEVANT TEXT DIRECTLY FROM THE DOCUMENTS. DO NOT 
        ADD ANYTHING EXTRA. DO NOT INVENT ANYTHING."
}}

The JSON must be a valid json format and can be read with json.loads() in
Python. Answer:
"""

CUSTOM_PROMPT = PromptTemplate(
    template=CUSTOM_PROMPT_TEMPLATE, input_variables=["context", "question"]
)


def setup_qa_system(text_chunks):
    try:
        vector_store = FAISS.from_documents(text_chunks, get_embedding_function())
        retriever = vector_store.as_retriever(
            search_type="mmr", search_kwargs={"k": 2, "fetch_k": 4}
        )

        return RetrievalQA.from_chain_type(
            initialize_language_model(),
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": CUSTOM_PROMPT},
        )
    except Exception as e:
        raise  Exception(f"Error setting up QA system: {str(e)}")
    
def initialize_language_model():
    load_dotenv()
    return ChatGroq(
        temperature=0,
        groq_api_key=os.getenv("GROQ_API_KEY"),
        model_name="llama-3.1-8b-instant"
    )
