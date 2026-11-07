from src.classifier import classify_ticket
from src.replier import reply_source, write_reply
from src.rules import apply_rules
from src.safety import decide_action


def process_ticket(message: str) -> dict:
    """Run one customer message through the whole system."""
    result = apply_rules(message)
    sorted_by = "RULES" if result is not None else "AI"
    if result is None:
        result = classify_ticket(message)

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
