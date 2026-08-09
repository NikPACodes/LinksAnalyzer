import redis.asyncio as redis
from app.core.config import Settings, get_settings


def get_redis_cache_client(settings: Settings | None = None) -> redis.Redis:
    """
    Клиент Redis для работы с кэшем
    """
    settings = settings or get_settings()

    if settings.redis_cache_url:
        return redis.from_url(
            settings.redis_cache_url,
            decode_responses=True,
            socket_timeout=settings.redis_socket_timeout_seconds,
            socket_connect_timeout=settings.redis_socket_connect_timeout_seconds,
            health_check_interval=30,
        )
    else:
        return redis.Redis(
            username=settings.redis_username,
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_cache_db,
            password=settings.redis_password,
            decode_responses=True,
            socket_timeout=settings.redis_socket_timeout_seconds,
            socket_connect_timeout=settings.redis_socket_connect_timeout_seconds,
            health_check_interval=30,
        )