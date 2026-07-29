import asyncio
import time
import aiohttp
from collections.abc import AsyncIterator
from app.analyzer.dto import FetchResult


class WebsiteFetcher:
    """
    Асинхронная загрузка HTML-страниц по списку URL.

    Для всех запросов используется одна aiohttp.ClientSession.
    Количество одновременных запросов ограничивается через asyncio.Semaphore.
    """
    def __init__(self, timeout_seconds: int, concurrency: int,
                 max_response_size_bytes: int, user_agent: str) -> None:
            self.timeout_seconds = timeout_seconds                  # Максимальное время выполнения одного HTTP-запроса
            self.concurrency = concurrency                          # Максимальное количество одновременно выполняемых запросов
            self.max_response_size_bytes = max_response_size_bytes  # Максимальный размер загружаемого ответа
            self.user_agent = user_agent                            # Значение HTTP-заголовка User-Agent
            self.supported_content_types = {                        # Поддерживаемые типы ответа
                'text/html',
                'application/xhtml+xml',
            }


    @staticmethod
    def _response_time_ms(started_at: float) -> int:
        """
        Возвращает время, прошедшее с начала операции, в миллисекундах.
        """
        return int((time.perf_counter() - started_at) * 1000)


    async def _fetch_one(self, session: aiohttp.ClientSession,
                         semaphore: asyncio.Semaphore, url: str) -> FetchResult:
        """
        Загрузка одной HTML-страницы.

        HTTP-коды 4xx и 5xx не считаем ошибками.
        """
        # Ограничение количества конкурентных запросов
        async with semaphore:
            started_at = time.perf_counter()

            try:
                async with session.get(url, allow_redirects=True) as response:
                    # Читаем на 1 байт больше лимита, для определения превышения.
                    body = await response.content.read(self.max_response_size_bytes + 1)
                    # Получаем время затраченное на запрос
                    response_time = self._response_time_ms(started_at)

                    # Проверка превышения максимального размера
                    if len(body) > self.max_response_size_bytes:
                        return FetchResult(
                            url=url,
                            status_code=response.status,
                            response_time_ms=response_time,
                            html=None,
                            html_size_bytes=len(body),
                            error=f'Response превышает максимально допустимый размер',
                        )

                    # aiohttp возвращает MIME-тип без параметров:
                    # "text/html; charset=utf-8" → "text/html"
                    content_type = response.content_type.lower()

                    # Проверка типа
                    if content_type.lower() not in self.supported_content_types:
                        return FetchResult(
                            url=url,
                            status_code=response.status,
                            response_time_ms=response_time,
                            html=None,
                            html_size_bytes=len(body),
                            error=f'Неподдерживаемый content-type: {content_type or "unknown"}',
                        )

                    html = body.decode(
                        response.charset or 'utf-8',    # Берем кодировку из response или UTF-8
                        errors='replace',               # Замена некорректных байтов спецсимволами
                                       )

                    return FetchResult(
                        url=url,
                        status_code=response.status,
                        response_time_ms=response_time,
                        html=html,
                        html_size_bytes=len(body),
                        error=None,
                    )

            except TimeoutError:
                return FetchResult(
                    url=url,
                    status_code=None,
                    response_time_ms=self._response_time_ms(started_at),
                    html=None,
                    html_size_bytes=0,
                    error='Request timeout',
                )

            except aiohttp.ClientError as exc:
                return FetchResult(
                    url=url,
                    status_code=None,
                    response_time_ms=self._response_time_ms(started_at),
                    html=None,
                    html_size_bytes=0,
                    error=f'ClientError: {exc}',
                )

            except Exception as exc:
                return FetchResult(
                    url=url,
                    status_code=None,
                    response_time_ms=self._response_time_ms(started_at),
                    html=None,
                    html_size_bytes=0,
                    error=f'Error: {exc}',
                )


    async def fetch_many(self, urls: list[str]) -> list[FetchResult]:
        """
        Конкурентная загрузка страниц по переданному списку URL.
        Возвращает результаты после завершения всех запросов.

        ! Порядок FetchResult соответствует порядку URLs.
        """
        # Ограничение времени операции
        timeout = aiohttp.ClientTimeout(total=self.timeout_seconds)
        # Ограничение конкурентных запросов
        semaphore = asyncio.Semaphore(self.concurrency)

        headers = {
            'User-Agent': self.user_agent,
            'Accept': (
                'text/html,'
                'application/xhtml+xml;q=0.9,'
            ),
        }
        # Выполняем все запросы в рамках одной HTTP-сессии
        async with aiohttp.ClientSession(timeout=timeout, headers=headers,
                                         raise_for_status=False) as session:

            tasks = [self._fetch_one(session=session, semaphore=semaphore, url=url) for url in urls]

            return await asyncio.gather(*tasks)


    async def fetch_many_iter(self, urls: list[str]) -> AsyncIterator[FetchResult]:
        """
        Конкурентная загрузка страниц по переданному списку URL.
        Возвращает результат сразу после завершения каждого запроса.

        ! Порядок FetchResult НЕ соответствует порядку URLs.

        Отличие от fetch_many:
            fetch_many() ждет завершения всех URL и возвращает list[FetchResult].
            fetch_many_iter() отдает FetchResult по одному, по мере готовности.
        """
        # Ограничение времени операции
        timeout = aiohttp.ClientTimeout(total=self.timeout_seconds)
        # Ограничение конкурентных запросов
        semaphore = asyncio.Semaphore(self.concurrency)

        headers = {
            'User-Agent': self.user_agent,
            'Accept': (
                'text/html,'
                'application/xhtml+xml;q=0.9,'
            ),
        }

        # Выполняем все запросы в рамках одной HTTP-сессии
        async with aiohttp.ClientSession(timeout=timeout, headers=headers,
                                             raise_for_status=False) as session:
            tasks = [self._fetch_one(session=session, semaphore=semaphore, url=url) for url in urls]

            for completed_task in asyncio.as_completed(tasks):
                yield await completed_task