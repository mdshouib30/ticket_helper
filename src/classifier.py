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
- refund: wants money back, wants to return an item, or asks about return or refund rules
- general: any other question

Pick ONE urgency. Be careful: most tickets are NOT high.
- high: the customer is blocked or losing money right now. For example: locked out of the account, money taken by mistake, account hacked, customer says they will leave.
- medium: something is broken or wrong, but the customer can still manage or wait a day. For example: a button does not work, an image will not load, a late delivery.
- low: a simple question and nothing is broken.

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
