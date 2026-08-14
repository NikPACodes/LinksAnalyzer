from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.analyzer.models import AnalysisTask, AnalysisTaskStatus


class TaskResponse(BaseModel):
    """
    Схема ответа на получение информации о задаче.

    GET /api/v1/tasks/{task_id}
    """
    task_id: UUID = Field(description='UUID задачи')
    status: AnalysisTaskStatus = Field(description='Статус задачи')
    total_urls: int = Field(ge=0, description='Количество URLs в задаче')
    processed_urls: int = Field(ge=0, description='Количество уже обработанных URL')
    progress_percent: int = Field(ge=0, le=100, description='Процент выполнения задачи')
    error: str | None = Field(default=None, description='Общая ошибка задачи')
    created_at: datetime = Field(description='Создания задачи')
    updated_at: datetime = Field(description='Последнее обновление')

    @classmethod
    def build(cls, task: AnalysisTask) -> TaskResponse:
        """
        Helper для сборки ответа на основе AnalysisTask.
        """
        progress_percent = 0

        if task.total_urls > 0:
            progress_percent = min(100, int(task.processed_urls / task.total_urls * 100))

        return cls(task_id=task.id, status=task.status,
                   total_urls=task.total_urls, processed_urls=task.processed_urls, progress_percent=progress_percent,
                   error=task.error, created_at=task.created_at, updated_at=task.updated_at)


class TasksListResponse(BaseModel):
    """
    Схема ответа на получение списка задач анализа с пагинацией.

    GET /api/v1/tasks
    """
    items: list[TaskResponse] = Field(description='Список задач')
    total: int = Field(ge=0, description='Всего задач')
    limit: int = Field(ge=1, description='Количество задач в ответе')
    offset: int = Field(ge=0, description='Количество пропущенных задач')


class WebsiteResultResponse(BaseModel):
    """
    Схема ответа по результату анализа одного URL.

    GET /api/v1/tasks/{task_id}/results
    !!! Endpoint возвращает список объектов: list[WebsiteResultResponse]
    """
    id: UUID = Field(description='UUID результата')
    task_id: UUID = Field(description='UUID задачи')
    url: str = Field(description='URL')
    status_code: int|None = Field(default=None, description='HTTP status code')
    response_time_ms: int|None = Field(default=None, description='Время ответа сайта')
    title: str|None = Field(default=None, description='Содержимое HTML-тега <title>')
    description: str|None = Field(default=None, description='Содержимое meta description')
    links_count: int = Field(ge=0, description='Количество ссылок')
    images_count: int = Field(ge=0, description='Количество картинок')
    html_size_bytes: int = Field(ge=0, description='Размер HTML в байтах')
    cached: bool = Field(description='Результат взят из кэша',)
    error: str|None = Field(default=None, description='Ошибка обработки URL')
    created_at: datetime = Field(description='Создания задачи')
