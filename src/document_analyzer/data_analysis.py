from typing import List, Optional
from pathlib import Path
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema import Document
from pydantic import BaseModel
from logger.custom_logger import CustomLogger
from exception.custom_exception import DocumentPortalException
from utils.model_loader import ModelLoader
import sys
import time  # Added for rate limiting

log = CustomLogger().get_logger(__name__)

class Metadata(BaseModel):
    Summary: List[str]
    Title: str
    Author: str
    DateCreated: str
    LastModifiedDate: str
    Publisher: str
    Language: str
    PageCount: str
    SentimentTone: str

def analyze_document(docs: List[Document], file_path: Path) -> Metadata:
    """
    Analyzes document content to extract metadata using an LLM, processing chunks individually with rate limiting.
    """
    try:
        model_loader = ModelLoader()
        llm = model_loader.load_llm()
        parser = PydanticOutputParser(pydantic_object=Metadata)

        prompt = ChatPromptTemplate.from_template(
            """
            Analyze the following document content and extract metadata including a summary, title, author, creation date,
            last modified date, publisher, language, page count, and sentiment tone.
            If metadata is not explicitly available, infer it or mark as "Not Available".
            Provide the output in the following JSON format:
            {format_instructions}

            Content:
            {content}
            """
        ).partial(format_instructions=parser.get_format_instructions())

        chain = prompt | llm | parser

        # Split documents into smaller chunks for analysis to avoid TPM limits
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)  # Reduced chunk size
        split_docs = []
        for doc in docs:
            split_texts = splitter.split_text(doc.page_content)
            for i, text in enumerate(split_texts):
                split_docs.append(Document(
                    page_content=text,
                    metadata={**doc.metadata, "analysis_chunk_index": i}
                ))

        # Process each chunk individually with a delay to avoid rate limits
        summaries = []
        metadata = None
        for doc in split_docs:
            response = chain.invoke({
                "content": doc.page_content
            })
            summaries.extend(response.Summary)
            if metadata is None:  # Use first chunk's metadata as base
                metadata = response
            time.sleep(2)  # Delay to respect Groq API rate limits

        # Aggregate metadata (use first chunk's metadata for fields like Title, Author, etc.)
        if metadata is None:
            raise ValueError("No metadata extracted from document chunks")

        metadata.Summary = summaries  # Combine summaries from all chunks
        log.info("Document analyzed successfully", file_path=str(file_path), chunks=len(split_docs))
        return metadata

    except Exception as e:
        log.error("Metadata extraction failed", file_path=str(file_path), error=str(e))
        raise DocumentPortalException("Metadata extraction failed", sys) from e

class DocumentAnalyzer:
    """
    A class to handle document analysis, providing an interface for metadata extraction.
    """
    def __init__(self):
        self.log = CustomLogger().get_logger(__name__)

    def analyze_document(self, docs: List[Document], file_path: Path) -> Metadata:
        """
        Analyzes the provided documents and returns metadata.
        """
        try:
            result = analyze_document(docs, file_path)
            self.log.info("Document analysis completed", file_path=str(file_path))
            return result
        except Exception as e:
            self.log.error("Document analysis failed", file_path=str(file_path), error=str(e))
            raise DocumentPortalException("Document analysis failed", sys) from e