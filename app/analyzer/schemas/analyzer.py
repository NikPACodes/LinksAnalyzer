from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl

from app.analyzer.models import AnalysisTaskStatus


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
    task_id: UUID = Field(description='UUID задачи')
    status: AnalysisTaskStatus = Field(description='Статус задачи')
    total_urls: int = Field(ge=0, description='Количество URLs в задаче')
    processed_urls: int = Field(ge=0, description='Количество уже обработанных URL')