from __future__ import annotations
import os
import sys
import json
import uuid
import hashlib
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import Iterable, List, Optional, Dict, Any

import fitz  # PyMuPDF
from langchain.schema import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import CSVLoader, UnstructuredExcelLoader, UnstructuredPowerPointLoader  # New imports for extended support

from utils.model_loader import ModelLoader
from logger.custom_logger import CustomLogger
from exception.custom_exception import DocumentPortalException

from utils.file_io import generate_session_id, save_uploaded_files
from utils.document_ops import load_documents, concat_for_analysis, concat_for_comparison  # Assuming load_documents is here or imported; integrated additions
from utils.extractors import extract_tables, extract_and_describe_images, load_sqlite_db  # New import from extractors

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".pptx", ".md", ".xlsx", ".csv", ".sql", ".db"}  # Extended with new types

# Module-level logger
log = CustomLogger().get_logger(__name__)

# Assuming load_documents is defined in this file or utils/document_ops.py; providing integrated version here with additions
def load_documents(file_path: str) -> List[Document]:
    """
    Loads documents from the file, including text, tables, and image descriptions.
    """
    try:
        extension = os.path.splitext(file_path)[1].lower()
        if extension not in SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file extension: {extension}")

        # Load base documents using appropriate loader
        if extension == '.pdf':
            loader = PyPDFLoader(file_path)
        elif extension == '.docx':
            loader = Docx2txtLoader(file_path)
        elif extension in {'.txt', '.md', '.sql'}:
            loader = TextLoader(file_path)
        elif extension == '.pptx':
            loader = UnstructuredPowerPointLoader(file_path)
        elif extension == '.xlsx':
            loader = UnstructuredExcelLoader(file_path)
        elif extension == '.csv':
            loader = CSVLoader(file_path)
        elif extension == '.db':
            return load_sqlite_db(file_path)  # Special handling for SQLite
        else:
            raise ValueError("Unknown loader")

        docs = loader.load()

        # Add extracted tables and images
        model_loader = ModelLoader()
        llm = model_loader.load_llm()
        provider = model_loader.get_provider()
        table_docs = extract_tables(file_path, extension)
        image_docs = extract_and_describe_images(file_path, extension, llm, provider)

        log.info("Documents loaded with extensions", file_path=file_path, base_count=len(docs), table_count=len(table_docs), image_count=len(image_docs))
        return docs + table_docs + image_docs

    except Exception as e:
        log.error(f"Document loading failed for {file_path}", error=str(e))
        raise DocumentPortalException("Document loading failed", sys) from e

# FAISS Manager (load-or-create)
class FaissManager:
    def __init__(self, index_dir: Path, model_loader: Optional[ModelLoader] = None):
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        self.meta_path = self.index_dir / "ingested_meta.json"
        self._meta: Dict[str, Any] = {"rows": {}} ## this is dict of rows
        
        if self.meta_path.exists():
            try:
                self._meta = json.loads(self.meta_path.read_text(encoding="utf-8")) or {"rows": {}} # load it if alrady there
            except Exception:
                self._meta = {"rows": {}} # init the empty one if dones not exists
        

        self.model_loader = model_loader or ModelLoader()
        self.emb = self.model_loader.load_embeddings()
        self.vs: Optional[FAISS] = None
        
    def _exists(self)-> bool:
        return (self.index_dir / "index.faiss").exists() and (self.index_dir / "index.pkl").exists()
    
    @staticmethod
    def _fingerprint(text: str, md: Dict[str, Any]) -> str:
        src = md.get("source") or md.get("file_path")
        rid = md.get("row_id")
        if src is not None:
            return f"{src}::{'' if rid is None else rid}"
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
    
    def _save_meta(self):
        self.meta_path.write_text(json.dumps(self._meta, ensure_ascii=False, indent=2), encoding="utf-8")
        
        
    def add_documents(self,docs: List[Document]):
        
        if self.vs is None:
            raise RuntimeError("Call load_or_create() before add_documents_idempotent().")
        
        new_docs: List[Document] = []
        
        for d in docs:
            
            key = self._fingerprint(d.page_content, d.metadata or {})
            if key in self._meta["rows"]:
                continue
            self._meta["rows"][key] = True
            new_docs.append(d)
            
        if new_docs:
            self.vs.add_documents(new_docs)
            self.vs.save_local(str(self.index_dir))
            self._save_meta()
        return len(new_docs)
    
    def load_or_create(self,texts:Optional[List[str]]=None, metadatas: Optional[List[dict]] = None):
        ## if we running first time then it will not go in this block
        if self._exists():
            self.vs = FAISS.load_local(
                str(self.index_dir),
                embeddings=self.emb,
                allow_dangerous_deserialization=True,
            )
            return self.vs
        
        
        if not texts:
            raise DocumentPortalException("No existing FAISS index and no data to create one", sys)
        self.vs = FAISS.from_texts(texts=texts, embedding=self.emb, metadatas=metadatas or [])
        self.vs.save_local(str(self.index_dir))
        return self.vs
        
        
class ChatIngestor:
    def __init__( self,
        temp_base: str = "data",
        faiss_base: str = "faiss_index",
        use_session_dirs: bool = True,
        session_id: Optional[str] = None,
    ):
        try:
            self.log = CustomLogger().get_logger(__name__)
            self.model_loader = ModelLoader()
            
            self.use_session = use_session_dirs
            self.session_id = session_id or generate_session_id()
            
            self.temp_base = Path(temp_base); self.temp_base.mkdir(parents=True, exist_ok=True)
            self.faiss_base = Path(faiss_base); self.faiss_base.mkdir(parents=True, exist_ok=True)
            
            self.temp_dir = self._resolve_dir(self.temp_base)
            self.faiss_dir = self._resolve_dir(self.faiss_base)
            
            self.log.info("ChatIngestor initialized",
                          session_id=self.session_id,
                          temp_dir=str(self.temp_dir),
                          faiss_dir=str(self.faiss_dir),
                          sessionized=self.use_session)
        except Exception as e:
            self.log.error("Failed to initialize ChatIngestor", error=str(e))
            raise DocumentPortalException("Initialization error in ChatIngestor", e) from e

    def _resolve_dir(self, base: Path) -> Path:
        if self.use_session:
            dir_path = base / self.session_id
            dir_path.mkdir(parents=True, exist_ok=True)
            return dir_path
        return base

    def build_retriever(self, uploaded_files, chunk_size=1000, chunk_overlap=200, k=5):  # Assuming this is the method name, corrected from 'built_retriver'
        try:
            saved_paths = save_uploaded_files(uploaded_files, self.temp_dir)
            docs = []
            for path in saved_paths:
                loaded_docs = load_documents(str(path))
                splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
                split_docs = splitter.split_documents(loaded_docs)
                docs.extend(split_docs)
            fm = FaissManager(self.faiss_dir)
            fm.load_or_create()
            added = fm.add_documents(docs)
            self.log.info("Retriever built", added_docs=added, session_id=self.session_id)
        except Exception as e:
            self.log.error("Failed to build retriever", error=str(e))
            raise DocumentPortalException("Retriever build failed", sys) from e

class DocHandler:
    def __init__(self, base_dir: str = "data/document_analysis", session_id: Optional[str] = None):
        self.log = CustomLogger().get_logger(__name__)
        self.base_dir = Path(base_dir)
        self.session_id = session_id or generate_session_id()
        self.session_path = self.base_dir / self.session_id
        self.session_path.mkdir(parents=True, exist_ok=True)
        self.log.info("DocHandler initialized", session_path=str(self.session_path))

    def save_pdf(self, uploaded_file):  # Renamed internally to save_file but kept name for compatibility; added extension check
        try:
            filename = uploaded_file.name
            extension = os.path.splitext(filename)[1].lower()
            if extension not in SUPPORTED_EXTENSIONS:
                raise ValueError(f"Unsupported file type: {extension}")
            save_path = self.session_path / filename
            with open(save_path, "wb") as f:
                if hasattr(uploaded_file, "read"):
                    f.write(uploaded_file.read())
                else:
                    f.write(uploaded_file.getbuffer())
            self.log.info("File saved successfully", file=filename, save_path=save_path, session_id=self.session_id)
            return save_path
        except Exception as e:
            self.log.error("Failed to save file", error=str(e), session_id=self.session_id)
            raise DocumentPortalException(f"Failed to save file: {str(e)}", sys) from e

    def read_pdf(self, pdf_path: str) -> str:  # Renamed internally to read_document but kept name; now uses load_documents
        try:
            docs = load_documents(pdf_path)
            text = "\n\n".join([d.page_content for d in docs])
            self.log.info("Document read successfully", pdf_path=pdf_path, session_id=self.session_id, pages=len(docs))
            return text
        except Exception as e:
            self.log.error("Failed to read document", error=str(e), pdf_path=pdf_path, session_id=self.session_id)
            raise DocumentPortalException(f"Could not process document: {pdf_path}", sys) from e

class DocumentComparator:
    """
    Save, read & combine documents for comparison with session-based versioning.
    """
    def __init__(self, base_dir: str = "data/document_compare", session_id: Optional[str] = None):
        self.log = CustomLogger().get_logger(__name__)
        self.base_dir = Path(base_dir)
        self.session_id = session_id or generate_session_id()
        self.session_path = self.base_dir / self.session_id
        self.session_path.mkdir(parents=True, exist_ok=True)
        self.log.info("DocumentComparator initialized", session_path=str(self.session_path))

    def save_uploaded_files(self, reference_file, actual_file):
        try:
            ref_ext = os.path.splitext(reference_file.name)[1].lower()
            act_ext = os.path.splitext(actual_file.name)[1].lower()
            if ref_ext not in SUPPORTED_EXTENSIONS or act_ext not in SUPPORTED_EXTENSIONS:
                raise ValueError("Unsupported file type.")
            ref_path = self.session_path / reference_file.name
            act_path = self.session_path / actual_file.name
            for fobj, out in ((reference_file, ref_path), (actual_file, act_path)):
                with open(out, "wb") as f:
                    if hasattr(fobj, "read"):
                        f.write(fobj.read())
                    else:
                        f.write(fobj.getbuffer())
            self.log.info("Files saved", reference=str(ref_path), actual=str(act_path), session=self.session_id)
            return ref_path, act_path
        except Exception as e:
            self.log.error("Error saving files", error=str(e), session=self.session_id)
            raise DocumentPortalException("Error saving files", sys) from e

    def read_pdf(self, pdf_path: Path) -> str:  # Kept name but now handles general documents
        try:
            docs = load_documents(str(pdf_path))
            parts = []
            for d in docs:
                if d.metadata.get("type") == "table":
                    parts.append(f"\n --- Table --- \n{d.page_content}")
                elif d.metadata.get("type") == "image":
                    parts.append(f"\n --- Image Description --- \n{d.page_content}")
                else:
                    parts.append(d.page_content)
            self.log.info("Document read successfully", file=str(pdf_path), parts=len(parts))
            return "\n".join(parts)
        except Exception as e:
            self.log.error("Error reading document", file=str(pdf_path), error=str(e))
            raise DocumentPortalException("Error reading document", sys) from e

    def combine_documents(self) -> str:
        try:
            doc_parts = []
            for file in sorted(self.session_path.iterdir()):
                if file.is_file() and file.suffix.lower() in SUPPORTED_EXTENSIONS:
                    content = self.read_pdf(file)
                    doc_parts.append(f"Document: {file.name}\n{content}")
            combined_text = "\n\n".join(doc_parts)
            self.log.info("Documents combined", count=len(doc_parts), session=self.session_id)
            return combined_text
        except Exception as e:
            self.log.error("Error combining documents", error=str(e), session=self.session_id)
            raise DocumentPortalException("Error combining documents", sys) from e

    def clean_old_sessions(self, keep_latest: int = 3):
        try:
            sessions = sorted([f for f in self.base_dir.iterdir() if f.is_dir()], reverse=True)
            for folder in sessions[keep_latest:]:
                shutil.rmtree(folder, ignore_errors=True)
                self.log.info("Old session folder deleted", path=str(folder))
        except Exception as e:
            self.log.error("Error cleaning old sessions", error=str(e))
            raise DocumentPortalException("Error cleaning old sessions", sys) from e