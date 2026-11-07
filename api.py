from fastapi import FastAPI
from pydantic import BaseModel

from src.pipeline import process_ticket

app = FastAPI(title="AI Support Ticket Helper")


class TicketIn(BaseModel):
    message: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/tickets")
def create_ticket(ticket: TicketIn):
    return process_ticket(ticket.message)
