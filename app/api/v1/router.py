from fastapi import APIRouter
from app.api.v1.health import router as health_router
from app.api.v1.analyzer import router as analyze_router
from app.api.v1.tasks import router as tasks_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(analyze_router)
api_router.include_router(tasks_router)