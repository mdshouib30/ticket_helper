import json

from src.classifier import classify_ticket
from src.rules import apply_rules

PRACTICE_LAST_ID = 10  # tickets 1-10 are the ones we tuned on

with open("data/tickets.json") as f:
    tickets = json.load(f)

with open("data/answer_key.json") as f:
    answer_key = {item["id"]: item for item in json.load(f)}

scores = {
    "practice": {"category": 0, "urgency": 0, "total": 0},
    "fresh": {"category": 0, "urgency": 0, "total": 0},
}

for ticket in tickets:
    message = ticket["message"]

    result = apply_rules(message)
    if result is None:
        result = classify_ticket(message)

    correct = answer_key[ticket["id"]]
    category_ok = result.category.value == correct["category"]
    urgency_ok = result.urgency.value == correct["urgency"]

    group = "practice" if ticket["id"] <= PRACTICE_LAST_ID else "fresh"
    scores[group]["total"] += 1
    if category_ok:
        scores[group]["category"] += 1
    if urgency_ok:
        scores[group]["urgency"] += 1

    if not (category_ok and urgency_ok):
        print(f"Ticket {ticket['id']}: {message}")
        print(f"  AI said : {result.category.value} / {result.urgency.value}")
        print(f"  Correct : {correct['category']} / {correct['urgency']}")
        print()

for group, s in scores.items():
    print(f"{group.upper()} tickets ({s['total']}):")
    print(f"  Category correct: {s['category']} of {s['total']}")
    print(f"  Urgency correct : {s['urgency']} of {s['total']}")
