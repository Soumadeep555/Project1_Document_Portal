# tests/test_processors.py
from src.document_ingestion.data_ingestion import load_document
from src.document_processors.analysis import text_summary
from src.document_processors.comparison import compare_texts

def test_analysis_text():
    d = load_document("tests/fixtures/sample.txt")
    s = text_summary(d)
    assert isinstance(s, str)

def test_compare():
    a = load_document("tests/fixtures/sample.txt")
    b = load_document("tests/fixtures/sample2.txt")
    r = compare_texts(a, b)
    assert "cosine_similarity" in r
