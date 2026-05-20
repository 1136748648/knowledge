from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Knowledge Platform"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://knowledge:knowledge123@localhost:5432/knowledge"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Milvus
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_COLLECTION: str = "knowledge_vectors"

    # Keycloak
    KEYCLOAK_SERVER_URL: str = "http://localhost:8080"
    KEYCLOAK_REALM: str = "knowledge-platform"
    KEYCLOAK_CLIENT_ID: str = "knowledge-backend"
    KEYCLOAK_CLIENT_SECRET: str = ""

    # JWT
    JWT_ALGORITHM: str = "RS256"
    JWT_AUDIENCE: str = "knowledge-platform"

    # LLM
    LLM_API_BASE: str = "https://api.openai.com/v1"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4"
    LLM_EMBEDDING_MODEL: str = "text-embedding-3-small"
    LLM_EMBEDDING_DIM: int = 1536

    # Security
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    ENCRYPTION_KEY: str = ""  # Fernet key for sensitive config encryption

    # Audit
    AUDIT_LOG_ENABLED: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
