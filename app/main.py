from fastapi import FastAPI
from app.analyzer.api.v1.router import api_router as api_v1_router
from app.ops.api.router import ops_router
from app.core.config import get_settings

settings = get_settings()

def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name,
                  debug=settings.app_debug,
                  version='0.1.0')
    app.include_router(api_v1_router, prefix='/api/v1')
    app.include_router(ops_router, prefix='/api/ops')
    return app


app = create_app()