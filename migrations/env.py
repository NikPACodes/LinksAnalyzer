import asyncio
from logging.config import fileConfig
from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from app.core.config import get_settings
from app.db.base import Base
# Модели нужны для регистрации в Base.metadata
from app.db.models import AnalysisTask, WebsiteResult  # noqa: F401



# Объект конфигурации Alembic c настройками из alembic.ini:
config = context.config

# Настройка логирования Alembic
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

settings = get_settings()
# Переопределяем sqlalchemy.url из alembic.ini
config.set_main_option("sqlalchemy.url", settings.database_url)

# Метаданные моделей для создания/обновления схемы БД
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Запуск миграции в 'offline' режиме.
    На вход передаем URL подключение к БД, а не реальное подключение.
    Генерирует SQL без применения миграции к БД
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,                    # использовать значения при генерации SQL
        dialect_opts={"paramstyle": "named"},  # стиль параметров SQL
        compare_type=True,                     # проверять типы колонок при сравнении моделей
    )

    # Запуск миграции
    # В offline-режиме генерирует SQL без применения миграции к БД
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """
    Запуск миграций в 'online' режиме.
    На вход передаем подключение к БД.
    Миграции применяются к PostgreSQL.
    """
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)

    # Запуск миграции и применение к БД
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Async запуск миграции с использованием async подключения
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    # Запуск sync миграции внутри async соединения
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    # Закрываем engine и освобождаем ресурсы
    await connectable.dispose()


def run_migrations_online() -> None:
    """
    Запуск миграций async в 'online' режиме.
    """
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
