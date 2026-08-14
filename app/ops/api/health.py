from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.ops.health_checks import check_postgres, check_redis, check_celery

router = APIRouter(prefix='/health', tags=['ops-health'])

@router.get('')
async def health_check(settings: Settings = Depends(get_settings)) -> dict[str, str]:
    """
    Проверка работы FastAPI сервиса
    """
    return {
        'status': 'ok',
        'service': settings.app_name,
        'environment': settings.app_env,
    }


@router.get('/db')
async def db_health_check(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """
    Проверка доступности БД Postgres
    """
    try:
        return await check_postgres(db)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                'status': 'error',
                'component': 'Postgres',
                'error': f'{exc.__class__.__name__}: {exc}',
            },
        ) from exc


@router.get("/redis")
async def redis_health_check() -> dict[str, Any]:
    """
    Проверка доступности Redis
    """
    try:
        return await check_redis()

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                'status': 'error',
                'component': 'Redis',
                'error': f'{exc.__class__.__name__}: {exc}',
            },
        ) from exc


@router.get("/celery")
async def celery_health_check() -> dict[str, Any]:
    """
    Проверка работы Celery
    """
    try:
        return await check_celery()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                'status': 'error',
                'component': 'Celery',
                'error': f'{exc.__class__.__name__}: {exc}',
            },
        ) from exc


@router.get("/full")
async def readiness_check(db: AsyncSession = Depends(get_db), settings: Settings = Depends(get_settings)) -> dict[str, Any]:
    """
    Проверка работы всех сервисов проекта
    """
    checks: dict[str, Any] = {}

    try:
        checks['postgres'] = await check_postgres(db)
    except Exception as exc:
        checks['postgres'] = {
            'status': 'error',
            'error': f'{exc.__class__.__name__}: {exc}',
        }

    try:
        checks['redis'] = await check_redis()
    except Exception as exc:
        checks['redis'] = {
            'status': 'error',
            'error': f'{exc.__class__.__name__}: {exc}',
        }

    try:
        checks['celery'] = await check_celery()
    except Exception as exc:
        checks['celery'] = {
            'status': 'error',
            'error': f'{exc.__class__.__name__}: {exc}',
        }

    is_ready = all(check.get('status') == 'ok' for check in checks.values())

    if not is_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                'status': 'error',
                'checks': checks,
            },
        )

    return {
        'status': 'ok',
        'service': settings.app_name,
        'environment': settings.app_env,
        'checks': checks,
    }










