# src/document_processors/multichat.py
from typing import List, Dict, Any, Tuple
from src.document_ingestion.loaders.base import LoadedDocument
from src.embeddings.embeddings import get_embedding, embed_texts
import numpy as np
import pickle
from pathlib import Path
import os

STORE_DIR = Path("data/vectorstores")
STORE_DIR.mkdir(parents=True, exist_ok=True)


class SimpleVectorStore:
    def __init__(self, name: str):
        self.name = name
        self.path = STORE_DIR / f"{name}.pkl"
        if self.path.exists():
            with open(self.path, "rb") as f:
                payload = pickle.load(f)
                self.docs = payload["docs"]
                self.vectors = payload["vectors"]
        else:
            self.docs = []
            self.vectors = np.zeros((0, 1))

    def save(self):
        with open(self.path, "wb") as f:
            pickle.dump({"docs": self.docs, "vectors": self.vectors}, f)

    def add(self, doc_id: str, texts: List[str], embeddings: List[List[float]]):
        if len(embeddings) == 0:
            return
        embeddings = np.array(embeddings)
        if self.vectors.size == 0:
            self.vectors = embeddings
        else:
            self.vectors = np.vstack([self.vectors, embeddings])
        for t in texts:
            self.docs.append({"doc_id": doc_id, "text": t})
        self.save()

    def query(self, query_emb: List[float], top_k: int = 5) -> List[Tuple[float, Dict]]:
        q = np.array(query_emb).astype(float)
        if self.vectors.size == 0:
            return []
        norms = np.linalg.norm(self.vectors, axis=1) * (np.linalg.norm(q) or 1.0)
        sims = np.dot(self.vectors, q) / np.where(norms == 0, 1.0, norms)
        topk = np.argsort(-sims)[:top_k]
        return [(float(sims[i]), self.docs[i]) for i in topk]


def index_documents(store_name: str, docs: List[LoadedDocument], chunk_size: int = 1000):
    store = SimpleVectorStore(store_name)
    for idx, d in enumerate(docs):
        text = d.text or ""
        chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)] or [""]
        import pandas as pd
        for t in (d.tables or []):
            chunks.append(t.to_csv(index=False)[:chunk_size])
        embeddings = embed_texts(chunks)
        store.add(f"{idx}:{Path(d.source).name}", chunks, embeddings)
    return store


def generate_answer_with_llm(question: str, context: str) -> str:
    # Replace this with your project LLM call
    return f"Q: {question}\n\nContext:\n{context}\n\n[LLM not configured]"


def chat_query(store: SimpleVectorStore, question: str, top_k: int = 5) -> Dict[str, Any]:
    q_emb = get_embedding(question)
    hits = store.query(q_emb, top_k=top_k)
    context = "\n\n".join([h[1]["text"] for h in hits])
    answer = generate_answer_with_llm(question, context)
    return {"answer": answer, "sources": [h[1]["doc_id"] for h in hits], "scores": [h[0] for h in hits]}
