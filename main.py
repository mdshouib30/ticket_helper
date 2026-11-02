import json

from src.classifier import classify_ticket
from src.rules import apply_rules

with open("data/tickets.json") as f:
    tickets = json.load(f)

rules_count = 0

for ticket in tickets:
    message = ticket["message"]

    result = apply_rules(message)
    if result is not None:
        handled_by = "RULES (no AI used)"
        rules_count += 1
    else:
        result = classify_ticket(message)
        handled_by = "AI"

    print(f"Ticket {ticket['id']}: {message}")
    print(f"  Handled by : {handled_by}")
    print(f"  Category   : {result.category.value}")
    print(f"  Urgency    : {result.urgency.value}")
    print(f"  Reason     : {result.reason}")
    print()

print(f"{rules_count} of {len(tickets)} tickets handled without AI.")
