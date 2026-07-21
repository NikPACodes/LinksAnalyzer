from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from collections.abc import AsyncGenerator
from app.core.config import get_settings

settings = get_settings()

# Объект подключения к БД
engine = create_async_engine(settings.database_url,
                             echo=settings.app_debug, # Для Debug=True будем печатать SQL в log
                             pool_pre_ping=True)      # Проверка подключения

# Фабрика сессий
AsyncSessionLocal = async_sessionmaker(bind=engine,            # Подключение
                                       expire_on_commit=False,
                                       autoflush=False)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session