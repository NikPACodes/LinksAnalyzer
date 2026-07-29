from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.analyzer.schemas.task import TaskResponse
from app.analyzer.services.analyzer_service import AnalyzerService

router = APIRouter(prefix='/tasks', tags=['tasks'])

@router.post('/{task_id}/fetch', response_model=TaskResponse)
async def post_fetch_task_urls(task_id: UUID, db: AsyncSession = Depends(get_db)) -> TaskResponse:
    """
    Запуск загрузки URLs для задачи анализа.
    Технический endpoint для ручного запуска обработки задачи.
    """
    service = AnalyzerService(db)
    task = await service.fetch_task_urls(task_id)

    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена.")

    return TaskResponse(task_id=task.id, status=task.status,
                        total_urls=task.total_urls, processed_urls=task.processed_urls, error=task.error,
                        created_at=task.created_at, updated_at=task.updated_at)