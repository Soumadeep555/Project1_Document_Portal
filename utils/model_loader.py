import os
import sys
from dotenv import load_dotenv
from yaml import safe_load
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from logger.custom_logger import CustomLogger
from exception.custom_exception import DocumentPortalException

load_dotenv()
log = CustomLogger().get_logger(__name__)

class ModelLoader:
    """
    Loads LLMs and embeddings based on config.yaml.
    """
    def __init__(self):
        self.provider = None
        self.log = CustomLogger().get_logger(__name__)
        try:
            with open("config/config.yaml", "r") as f:
                self.config = safe_load(f)
            self.log.info("Config loaded successfully")
        except Exception as e:
            self.log.error(f"Failed to load config: {e}")
            raise DocumentPortalException("Config loading failed", sys) from e

    def load_llm(self):
        try:
            if "groq" in self.config["llm"]:
                self.provider = "groq"
                api_key = os.getenv("GROQ_API_KEY")
                if not api_key:
                    raise ValueError("GROQ_API_KEY not set")
                return ChatGroq(
                    model=self.config["llm"]["groq"]["model_name"],
                    temperature=self.config["llm"]["groq"]["temperature"],
                    max_tokens=self.config["llm"]["groq"]["max_output_tokens"],
                    api_key=api_key,
                )
            elif "google" in self.config["llm"]:
                self.provider = "google"
                api_key = os.getenv("GOOGLE_API_KEY")
                if not api_key:
                    raise ValueError("GOOGLE_API_KEY not set")
                return ChatGoogleGenerativeAI(
                    model=self.config["llm"]["google"]["model_name"],
                    temperature=self.config["llm"]["google"]["temperature"],
                    max_output_tokens=self.config["llm"]["google"]["max_output_tokens"],
                    google_api_key=api_key,
                )
            else:
                raise ValueError("No valid LLM provider in config")
        except Exception as e:
            self.log.error(f"Failed to load LLM: {e}")
            raise DocumentPortalException("LLM loading failed", sys) from e

    def load_embeddings(self):
        try:
            emb_config = self.config["embedding_model"]
            if emb_config["provider"] == "google":
                api_key = os.getenv("GOOGLE_API_KEY")
                if not api_key:
                    raise ValueError("GOOGLE_API_KEY not set")
                return GoogleGenerativeAIEmbeddings(
                    model=emb_config["model_name"],
                    google_api_key=api_key,
                )
            else:
                raise ValueError("No valid embedding provider in config")
        except Exception as e:
            self.log.error(f"Failed to load embeddings: {e}")
            raise DocumentPortalException("Embeddings loading failed", sys) from e

    def get_provider(self) -> str:
        if self.provider is None:
            self.load_llm()  # Load to set provider if not already
        return self.provider