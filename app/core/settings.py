from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr


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

    # Upstash Redis (REST API)
    UPSTASH_REDIS_REST_URL: SecretStr
    UPSTASH_REDIS_REST_TOKEN: SecretStr
    REDIS_PORT: int

    SOFT_DELETE_RETENTION_DAYS: int

    RESEND_API_KEY: SecretStr
    RECOVERY_SECRET_KEY: SecretStr
    RECOVERY_MINUTES: int


settings = Settings()  # type: ignore LOAD FROM ENV FILE
