from celery import Celery

from app.core.config import get_settings


settings = get_settings()

celery_app = Celery('links_analyzer',
                    broker=settings.celery_broker_url,          # Redis-очередь Celery-задач
                    backend=settings.celery_result_backend_url, # Redis-хранилище для статусов и результатов Celery-задач
                    include=[
                        'app.analyzer.celery_tasks',
                        'app.worker.celery_tasks',
                    ],
                    )

celery_app.conf.update(task_default_queue=settings.celery_task_default_queue,
                       timezone=settings.celery_timezone,
                       enable_utc=True,
                       task_track_started=True, # Отслеживание состояния STARTED у Celery-задач
                       task_serializer='json',
                       result_serializer='json',
                       accept_content=['json'],
                       )