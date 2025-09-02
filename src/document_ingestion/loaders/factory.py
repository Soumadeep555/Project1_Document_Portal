# src/document_ingestion/loaders/factory.py
from pathlib import Path
from typing import Optional
from .base import LoadedDocument
from .txt_loader import TxtLoader
from .md_loader import MdLoader
from .pdf_loader import PdfLoader
from .docx_loader import DocxLoader
from .ppt_loader import PptLoader
from .xlsx_loader import XlsxLoader
from .csv_loader import CsvLoader
from .sql_loader import SqlLoader

EXT_MAP = {
    ".txt": TxtLoader,
    ".md": MdLoader,
    ".pdf": PdfLoader,
    ".docx": DocxLoader,
    ".pptx": PptLoader,
    ".ppt": PptLoader,
    ".xlsx": XlsxLoader,
    ".csv": CsvLoader,
    ".db": SqlLoader,
    ".sqlite": SqlLoader,
    ".sqlite3": SqlLoader,
}


def load_document(path: str, sql_url: Optional[str] = None) -> LoadedDocument:
    p = Path(path)
    if not p.exists() and not sql_url:
        raise FileNotFoundError(f"Path not found: {path}")
    ext = p.suffix.lower()
    Loader = EXT_MAP.get(ext)
    if Loader is None:
        # allow db via sql_url even if path non-existent
        if sql_url:
            return SqlLoader(sql_url).load(path)
        raise ValueError(f"Unsupported file extension: {ext}")
    if Loader is SqlLoader:
        return Loader(sql_url).load(path)
    return Loader().load(path)
