from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import cache


class Settings(BaseSettings):
    ENV: str
    DATABASE_HOSTNAME: str
    DATABASE_PORT: str
    DATABASE_PASSWORD: str
    DATABASE_NAME: str
    DATABASE_USERNAME: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    DEBUG: bool = True

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    def get_db_url(
        self, username: str, password: str, host: str, port: int, db_name: str
    ):
        return (
            "postgresql+asyncpg://" + f"{username}:{password}@{host}:{port}/{db_name}"
        )


class TestSettings(Settings):
    TEST_DATABASE_HOSTNAME: str
    TEST_DATABASE_PORT: str
    TEST_DATABASE_PASSWORD: str
    TEST_DATABASE_NAME: str
    TEST_DATABASE_USERNAME: str


@cache
def get_db_url():
    settings = get_settings()

    if isinstance(settings, TestSettings):
        return settings.get_db_url(
            settings.TEST_DATABASE_USERNAME,
            settings.TEST_DATABASE_PASSWORD,
            settings.TEST_DATABASE_HOSTNAME,
            settings.TEST_DATABASE_PORT,
            settings.TEST_DATABASE_NAME,
        )
    else:
        return settings.get_db_url(
            settings.DATABASE_USERNAME,
            settings.DATABASE_PASSWORD,
            settings.DATABASE_HOSTNAME,
            settings.DATABASE_PORT,
            settings.DATABASE_NAME,
        )


@cache
@cache
def get_settings():
    settings = Settings.model_validate({})

    if settings.ENV == "TEST":
        return TestSettings.model_validate({})

    return settings


settings = get_settings()
db_url = get_db_url()
