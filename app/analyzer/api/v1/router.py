from fastapi import APIRouter

from app.analyzer.api.v1.analyzer import router as analyze_router
from app.analyzer.api.v1.tasks import router as tasks_router

api_router = APIRouter()

api_router.include_router(analyze_router)
api_router.include_router(tasks_router)
