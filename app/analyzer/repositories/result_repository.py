from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analyzer.dto import FetchResult, HtmlParseResult
from app.analyzer.models import WebsiteResult


class WebsiteResultRepository:
    """
    Репозиторий для работы с результатами анализа.
    """
    def __init__(self, db: AsyncSession):
        self.db = db


    async def create_pending_results(self, *, task_id: UUID,
                                     urls: list[str]) -> list[WebsiteResult]:
        """
        Создание предварительных записей результатов для списка URL.
        !!! Commit будет выполняться на service уровне.
        """
        results = [WebsiteResult(task_id=task_id, url=url) for url in urls]

        self.db.add_all(results)
        await self.db.flush()

        return results


    async def get_results(self, task_id: UUID) -> list[WebsiteResult]:
        """
        Получение всех результатов анализа по конкретной задаче.
        """
        results = await self.db.execute(select(WebsiteResult)
                                        .where(WebsiteResult.task_id == task_id)
                                        .order_by(WebsiteResult.created_at.asc()))
        return list(results.scalars().all())


    async def get_urls(self, task_id: UUID) -> list[str]:
        """
        Получение URLs по конкретной задаче.
        """
        results = await self.db.execute(select(WebsiteResult.url)
                                        .where(WebsiteResult.task_id == task_id)
                                        .order_by(WebsiteResult.created_at.asc()))
        return list(results.scalars().all())


    async def update_fetch_result(self, *, task_id: UUID,
                                  fetch_result: FetchResult,
                                  parse_result: HtmlParseResult|None=None) -> WebsiteResult|None:
        """
        Обновление результата анализа URL данными HTTP-запроса.
        """
        query_result = await self.db.execute(select(WebsiteResult)
                                             .where(WebsiteResult.task_id == task_id,
                                                    WebsiteResult.url == fetch_result.url))
        # Для пары task_id + URL должна быть лишь одна записи.
        website_result = query_result.scalar_one_or_none()

        if website_result is None:
            return None

        website_result.status_code = fetch_result.status_code
        website_result.response_time_ms = fetch_result.response_time_ms
        website_result.html_size_bytes = fetch_result.html_size_bytes
        website_result.error = fetch_result.error

        if parse_result is not None:
            website_result.title = parse_result.title
            website_result.description = parse_result.description
            website_result.links_count = parse_result.links_count
            website_result.images_count = parse_result.images_count

        await self.db.flush()
        return website_result