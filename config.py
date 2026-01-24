from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # LLM Configuration
    openai_api_base: str
    openai_api_key: str
    model_name: str = "gpt-4o"

    # Server Configuration
    port: int = 8000
    host: str = "0.0.0.0"
    log_level: str = "INFO"

    # Optional
    debug: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )


settings = Settings()
