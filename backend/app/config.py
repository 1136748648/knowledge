from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Knowledge Platform"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://knowledge:knowledge123@localhost:5432/knowledge"
    DATABASE_USER: str = "knowledge"
    DATABASE_PASSWORD: str = "knowledge123"
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str = "knowledge"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str | None = None

    # Heatmap
    HEATMAP_ENABLED: bool = True
    HEATMAP_REDIS_TTL: int = 86400
    HEATMAP_AGGREGATE_INTERVAL: int = 5

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
    LLM_PROVIDER: str = "openai"
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

    # Built-in Admin (for initial setup)
    BUILTIN_ADMIN_USER: str = "builtin-admin"
    BUILTIN_ADMIN_PASS: str = "admin123"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


def validate_settings(settings: Settings) -> None:
    """验证必需的环境变量"""
    errors = []
    
    if not settings.ENCRYPTION_KEY:
        logger.warning("WARNING: ENCRYPTION_KEY is not set. Using default secret for local development only.")
    
    if not settings.DATABASE_URL and (not settings.DATABASE_USER or not settings.DATABASE_PASSWORD):
        errors.append("DATABASE_URL or DATABASE_USER/DATABASE_PASSWORD is required")
    
    if errors:
        raise ValueError("Configuration validation failed:\n" + "\n".join(f"- {e}" for e in errors))


@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    validate_settings(settings)
    return settings


def reload_settings() -> Settings:
    """清除缓存并重新加载配置（初始化后调用）"""
    get_settings.cache_clear()
    return get_settings()
