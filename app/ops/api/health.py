from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_db

router = APIRouter(prefix='/health', tags=['health'])

@router.get('')
async def health_check(settings: Settings = Depends(get_settings)) -> dict[str, str]:
    """
    Проверка работы сервиса
    """
    return {
        'status': 'ok',
        'service': settings.app_name,
        'environment': settings.app_env,
    }


@router.get('/db')
async def db_health_check(db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    """
    Проверка доступности БД
    """
    await db.execute(text('SELECT 1'))
    return {
        'status': 'ok',
        'database': 'available',
    }