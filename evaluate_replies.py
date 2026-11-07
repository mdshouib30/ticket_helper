import re

from src.classifier import Category, TicketResult, Urgency
from src.knowledge import best_faq
from src.replier import FAQ_THRESHOLD, HOLDING_REPLIES, write_reply

# (customer message, id of the FAQ that should match, or None if no FAQ has the answer)
TESTS = [
    ("Do you deliver abroad?", 4),
    ("I need to change my card", 6),
    ("When can I reach your support team?", 1),
    ("Is there a discount for students?", 3),
    ("Where do I download my old invoices?", 7),
    ("Can I use the app in Spanish?", 8),
    ("How much does the Pro plan cost?", 10),
    ("Do you sell gift cards?", None),
    ("Can I talk to a manager?", None),
    ("What is your phone number?", None),
]

POLITE_WORDS = {
    "thanks",
    "for",
    "your",
    "message",
    "support",
    "team",
    "the",
    "a",
    "to",
    "you",
    "we",
    "is",
    "are",
    "and",
    "can",
    "please",
    "of",
    "in",
    "at",
    "on",
    "with",
    "it",
    "this",
    "will",
    "our",
    "so",
    "if",
    "or",
    "as",
    "be",
}


def words(text: str) -> set:
    return set(re.findall(r"[a-z0-9$%]+", text.lower()))


result = TicketResult(category=Category.general, urgency=Urgency.low, reason="test")

match_right = 0
grounded_right = 0

for message, expected_id in TESTS:
    item, score = best_faq(message)
    matched_id = item["id"] if score >= FAQ_THRESHOLD else None
    match_ok = matched_id == expected_id
    reply = write_reply(message, result)

    extra = set()
    if matched_id is None:
        grounded = reply == HOLDING_REPLIES[Category.general]
    else:
        allowed = words(item["answer"]) | words(message) | POLITE_WORDS
        extra = words(reply) - allowed
        new_nums = set(re.findall(r"\d+", reply)) - set(
            re.findall(r"\d+", item["answer"])
        )
        grounded = len(extra) <= 3 and not new_nums

    match_right += match_ok
    grounded_right += grounded

    print(message)
    print(
        f"  expected FAQ: {expected_id} | matched: {matched_id} (score {score:.2f}) -> {'OK' if match_ok else 'WRONG'}"
    )
    print(f"  reply: {reply}")
    print(
        f"  grounded: {'OK' if grounded else 'CHECK, extra words: ' + ', '.join(sorted(extra))}"
    )
    print()

total = len(TESTS)
print(f"Right FAQ choice          : {match_right} of {total}")
print(f"Replies with no invention : {grounded_right} of {total}")
