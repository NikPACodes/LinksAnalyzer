from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from app.db.models import AnalysisTaskStatus


class TaskResponse(BaseModel):
    """
    Схема ответа на получение информации о задаче.

    GET /api/v1/tasks/{task_id}
    """
    task_id: UUID
    status: AnalysisTaskStatus
    total_urls: int               # Количество URL в задаче
    processed_urls: int           # Количество уже обработанных URL
    error: str|None
    created_at: datetime
    updated_at: datetime


class WebsiteResultResponse(BaseModel):
    """
    Схема ответа по результату анализа одного URL.

    GET /api/v1/tasks/{task_id}/results
    !!! Endpoint возвращает список объектов: list[WebsiteResultResponse]
    """
    id: UUID
    task_id: UUID
    url: str
    status_code: int|None        # HTTP status code
    response_time_ms: int|None   # Время ответа сайта
    title: str|None              # Содержимое HTML-тега
    description: str|None        # Содержимое meta description
    links_count: int             # Количество ссылок
    images_count: int            # Количество картинок
    html_size_bytes: int         # Размер HTML
    cached: bool
    error: str|None
    created_at: datetime
