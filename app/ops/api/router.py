from fastapi import APIRouter

from app.ops.api.health import router as health_router
from app.ops.api.tasks import router as ops_tasks_router

ops_router = APIRouter()

ops_router.include_router(health_router)
ops_router.include_router(ops_tasks_router)