from fastapi import FastAPI, Query, Depends
from pydantic import BaseModel
from typing import List
import requests
import uuid
import redis
from datetime import datetime, timezone

from workers.review_task import review_code_task
from backend.app.db import users, redo_list, revision_queue, reviews
from backend.app.auth import (
    hash_password,
    verify_password,
    create_token,
    get_current_user,
)
from backend.app.heatmap import topic_heatmap
from backend.app.flashcards import get_flashcards

app = FastAPI()

# Valkey / Redis (review status DB)
r = redis.Redis(host="localhost", port=6379, db=1)


# ---------- Request Model ----------
class ReviewRequest(BaseModel):
    code: str
    title: str
    description: str
    topics: List[str]


# ---------- AUTH ----------
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


# ---------- FETCH PROBLEM ----------
@app.get("/fetch-problem")
def fetch_problem(slug: str = Query(...)):
    url = "https://leetcode.com/graphql"
    query = """
    query getQuestion($titleSlug: String!) {
      question(titleSlug: $titleSlug) {
        title
        content
        topicTags { name }
      }
    }
    """
    res = requests.post(url, json={"query": query, "variables": {"titleSlug": slug}})
    q = res.json()["data"]["question"]

    if not q:
        return {"error": "Problem not found"}

    return {
        "title": q["title"],
        "description": q["content"] or "",
        "topics": [t["name"] for t in q["topicTags"]]
    }


# ---------- REVIEW CODE (ASYNC WITH CELERY) ----------
@app.post("/review_code")
def review_code(req: ReviewRequest, user_id: str = Depends(get_current_user)):
    review_id = str(uuid.uuid4())

    review_code_task.delay(
        review_id,
        req.code,
        user_id,
        req.title,
        req.description,
        req.topics
    )

    return {"review_id": review_id, "status": "PROCESSING"}


# ---------- REVIEW STATUS (POLLING) ----------
@app.get("/review_status/{review_id}")
def review_status(review_id: str):
    status = r.get(f"review:{review_id}")

    if not status:
        return {"status": "NOT_FOUND"}

    if status.decode() == "DONE":
        result = r.get(f"review:{review_id}:result").decode()
        return {"status": "DONE", "result": result}

    return {"status": "PROCESSING"}


# ---------- ANALYTICS ----------
@app.get("/heatmap")
def get_heatmap(user_id: str = Depends(get_current_user)):
    return topic_heatmap(user_id)


@app.get("/flashcards")
def flashcards(user_id: str = Depends(get_current_user)):
    return get_flashcards(user_id)


@app.get("/revision-today")
def revision_today(user_id: str = Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    return list(
        revision_queue.find(
            {"user_id": user_id, "next_revision": {"$lte": now}},
            {"_id": 0}
        ).sort("next_revision", 1)
    )


@app.get("/redo-list")
def get_redo_list(user_id: str = Depends(get_current_user)):
    return list(redo_list.find({"user_id": user_id}, {"_id": 0}))


@app.delete("/redo-list/{slug}")
def remove_redo(slug: str, user_id: str = Depends(get_current_user)):
    redo_list.delete_one({"user_id": user_id, "slug": slug})
    return {"message": "Removed"}


@app.get("/mistake-history")
def mistake_history(user_id: str = Depends(get_current_user)):
    pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {"_id": "$pattern", "count": {"$sum": 1}}},
        {"$project": {"pattern": "$_id", "count": 1, "_id": 0}},
        {"$sort": {"count": -1}}
    ]
    return list(reviews.aggregate(pipeline))


@app.get("/pattern-stats")
def pattern_stats(user_id: str = Depends(get_current_user)):
    pipeline = [
        {"$match": {"user_id": user_id}},
        {
            "$group": {
                "_id": "$pattern",
                "count": {"$sum": 1},
                "last_date": {"$max": "$date"}
            }
        },
        {"$project": {"pattern": "$_id", "count": 1, "last_date": 1, "_id": 0}},
        {"$sort": {"count": -1}}
    ]

    data = list(reviews.aggregate(pipeline))

    for d in data:
        if d["count"] >= 4:
            d["status"] = "Critical"
        elif d["count"] >= 2:
            d["status"] = "Weak"
        else:
            d["status"] = "Improving"

    return data
