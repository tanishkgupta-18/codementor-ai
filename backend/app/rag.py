import os
import hashlib
import json
import redis
from dotenv import load_dotenv

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

NOTES_PATH = "backend/knowledge/dsa_notes.txt"
INDEX_PATH = "backend/app/faiss_index"

# Valkey for RAG cache (DB 3)
r = redis.Redis(host="localhost", port=6379, db=3)


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


# ----------- NEW: Cached similarity search -----------

vectorstore = load_vectorstore()


def get_cached_context(query: str) -> str:
    query_hash = hashlib.sha256(query.encode()).hexdigest()
    cache_key = f"rag_query:{query_hash}"

    cached = r.get(cache_key)
    if cached:
        return cached.decode()

    # Do expensive FAISS search
    docs = vectorstore.similarity_search(query, k=4)
    context = "\n\n".join([d.page_content for d in docs])

    # Store in cache for 1 day
    r.set(cache_key, context, ex=86400)

    return context
