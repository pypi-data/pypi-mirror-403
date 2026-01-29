"""Configuration settings for OBS Controller."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class OBSSettings(BaseSettings):
    """OBS WebSocket connection settings."""

    model_config = SettingsConfigDict(
        env_prefix="OBS_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    host: str = "localhost"
    port: int = 4455
    password: str = ""
    timeout: int = 10


settings = OBSSettings()
