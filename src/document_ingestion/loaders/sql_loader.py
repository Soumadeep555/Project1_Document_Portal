# src/document_ingestion/loaders/sql_loader.py
from pathlib import Path
from typing import Optional, List
import pandas as pd
from sqlalchemy import create_engine, inspect, text as sql_text
from .base import BaseLoader, LoadedDocument


class SqlLoader(BaseLoader):
    def __init__(self, url: Optional[str] = None):
        self.url = url

    def load(self, path: str) -> LoadedDocument:
        p = Path(path)
        engine_url = self.url or (f"sqlite:///{p}" if p.suffix in (".db", ".sqlite", ".sqlite3") else None)
        if not engine_url:
            raise ValueError("Provide a .db/.sqlite file or a SQLAlchemy connection URL")

        engine = create_engine(engine_url)
        insp = inspect(engine)
        tables = []
        text_pieces: List[str] = []
        with engine.connect() as conn:
            for tname in insp.get_table_names():
                df = pd.read_sql(sql_text(f"SELECT * FROM \"{tname}\""), conn)
                tables.append(df)
                text_pieces.append(f"[SQL:{tname}] {len(df)} rows x {len(df.columns)} cols")
        return LoadedDocument(source=str(p), text="\n".join(text_pieces), tables=tables, metadata={"engine_url": engine_url})
