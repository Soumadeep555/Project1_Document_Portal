# src/document_ingestion/loaders/csv_loader.py
from pathlib import Path
import pandas as pd
from .base import BaseLoader, LoadedDocument


class CsvLoader(BaseLoader):
    def load(self, path: str) -> LoadedDocument:
        p = Path(path)
        df = pd.read_csv(str(p))
        text = f"[CSV] {len(df)} rows x {len(df.columns)} cols"
        return LoadedDocument(source=str(p), text=text, tables=[df])
