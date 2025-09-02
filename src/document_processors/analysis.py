# src/document_processors/analysis.py
from typing import List, Dict
from src.document_ingestion.loaders.base import LoadedDocument, ImageBlob
from src.embeddings.embeddings import get_embedding
import pandas as pd
import pytesseract
from PIL import Image
from pathlib import Path


def text_summary(doc: LoadedDocument, max_chars: int = 2000) -> str:
    text = (doc.text or "")[:max_chars]
    table_summaries = []
    for i, t in enumerate(doc.tables or []):
        table_summaries.append(f"[Table {i}] {len(t)} rows x {len(t.columns)} cols")
    return "\n".join([text] + table_summaries)


def tables_to_markdown(tables: List[pd.DataFrame]) -> List[str]:
    md_tables = []
    for df in tables:
        md = df.to_markdown(index=False)
        md_tables.append(md)
    return md_tables


def ocr_image_blob(image_blob: ImageBlob) -> str:
    p = Path(image_blob.path)
    if not p.exists():
        return ""
    try:
        img = Image.open(p)
        text = pytesseract.image_to_string(img)
        return text
    except Exception:
        return ""


def extract_all_ocr(doc: LoadedDocument) -> Dict[str, str]:
    results = {}
    for img in doc.images or []:
        results[img.path] = ocr_image_blob(img)
    return results


def document_embedding_summary(doc: LoadedDocument, chunk_size: int = 1000):
    text = doc.text or ""
    chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)] or [""]
    for md in tables_to_markdown(doc.tables or []):
        chunks.append(md[:chunk_size])
    return [get_embedding(c) for c in chunks]
