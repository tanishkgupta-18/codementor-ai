from datetime import datetime, timezone, timedelta

# Anki-style gaps by level
GAPS = {
    1: 1,    # 1 day
    2: 3,    # 3 days
    3: 7,    # 7 days
    4: 15,   # 15 days
}


def next_date(level: int):
    days = GAPS.get(level, 15)
    return datetime.now(timezone.utc) + timedelta(days=days)
