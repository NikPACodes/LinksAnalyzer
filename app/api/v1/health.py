from fastapi import APIRouter, Depends
from app.core.config import Settings, get_settings

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