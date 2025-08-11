import sys
import os
from operator import itemgetter
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.vectorstores import FAISS
from utils.model_loader import ModelLoader
from exception.custom_exception import DocumentPortalException
from logger.custom_logger import CustomLogger
from prompt.prompt_library import PROMPT_REGISTRY
from model.models import PromptType


class ConversationalRAG:
    def __init__(self,session_id:str, retriever=None):
        try:
            self.log = CustomLogger().get_logger(__name__)
            self.session_id = session_id
            self.retriever = retriever
            self.llm = self._load_llm()
            self.contextualize_prompt: ChatPromptTemplate = PROMPT_REGISTRY[PromptType.CONTEXTUALIZE_QUESTION.value]
            self.qa_prompt: ChatPromptTemplate = PROMPT_REGISTRY[PromptType.CONTEXT_QA.value]
            if retriever is None:
                raise ValueError("Retriever cannot be None")
            self.retriever = retriever
            self._build_lcel_chain()
            self.log.info("ConversationalRAG initialized", session_id=self.session_id)

        except Exception as e:
            self.log.error("Failed to initialize ConversationalRAG", error=str(e))
            raise DocumentPortalException("Initialization error in ConversationalRAG", sys)

    def load_retriever_from_faiss(self,index_path:str):
        """
        Load a FAISS vectorstore from disk and convert to retriever
        """

        try:
            embeddings = ModelLoader().load_embeddings()
            if not os.path.isdir(index_path):
                raise FileNotFoundError(f"FAISS index directory not found: {index_path}")
            
            FAISS.load_local(
                index_path,
                embeddings,
                allow_dangerous_deserialization=True
            )

        except Exception as e:
            self.log.error("Failed to load retriever from FAISS", error=str(e))
            raise DocumentPortalException("Loading error in ConversationalRAG", sys)

    def invoke(self):
        pass

    def _load_llm(self):
        pass

    @staticmethod
    def _format_docs(docs):
        pass

    def _build_lcel_chain(self):
        pass



