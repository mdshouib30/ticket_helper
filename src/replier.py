from src.classifier import MODEL, Category, TicketResult, client
from src.knowledge import best_faq

FAQ_THRESHOLD = 0.60  # how close a match must be to count as a match

STYLES = {
    Category.billing: "Be calm and careful.",
    Category.technical: "Be helpful and clear.",
    Category.refund: "Be polite and careful.",
    Category.general: "Be friendly and short.",
}

# Used when the AI has no fact to work from. No AI is involved.
HOLDING_REPLIES = {
    Category.billing: (
        "Thanks for your message. A team member will review your "
        "billing question and follow up with you.\n\nSupport Team"
    ),
    Category.technical: (
        "Thanks for your message. A team member will look into the "
        "problem and follow up with you.\n\nSupport Team"
    ),
    Category.refund: (
        "Thanks for your message. A team member will review your "
        "request and follow up with you.\n\nSupport Team"
    ),
    Category.general: (
        "Thanks for your message. A team member will follow up "
        "with you.\n\nSupport Team"
    ),
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


def find_fact(message: str):
    """Return the FAQ answer if one matches well enough, otherwise None."""
    item, score = best_faq(message)
    if score >= FAQ_THRESHOLD:
        return item["answer"]
    return None


def write_reply(message: str, result: TicketResult) -> str:
    # 1. A rule already handled this ticket: use the fixed reply.
    if result.reason in FIXED_REPLIES:
        return FIXED_REPLIES[result.reason]

    # 2. No company fact: do not let the AI write anything.
    fact = find_fact(message)
    if fact is None:
        return HOLDING_REPLIES[result.category]

    # 3. A fact exists: the AI may only turn it into a friendly reply.
    completion = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": (
                    "You write short customer support replies, "
                    "maximum 3 sentences. "
                    f"{STYLES[result.category]} "
                    f"The ONLY information you may use is this fact: {fact} "
                    "Do not add any other information, offers, or guesses. "
                    "End with: Support Team"
                ),
            },
            {"role": "user", "content": message},
        ],
    )
    return completion.choices[0].message.content.strip()
