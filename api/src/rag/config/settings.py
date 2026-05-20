from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Mistral AI
    mistral_api_key: str | None = None
    mistral_chat_model: str = "mistral-large-latest"
    mistral_small_chat_model: str = "mistral-small-latest"
    mistral_embed_model: str = "mistral-embed"

    # Storage
    storage_provider: str = "local"  # "local", "minio", "gcs"
    gcs_bucket_name: str = "simplon-rag-corpus"
    minio_endpoint: str = "http://localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"

    # Database connection pool
    db_pool_size: int = 5
    db_max_overflow: int = 10

    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "rag"
    postgres_user: str = "rag_user"
    postgres_password: str
    postgres_schema: str = "rag"

    # Application
    app_env: str = "development"
    app_log_level: str = "INFO"
    app_port: int = 8000

    # Observability
    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None
    langfuse_host: str = "https://cloud.langfuse.com"

    # RAG tuning
    chunk_size: int = 512
    chunk_overlap: int = 64
    retrieval_top_k: int = 5

    # Web loader
    web_max_pages: int = 100

    # Agent
    product_name: str = "Dev IA"
    agent_max_retries: int = 2

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def database_url_sync(self) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
