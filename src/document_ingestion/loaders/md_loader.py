# src/document_ingestion/loaders/md_loader.py
from pathlib import Path
from bs4 import BeautifulSoup
from markdown import markdown
import pandas as pd
from .base import BaseLoader, LoadedDocument


class MdLoader(BaseLoader):
    def load(self, path: str) -> LoadedDocument:
        p = Path(path)
        raw = p.read_text(encoding="utf-8", errors="ignore")
        html = markdown(raw, extensions=["tables"])
        soup = BeautifulSoup(html, "html.parser")

        # extract text
        text = soup.get_text(separator="\n")

        # extract markdown tables as DataFrames
        tables = []
        for tbl in soup.find_all("table"):
            rows = []
            for tr in tbl.find_all("tr"):
                cells = [c.get_text(strip=True) for c in tr.find_all(["td", "th"])]
                if cells:
                    rows.append(cells)
            if rows:
                header = rows[0]
                data = rows[1:] if len(rows) > 1 else []
                if data:
                    tables.append(pd.DataFrame(data, columns=header))
        return LoadedDocument(source=str(p), text=text, tables=tables)
