from datetime import datetime
from typing import Any

from pydantic import BaseModel, field_serializer


class RBAppointmentRead(BaseModel):
    """Схема ответа для записи на приём (Appointment).

    Attributes:
        id (int): Уникальный идентификатор записи.
        patient_id (int): Идентификатор пациента.
        doctor_id (int): Идентификатор врача.
        start_time (datetime): Время начала приёма.

    Methods:
        serialize_start_time(value: datetime, _info: Any) -> str:
            Форматирует время начала приёма в строку формата 'YYYY-MM-DD HH:MM'.
    """

    id: int  # Уникальный идентификатор записи
    patient_id: int  # ID пациента
    doctor_id: int  # ID врача
    start_time: datetime  # Время начала приёма

    @field_serializer("start_time")
    def serialize_start_time(self, value: datetime, _info: Any) -> str:
        """Форматирование времени в виде строки: YYYY-MM-DD HH:MM.

        Args:
            value (datetime): Входящее значение времени начала приёма.
            _info (Any): Дополнительная информация сериализатора (не используется).

        Returns:
            str: Отформатированное время начала приёма.
        """
        return value.strftime("%Y-%m-%d %H:%M")

    model_config = {"from_attributes": True}
