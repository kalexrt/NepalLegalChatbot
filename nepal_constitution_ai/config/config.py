import os
from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: str
    LANGSMITH_API_KEY: str
    PINECONE_API_KEY: str
    OPENAI_API_KEY: str
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIM: str = "1536"
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    VECTOR_DB: str = "pinecone"
    PINECONE_INDEX: str = ""
    PINECONE_CLOUD: str = "aws"
    PINECONE_REGION: str = "us-east-1"
    CHUNK_SIZE:int = 800
    VECTORS_UPLOAD_BATCH_SIZE: int = 200
    CHUNK_OVERLAP:int = 200
    TOP_K:int = 8
    CREATE_NAMESPACE: bool = False
    FILE_PATH: str=" data/nepal_constitution_2072.pdf"
    DOWNLOADED_PDF_PATH: str = "data/downloaded_pdfs"
    OCR_JSON_FOLDER_PATH: str = "data/ocr_json"
    EMBS_JSON_FOLDER_PATH: str = "data/embeddings"
    OCR_JSON_BATCH_SIZE: int = 5
    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
os.environ["LANGCHAIN_TRACING_V2"]="true" # enables the tracing
os.environ["LANGCHAIN_ENDPOINT"]="https://api.smith.langchain.com"
os.environ["LANGCHAIN_API_KEY"]=settings.LANGSMITH_API_KEY
os.environ["LANGCHAIN_PROJECT"]="RAG-FINAL_PROJECT_NEPALI_EMBS"
__all__ = ["settings"]