from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_ENV: Literal["development", "production", "testing"] = "development"
    APP_DEBUG: bool = True
    APP_SECRET_KEY: str = "default-development-secret-key-change-it"

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/talentmind"
    SQLITE_DATABASE_URL: str = "sqlite+aiosqlite:///./talentmind.db"
    REDIS_URL: str = "redis://localhost:6379/0"

    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    JSON_LOGS: bool = False

    CACHE_DIR: str = ".cache"
    UPLOAD_DIR: str = "uploads"
    PROCESSING_BATCH_SIZE: int = 1000

    # Semantic Search Settings
    EMBEDDING_PROVIDER: str = "local"
    EMBEDDING_MODEL: str = "BAAI/bge-base-en-v1.5"
    EMBEDDING_DIMENSION: int = 768
    VECTOR_INDEX_TYPE: str = "flat"
    VECTOR_METRIC: str = "cosine"
    VECTOR_INDEX_PATH: str = "vector_indices"
    TOP_K_DEFAULT: int = 1000
    EMBEDDING_CACHE_DIR: str = ".embeddings_cache"
    
    # Reranking Settings
    RERANK_MODEL: str = "BAAI/bge-reranker-base"
    TOP_K_RERANK: int = 20


    # Feature Flags
    FLAG_SEMANTIC_SEARCH: bool = True
    FLAG_EMBEDDING_ENGINE: bool = True
    FLAG_BEHAVIOR_ENGINE: bool = True
    FLAG_EVIDENCE_ENGINE: bool = True
    FLAG_ANALYTICS: bool = True
    FLAG_EXPLAINABILITY: bool = True
    FLAG_KNOWLEDGE_GRAPH: bool = True
    FLAG_AUTHENTICATION: bool = False

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def get_database_url(self) -> str:
        # Fallback to SQLite if DATABASE_URL is unset, default, or explicitly set to sqlite
        if self.DATABASE_URL and self.DATABASE_URL.startswith("postgresql"):
            return self.DATABASE_URL
        return self.SQLITE_DATABASE_URL

settings = Settings()
