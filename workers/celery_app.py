from celery import Celery

celery_app = Celery(
    "codementor",
    broker="pyamqp://guest@localhost//",
    backend="redis://localhost:6379/0",
)

# IMPORTANT: tell celery where tasks are
celery_app.autodiscover_tasks(["workers"])
