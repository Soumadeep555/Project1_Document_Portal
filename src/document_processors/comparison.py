# src/document_processors/comparison.py
from typing import Dict, Any
from src.document_ingestion.loaders.base import LoadedDocument
from src.embeddings.embeddings import get_embedding
import numpy as np
import pandas as pd
from difflib import SequenceMatcher
from PIL import Image
import imagehash


def cosine(a: list, b: list) -> float:
    a = np.array(a); b = np.array(b)
    if a.size == 0 or b.size == 0:
        return 0.0
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    return float(np.dot(a, b) / denom) if denom else 0.0


def compare_texts(doc_a: LoadedDocument, doc_b: LoadedDocument) -> Dict[str, Any]:
    emb_a = get_embedding((doc_a.text or "")[:20000])
    emb_b = get_embedding((doc_b.text or "")[:20000])
    sim = cosine(emb_a, emb_b)
    ratio = SequenceMatcher(None, doc_a.text or "", doc_b.text or "").ratio()
    return {"cosine_similarity": sim, "sequence_ratio": ratio}


def compare_tables(doc_a: LoadedDocument, doc_b: LoadedDocument) -> Dict[str, Any]:
    results = []
    for i, ta in enumerate(doc_a.tables or []):
        best = {"score": 0.0, "match_idx": None}
        for j, tb in enumerate(doc_b.tables or []):
            score = 0.0
            try:
                if list(ta.columns) == list(tb.columns):
                    cellsa = ta.astype(str).fillna("").to_numpy().flatten()
                    cellsb = tb.astype(str).fillna("").to_numpy().flatten()
                    seta, setb = set(cellsa), set(cellsb)
                    inter = len(seta & setb)
                    union = max(1, len(seta | setb))
                    score = inter / union
            except Exception:
                score = 0.0
            if score > best["score"]:
                best = {"score": score, "match_idx": j}
        results.append({"table_idx": i, "best_match": best})
    return {"matches": results}


def _image_phash(path: str):
    try:
        img = Image.open(path)
        return str(imagehash.phash(img))
    except Exception:
        return None


def compare_images(doc_a: LoadedDocument, doc_b: LoadedDocument) -> Dict[str, Any]:
    a_hashes = {_image_phash(i.path): i for i in (doc_a.images or [])}
    b_hashes = {_image_phash(i.path): i for i in (doc_b.images or [])}
    common = [h for h in a_hashes if h and h in b_hashes]
    return {"common_phash_count": len(common), "common_hashes": common}
