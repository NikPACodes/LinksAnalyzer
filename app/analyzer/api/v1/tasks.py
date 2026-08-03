from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.analyzer.models import AnalysisTaskStatus
from app.analyzer.repositories.result_repository import WebsiteResultRepository
from app.analyzer.repositories.task_repository import TaskRepository
from app.analyzer.schemas.task import TaskResponse, TasksListResponse, WebsiteResultResponse
from app.db.session import get_db

router = APIRouter(prefix='/tasks', tags=['tasks'])


@router.get('', response_model=TasksListResponse)
async def get_tasks_list(status: Annotated[list[AnalysisTaskStatus]|None,
                                            Query(alias="status",
                                                  description="Фильтр по статусам задачи.")] = None,
                         limit: int = 20, offset: int = 0,
                         db: AsyncSession = Depends(get_db)) -> TasksListResponse:
    """
    Получение списка задач анализа.
    """
    task_repository = TaskRepository(db)
    # Получаем страницу задач и общее количество записей.
    tasks, total = await task_repository.get_tasks(status_list=status, limit=limit, offset=offset)

    items = [TaskResponse(
                task_id=task.id,
                status=task.status,
                total_urls=task.total_urls,
                processed_urls=task.processed_urls,
                error=task.error,
                created_at=task.created_at,
                updated_at=task.updated_at,
            ) for task in tasks]

    return TasksListResponse(items=items, total=total,
                             limit=limit, offset=offset)


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