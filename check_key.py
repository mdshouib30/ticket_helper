import os

from dotenv import load_dotenv

load_dotenv()

key = os.getenv("LLM_API_KEY") or ""
print("length:", len(key))
print("starts with:", key[:4])
print("has spaces or quotes:", key != key.strip() or '"' in key or "'" in key)
print("base url:", os.getenv("LLM_BASE_URL"))
print("chat model:", os.getenv("LLM_MODEL"))
print("embedding model:", os.getenv("EMBED_MODEL"))
