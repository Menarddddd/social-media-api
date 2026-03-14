from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="UTF-8")

    DATABASE_URL: SecretStr
    DATABASE_USER: SecretStr
    DATABASE_PASSWORD: SecretStr

    ACCESS_SECRET_KEY: SecretStr
    ACCESS_MINUTES_EXPIRE: int

    REFRESH_SECRET_KEY: SecretStr
    REFRESH_DAYS_EXPIRE: int

    ALGORITHM: str


settings = Settings()  # type: ignore LOAD FROM ENV FILE
