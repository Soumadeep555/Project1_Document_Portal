# src/document_ingestion/loaders/txt_loader.py
from pathlib import Path
from .base import BaseLoader, LoadedDocument


class TxtLoader(BaseLoader):
    def load(self, path: str) -> LoadedDocument:
        p = Path(path)
        text = p.read_text(encoding="utf-8", errors="ignore")
        return LoadedDocument(source=str(p), text=text)
