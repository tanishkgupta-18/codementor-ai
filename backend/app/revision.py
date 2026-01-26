from datetime import datetime, timezone
from backend.app.db import reviews


def make_aware(dt):
    """Ensure Mongo datetime is timezone-aware (UTC)."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def get_revision_problem(user_id):
    data = list(reviews.find({"user_id": user_id}))

    topic_last = {}
    pattern_count = {}

    for doc in data:
        doc_date = make_aware(doc["date"])

        # Track last practice date per topic
        for t in doc.get("topics", []):
            if t not in topic_last or doc_date > topic_last[t]:
                topic_last[t] = doc_date

        # Count pattern mistakes
        review = doc.get("review", "")
        if "PATTERN:" in review:
            pattern = review.split("PATTERN:")[1].split("\n")[0].strip()
            pattern_count[pattern] = pattern_count.get(pattern, 0) + 1

    if not topic_last or not pattern_count:
        return {
            "message": "Not enough data yet. Solve a few problems first."
        }

    # Most forgotten topic
    now = datetime.now(timezone.utc)
    worst_topic = None
    max_days = -1

    for t, d in topic_last.items():
        days = (now - d).days
        if days > max_days:
            max_days = days
            worst_topic = t

    # Most repeated mistake pattern
    worst_pattern = max(pattern_count, key=pattern_count.get)

    return {
        "revise_topic": worst_topic,
        "revise_pattern": worst_pattern,
        "message": f"You should revise {worst_pattern} problems from {worst_topic} today."
    }
