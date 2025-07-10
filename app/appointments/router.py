from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.appointments.dao import AppointmentDAO
from app.appointments.rb import RBAppointmentRead
from app.appointments.schemas import SAppointmentCreate
from app.appointments.services import AppointmentService
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
    """Получить запись на приём по уникальному идентификатору.

    Args:
        appointment_id (int): Уникальный идентификатор записи на приём.
        session (AsyncSession): Асинхронная сессия для работы с базой данных.

    Returns:
        RBAppointmentRead: Данные о записи на приём.

    Raises:
        HTTPException: Возникает, если запись с указанным ID не найдена (404).
    """
    logger.info(f"Запрос на получение записи с ID={appointment_id}")
    appointment = await AppointmentDAO.find_one_or_none_by_id(session, appointment_id)
    if appointment is None:
        logger.warning(f"Запись с ID={appointment_id} не найдена")
        raise HTTPException(status_code=404, detail="Запись не найдена")

    logger.success(
        f"Найдена запись: ID={appointment.id}, "
        f"start_time={appointment.start_time.strftime('%Y-%m-%d %H:%M')}"
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
    """Создать новую запись на приём.

    Args:
        data (SAppointmentCreate): Данные для создания записи.
        session (AsyncSession): Асинхронная сессия базы данных.

    Returns:
        RBAppointmentRead: Созданная запись на приём.
    """
    logger.info(
        f"Попытка создать запись: доктор={data.doctor_id}, пациент={data.patient_id}, время={data.start_time}"
    )

    new_appointment = await AppointmentService.create_appointment(session, data)

    logger.success(f"Запись создана: ID={new_appointment.id}")
    return RBAppointmentRead.model_validate(new_appointment)
