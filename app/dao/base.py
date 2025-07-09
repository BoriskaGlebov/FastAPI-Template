from typing import Any, Generic, List, Sequence, Type, TypeVar

from sqlalchemy import delete as sqlalchemy_delete, update as sqlalchemy_update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import Base

# Определяем тип переменной для модели
M = TypeVar("M", bound=Base)


class BaseDAO(Generic[M]):
    """
    Базовый класс для доступа к данным в БД.

    Универсальные методы для работы с БД.
    """

    model: Type[M]  # Указываем, что model будет типа M

    @classmethod
    async def find_all(cls, async_session: AsyncSession, **filter_by) -> Sequence[M] | None:
        """
        Получение списка всех строк таблицы.

        :param async_session: Асинхронная сессия базы данных.
        :param filter_by: Фильтры для выборки.
        :return: Список экземпляров модели.
        """
        query = select(cls.model).filter_by(**filter_by)
        result = await async_session.execute(query)
        return result.scalars().all()

    @classmethod
    async def find_one_or_none_by_id(cls, async_session: AsyncSession, data_id: int) -> M | None:
        """
        Получение строки таблицы по id.

        async_session: Асинхронная сессия базы данных.
        data_id: Фильтры для выборки по id
        return: Экземпляр модели.
        """
        query = select(cls.model).filter_by(id=data_id)
        result = await async_session.execute(query)
        return result.unique().scalar_one_or_none()

    @classmethod
    async def find_one_or_none(cls, async_session: AsyncSession, **filter_by) -> M | None:
        """
        Получение строки таблицы.

        :param async_session: Асинхронная сессия базы данных.
        :param filter_by: Фильтры для выборки
        :return: Экземпляр модели.
        """
        query = select(cls.model).filter_by(**filter_by)
        result = await async_session.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def add(cls, async_session: AsyncSession, **values) -> M:
        """
        Добавить строку.

        :param async_session: Асинхронная сессия базы данных.
        :param values: Значения которые надо добавить в таблицу
        :return: Экземпляр модели
        """
        new_instance = cls.model(**values)
        async_session.add(new_instance)
        try:
            await async_session.commit()
        except SQLAlchemyError as e:
            await async_session.rollback()
            raise e
        return new_instance

    @classmethod
    async def update(cls, async_session: AsyncSession, filter_by: dict[Any, Any], **values) -> List[M]:
        """
        Обновить строку.

        :param async_session: Асинхронная сессия базы данных.
        :param filter_by: Параметры для фильтрации
        :param values: Значения которые надо добавить в таблицу
        :return: Экземпляр модели
        """
        query = (
            sqlalchemy_update(cls.model)
            .where(*[getattr(cls.model, k) == v for k, v in filter_by.items()])
            .values(**values)
            .execution_options(synchronize_session="fetch")
            .returning(*[getattr(cls.model, column).label(column) for column in cls.model.__table__.columns.keys()])
        )

        result = await async_session.execute(query)
        try:
            updated_rows = result.fetchall()  # Получаем все измененные строки
            await async_session.commit()
            # return updated_rows
            return [cls.model(**{column: value for column, value in zip(result.keys(), row)}) for row in updated_rows]
        except SQLAlchemyError as e:
            await async_session.rollback()
            raise e

    @classmethod
    async def delete(cls, async_session: AsyncSession, delete_all: bool = False, **filter_by) -> int:
        """
        Удаление строки или очистка таблицы.

        :param async_session: Асинхронная сессия базы данных.
        :param delete_all: Параметр, который определяет полную очистку таблицы
        :param filter_by: Параметры для фильтрации
        :return: Количество удаленных строк
        """
        if not delete_all and not filter_by:
            raise ValueError("Необходимо указать хотя бы один параметр для удаления.")

        if delete_all:
            query = sqlalchemy_delete(cls.model)  # Удаление всех записей
        else:
            query = sqlalchemy_delete(cls.model).filter_by(**filter_by)  # Удаление по фильтрам

        result = await async_session.execute(query)
        try:
            await async_session.commit()
        except SQLAlchemyError as e:
            await async_session.rollback()
            raise e

        return result.rowcount  # Возвращает количество удаленных строк
