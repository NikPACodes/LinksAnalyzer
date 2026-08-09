import hashlib
import json
import logging

import redis.asyncio as redis
from redis.exceptions import RedisError

from pydantic import ValidationError

from app.analyzer.dto import CachedAnalysisResult

# Логгер ошибок кэша
logger = logging.getLogger(__name__)


class AnalysisCache:
    """
    Кэш результатов анализа URL на базе Redis.
    """
    def __init__(self, client: redis.Redis, ttl_seconds: int, key_prefix: str):
        """
        Инициализация кэша с Redis-клиентом, временем жизни записей и префиксом ключей.
        """
        self._client = client
        self.ttl_seconds = ttl_seconds
        self.key_prefix = key_prefix


    def _make_key(self, url: str) -> str:
        """
        Формирование ключа Redis из префикса и SHA-256-хеша URL.
        """
        url_hash = hashlib.sha256(url.encode('utf-8')).hexdigest()
        return f'{self.key_prefix}:{url_hash}'


    async def get(self, url: str) -> CachedAnalysisResult | None:
        """
        Получение результата из кэша.
        """
        key = self._make_key(url)

        try:
            raw_data = await self._client.get(key)
        except RedisError:
            logger.exception('Ошибка чтения кэш')
            return None

        if raw_data is None:
            return None

        try:
            data = json.loads(raw_data)
            return CachedAnalysisResult.model_validate(data)
        except (json.JSONDecodeError, KeyError, TypeError, ValidationError):
            logger.exception('Некорректные данные в кэше')
            # Удаляем поврежденную запись кэш
            await self.delete(url)
            return None


    async def set(self, result: CachedAnalysisResult) -> None:
        """
        Сохранение результата в кэше с TTL.
        """
        key = self._make_key(result.url)
        payload = json.dumps(result.model_dump(), ensure_ascii=False)

        try:
            await self._client.set(key, payload, ex=self.ttl_seconds)
        except RedisError:
            logger.exception('Ошибка записи кэш')


    async def delete(self, url: str) -> None:
        """
        Удаление результата из кэша.
        """
        try:
            await self._client.delete(self._make_key(url))

        except RedisError:
            logger.exception('Ошибка удаления кэш записи')


    async def close(self) -> None:
        """
        Закрытие соединений Redis-клиента.
        """
        await self._client.aclose()