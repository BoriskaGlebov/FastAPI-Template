from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.appointments.dao import AppointmentDAO, DoctorDAO, PatientDAO
from app.appointments.rb import RBAppointmentRead
from app.appointments.schemas import SAppointmentCreate
from app.config import logger
from app.dependencies import get_session

router = APIRouter(prefix="/api", tags=["Appointments"])


@router.get(
    "/appointments/{appointment_id}",
    response_model=RBAppointmentRead,
    summary="Получить запись на приём по ID",
)
async def get_appointment_by_id(
    appointment_id: int,
    session: AsyncSession = Depends(get_session),
) -> RBAppointmentRead:
    """
    Получить запись на приём по ID.

    Args:
        appointment_id (int): Уникальный идентификатор записи.
        session (AsyncSession): Асинхронная сессия базы данных.

    Returns:
        AppointmentRead: Данные о записи на приём.

    Raises:
        HTTPException: 404, если запись не найдена.
    """
    logger.info(f"🔍 Запрос на получение записи с ID={appointment_id}")

    appointment = await AppointmentDAO.find_one_or_none_by_id(session, appointment_id)
    if appointment is None:
        logger.warning(f"❌ Запись с ID={appointment_id} не найдена")
        raise HTTPException(status_code=404, detail="Запись не найдена")

    logger.success(
        f"✅ Найдена запись: ID={appointment.id}, " f"start_time={appointment.start_time.strftime('%Y-%m-%d %H:%M')}"
    )

    return RBAppointmentRead.model_validate(appointment)


@router.post(
    "/appointments",
    response_model=RBAppointmentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать запись на приём",
)
async def create_appointment(
    data: SAppointmentCreate,
    session: AsyncSession = Depends(get_session),
) -> RBAppointmentRead:
    """
    Создать новую запись на приём.

    Проверяет, что у врача нет другой записи в это время и в течение часа после,
    а так же записи с этим пациентом.
    """
    # Проверка, что доктор существует
    doctor = await DoctorDAO.find_one_or_none_by_id(session, data.doctor_id)
    if not doctor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Доктор с ID {data.doctor_id} не найден.")

    # Проверка, что пациент существует
    patient = await PatientDAO.find_one_or_none_by_id(session, data.patient_id)
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Пациент с ID {data.patient_id} не найден.")
    logger.info(
        f"📝 Попытка создать запись: доктор={data.doctor_id}, пациент={data.patient_id}, время={data.start_time}"
    )
    try:
        new_appointment = await AppointmentDAO.add(async_session=session, **data.model_dump())
    except ValueError as e:
        logger.warning(f"Не удалось создать запись в lifespan: {e}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Время приёма занято или перекрывается с другим приёмом."
        )

    logger.success(f"✅ Запись создана: ID={new_appointment.id}")
    return RBAppointmentRead.model_validate(new_appointment)
