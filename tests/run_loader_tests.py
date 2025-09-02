# tests/run_loader_tests.py
from pathlib import Path
from src.document_ingestion.data_ingestion import load_document

fixtures = Path("tests/fixtures").glob("*")
ok = []
fail = []

for p in sorted(fixtures):
    print("----")
    print("TEST FILE:", p.name)
    try:
        doc = load_document(str(p))
        print("source:", doc.source)
        txt_snip = (doc.text or "")[:200].replace("\n", "\\n")
        print("text_preview:", txt_snip or "<no-text>")
        print("tables_count:", len(doc.tables or []))
        # print table shapes
        for i, t in enumerate(doc.tables or []):
            try:
                print(f"  table[{i}]: {t.shape}")
            except Exception:
                print(f"  table[{i}]: <unreadable DataFrame>")
        print("images_count:", len(doc.images or []))
        for i, im in enumerate(doc.images or []):
            print(f"  img[{i}]: {im.path} (page/index={im.page_or_index})")
        ok.append(p.name)
    except Exception as e:
        print("FAILED:", e)
        fail.append((p.name, str(e)))

print("==== SUMMARY ====")
print("OK:", ok)
print("FAILED:", fail)
