from backend.app.db import reviews


def extract_block(text, key):
    if key not in text:
        return None

    part = text.split(key)[1].strip()
    lines = part.split("\n")

    for line in lines:
        line = line.strip()
        if line:
            return line

    return None


def get_flashcards(user_id):
    data = list(reviews.find({"user_id": user_id}))

    concept_map = {}

    for doc in data:
        review = doc.get("review", "")

        mistake = extract_block(review, "MISTAKE:")
        reminder = extract_block(review, "REMINDER:")
        pattern = extract_block(review, "PATTERN:")

        if mistake and reminder and pattern:
            key = pattern.lower()

            if key not in concept_map:
                concept_map[key] = {
                    "pattern": pattern,
                    "mistake": mistake,
                    "reminder": reminder,
                    "count": 1,
                    "last_title": doc["title"],
                    "last_date": doc["date"],
                }
            else:
                concept_map[key]["count"] += 1

                # update latest occurrence
                if doc["date"] > concept_map[key]["last_date"]:
                    concept_map[key]["last_date"] = doc["date"]
                    concept_map[key]["last_title"] = doc["title"]

    # format output
    flashcards = []
    for c in concept_map.values():
        flashcards.append({
            "pattern": c["pattern"],
            "mistake": c["mistake"],
            "reminder": c["reminder"],
            "count": c["count"],
            "last_title": c["last_title"],
            "last_date": c["last_date"].strftime("%d %b"),
        })

    return flashcards
