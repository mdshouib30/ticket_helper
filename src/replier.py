from src.classifier import MODEL, Category, TicketResult, client

STYLES = {
    Category.billing: "Be calm and careful. Say we will check the charge. Never promise a refund.",
    Category.technical: "Be helpful and clear. Give one or two simple steps to try.",
    Category.refund: "Be polite. Say we will review the request. Never promise money back.",
    Category.general: "Be friendly and short. Answer the question simply.",
}

FIXED_REPLIES = {
    "Customer wants to stop receiving emails.": (
        "Thanks for your message. We have noted your request "
        "to stop receiving emails.\n\nSupport Team"
    ),
    "Simple question about opening hours.": (
        "Thanks for your message. A team member will send you "
        "our opening hours.\n\nSupport Team"
    ),
    "Customer needs a password reset.": (
        "Thanks for your message. A team member will help you "
        "reset your password.\n\nSupport Team"
    ),
    "Customer asks about returning an item.": (
        "Thanks for your message. A team member will explain our "
        "return rules.\n\nSupport Team"
    ),
}


def write_reply(message: str, result: TicketResult) -> str:
    if result.reason in FIXED_REPLIES:
        return FIXED_REPLIES[result.reason]
    style = STYLES[result.category]
    completion = client.chat.completions.create(
        model=MODEL,
        temperature=0.3,
        messages=[
            {
                "role": "system",
                "content": (
                    "You write short customer support replies, "
                    "maximum 3 sentences. "
                    f"{style} "
                    "Do not invent facts, prices, or dates. "
                    "End with: Support Team"
                ),
            },
            {"role": "user", "content": message},
        ],
    )
    return completion.choices[0].message.content.strip()
