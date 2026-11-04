from src.rules import apply_rules


def test_unsubscribe_is_caught():
    result = apply_rules("Please unsubscribe me from your emails.")
    assert result is not None
    assert result.category.value == "general"
    assert result.urgency.value == "low"


def test_opening_hours_is_caught():
    result = apply_rules("What are your opening hours?")
    assert result is not None
    assert result.category.value == "general"


def test_password_reset_is_caught():
    result = apply_rules("I forgot password, please help")
    assert result is not None
    assert result.category.value == "technical"


def test_return_question_is_refund():
    result = apply_rules("Can I return an item after 30 days?")
    assert result is not None
    assert result.category.value == "refund"


def test_capital_letters_do_not_matter():
    result = apply_rules("UNSUBSCRIBE ME NOW")
    assert result is not None


def test_hard_ticket_goes_to_ai():
    assert apply_rules("I was charged twice this month!") is None
