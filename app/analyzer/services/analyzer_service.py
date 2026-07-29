from pydantic import HttpUrl
from uuid import UUID
import time
from sqlalchemy.ext.asyncio import AsyncSession
from app.analyzer.models import AnalysisTask
from app.analyzer.repositories.task_repository import TaskRepository, AnalysisTaskStatus
from app.analyzer.repositories.result_repository import WebsiteResultRepository
from app.analyzer.fetcher import WebsiteFetcher
from app.core.config import get_settings


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
        self.settings = get_settings()
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


    async def fetch_task_urls(self,task_id: UUID) -> AnalysisTask | None:
        """
        Выполнение асинхронной загрузки всех URL, связанных с задачей.
        """
        task = await self.task_repository.get_task(task_id=task_id)

        if task is None:
            return None

        # Получение перечня URLs по задаче
        urls = await self.result_repository.get_urls(task_id)

        # Создаем aiohttp загрузчик
        fetcher = WebsiteFetcher(
            timeout_seconds=self.settings.fetch_timeout_seconds,
            concurrency=self.settings.fetch_concurrency,
            max_response_size_bytes=self.settings.fetch_max_response_size_bytes,
            user_agent=self.settings.fetch_user_agent,
        )

        try:
            await self.task_repository.set_status(task, status=AnalysisTaskStatus.PROCESSING)
            # Commit делается сразу, для отображения, что задача обрабатывается.
            await self.db.commit()
            commit_at = time.monotonic()

            # # Асинхронная загрузка URLs.
            # fetch_results = await fetcher.fetch_many(urls)

            processed_urls = 0

            # for fetch_result in fetch_results:
            #     await self.result_repository.update_fetch_result(task_id=task.id, fetch_result=fetch_result)
            #     processed_urls += 1
            #     await self.task_repository.set_processed_urls(task, processed_urls=processed_urls)

            commit_every = 5              # Интервал обработанных URL
            commit_interval_seconds = 2   # Интервал времени между коммитами

            # Для получения live-progress используем метод fetcher.fetch_many_iter,
            # т.к. он позволяет не дожидаться загрузке всех URLs и позволяет обновлять результаты по готовности.
            # ! Данный подход создает live-progress, но значительно повышает нагрузку на БД из-за коммитов.
            # Для уменьшения нагрузки на БД коммиты делаются с интерваломи (commit_interval_seconds),
            # либо по достижению N результатов (commit_every).
            async for fetch_result in fetcher.fetch_many_iter(urls):
                await self.result_repository.update_fetch_result(task_id=task.id, fetch_result=fetch_result)
                processed_urls += 1
                await self.task_repository.set_processed_urls(task, processed_urls=processed_urls)

                now = time.monotonic()
                interval = now - commit_at

                # Делаем commit только при условии достижения commit_every, либо commit_interval_seconds
                if processed_urls % commit_every == 0 or interval >= commit_interval_seconds:
                    await self.db.commit()
                    commit_at = now


            await self.task_repository.set_status(task, status=AnalysisTaskStatus.DONE)
            # Фиксируем все изменения
            await self.db.commit()
            await self.db.refresh(task)

            return task

        except Exception as exc:
            await self.db.rollback()

            await self.task_repository.set_status(task, status=AnalysisTaskStatus.FAILED, error=f'{exc}')
            await self.db.commit()
            await self.db.refresh(task)

            return task