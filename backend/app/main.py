from fastapi import FastAPI
from fastapi import Query
import requests
import os
from dotenv import load_dotenv
from openai import OpenAI
from fastapi import Body

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "CodeMentor AI backend is running 🚀"}

@app.get("/health")
def health():
    return {"status": "ok"}

from fastapi import Query
import requests

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
    prompt = f"""
You are a DSA mentor.

Problem:
{problem['title']}

Description:
{problem['description']}

User Code:
{problem['code']}

Give feedback on:
1. Correctness
2. Time & Space Complexity
3. How to improve
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
    )

    return {"review": response.choices[0].message.content}