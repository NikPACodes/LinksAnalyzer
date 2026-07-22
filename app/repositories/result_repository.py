from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import WebsiteResult


class WebsiteResultRepository:
    """
    Репозиторий для работы с результатами анализа.
    """
    def __init__(self, db: AsyncSession):
        self.db = db


    async def create_pending_results(self, task_id: UUID,
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