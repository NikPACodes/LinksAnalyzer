from unittest import result
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.analyzer.models import AnalysisTask, AnalysisTaskStatus


class TaskRepository:
    """
    Репозиторий для работы с задачами анализа.
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_task(self, total_urls: int) -> AnalysisTask:
        """
        Создание новой задачи.
        !!! Commit будет выполняться на service уровне.
        """
        task = AnalysisTask(status=AnalysisTaskStatus.PENDING.value,
                            total_urls=total_urls, processed_urls=0)

        self.db.add(task)
        await self.db.flush()

        return task


    async def get_task(self, task_id: UUID) -> AnalysisTask|None:
        """
        Получение задачи по UUID.
        """
        return await self.db.get(AnalysisTask, task_id)


    async def set_status(self, task: AnalysisTask, status: AnalysisTaskStatus, error: str|None = None) -> AnalysisTask:
        """
        Установка статуса задачи и обновление информацию об ошибке.
        """
        if task.status == status.value and task.error == error:
            return task

        if status == AnalysisTaskStatus.FAILED and not error:
            raise ValueError('Для статуса FAILED необходимо указать ошибку.')

        task.status = status.value
        task.error = error if task.status == AnalysisTaskStatus.FAILED else None
        await self.db.flush()

        return task


    async def set_processed_urls(self, task: AnalysisTask, processed_urls: int) -> AnalysisTask:
        """
        Установка количества обработанных URL.
        """
        if processed_urls < 0:
            raise ValueError('Количество обработанных URLs не может быть отрицательным.')

        if processed_urls > task.total_urls:
            raise ValueError('Количество обработанных URLs не может превысить максимальное количество URLs.')

        if task.processed_urls == processed_urls:
            return task

        task.processed_urls = processed_urls
        await self.db.flush()

        return task