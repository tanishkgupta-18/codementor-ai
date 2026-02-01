import os
from celery import Celery

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")

celery_app = Celery(
    "codementor",
    broker=f"amqp://guest:guest@{RABBITMQ_HOST}:5672//",
    backend=f"redis://{REDIS_HOST}:6379/0",
)

celery_app.autodiscover_tasks(["workers"])

celery_app.conf.task_routes = {
    "workers.review_task.review_code_task": {"queue": "review_queue"}
}

# Reliability
celery_app.conf.task_acks_late = True
celery_app.conf.worker_prefetch_multiplier = 1
