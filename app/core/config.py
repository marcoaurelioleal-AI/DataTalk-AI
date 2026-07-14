from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/datatalk",
        alias="DATABASE_URL",
    )
    query_database_url: str = Field(
        default="postgresql+psycopg://datatalk_reader:datatalk_reader@localhost:5432/datatalk",
        alias="QUERY_DATABASE_URL",
    )
    secret_key: str = Field(default="change_this_secret_key_use_at_least_32_chars", alias="SECRET_KEY")
    algorithm: str = Field(default="HS256", alias="ALGORITHM")
    access_token_expire_minutes: int = Field(default=60, alias="ACCESS_TOKEN_EXPIRE_MINUTES")

    llm_provider: str = Field(default="mock", alias="LLM_PROVIDER")
    llm_request_timeout_seconds: float = Field(default=30, gt=0, alias="LLM_REQUEST_TIMEOUT_SECONDS")
    llm_max_retries: int = Field(default=2, ge=0, le=5, alias="LLM_MAX_RETRIES")
    llm_retry_backoff_seconds: float = Field(default=0.25, ge=0, alias="LLM_RETRY_BACKOFF_SECONDS")
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    gemini_chat_model: str = Field(default="gemini-2.5-flash", alias="GEMINI_CHAT_MODEL")
    openai_api_key: str = Field(default="your_openai_key_here", alias="OPENAI_API_KEY")
    openai_chat_model: str = Field(default="gpt-4o-mini", alias="OPENAI_CHAT_MODEL")

    query_max_rows: int = Field(default=100, alias="QUERY_MAX_ROWS")
    default_query_limit: int = Field(default=20, alias="DEFAULT_QUERY_LIMIT")
    query_statement_timeout_ms: int = Field(default=5_000, gt=0, alias="QUERY_STATEMENT_TIMEOUT_MS")
    query_lock_timeout_ms: int = Field(default=1_000, gt=0, alias="QUERY_LOCK_TIMEOUT_MS")

    environment: str = Field(default="development", alias="ENVIRONMENT")
    cors_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        alias="CORS_ORIGINS",
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
