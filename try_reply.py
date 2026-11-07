from src.classifier import Category, TicketResult, Urgency
from src.replier import write_reply

result = TicketResult(category=Category.general, urgency=Urgency.low, reason="test")

messages = [
    "Do you deliver abroad?",
    "I need to change my card",
    "Do you sell gift cards?",
]

for message in messages:
    print(message)
    print(write_reply(message, result))
    print("---")
