import json

from src.classifier import classify_ticket

with open("data/tickets.json") as f:
    tickets = json.load(f)

for ticket in tickets:
    result = classify_ticket(ticket["message"])
    print(f"Ticket {ticket['id']}: {ticket['message']}")
    print(f"  Category : {result.category.value}")
    print(f"  Urgency  : {result.urgency.value}")
    print(f"  Reason   : {result.reason}")
    print()
