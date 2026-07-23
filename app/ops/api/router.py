from fastapi import APIRouter
from app.ops.api.health import router as health_router

ops_router = APIRouter()

ops_router.include_router(health_router)