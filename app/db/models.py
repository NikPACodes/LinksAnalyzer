from datetime import datetime
from enum import StrEnum, Enum
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.engine import default
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

class AnalysisTaskStatus(StrEnum):
    PENDING = 'pending'
    PROCESSING = 'processing'
    DONE = 'done'
    FAILED = 'failed'


class AnalysisTask(Base):
    """
    Задача анализа списка URL.

    Одна AnalysisTask может иметь несколько WebsiteResult
    """
    __tablename__ = 'analysis_tasks'
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'processing', 'done', 'failed')", name='ch_status_task'),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    status: Mapped[str] = mapped_column(String(32), nullable=False,
                                        default=AnalysisTaskStatus.PENDING,              # на стороне SQLAlchemy
                                        server_default=AnalysisTaskStatus.PENDING.value, # на стороне Postgres
                                        index=True)
    # Количество URL в задаче
    total_urls: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default='0')
    # Количество уже обработанных URL
    processed_urls: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default='0')
    # Ошибка задачи
    error: Mapped[str|None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(),
                                                 onupdate=func.now())
    # Связь с результатами
    results: Mapped[list['WebsiteResult']] = relationship(back_populates='task',
                                                          cascade='all, delete-orphan', # каскадное удаление результатов
                                                          passive_deletes=True)         # БД может выполнять каскадное удаление


class WebsiteResult(Base):
    """
    Результат анализа URL
    """
    __tablename__ = 'website_result'
    __table_args__ = (
        Index('idx_result_task_id_url', 'task_id', 'url'),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    task_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True),
                                          ForeignKey('analysis_tasks.id', ondelete='CASCADE'),
                                          nullable=False, index=True)

    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    # HTTP status code
    status_code: Mapped[int|None] = mapped_column(Integer, nullable=True)
    # Время ответа сайта
    response_time_ms: Mapped[int|None] = mapped_column(Integer, nullable=True)
    # Содержимое HTML-тега
    title: Mapped[str|None] = mapped_column(String(512), nullable=True)
    # Содержимое meta description
    description: Mapped[str|None] = mapped_column(Text, nullable=True)
    # Количество ссылок
    links_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default='0')
    # Количество картинок
    images_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default='0')
    # Размер HTML
    html_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default='0')

    cached: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default='false')
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Связь с задачей
    task: Mapped[AnalysisTask] = relationship(back_populates='results')