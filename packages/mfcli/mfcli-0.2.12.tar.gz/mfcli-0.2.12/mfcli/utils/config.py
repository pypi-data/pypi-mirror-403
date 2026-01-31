from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from mfcli.constants.openai import OPENAI_DEFAULT_EMBEDDING_MODEL, OPENAI_DEFAULT_EMBEDDING_DIMENSIONS
from mfcli.utils.directory_manager import app_dirs


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    digikey_client_id: str
    digikey_client_secret: str
    openai_api_key: str
    google_api_key: str
    log_level: str = Field(default="INFO")
    use_docling: bool = Field(default=True)
    chunk_tokens: int = Field(default=2000)
    chunk_size: int = Field(default=500)
    chunk_overlap: int = Field(default=50)
    embedding_model: str = Field(default=OPENAI_DEFAULT_EMBEDDING_MODEL)
    embedding_dimensions: int = Field(default=OPENAI_DEFAULT_EMBEDDING_DIMENSIONS)

    model_config = SettingsConfigDict(
        env_file=str(app_dirs.env_file_path),
        extra="allow",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


@lru_cache
def get_config() -> Settings:
    """Get cached application settings."""
    return Settings()
