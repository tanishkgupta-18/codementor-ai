from fastapi import FastAPI, Query, Body, Depends
import requests
import os
from dotenv import load_dotenv
from openai import OpenAI
from backend.app.db import reviews
from backend.app.auth import hash_password, verify_password, create_token
from backend.app.db import users
from backend.app.auth import get_current_user
from datetime import datetime
from backend.app.agents import build_graph
from backend.app.heatmap import topic_heatmap

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
graph = build_graph()

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "CodeMentor AI backend is running"}


@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/register")
def register(data: dict):
    if users.find_one({"email": data["email"]}):
        return {"error": "User already exists"}

    users.insert_one({
        "email": data["email"],
        "password": hash_password(data["password"])
    })

    return {"message": "User registered"}


@app.post("/login")
def login(data: dict):
    user = users.find_one({"email": data["email"]})
    if not user or not verify_password(data["password"], user["password"]):
        return {"error": "Invalid credentials"}

    token = create_token({"email": user["email"]})
    return {"token": token}

@app.get("/fetch-problem")
def fetch_problem(slug: str = Query(...)):
    url = "https://leetcode.com/graphql"

    query = """
    query getQuestion($titleSlug: String!) {
      question(titleSlug: $titleSlug) {
        title
        content
        topicTags {
          name
        }
      }
    }
    """

    variables = {"titleSlug": slug}

    res = requests.post(url, json={"query": query, "variables": variables})
    data = res.json()["data"]["question"]

    topics = [tag["name"] for tag in data["topicTags"]]

    return {
        "title": data["title"],
        "description": data["content"][:1200],
        "topics": topics
    }


@app.post("/review-code")
def review_code(
    problem: dict = Body(...),
    user_id: str = Depends(get_current_user)
):
    result = graph.invoke({
        "title": problem["title"],
        "description": problem["description"],
        "code": problem["code"],
        "context": "",
        "review": ""
    })

    review_text = result["review"]

    # Extract pattern from review
    pattern_line = review_text.split("PATTERN:")[1].split("\n")[0].strip()

    reviews.insert_one({
        "user_id": user_id,
        "title": problem["title"],
        "topics": problem.get("topics", []),
        "pattern": pattern_line,
        "review": review_text,
        "date": datetime.utcnow()
    })

    return {"review": review_text}

@app.get("/heatmap")
def get_heatmap(user_id: str = Depends(get_current_user)):
    return topic_heatmap(user_id)