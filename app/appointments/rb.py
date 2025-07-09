from datetime import datetime
from typing import Any

from pydantic import BaseModel, field_serializer


class RBAppointmentRead(BaseModel):
    """Схема ответа для записи на приём (Appointment)."""

    id: int  # Уникальный идентификатор записи
    patient_id: int  # ID пациента
    doctor_id: int  # ID врача
    start_time: datetime  # Время начала приёма

    @field_serializer("start_time")
    def serialize_start_time(self, value: datetime, _info: Any) -> str:
        """Форматирование времени в виде строки: YYYY-MM-DD HH:MM."""
        return value.strftime("%Y-%m-%d %H:%M")

    model_config = {"from_attributes": True}  # Важный параметр для ORM объектов в Pydantic 2
