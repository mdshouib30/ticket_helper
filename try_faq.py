from src.knowledge import best_faq

messages = [
    "Do you deliver abroad?",
    "I need to change my card",
    "The app crashes when I open settings.",
]

for message in messages:
    item, score = best_faq(message)
    print(message)
    print(f"  best match: {item['question']}  (score {score:.2f})")
