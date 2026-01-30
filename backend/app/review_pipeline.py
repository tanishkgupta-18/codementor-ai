from datetime import datetime, timezone
from backend.app.patterns import normalize_pattern
from backend.app.db import reviews, redo_list, revision_queue
from backend.app.spaced import next_date
from backend.app.agents import build_graph
import re
import os
import hashlib
import json
import redis

graph = build_graph()

# Valkey
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
r = redis.Redis(host=REDIS_HOST, port=6379, db=1)


def extract(field, text):
    pattern = rf"{field}:\s*(.+)"
    match = re.search(pattern, text)
    return match.group(1).strip() if match else "Unknown"


def run_full_review_pipeline(code, user_id, title, description, topics):
    # ---------- REVIEW CACHE ----------
    code_hash = hashlib.sha256(code.encode()).hexdigest()
    review_cache_key = f"review_cache:{user_id}:{code_hash}"

    cached_review = r.get(review_cache_key)
    if cached_review:
        return json.loads(cached_review)

    # ---------- RAG CACHE (by title/problem) ----------
    rag_cache_key = f"rag_cache:{title}"
    cached_context = r.get(rag_cache_key)

    if cached_context:
        context_to_use = cached_context.decode()
    else:
        context_to_use = description

    # ---------- ACTUAL REVIEW ----------
    result = graph.invoke({
        "title": title,
        "description": description,
        "code": code,
        "context": context_to_use,
        "review": ""
    })

    review_text = result["review"]

    # store RAG context for future runs
    if not cached_context:
        r.set(rag_cache_key, description, ex=86400)

    if "NO_MISTAKE" in review_text:
        final_result = {"review": "Your solution is already optimal. No mistakes detected."}
        r.set(review_cache_key, json.dumps(final_result), ex=86400)
        return final_result

    pattern = normalize_pattern(extract("PATTERN", review_text))
    mistake = extract("MISTAKE", review_text)
    now = datetime.now(timezone.utc)

    # ---------- SPACED REPETITION ----------
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

    # ---------- SAVE REVIEW ----------
    reviews.insert_one({
        "user_id": user_id,
        "title": title,
        "topics": topics,
        "pattern": pattern,
        "review": review_text,
        "date": now
    })

    # ---------- REDO LIST ----------
    if not redo_list.find_one({"user_id": user_id, "title": title}):
        redo_list.insert_one({
            "user_id": user_id,
            "title": title,
            "slug": title.lower().replace(" ", "-"),
            "pattern": pattern,
            "mistake": mistake,
            "added_on": now
        })

    final_result = {"review": review_text}

    # ---------- STORE REVIEW CACHE ----------
    r.set(review_cache_key, json.dumps(final_result), ex=86400)

    return final_result
