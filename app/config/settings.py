from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # =========================
    # Application
    # =========================

    app_name: str = "Larvi"
    app_env: str = "development"
    debug: bool = True

    backend_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:8000"

    # =========================
    # LLM - Ollama Cloud
    # =========================

    ollama_api_key: str
    ollama_model: str = "qwen3:8b"

    # =========================
    # Google OAuth
    # =========================

    google_client_id: str
    google_client_secret: str

    google_redirect_uri: str = (
        "http://localhost:8000/auth/callback"
    )

    # =========================
    # Google APIs
    # =========================

    google_gmail_scopes: str = (
        "https://www.googleapis.com/auth/gmail.readonly "
        "https://www.googleapis.com/auth/gmail.send "
        "https://www.googleapis.com/auth/gmail.compose "
        "https://www.googleapis.com/auth/gmail.modify"
    )

    google_calendar_scopes: str = (
        "https://www.googleapis.com/auth/calendar"
    )

    # =========================
    # Configuration
    # =========================

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()