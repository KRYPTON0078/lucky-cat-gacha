"""Environment-based configuration for RepoPulse."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT_DIR / ".env"
DEFAULT_PRIVATE_KEY_PATH = ROOT_DIR / "private-key.pem"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH) if ENV_PATH.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_id: str = ""
    app_slug: str = ""
    webhook_secret: str = ""
    private_key_path: str = str(DEFAULT_PRIVATE_KEY_PATH)
    support_email: str = "magnedinanevesdina@gmail.com"
    github_api_base: str = "https://api.github.com"
    app_name: str = "RepoPulse"
    host: str = "0.0.0.0"
    port: int = 8000
    public_base_url: str = ""
    github_app_create_url: str = "https://github.com/settings/apps/new"

    @property
    def configured(self) -> bool:
        return bool(self.app_id and self.webhook_secret and Path(self.private_key_path).is_file())

    @property
    def private_key_pem(self) -> str:
        path = Path(self.private_key_path)
        if not path.is_file():
            raise FileNotFoundError(
                f"GitHub App private key not found at {path.resolve()}. "
                "Complete /setup (App Manifest) or set PRIVATE_KEY_PATH."
            )
        return path.read_text(encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()


def reload_settings() -> Settings:
    get_settings.cache_clear()
    return get_settings()
