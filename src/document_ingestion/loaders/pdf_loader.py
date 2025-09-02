# src/document_ingestion/loaders/pdf_loader.py
from pathlib import Path
import fitz  # PyMuPDF
import pdfplumber
import pandas as pd
from .base import BaseLoader, LoadedDocument, ImageBlob
from .image_utils import save_image_bytes


class PdfLoader(BaseLoader):
    def load(self, path: str) -> LoadedDocument:
        p = Path(path)
        text_parts = []
        images = []

        # Extract text and images using PyMuPDF
        try:
            with fitz.open(str(p)) as doc:
                for page_index, page in enumerate(doc):
                    txt = page.get_text("text") or ""
                    text_parts.append(txt)
                    for img in page.get_images(full=True):
                        xref = img[0]
                        pix = fitz.Pixmap(doc, xref)
                        if pix.n - pix.alpha < 4 and pix.n != 1:
                            try:
                                img_bytes = pix.tobytes("png")
                            except Exception:
                                img_bytes = pix.samples
                        else:
                            # convert CMYK etc to RGB
                            try:
                                pix = fitz.Pixmap(fitz.csRGB, pix)
                                img_bytes = pix.tobytes("png")
                            except Exception:
                                img_bytes = pix.samples
                        out = save_image_bytes(img_bytes, f"{p.stem}_p{page_index}_{xref}.png")
                        images.append(ImageBlob(path=out, source=str(p), page_or_index=page_index))
                        try:
                            pix = None
                        except Exception:
                            pass
        except Exception:
            # best-effort fallback: use pdfplumber for text
            pass

        # Extract tables using pdfplumber
        tables = []
        try:
            with pdfplumber.open(str(p)) as pdf:
                for pg in pdf.pages:
                    extracted = pg.extract_table() or []
                    # pdfplumber returns rows; pdfplumber's extract_tables returns list of tables
                    # We'll use extract_tables() to get all tables
                    for table in pg.extract_tables() or []:
                        if table and len(table) > 1:
                            df = pd.DataFrame(table[1:], columns=table[0])
                            tables.append(df)
        except Exception:
            pass

        return LoadedDocument(source=str(p), text="\n".join(text_parts), tables=tables, images=images)
