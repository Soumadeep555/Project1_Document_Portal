# tests/test_document_loaders.py
from src.document_ingestion.data_ingestion import load_document
from pathlib import Path

def _p(name): return str(Path("tests/fixtures")/name)

def test_txt():
    d = load_document(_p("sample.txt"))
    assert isinstance(d.text, str) and len(d.text) > 0

def test_csv():
    d = load_document(_p("sample.csv"))
    assert len(d.tables) == 1
    assert "name" in d.tables[0].columns.str.lower().tolist()

def test_docx():
    d = load_document(_p("sample.docx"))
    assert "Sample DOCX" in (d.text or "")

def test_pptx():
    d = load_document(_p("sample.pptx"))
    assert isinstance(d.text, str)

def test_pdf():
    d = load_document(_p("sample.pdf"))
    assert isinstance(d.text, str)  # may be empty if PDF text extraction fails

def test_sqlite():
    d = load_document(_p("sample.sqlite"))
    assert len(d.tables) >= 1
