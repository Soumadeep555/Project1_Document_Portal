# src/document_ingestion/loaders/xlsx_loader.py
from pathlib import Path
import pandas as pd
from .base import BaseLoader, LoadedDocument


class XlsxLoader(BaseLoader):
    def load(self, path: str) -> LoadedDocument:
        p = Path(path)
        xls = pd.ExcelFile(str(p))
        tables = [xls.parse(sheet_name) for sheet_name in xls.sheet_names]
        text = "\n".join([f"[Sheet: {name}] {len(df)} rows x {len(df.columns)} cols"
                          for name, df in zip(xls.sheet_names, tables)])
        return LoadedDocument(source=str(p), text=text, tables=tables)
