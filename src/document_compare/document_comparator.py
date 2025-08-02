import sys
from dotenv import load_dotenv
import pandas as pd
from logger.custom_logger import CustomLogger
from exception.custom_exception import DocumentPortalException
from model.models import *
from prompt.prompt_library import PROMPT_REGISTRY
from utils.model_loader import ModelLoader
from langchain_core.output_parsers import JsonOutputParser
from langchain.output_parsers import OutputFixingParser

class DocumentComparatorLLM:
    def __init__(self):
        load_dotenv()
        self.log = CustomLogger().get_logger(__name__)
        self.loader = ModelLoader()
        self.llm = self.loader.load_llm()
        self.parser = JsonOutputParser(pydantic_object=SummaryResponse)
        self.fixing_parser = OutputFixingParser.from_llm(parser=self.parser, llm=self.llm)
        self.prompt = PROMPT_REGISTRY["document_comparison"]
        self.chain = self.prompt | self.llm | self.parser | self.fixing_parser
        self.log.info("DocumentComparatorLLM initialized successfully with model and parser")

    def compare_documents(self):
        """
        Compares two documents and returns a structured summary of changes.
        """
        try:
            pass

        except Exception as e:
            self.log.error("Error during document comparison", error=str(e))
            raise DocumentPortalException("An error occurred during document comparison") from e

    def _format_response(self):
        """
        Formats the response from the LLM into a structured format.
        """
        try:
            pass

        except Exception as e:
            self.log.error("Error formatting response", error=str(e))
            raise DocumentPortalException("Error formatting response") from e

