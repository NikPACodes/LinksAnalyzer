from app.worker.celery_app import celery_app


@celery_app.task(name="system.ping")
def celery_ping_task() -> str:
    return 'pong'