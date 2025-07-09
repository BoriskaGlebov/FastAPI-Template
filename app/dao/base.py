from typing import Any, Generic, List, Sequence, Type, TypeVar, Union, cast

from sqlalchemy import delete as sqlalchemy_delete, update as sqlalchemy_update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import Base

M = TypeVar("M", bound=Base)


class BaseDAO(Generic[M]):
    """Базовый класс DAO для работы с базой данных.

    Обеспечивает универсальные методы CRUD для моделей SQLAlchemy.
    """

    model: Type[M]

    @classmethod
    async def find_all(
        cls,
        async_session: AsyncSession,
        **filter_by: Any,
    ) -> Sequence[M]:
        """Получить все записи модели с опциональной фильтрацией.

        Args:
            async_session (AsyncSession): Асинхронная сессия SQLAlchemy.
            **filter_by: Ключевые аргументы для фильтрации (поле=значение).

        Returns:
            Sequence[M]: Список объектов модели или None, если ничего не найдено.
        """
        query = select(cls.model).filter_by(**filter_by)
        result = await async_session.execute(query)
        items = result.scalars().all()
        return cast(Sequence[M], items)

    @classmethod
    async def find_one_or_none_by_id(
        cls,
        async_session: AsyncSession,
        data_id: int,
    ) -> Union[M, None]:
        """Получить одну запись по первичному ключу.

        Args:
            async_session (AsyncSession): Асинхронная сессия SQLAlchemy.
            data_id (int): Значение первичного ключа (id).

        Returns:
            Union[M, None]: Объект модели или None, если не найден.
        """
        query = select(cls.model).filter_by(id=data_id)
        result = await async_session.execute(query)
        item = result.unique().scalar_one_or_none()
        return cast(Union[M, None], item)

    @classmethod
    async def find_one_or_none(
        cls,
        async_session: AsyncSession,
        **filter_by: Any,
    ) -> Union[M, None]:
        """Получить одну запись по фильтру.

        Args:
            async_session (AsyncSession): Асинхронная сессия SQLAlchemy.
            **filter_by: Ключевые аргументы для фильтрации.

        Returns:
            Union[M, None]: Объект модели или None, если не найден.
        """
        query = select(cls.model).filter_by(**filter_by)
        result = await async_session.execute(query)
        item = result.unique().scalar_one_or_none()
        return cast(Union[M, None], item)

    @classmethod
    async def add(
        cls,
        async_session: AsyncSession,
        **values: Any,
    ) -> M:
        """Добавить новую запись в базу.

        Args:
            async_session (AsyncSession): Асинхронная сессия SQLAlchemy.
            **values: Значения для полей модели.

        Raises:
            SQLAlchemyError: При ошибках добавления записи.

        Returns:
            M: Созданный объект модели.
        """
        new_instance = cls.model(**values)
        async_session.add(new_instance)
        try:
            await async_session.commit()
            await async_session.refresh(new_instance)
        except SQLAlchemyError as e:
            await async_session.rollback()
            raise e
        return cast(M, new_instance)

    @classmethod
    async def update(
        cls,
        async_session: AsyncSession,
        filter_by: dict[Any, Any],
        **values: Any,
    ) -> List[M]:
        """Обновить записи, соответствующие фильтру, и вернуть обновлённые объекты.

        Args:
            async_session (AsyncSession): Асинхронная сессия SQLAlchemy.
            filter_by (dict[Any, Any]): Фильтр для выбора записей.
            **values: Новые значения для обновления.

        Raises:
            SQLAlchemyError: При ошибках обновления.

        Returns:
            List[M]: Список обновлённых объектов модели.
        """
        query = (
            sqlalchemy_update(cls.model)
            .where(
                *[getattr(cls.model, key) == value for key, value in filter_by.items()]
            )
            .values(**values)
            .execution_options(synchronize_session="fetch")
            .returning(
                *[
                    getattr(cls.model, col).label(col)
                    for col in cls.model.__table__.columns.keys()
                ]
            )
        )
        result = await async_session.execute(query)
        try:
            updated_rows = result.fetchall()
            await async_session.commit()
            return [
                cls.model(
                    **{column: value for column, value in zip(result.keys(), row)}
                )
                for row in updated_rows
            ]
        except SQLAlchemyError as e:
            await async_session.rollback()
            raise e

    @classmethod
    async def delete(
        cls,
        async_session: AsyncSession,
        delete_all: bool = False,
        **filter_by: Any,
    ) -> int:
        """Удалить записи по фильтру или очистить всю таблицу.

        Args:
            async_session (AsyncSession): Асинхронная сессия SQLAlchemy.
            delete_all (bool, optional): Если True — удалить все записи. По умолчанию False.
            **filter_by: Ключевые аргументы для фильтрации записей на удаление.

        Raises:
            ValueError: Если не указан фильтр и delete_all=False.
            SQLAlchemyError: При ошибках удаления.

        Returns:
            int: Количество удалённых записей.
        """
        if not delete_all and not filter_by:
            raise ValueError(
                "Для удаления необходимо указать фильтр или установить delete_all=True."
            )

        if delete_all:
            query = sqlalchemy_delete(cls.model)
        else:
            query = sqlalchemy_delete(cls.model).filter_by(**filter_by)

        result = await async_session.execute(query)
        try:
            await async_session.commit()
        except SQLAlchemyError as e:
            await async_session.rollback()
            raise e

        return result.rowcount
