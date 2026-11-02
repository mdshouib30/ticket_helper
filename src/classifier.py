import os
from enum import Enum

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

load_dotenv()

client = OpenAI(
    base_url=os.getenv("LLM_BASE_URL"),
    api_key=os.getenv("LLM_API_KEY"),
)
MODEL = os.getenv("LLM_MODEL")


class Category(str, Enum):
    billing = "billing"
    technical = "technical"
    refund = "refund"
    general = "general"


class Urgency(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class TicketResult(BaseModel):
    category: Category
    urgency: Urgency
    reason: str


SYSTEM_PROMPT = """You sort customer support tickets.

Pick ONE category:
- billing: charges, invoices, payments
- technical: app or website not working
- refund: wants money back or to return something
- general: any other question

Pick ONE urgency:
- high: money lost, cannot log in, deadline, or very angry customer
- medium: something is broken but there is a workaround
- low: a simple question

Give a short reason (one sentence)."""


def classify_ticket(message: str) -> TicketResult:
    completion = client.beta.chat.completions.parse(
        model=MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message},
        ],
        response_format=TicketResult,
    )
    return completion.choices[0].message.parsed
