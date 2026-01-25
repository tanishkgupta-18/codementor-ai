from backend.app.db import reviews
from datetime import datetime
from collections import defaultdict


def topic_heatmap(user_id: str):
    data = list(reviews.find({"user_id": user_id}))

    topic_last_date = defaultdict(lambda: None)

    for doc in data:
        for t in doc.get("topics", []):
            if topic_last_date[t] is None or doc["date"] > topic_last_date[t]:
                topic_last_date[t] = doc["date"]

    result = []

    for topic, last_date in topic_last_date.items():
        days_gap = (datetime.utcnow() - last_date).days

        if days_gap <= 2:
            status = "Fresh"
        elif days_gap <= 5:
            status = "Revise Soon"
        else:
            status = "Forgotten"

        result.append({
            "topic": topic,
            "days_since_practice": days_gap,
            "status": status
        })

    return result
