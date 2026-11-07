import pytest
from fastapi.testclient import TestClient

import api
from src import database


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", str(tmp_path / "test.db"))
    database.init_db()

    # Replace the real pipeline with a fake one, so no AI is needed.
    def fake_process_ticket(message):
        return {
            "message": message,
            "sorted_by": "RULES",
            "category": "general",
            "urgency": "low",
            "reason": "test",
            "reply": "Hello",
            "reply_source": "Fixed rule reply (no AI)",
            "action": "AUTO-REPLY",
            "why": "Safe to send.",
        }

    monkeypatch.setattr(api, "process_ticket", fake_process_ticket)
    return TestClient(api.app)


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_create_and_read_ticket(client):
    created = client.post("/tickets", json={"message": "Hi there"}).json()
    assert created["id"] == 1
    fetched = client.get(f"/tickets/{created['id']}").json()
    assert fetched["message"] == "Hi there"


def test_missing_ticket_is_404(client):
    assert client.get("/tickets/999").status_code == 404


def test_stats(client):
    client.post("/tickets", json={"message": "one"})
    assert client.get("/stats").json()["total"] == 1
