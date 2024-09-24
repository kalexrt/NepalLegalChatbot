from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    POSTGRES_USER: str = ""
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = ""
    POSTGRES_HOST: str = ""
    POSTGRES_PORT: str = ""
    LANGSMITH_API_KEY: str = ""
    PINECONE_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIM: int = 1536
    OPENAI_MODEL: str = ""
    PINECONE_INDEX: str = "test"
    PINECONE_CLOUD: str = "aws"
    PINECONE_REGION: str = "us-east-1"
    FILE_PATH: str = "data/nepal_constitution_2072.pdf"
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()

__all__ = ["settings"]