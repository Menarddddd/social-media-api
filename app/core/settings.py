from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr

"""
ARQ Worker Configuration

This worker uses ARQ with Redis for background task processing.
Currently using asyncio.create_task() for deployment simplicity.
To enable ARQ worker, configure Redis and run:

    arq app.worker.settings.WorkerSettings

Requires:
    - Redis instance (local or cloud)
    - REDIS_HOST, REDIS_PORT, REDIS_PASSWORD in .env
"""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="UTF-8")

    DATABASE_URL: SecretStr
    DATABASE_USER: SecretStr
    DATABASE_PASSWORD: SecretStr
    DATABASE_NAME: str

    ACCESS_SECRET_KEY: SecretStr
    ACCESS_MINUTES_EXPIRE: int

    REFRESH_SECRET_KEY: SecretStr
    REFRESH_DAYS_EXPIRE: int

    ALGORITHM: str

    ADMIN_FIRST_NAME: str
    ADMIN_LAST_NAME: str
    ADMIN_USERNAME: str
    ADMIN_EMAIL: str
    ADMIN_PASSWORD: str

    SOFT_DELETE_RETENTION_DAYS: int

    GMAIL_USERNAME: str
    GMAIL_PASSWORD: SecretStr
    RECOVERY_MINUTES: int
    RECOVERY_SECRET_KEY: SecretStr


settings = Settings()  # type: ignore LOAD FROM ENV FILE
