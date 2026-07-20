from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = 'links-analyzer'
    app_env: str = 'local'
    app_debug: bool = True

    postgres_host: str = 'postgres'
    postgres_port: int = 5432
    postgres_db: str = 'links_analyzer_db'
    postgres_user: str = 'links_analyzer'
    postgres_password: str = 'links_analyzer'

    redis_host: str = 'redis'
    redis_port: int = 6379

    model_config = SettingsConfigDict(env_file='.env',
                                      env_file_encoding='utf-8',
                                      extra='ignore')


@lru_cache
def get_settings() -> Settings:
    return Settings()