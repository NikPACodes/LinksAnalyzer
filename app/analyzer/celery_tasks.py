import asyncio
import logging
from uuid import UUID

from app.analyzer.services.analyzer_service import AnalyzerService
from app.db.worker_session import WorkerAsyncSessionLocal, dispose_worker_engine
from app.worker.celery_app import celery_app

logger = logging.getLogger(__name__)

@celery_app.task(name="analyzer.run_analysis")
def run_analysis_task(task_id: str, use_cache: bool = True) -> None:
    """
    Celery-задача для фонового запуска анализа URL.
    """
    asyncio.run(_run_analysis_task(UUID(task_id), use_cache))


async def _run_analysis_task(task_id: UUID, use_cache: bool = True) -> None:
    """
    Асинхронная часть фоновой задачи анализа.

    Создаем отдельную AsyncSession и делегируем выполнение анализа в AnalyzerService.
    """
    async with WorkerAsyncSessionLocal() as db:
        service = AnalyzerService(db)
        task = await service.fetch_task_urls(task_id, use_cache=use_cache)

    if task is None:
        logger.warning(f'Задача анализа не найдена: task_id={task_id}')
        return

    logger.info(f'Задача выполнена: task_id={task.id} status={task.status} processed={task.processed_urls}/{task.total_urls}')