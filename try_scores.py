from src.knowledge import best_faq

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
    ("The app crashes when I open settings.", None),
    ("I was charged twice this month!", None),
]

good_scores = []
bad_scores = []

for message, expected_id in TESTS:
    item, score = best_faq(message)
    if expected_id is None:
        bad_scores.append(score)
        label = "NO MATCH SHOULD EXIST"
    elif item["id"] == expected_id:
        good_scores.append(score)
        label = "correct match"
    else:
        label = "WRONG FAQ PAGE"
    print(f"{score:.2f}  {label}: {message}  ->  {item['question']}")

print()
print("lowest score of a correct match :", round(min(good_scores), 2))
print("highest score of a bad match    :", round(max(bad_scores), 2))
