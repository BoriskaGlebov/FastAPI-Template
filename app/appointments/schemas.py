from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field


class SAppointmentCreate(BaseModel):
    """Валидатор данных для создания записи на приём.

    Attributes:
        doctor_id (int): Идентификатор врача.
        patient_id (int): Идентификатор пациента.
        start_time (datetime): Время начала приёма в формате 'YYYY-MM-DD HH:MM'.

    Methods:
        serialize_start_time(value: datetime, _info: Any) -> str:
            Форматирует время начала приёма в строку формата 'YYYY-MM-DD HH:MM'.
    """

    doctor_id: int
    patient_id: int
    start_time: Annotated[
        datetime,
        Field(
            description="Время начала приёма. Формат: YYYY-MM-DD HH:MM",
            json_schema_extra={"example": "2025-07-05 10:30"},
        ),
    ]
