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