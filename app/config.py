from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    anthropic_api_key: str | None = None
    jobs_dir: str = "./jobs"
    max_upload_size_mb: int = 10
    default_machine_rate_inr: float = 800.0
    default_margin_pct: float = 20.0
    log_level: str = "INFO"
    inr_to_usd_rate: float = 83.5

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def ai_enabled(self) -> bool:
        return bool(self.anthropic_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
