import asyncio
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Функция для получения асинхронной сессии базы данных.

    Эта функция используется для тестирования и работы с базой данных.
    В тестах происходит обращение к тестовой базе данных,
    а в рабочем приложении — к боевой базе данных.

    :yield: Асинхронная сессия базы данных (AsyncSession)
    """
    async with async_session() as session:
        yield session


async def main():
    """Здесь я тестирую методы работы с БД."""


if __name__ == "__main__":
    asyncio.run(main())
