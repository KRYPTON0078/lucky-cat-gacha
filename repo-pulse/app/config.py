"""Environment-based configuration for RepoPulse."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_id: str = ""
    webhook_secret: str = ""
    private_key_path: str = "./private-key.pem"
    support_email: str = "support@example.com"
    github_api_base: str = "https://api.github.com"
    app_name: str = "RepoPulse"
    host: str = "0.0.0.0"
    port: int = 8000

    @property
    def private_key_pem(self) -> str:
        path = Path(self.private_key_path)
        if not path.is_file():
            raise FileNotFoundError(
                f"GitHub App private key not found at {path.resolve()}. "
                "Download the .pem from your GitHub App settings and set PRIVATE_KEY_PATH."
            )
        return path.read_text(encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
