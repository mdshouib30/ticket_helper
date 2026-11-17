import os
import time

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url=os.getenv("LLM_BASE_URL"),
    api_key=os.getenv("LLM_API_KEY"),
    max_retries=0,
    timeout=90,
)

print("model:", os.getenv("LLM_MODEL"))
start = time.time()
try:
    reply = client.chat.completions.create(
        model=os.getenv("LLM_MODEL"),
        messages=[
            {
                "role": "user",
                "content": (
                    "You write short customer support replies, maximum 3 sentences. "
                    "The ONLY information you may use is this fact: We ship to the US, "
                    "UK, Canada, and India. Delivery takes 5 to 7 business days. "
                    "Customer asks: Do you deliver abroad?"
                ),
            }
        ],
    )
    seconds = time.time() - start
    print("WORKS in", round(seconds, 1), "seconds")
    print(reply.choices[0].message.content)
except Exception as exc:
    print("ERROR after", round(time.time() - start, 1), "seconds:", exc)
