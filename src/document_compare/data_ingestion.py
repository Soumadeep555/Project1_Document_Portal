import sys
from pathlib import Path
import fitz
from logger.custom_logger import CustomLogger
from exception.custom_exception import DocumentPortalException

class DocumentComparator:
    def __init__(self):
        pass

    def delete_existing_files(self):
        """
        Deletes all existing files in the specified directory.
        """
        pass

    def save_uploaded_files(self):
        """
        Saves uploaded files to the specified directory.
        """
        pass

    def read_pdf(self):
        """
        Reads a PDF file and extracts its text content from each page.
        """
        pass