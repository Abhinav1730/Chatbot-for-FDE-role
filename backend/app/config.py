from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    llm_model: str = "google/gemma-4-26b-a4b-it:free"
    analytics_model: str = "google/gemma-4-26b-a4b-it:free"
    booking_mode: str = "success"
    cors_origins: str = "http://localhost:3000"


settings = Settings()
