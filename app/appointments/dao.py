from typing import Type

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
