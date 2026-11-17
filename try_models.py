import os
import time

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url=os.getenv("LLM_BASE_URL"),
    api_key=os.getenv("LLM_API_KEY"),
    max_retries=0,
    timeout=60,
)

# Add model names from Google's docs page here.
# A name that does not exist just shows an error. It does no harm.
MODELS = [
    "gemini-3.8-flash",
    "gemini-flash-latest",
    "gemini-flash-lite-latest",
    "gemini-4-hydrogen",
]

for model in MODELS:
    start = time.time()
    try:
        reply = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Say hello in 5 words."}],
        )
        seconds = round(time.time() - start, 1)
        text = reply.choices[0].message.content.strip()
        print(f"WORKS  {model}  ({seconds}s): {text}")
    except Exception as exc:
        seconds = round(time.time() - start, 1)
        print(f"ERROR  {model}  ({seconds}s): {exc}")
    time.sleep(3)
