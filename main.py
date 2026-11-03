import json
import logging
import os

from src.classifier import classify_ticket
from src.replier import write_reply
from src.rules import apply_rules
from src.safety import decide_action

LIMIT = 5  # how many tickets to run while testing

logging.basicConfig(
    filename="tickets.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logging.getLogger("httpx").setLevel(logging.WARNING)

with open("data/tickets.json") as f:
    tickets = json.load(f)[:LIMIT]

rules_count = 0
human_count = 0
results = []

for ticket in tickets:
    message = ticket["message"]

    result = apply_rules(message)
    if result is not None:
        sorted_by = "RULES"
        rules_count += 1
    else:
        result = classify_ticket(message)
        sorted_by = "AI"

    reply = write_reply(message, result)
    action, why = decide_action(result, reply)
    if action == "SEND TO HUMAN":
        human_count += 1

    logging.info(  # noqa: LOG015
        "ticket=%s sorted_by=%s category=%s urgency=%s action=%s why=%s",
        ticket["id"],
        sorted_by,
        result.category.value,
        result.urgency.value,
        action,
        why,
    )

    results.append(
        {
            "id": ticket["id"],
            "message": message,
            "sorted_by": sorted_by,
            "category": result.category.value,
            "urgency": result.urgency.value,
            "reason": result.reason,
            "reply": reply,
            "action": action,
            "why": why,
        }
    )

    print(f"Ticket {ticket['id']}: {message}")
    print(f"  Sorted by   : {sorted_by}")
    print(f"  Category    : {result.category.value}")
    print(f"  Urgency     : {result.urgency.value}")
    print(f"  Reply draft : {reply}")
    print(f"  Action      : {action} ({why})")
    print()

os.makedirs("output", exist_ok=True)
with open("output/results.json", "w") as f:
    json.dump(results, f, indent=2)

print(f"{rules_count} of {len(tickets)} tickets sorted without AI.")
print(f"{human_count} of {len(tickets)} tickets sent to a human.")
