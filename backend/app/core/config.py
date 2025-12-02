import os
from pydantic_settings import BaseSettings
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "Uffizio RAG"
    API_V1_STR: str = "/api/v1"
    
    # Gemini
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    EMBEDDING_MODEL: str = "models/gemini-embedding-001"
    GENERATION_MODEL: str = "gemini-2.5-flash"
    
    # Paths
    DATA_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data")
    KNOWLEDGE_FILE: str = "uffizio_knowledge.txt"
    INDEX_FILE: str = "faiss_index.bin"
    METADATA_FILE: str = "metadata.jsonl"
    
    # RAG
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    BATCH_SIZE: int = 10
    TOP_K: int = 8
    
    # Auth
    API_KEY_HEADER: str = "x-api-key"
    ADMIN_API_KEY: str = os.getenv("ADMIN_API_KEY", "secret-key")

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
os.makedirs(settings.DATA_DIR, exist_ok=True)
