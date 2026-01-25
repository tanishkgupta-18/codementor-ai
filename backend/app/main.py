from fastapi import FastAPI, Query, Body
import requests
import os
from dotenv import load_dotenv
from openai import OpenAI
from backend.app.db import reviews

from backend.app.agents import build_graph

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
def review_code(problem: dict = Body(...)):
    result = graph.invoke({
        "title": problem["title"],
        "description": problem["description"],
        "code": problem["code"],
        "context": "",
        "review": ""
    })

    reviews.insert_one({
        "title": problem["title"],
        "topics": problem.get("topics", []),
        "review": result["review"]
    })

    return {"review": result["review"]}
