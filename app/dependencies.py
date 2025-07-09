import asyncio
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Создаёт и предоставляет асинхронную сессию базы данных.

    Используется для работы с базой данных в приложении и в тестах.
    В тестах сессия подключается к тестовой базе, в продакшене — к основной.

    Yields:
        AsyncSession: Асинхронная сессия SQLAlchemy.
    """
    async with async_session() as session:
        yield session


async def main():
    """Точка входа для тестирования методов работы с базой данных."""
    # Здесь можно вызывать и тестировать функции работы с БД


if __name__ == "__main__":
    asyncio.run(main())
