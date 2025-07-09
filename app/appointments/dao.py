from datetime import datetime, timedelta
from typing import Sequence, Type

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.appointments.models import Appointment, Doctor, Patient
from app.dao.base import BaseDAO


class PatientDAO(BaseDAO[Patient]):
    """Класс доступа к данным для модели Patient.

    Attributes:
        model (Type[Patient]): SQLAlchemy модель пациента.
    """

    model: Type[Patient] = Patient


class DoctorDAO(BaseDAO[Doctor]):
    """Класс доступа к данным для модели Doctor.

    Attributes:
        model (Type[Doctor]): SQLAlchemy модель доктора.
    """

    model: Type[Doctor] = Doctor


class AppointmentDAO(BaseDAO[Appointment]):
    """Класс доступа к данным для модели Appointment.

    Attributes:
        model (Type[Appointment]): SQLAlchemy модель запись к врачу.
    """

    model: Type[Appointment] = Appointment

    @staticmethod
    async def find_overlapping_appointments(
        async_session: AsyncSession,
        doctor_id: int,
        start_time: datetime,
        min_gap: timedelta,
    ) -> Sequence[Appointment]:
        """Найти записи на приём врача, которые пересекаются с указанным временем приёма с учётом минимального интервала.

        Поиск происходит в диапазоне времени от (start_time - min_gap) до (start_time + min_gap).

        Args:
            async_session (AsyncSession): Асинхронная сессия базы данных.
            doctor_id (int): Идентификатор врача.
            start_time (datetime): Время начала приёма для проверки.
            min_gap (timedelta): Минимальный интервал между приёмами.

        Returns:
            Sequence[Appointment]: Список записей, которые пересекаются с указанным временем.
        """
        start_window = start_time - min_gap
        end_window = start_time + min_gap
        query = select(Appointment).where(
            Appointment.doctor_id == doctor_id,
            Appointment.start_time.between(start_window, end_window),
        )
        result = await async_session.execute(query)
        return result.scalars().all()

    @staticmethod
    async def find_by_patient_and_time(
        async_session: AsyncSession,
        patient_id: int,
        start_time: datetime,
    ) -> Appointment | None:
        """Найти запись на приём пациента в указанное время.

        Args:
            async_session (AsyncSession): Асинхронная сессия базы данных.
            patient_id (int): Идентификатор пациента.
            start_time (datetime): Время начала приёма.

        Returns:
            Appointment | None: Объект записи, если найден; иначе None.
        """
        query = select(Appointment).where(
            Appointment.patient_id == patient_id,
            Appointment.start_time == start_time,
        )
        result = await async_session.execute(query)
        return result.scalars().first()
