"""GraphWeave Application Configuration Module.
Loads settings from environment variables and .env file with validation.
"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    APP_NAME: str = "GraphWeave"
    APP_ENV: str = "development"
    APP_PORT: int = 8000
    APP_HOST: str = "0.0.0.0"
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str = "dev-insecure-secret-key-change-in-production"

    # Multi-Tenancy & Corpus Defaults
    DEFAULT_TENANT_ID: str = "tenant-default"
    DEFAULT_CORPUS_ID: str = "corpus-primary"

    # PostgreSQL + pgvector
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "graphweave"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/graphweave"

    # Neo4j Graph Database
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "graphweave_secret"
    NEO4J_DATABASE: str = "neo4j"

    # LLM & Embedding Adapter Configuration
    LLM_PROVIDER: str = "mock"  # "mock", "openai", "azure_openai", "ollama"
    EMBEDDING_PROVIDER: str = "mock"
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    LLM_MODEL_NAME: str = "gpt-4o-mini"
    EMBEDDING_MODEL_NAME: str = "text-embedding-3-small"
    EMBEDDING_DIMENSION: int = 1536

    # Graph Traversal Bounds & Query Budgets
    MAX_TRAVERSAL_DEPTH: int = 2
    MAX_FAN_OUT: int = 15
    TRAVERSAL_TIMEOUT_SECONDS: float = 5.0
    QUERY_BUDGET_MAX_NODES: int = 100
    CONFIDENCE_THRESHOLD: float = 0.65

    # Feature Flags
    ENABLE_MOCK_FALLBACK: bool = True
    ENABLE_DETAILED_TELEMETRY: bool = True
    CORS_ORIGINS: List[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
        ]
    )


settings = Settings()
