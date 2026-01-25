import os
from dotenv import load_dotenv
load_dotenv()

from langchain_text_splitters import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings


def build_vectorstore():
    with open("backend/knowledge/dsa_notes.txt", "r") as f:
        text = f.read()

    splitter = CharacterTextSplitter(chunk_size=300, chunk_overlap=50)
    docs = splitter.create_documents([text])

    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(docs, embeddings)
    vectorstore.save_local("backend/faiss_index")


def load_vectorstore():
    embeddings = OpenAIEmbeddings()
    return FAISS.load_local("backend/faiss_index", embeddings, allow_dangerous_deserialization=True)
