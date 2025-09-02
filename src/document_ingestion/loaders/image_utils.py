# src/document_ingestion/loaders/image_utils.py
from pathlib import Path
import os

DEFAULT_IMG_OUT = Path("static/uploads/images")


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def save_image_bytes(img_bytes: bytes, filename_hint: str) -> str:
    """
    Save image bytes under static/uploads/images and return the saved path string.
    """
    ensure_dir(DEFAULT_IMG_OUT)
    safe_name = filename_hint.replace(os.sep, "_").replace(" ", "_")
    out_path = DEFAULT_IMG_OUT / safe_name
    # ensure extension
    if not out_path.suffix:
        out_path = out_path.with_suffix(".png")
    with open(out_path, "wb") as f:
        f.write(img_bytes)
    return str(out_path)
