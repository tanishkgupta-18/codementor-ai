from .celery_app import celery_app
from backend.app.review_pipeline import run_full_review_pipeline
import redis
import os
import json
import time
import logging
from prometheus_client import Counter, Histogram, start_http_server

# ---------- Prometheus for Worker ----------
start_http_server(9100)

TASK_COUNT = Counter(
    "celery_tasks_total",
    "Total Celery Tasks Executed"
)

TASK_LATENCY = Histogram(
    "celery_task_latency_seconds",
    "Time spent processing review task"
)

# ---------- Logging ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

# ---------- Redis ----------
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
r = redis.Redis(host=REDIS_HOST, port=6379, db=1)


@celery_app.task(
    queue="review_queue",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3}
)
def review_code_task(self, review_id, code, user_id, title, description, topics):
    start_time = time.time()
    TASK_COUNT.inc()

    logger.info(f"Started review task | review_id={review_id}")

    try:
        r.set(f"review:{review_id}", "PROCESSING")

        result = run_full_review_pipeline(
            code, user_id, title, description, topics
        )

        review_text = result["review"]

        r.set(f"review:{review_id}:result", review_text)
        r.set(f"review:{review_id}", "DONE")

        latency = time.time() - start_time
        TASK_LATENCY.observe(latency)

        logger.info(f"Completed review | review_id={review_id} | {latency:.2f}s")

    except Exception as e:
        logger.error(f"Error in review task | review_id={review_id} | {str(e)}")
        raise e
