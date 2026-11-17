from src.classifier import Category, TicketResult, Urgency, classify_ticket
from src.replier import reply_source, write_reply
from src.rules import apply_rules
from src.safety import decide_action


def process_ticket(message: str) -> dict:
    """Run one customer message through the whole system."""
    result = apply_rules(message)
    sorted_by = "RULES" if result is not None else "AI"
    if result is None:
        try:
            result = classify_ticket(message)
        except Exception:
            # Fail safe: if the AI is unavailable, a person looks at the ticket.
            result = TicketResult(
                category=Category.general,
                urgency=Urgency.high,
                reason="The AI was unavailable, so a person should look at this ticket.",
            )
            sorted_by = "AI unavailable"

    reply = write_reply(message, result)
    source, _ = reply_source(message, result)
    action, why = decide_action(result, reply)

    return {
        "message": message,
        "sorted_by": sorted_by,
        "category": result.category.value,
        "urgency": result.urgency.value,
        "reason": result.reason,
        "reply": reply,
        "reply_source": source,
        "action": action,
        "why": why,
    }
