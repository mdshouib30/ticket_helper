import json
import math
import os

from src.classifier import client

EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")


def _load_faq() -> list:
    with open("data/faq.json") as f:
        return json.load(f)


FAQ = _load_faq()
_faq_vectors = None


def reload_faq():
    """Read data/faq.json again after it has changed."""
    global FAQ, _faq_vectors
    FAQ = _load_faq()
    _faq_vectors = None


def _embed(text: str) -> list:
    response = client.embeddings.create(model=EMBED_MODEL, input=text)
    return response.data[0].embedding


def _similarity(a: list, b: list) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    size_a = math.sqrt(sum(x * x for x in a))
    size_b = math.sqrt(sum(y * y for y in b))
    return dot / (size_a * size_b)


def best_faq(message: str):
    """Return (best matching FAQ entry, similarity score)."""
    global _faq_vectors
    if _faq_vectors is None:
        _faq_vectors = [_embed(item["question"]) for item in FAQ]

    message_vector = _embed(message)
    best_item = None
    best_score = -1.0
    for item, vector in zip(FAQ, _faq_vectors):
        score = _similarity(message_vector, vector)
        if score > best_score:
            best_item = item
            best_score = score
    return best_item, best_score
