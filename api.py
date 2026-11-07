from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src import database
from src.pipeline import process_ticket

database.init_db()
app = FastAPI(title="AI Support Ticket Helper")


class TicketIn(BaseModel):
    message: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/tickets")
def create_ticket(ticket: TicketIn):
    data = process_ticket(ticket.message)
    data["id"] = database.save_ticket(data)
    return data


@app.get("/tickets")
def list_all(limit: int = 50):
    return database.list_tickets(limit)


@app.get("/tickets/{ticket_id}")
def get_one(ticket_id: int):
    ticket = database.get_ticket(ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@app.get("/stats")
def get_stats():
    return database.stats()
