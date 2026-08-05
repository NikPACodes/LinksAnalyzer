from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.analyzer.celery_tasks import run_analysis_task
from app.analyzer.schemas.analyzer import AnalyzeRequest, AnalyzeResponse
from app.analyzer.services.analyzer_service import AnalyzerService
from app.db.session import get_db

router = APIRouter(prefix='/analyze', tags=['analyze'])

@router.post('', response_model=AnalyzeResponse, status_code=status.HTTP_201_CREATED)
async def create_analysis_task(payload: AnalyzeRequest,
                               db: AsyncSession = Depends(get_db)) -> AnalyzeResponse:
    """
    Запрос на создание задачи анализа URLs.
    """
    service = AnalyzerService(db)
    task = await service.create_task(payload.urls)

    # Отправка задачи в Celery
    run_analysis_task.delay(str(task.id))

    return AnalyzeResponse(task_id=task.id, status=task.status,
                           total_urls=task.total_urls, processed_urls=task.processed_urls)