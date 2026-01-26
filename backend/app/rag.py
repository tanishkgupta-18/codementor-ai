import os
from dotenv import load_dotenv

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

NOTES_PATH = "backend/knowledge/dsa_notes.txt"
INDEX_PATH = "backend/app/faiss_index"


def build_vectorstore():
    with open(NOTES_PATH, "r", encoding="utf-8") as f:
        text = f.read()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150
    )

    documents = splitter.create_documents([text])

    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

    vectorstore = FAISS.from_documents(documents, embeddings)
    vectorstore.save_local(INDEX_PATH)


def load_vectorstore():
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

    return FAISS.load_local(
        INDEX_PATH,
        embeddings,
        allow_dangerous_deserialization=True
    )
