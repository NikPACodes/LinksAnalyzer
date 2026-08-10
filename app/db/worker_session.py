"""
Асинхронное подключение к БД для Celery-воркеров.
Создан для отделения фонового выполнения от основной работы FastAPI.

Это сделано потому, что Celery task запускает async-код через asyncio.run(),
который создает и закрывает event loop на каждое выполнение задачи.
При использовании общего SQLAlchemy AsyncEngine с connection pool
asyncpg-соединения могут быть переиспользованы между разными event loop,
что приводит к ошибкам вида: "got Future attached to a different loop", "Event loop is closed".

!!! Для worker необходимо использовать отдельный session layer app/db/worker_session.py,
а не общий app/db/session.py, чтобы не переиспользовать SQLAlchemy AsyncEngine FastAPI-приложения
внутри Celery worker
"""
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings

settings = get_settings()

# Объект подключения к БД для Celery worker
worker_engine = create_async_engine(settings.database_url,
                                    echo=settings.app_debug, # Для Debug=True будем печатать SQL в log
                                    pool_pre_ping=True,      # Проверка подключения
                                    poolclass=NullPool)      # Отключение переиспользования DB-соединений

# Фабрика сессий для Celery worker
WorkerAsyncSessionLocal = async_sessionmaker(bind=worker_engine,            # Подключение
                                                           expire_on_commit=False,
                                                           autoflush=False)

async def dispose_worker_engine() -> None:
    """
    Закрытие соединения асинхронной сессии с БД,
    для завершения работы воркера.
    """
    await worker_engine.dispose()