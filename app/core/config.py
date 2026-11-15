from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./clinic.db"
    api_key: str = "change-me"
    rate_limit_attempts: int = 5
    rate_limit_window_seconds: int = 60
    seed_demo_slots: bool = True


settings = Settings()
