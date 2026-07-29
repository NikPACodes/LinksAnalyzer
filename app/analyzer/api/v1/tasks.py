from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.analyzer.repositories.result_repository import WebsiteResultRepository
from app.analyzer.repositories.task_repository import TaskRepository
from app.analyzer.schemas.task import TaskResponse, WebsiteResultResponse

router = APIRouter(prefix='/tasks', tags=['tasks'])


@router.get('/{task_id}', response_model=TaskResponse)
async def get_task_info(task_id: UUID, db: AsyncSession = Depends(get_db)) -> TaskResponse:
    """
    Получение информации о задаче анализа по UUID.
    """
    task_repository = TaskRepository(db)
    task = await task_repository.get_task(task_id=task_id)

    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='Задача не найдена')

    return TaskResponse(task_id=task.id, status=task.status,
                        total_urls=task.total_urls, processed_urls=task.processed_urls, error=task.error,
                        created_at=task.created_at, updated_at=task.updated_at)


@router.get('/{task_id}/results', response_model=list[WebsiteResultResponse])
async def get_task_results(task_id: UUID, db: AsyncSession = Depends(get_db)) -> list[WebsiteResultResponse]:
    """
    Получение списка результатов анализа для конкретной задачи
    """
    task_repository = TaskRepository(db)
    result_repository = WebsiteResultRepository(db)

    task = await task_repository.get_task(task_id=task_id)

    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='Задача не найдена')

    results = await result_repository.get_results(task_id)

    return [WebsiteResultResponse(
                id=result.id,
                task_id=result.task_id,
                url=result.url,
                status_code=result.status_code,
                response_time_ms=result.response_time_ms,
                title=result.title,
                description=result.description,
                links_count=result.links_count,
                images_count=result.images_count,
                html_size_bytes=result.html_size_bytes,
                cached=result.cached,
                error=result.error,
                created_at=result.created_at,
            ) for result in results]