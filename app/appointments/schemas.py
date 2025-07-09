from datetime import datetime
from typing import Annotated, Any

from pydantic import BaseModel, Field, field_serializer


class SAppointmentCreate(BaseModel):
    """
    Модель данных для создания записи на приём.

    Атрибуты:
        doctor_id (int): Идентификатор врача.
        patient_id (int): Идентификатор пациента.
        start_time (datetime): Время начала приёма в формате 'YYYY-MM-DD HH:MM'.
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

    @field_serializer("start_time")
    def serialize_start_time(self, value: datetime, _info: Any) -> str:
        """Форматирование времени в виде строки: YYYY-MM-DD HH:MM."""
        return value.strftime("%Y-%m-%d %H:%M")
