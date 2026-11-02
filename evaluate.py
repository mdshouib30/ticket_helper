import json

from src.classifier import classify_ticket
from src.rules import apply_rules

with open("data/tickets.json") as f:
    tickets = json.load(f)

with open("data/answer_key.json") as f:
    answer_key = {item["id"]: item for item in json.load(f)}

category_right = 0
urgency_right = 0

for ticket in tickets:
    message = ticket["message"]

    result = apply_rules(message)
    if result is None:
        result = classify_ticket(message)

    correct = answer_key[ticket["id"]]
    category_ok = result.category.value == correct["category"]
    urgency_ok = result.urgency.value == correct["urgency"]

    if category_ok:
        category_right += 1
    if urgency_ok:
        urgency_right += 1

    if not (category_ok and urgency_ok):
        print(f"Ticket {ticket['id']}: {message}")
        print(f"  AI said : {result.category.value} / {result.urgency.value}")
        print(f"  Correct : {correct['category']} / {correct['urgency']}")
        print()

total = len(tickets)
print(f"Category correct: {category_right} of {total}")
print(f"Urgency correct : {urgency_right} of {total}")
