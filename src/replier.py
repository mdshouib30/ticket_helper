from src.classifier import MODEL, Category, TicketResult, client

STYLES = {
    Category.billing: "Be calm and careful. Say we will check the charge. Never promise a refund.",
    Category.technical: "Be helpful and clear. Give one or two simple steps to try.",
    Category.refund: "Be polite. Say we will review the request. Never promise money back.",
    Category.general: "Be friendly and short. Answer the question simply.",
}


def write_reply(message: str, result: TicketResult) -> str:
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
