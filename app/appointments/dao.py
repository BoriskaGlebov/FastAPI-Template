from datetime import datetime, timedelta
from typing import Type

from sqlalchemy import and_, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.appointments.models import Appointment, Doctor, Patient
from app.dao.base import BaseDAO


class PatientDAO(BaseDAO[Patient]):
    """
    Класс для доступа к данным в БД.

    Работает с таблицей Patient
    """

    model: Type[Patient] = Patient


class DoctorDAO(BaseDAO[Doctor]):
    """
    Класс для доступа к данным в БД.

    Работает с таблицей Doctor
    """

    model: Type[Doctor] = Doctor


class AppointmentDAO(BaseDAO[Appointment]):
    """
    Класс для доступа к данным в БД.

    Работает с таблицей Appointment
    """

    model: Type[Appointment] = Appointment

    @classmethod
    async def add(cls, async_session: AsyncSession, **values) -> Appointment:
        """
        Добавить запись на приём с проверкой, что у врача нет другой записи в интервале ±1 час.

        :param async_session: Асинхронная сессия базы данных.
        :param doctor_id: ID доктора.
        :param patient_id: ID пациента.
        :param start_time: Время начала приёма.
        :raises HTTPException: Если время занято.
        :return: Экземпляр записи Appointment.
        """
        # Если start_time пришёл строкой, преобразуем в datetime
        start_time = values.get("start_time")
        if isinstance(start_time, str):
            try:
                # Парсим строку формата 'YYYY-MM-DD HH:MM' (или ISO)
                values["start_time"] = datetime.strptime(start_time, "%Y-%m-%d %H:%M")
            except ValueError:
                # Если формат другой, попробуй datetime.fromisoformat или кинь исключение
                try:
                    values["start_time"] = datetime.fromisoformat(start_time)
                except ValueError:
                    raise ValueError("Неверный формат даты start_time")
        new_instance = cls.model(**values)
        new_start = new_instance.start_time
        new_end = new_start + timedelta(hours=1)

        # Проверяем две вещи:
        # 1) Есть ли перекрывающая запись по времени у врача
        # 2) Есть ли уже запись с таким же сочетанием doctor_id и patient_id
        query = select(cls.model).where(
            cls.model.doctor_id == new_instance.doctor_id,
            or_(
                # Перекрытие по времени
                and_(
                    cls.model.start_time < new_end,
                    cls.model.start_time >= new_start - timedelta(hours=1),
                ),
                # Или уже есть запись для этого пациента с этим врачом
                cls.model.patient_id == new_instance.patient_id,
            ),
        )
        result = await async_session.execute(query)
        existing_appointment = result.scalars().first()

        if existing_appointment:
            raise ValueError(
                "Время занято, или есть пересечение пациент + " "доктор или пересечение по приему с другим пациентом"
            )

        # Создаём новую запись

        async_session.add(new_instance)
        try:
            await async_session.commit()
            await async_session.refresh(new_instance)
        except SQLAlchemyError:
            await async_session.rollback()
            raise
        return new_instance
