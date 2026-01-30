from .celery_app import celery_app
from backend.app.review_pipeline import run_full_review_pipeline
import redis
import os
import json

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
r = redis.Redis(host=REDIS_HOST, port=6379, db=1)

@celery_app.task(queue="review_queue")
def review_code_task(review_id, code, user_id, title, description, topics):
    r.set(f"review:{review_id}", "PROCESSING")

    result = run_full_review_pipeline(
        code, user_id, title, description, topics
    )

    review_text = result["review"]

    r.set(f"review:{review_id}:result", review_text)
    r.set(f"review:{review_id}", "DONE")
