from pydantic import HttpUrl
from sqlalchemy.ext.asyncio import AsyncSession
from app.analyzer.models import AnalysisTask
from app.analyzer.repositories.task_repository import TaskRepository
from app.analyzer.repositories.result_repository import WebsiteResultRepository


class AnalyzerService:
    """
    Сервисный слой анализа.
    Service объединяет несколько repository-операций в один бизнес-сценарий.
    """
    def __init__(self, db: AsyncSession):
        """
        Инициализировать сервис анализа.

        Внутри сервиса создаются repository-объекты AnalysisTask и WebsiteResult,
        для используют единой db-сессии и создания в рамках одной транзакции.
        """
        self.db = db
        self.task_repository = TaskRepository(db)
        self.result_repository = WebsiteResultRepository(db)

    @staticmethod
    def _normalize_urls(urls: list[HttpUrl]) -> list[str]:
        """
        Нормализация перечня URL.

        - Преобразуем каждый HttpUrl в str.
        - избавляемся от URL дубликатов.
        - сохраняем исходный порядок URL.
        """
        # dict.fromkeys использован для сохранения порядка URL
        return list(dict.fromkeys(str(url) for url in urls))


    async def create_task(self, urls:list[HttpUrl]) -> AnalysisTask:
        """
        Создание новой задачи для анализа сайтов.

        !!! Commit выполняется только после корректного создания всех записей AnalysisTask и WebsiteResult.
        !!! В случае возникновения ошибки производит rollback.
        """
        # Нормализуем URLs
        normalized_urls = self._normalize_urls(urls)

        try:
            # Создаем новую задачу
            task = await self.task_repository.create_task(total_urls=len(normalized_urls))
            # Создаем предварительных перечень результатов анализа
            await self.result_repository.create_pending_results(task_id=task.id, urls=normalized_urls)

            # Выполняем коммит только в случае выполнения всех repository-операций
            await self.db.commit()
            await self.db.refresh(task)

            return task

        except Exception:
            # Откатываем изменения при возникновении ошибки
            await self.db.rollback()
            raise