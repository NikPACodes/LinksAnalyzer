import asyncio
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.redis import get_redis_cache_client
from app.worker.celery_tasks import celery_ping_task

settings = get_settings()

async def check_postgres(db: AsyncSession) -> dict[str, Any]:
    """
    Проверка доступности Postgres
    """
    await db.execute(text('SELECT 1'))

    return {
        'status': 'ok',
        'component': 'Postgres',
    }


async def check_redis() -> dict[str, Any]:
    """
    Проверка доступности Redis
    """
    async with get_redis_cache_client() as client:
        result = await asyncio.wait_for(client.ping(),
                                        timeout=settings.redis_health_timeout_seconds)

    if result is not True:
        raise RuntimeError('Redis не отвечает.')

    return {
        'status': 'ok',
        'component': 'Redis',
        'ping': 'pong',
    }


async def check_celery() -> dict[str, Any]:
    """
    Проверка работы Celery
    """
    def _send_ping_task() -> str:
        """
        Проверка ответа от Celery
        """
        async_result = celery_ping_task.delay()

        return async_result.get(timeout=settings.celery_health_timeout_seconds, propagate=True)

    # Запускаем в отдельном потоке, чтобы async_result.get не блокировал event loop
    result = await asyncio.to_thread(_send_ping_task)

    if result != 'pong':
        raise RuntimeError('Celery не отвечает.')

    return {
        'status': 'ok',
        'component': 'celery',
        'ping': result,
    }