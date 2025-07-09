from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from app.appointments.models import Appointment, Doctor, Patient
from app.config import settings  # Импортируйте ваши настройки
from app.database import DATABASE_URL, TEST_DATABASE_URL, Base  # Импортируйте ваш Base

# Получение параметров из командной строки
params = context.get_x_argument(as_dictionary=True)
config = context.config
# Использование параметров
db_choice = params.get("db", "main")  # По умолчанию основная база данных
# alembic -x db=test upgrade head
if db_choice == "test":
    config.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)
else:
    config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Конфигурация логгирования Alembic
if context.config.config_file_name is not None:
    fileConfig(context.config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Запуск миграций в оффлайн-режиме (без подключения к БД).
    """
    url = settings.get_db_url()  # Используем URL из ваших настроек
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,  # Включение сравнения типов столбцов
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Основная функция для асинхронного выполнения миграций.
    """
    connectable = create_async_engine(
        config.get_main_option("sqlalchemy.url"),
        poolclass=None,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)


def do_run_migrations(connection):
    """
    Синхронная часть выполнения миграций.
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Запуск миграций в онлайн-режиме (с подключением к БД).
    """
    import asyncio

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
