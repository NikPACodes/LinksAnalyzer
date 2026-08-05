from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = 'links-analyzer'
    app_env: str = 'local'
    app_debug: bool = False

    # Postgres
    postgres_host: str = 'postgres'
    postgres_port: int = 5432
    postgres_db: str = 'links_analyzer_db'
    postgres_user: str = 'links_analyzer'
    postgres_password: str = 'links_analyzer'

    # Redis
    redis_host: str = 'redis'
    redis_port: int = 6379

    # Настройки HTTP
    fetch_timeout_seconds: int = 10                     # Время загрузки одного URL (aiohttp)
    fetch_concurrency : int = 10                        # Количество параллельных запросов (asyncio)
    fetch_max_response_size_bytes : int = 2000000       # Максимальный размер загружаемого ответа
    fetch_user_agent: str = 'LinkWebsiteAnalyzer/0.1'   # Значение HTTP-заголовка User-Agent

    # Настройки парсера
    html_parser_max_workers: int = 4                    # Максимальное количество параллельных потоков (workers)
    html_parser_max_title_length: int = 512             # Максимальная длина Title страницы, для БД
    html_parser_max_description_length: int = 2000      # Максимальная длина Description страницы, для БД

    # Настройка фонового выполнения Celery
    celery_broker_url: str = 'redis://redis:6379/0'     # Очередь Celery-задач
    celery_result_backend: str = 'redis://redis:6379/1' # Статусы и результаты выполнения Celery-задач
    celery_task_default_queue: str = 'analyzer'         # Очередь по умолчанию
    celery_timezone: str = 'UTC'

    @property
    def database_url(self):
        """
        Async-подключение к Postgres
        """
        return (f'postgresql+asyncpg://{self.postgres_user}:'
                f'{self.postgres_password}@{self.postgres_host}:'
                f'{self.postgres_port}/{self.postgres_db}')

    model_config = SettingsConfigDict(env_file='.env',
                                      env_file_encoding='utf-8',
                                      extra='ignore')


@lru_cache
def get_settings() -> Settings:
    return Settings()