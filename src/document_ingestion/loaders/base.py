# src/document_ingestion/loaders/base.py
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import pandas as pd


@dataclass
class ImageBlob:
    path: str
    source: str
    page_or_index: Optional[int] = None
    metadata: Dict = field(default_factory=dict)


@dataclass
class LoadedDocument:
    source: str
    text: str = ""
    tables: List[pd.DataFrame] = field(default_factory=list)
    images: List[ImageBlob] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)


class BaseLoader:
    """Loader interface — implement load(path: str) -> LoadedDocument"""

    def load(self, path: str) -> LoadedDocument:
        raise NotImplementedError
