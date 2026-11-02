from src.classifier import Category, TicketResult, Urgency

RULES = [
    (
        ["unsubscribe", "stop sending", "remove me from"],
        Category.general,
        Urgency.low,
        "Customer wants to stop receiving emails.",
    ),
    (
        ["opening hours", "business hours", "what time do you open"],
        Category.general,
        Urgency.low,
        "Simple question about opening hours.",
    ),
    (
        ["forgot password", "reset my password", "reset password"],
        Category.technical,
        Urgency.medium,
        "Customer needs a password reset.",
    ),
]


def apply_rules(message: str):
    text = message.lower()
    for words, category, urgency, reason in RULES:
        for word in words:
            if word in text:
                return TicketResult(category=category, urgency=urgency, reason=reason)
    return None
