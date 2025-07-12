from datetime import time, timedelta

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.appointments.dao import AppointmentDAO, DoctorDAO, PatientDAO
from app.appointments.models import Appointment
from app.appointments.schemas import SAppointmentCreate


class AppointmentService:
    """Сервис для работы с записями на приём.

    Включает бизнес-логику создания записи с проверками
    существования врача и пациента, проверки времени приёма,
    а также проверку на пересечения по времени.
    """

    WORK_START = time(8, 0)
    WORK_END = time(18, 0)
    MIN_GAP = timedelta(hours=1)

    @staticmethod
    async def create_appointment(
        session: AsyncSession, data: SAppointmentCreate
    ) -> Appointment:
        """Создает запись на приём с валидацией бизнес-правил.

        Правила проверки:
            - Врач с указанным ID существует.
            - Пациент с указанным ID существует.
            - Время начала приёма находится в рабочем интервале (08:00-18:00).
            - Отсутствуют записи к врачу в интервале ±1 час от указанного времени.
            - У пациента нет записи на то же время.

        Args:
            session (AsyncSession): Асинхронная сессия базы данных.
            data (SAppointmentCreate): Данные для создания записи на приём.

        Raises:
            HTTPException: В случае нарушения правил валидации с соответствующим кодом и сообщением.

        Returns:
            Appointment: Созданный объект записи на приём.
        """
        start_time = data.start_time.time()
        if not (
            AppointmentService.WORK_START <= start_time < AppointmentService.WORK_END
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Время приёма должно быть в интервале с 08:00 до 18:00.",
            )

        doctor = await DoctorDAO.find_one_or_none_by_id(session, data.doctor_id)
        if not doctor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Доктор с ID {data.doctor_id} не найден.",
            )

        patient = await PatientDAO.find_one_or_none_by_id(session, data.patient_id)
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Пациент с ID {data.patient_id} не найден.",
            )

        overlap_appointments = await AppointmentDAO.find_overlapping_appointments(
            async_session=session,
            doctor_id=data.doctor_id,
            start_time=data.start_time,
            min_gap=AppointmentService.MIN_GAP,
        )
        if overlap_appointments:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Время приёма занято или перекрывается с другим приёмом врача.",
            )

        patient_appointment = await AppointmentDAO.find_by_patient_and_time(
            async_session=session,
            patient_id=data.patient_id,
            start_time=data.start_time,
        )
        if patient_appointment:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Пациент уже имеет запись на это время.",
            )

        appointment = await AppointmentDAO.add(
            async_session=session, **data.model_dump()
        )
        return appointment
