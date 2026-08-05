import asyncio
from uuid import UUID

from app.analyzer.services.analyzer_service import AnalyzerService
from app.db.session import AsyncSessionLocal
from app.worker.celery_app import celery_app


@celery_app.task(name="analyzer.run_analysis")
def run_analysis_task(task_id: str) -> None:
    """
    Celery-задача для фонового запуска анализа URL.
    """
    asyncio.run(_run_analysis_task(UUID(task_id)))


async def _run_analysis_task(task_id: UUID) -> None:
    """
    Асинхронная часть фоновой задачи анализа.

    Создаем отдельную AsyncSession и делегируем выполнение анализа в AnalyzerService.
    """
    async with AsyncSessionLocal() as db:
        service = AnalyzerService(db)
        await service.fetch_task_urls(task_id)