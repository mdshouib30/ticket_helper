import pytest

from src import database


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    # Use a throwaway database so the real tickets.db is never touched.
    monkeypatch.setattr(database, "DB_PATH", str(tmp_path / "test.db"))
    database.init_db()


def sample(message="Hello"):
    return {
        "message": message,
        "sorted_by": "RULES",
        "category": "general",
        "urgency": "low",
        "reason": "test",
        "reply": "Hi",
        "reply_source": "Fixed rule reply (no AI)",
        "action": "AUTO-REPLY",
        "why": "Safe to send.",
    }


def test_save_and_get_ticket():
    ticket_id = database.save_ticket(sample("I need help"))
    ticket = database.get_ticket(ticket_id)
    assert ticket["message"] == "I need help"
    assert ticket["category"] == "general"


def test_missing_ticket_returns_none():
    assert database.get_ticket(999) is None


def test_list_tickets_newest_first():
    first = database.save_ticket(sample("one"))
    second = database.save_ticket(sample("two"))
    tickets = database.list_tickets()
    assert [t["id"] for t in tickets] == [second, first]


def test_stats_counts():
    database.save_ticket(sample("a"))
    human = sample("b")
    human["action"] = "SEND TO HUMAN"
    database.save_ticket(human)
    assert database.stats() == {
        "total": 2,
        "sent_to_human": 1,
        "sorted_by_rules": 2,
    }
