from fastapi import FastAPI, Query, Body, Depends
import requests
import os
import re
from dotenv import load_dotenv
from datetime import datetime, timezone

from backend.app.patterns import normalize_pattern
from backend.app.db import reviews, users, redo_list, revision_queue
from backend.app.auth import (
    hash_password,
    verify_password,
    create_token,
    get_current_user,
)
from backend.app.agents import build_graph
from backend.app.heatmap import topic_heatmap
from backend.app.flashcards import get_flashcards
from backend.app.spaced import next_date

load_dotenv()
graph = build_graph()
app = FastAPI()


# ---------- helpers ----------
def extract(field, text):
    pattern = rf"{field}:\s*(.+)"
    match = re.search(pattern, text)
    return match.group(1).strip() if match else "Unknown"


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
    data = res.json()["data"]["question"]

    return {
        "title": data["title"],
        "description": data["content"][:1200],
        "topics": [t["name"] for t in data["topicTags"]]
    }


# ---------- REVIEW CODE ----------
@app.post("/review-code")
def review_code(problem: dict = Body(...), user_id: str = Depends(get_current_user)):
    result = graph.invoke({
        "title": problem["title"],
        "description": problem["description"],
        "code": problem["code"],
        "context": "",
        "review": ""
    })

    review_text = result["review"]

    if "NO_MISTAKE" in review_text:
        return {"review": "Your solution is already optimal. No mistakes detected."}

    pattern = normalize_pattern(extract("PATTERN", review_text))
    mistake = extract("MISTAKE", review_text)
    now = datetime.now(timezone.utc)

    # spaced repetition
    rq = revision_queue.find_one({"user_id": user_id, "pattern": pattern})
    if not rq:
        revision_queue.insert_one({
            "user_id": user_id,
            "pattern": pattern,
            "level": 1,
            "next_revision": next_date(1)
        })
    else:
        if rq["next_revision"].date() != now.date():
            level = min(rq["level"] + 1, 4)
            revision_queue.update_one(
                {"_id": rq["_id"]},
                {"$set": {"level": level, "next_revision": next_date(level)}}
            )

    # save review
    reviews.insert_one({
        "user_id": user_id,
        "title": problem["title"],
        "topics": problem.get("topics", []),
        "pattern": pattern,
        "review": review_text,
        "date": now
    })

    # redo list
    if not redo_list.find_one({"user_id": user_id, "title": problem["title"]}):
        redo_list.insert_one({
            "user_id": user_id,
            "title": problem["title"],
            "slug": problem["title"].lower().replace(" ", "-"),
            "pattern": pattern,
            "mistake": mistake,
            "added_on": now
        })

    return {"review": review_text}


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
