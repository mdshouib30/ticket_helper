from src.classifier import Category, TicketResult, Urgency

RISKY_WORDS = ["refund", "guarantee", "promise", "100%", "compensat"]


def decide_action(result: TicketResult, reply: str):
    """Return (action, why). Action is AUTO-REPLY or SEND TO HUMAN."""
    if result.urgency == Urgency.high:
        return "SEND TO HUMAN", "High urgency."
    if result.category in (Category.billing, Category.refund):
        return "SEND TO HUMAN", "Money questions need a person."
    if any(ch.isdigit() for ch in reply):
        return (
            "SEND TO HUMAN",
            "Reply has numbers or times. A person must check the facts.",
        )
    for word in RISKY_WORDS:
        if word in reply.lower():
            return "SEND TO HUMAN", f"Reply contains risky word: {word}."
    return "AUTO-REPLY", "Safe to send."
