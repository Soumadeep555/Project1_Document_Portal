# src/embeddings/embeddings.py
from typing import List
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    _MODEL = SentenceTransformer("all-MiniLM-L6-v2")
except Exception:
    _MODEL = None


def get_embedding(text: str) -> List[float]:
    if _MODEL:
        return _MODEL.encode(text).tolist()
    # fallback deterministic pseudo-embedding (not for prod!)
    import hashlib
    h = hashlib.sha256(text.encode("utf-8")).digest()
    arr = np.frombuffer(h, dtype=np.uint8).astype(float)
    # create float vector and normalize
    vec = arr / (np.linalg.norm(arr) or 1.0)
    return vec.tolist()


def embed_texts(texts: List[str]) -> List[List[float]]:
    if _MODEL:
        return _MODEL.encode(texts).tolist()
    return [get_embedding(t) for t in texts]
