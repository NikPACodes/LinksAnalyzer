from pydantic import BaseModel, Field, HttpUrl
from uuid import UUID
from app.db.models import AnalysisTaskStatus


class AnalyzeRequest(BaseModel):
    """
    Схема запроса на анализ URLs.

    POST /api/v1/analyze
    """
    urls: list[HttpUrl]=Field(min_length=1, max_length=50,
                              description='URLs для анализа')


class AnalyzeResponse(BaseModel):
    """
    Схема ответа на запрос анализа URLs с информацией о созданной задаче.
    """
    task_id: UUID
    status: AnalysisTaskStatus
    total_urls: int             # Количество URL в задаче
    processed_urls: int         # Количество уже обработанных URL