from src.classifier import Category, TicketResult, Urgency
from src.safety import decide_action


def make(category, urgency):
    return TicketResult(category=category, urgency=urgency, reason="test")


def test_high_urgency_goes_to_human():
    ticket = make(Category.technical, Urgency.high)
    action, _ = decide_action(ticket, "We will help you.")
    assert action == "SEND TO HUMAN"


def test_money_tickets_go_to_human():
    ticket = make(Category.billing, Urgency.low)
    action, _ = decide_action(ticket, "We will check this.")
    assert action == "SEND TO HUMAN"


def test_numbers_in_reply_go_to_human():
    ticket = make(Category.general, Urgency.low)
    action, _ = decide_action(ticket, "We open at 9am.")
    assert action == "SEND TO HUMAN"


def test_risky_word_goes_to_human():
    ticket = make(Category.general, Urgency.low)
    action, _ = decide_action(ticket, "We guarantee a fix.")
    assert action == "SEND TO HUMAN"


def test_safe_ticket_is_auto_reply():
    ticket = make(Category.general, Urgency.low)
    action, _ = decide_action(ticket, "Thanks for asking. Support Team")
    assert action == "AUTO-REPLY"
