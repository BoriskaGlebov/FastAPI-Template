from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Patient(Base):
    """
    Модель пациента.

    Атрибуты:
        id (int): Уникальный идентификатор пациента.
        name (str): Имя пациента.
        email (str): Email пациента (уникальный).
        phone (Optional[str]): Телефон пациента (необязательное поле).
        appointments (List["Appointment"]): Список записей на приём пациента.
    """

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=True)

    appointments: Mapped[list["Appointment"]] = relationship(back_populates="patient")

    def __repr__(self) -> str:
        """Строковое представление пациента."""
        return f"<Patient(id={self.id}, name='{self.name}', email='{self.email}')>"


class Doctor(Base):
    """
    Модель врача.

    Атрибуты:
        id (int): Уникальный идентификатор врача.
        name (str): Имя врача.
        specialization (str): Специализация врача.
        experience_years (int): Опыт работы в годах.
        appointments (List["Appointment"]): Список записей к врачу.
    """

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    specialization: Mapped[str] = mapped_column(String(100), nullable=False)
    experience_years: Mapped[int] = mapped_column(Integer, nullable=False)

    appointments: Mapped[list["Appointment"]] = relationship(back_populates="doctor")

    def __repr__(self) -> str:
        """Строковое представление врача."""
        return (
            f"<Doctor(id={self.id}, name='{self.name}', "
            f"specialization='{self.specialization}', experience_years={self.experience_years})>"
        )


class Appointment(Base):
    """
    Модель записи на приём.

    Атрибуты:
        id (int): Уникальный идентификатор записи.
        doctor_id (int): ID врача, к которому записываются.
        patient_id (int): ID пациента, который записывается.
        start_time (datetime): Время начала приёма.
        doctor (Doctor): Связанный объект врача.
        patient (Patient): Связанный объект пациента.
    """

    id: Mapped[int] = mapped_column(primary_key=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    start_time: Mapped[datetime] = mapped_column(nullable=False)

    doctor: Mapped["Doctor"] = relationship(back_populates="appointments")
    patient: Mapped["Patient"] = relationship(back_populates="appointments")

    __table_args__ = (UniqueConstraint("doctor_id", "patient_id", name="unique_doctor_slot"),)

    def __repr__(self) -> str:
        """Строковое представление записи на приём."""
        start_str: Optional[str] = self.start_time.strftime("%Y-%m-%d %H:%M") if self.start_time else None
        return (
            f"<Appointment(id={self.id}, doctor_id={self.doctor_id}, patient_id={self.patient_id}, "
            f"start_time='{start_str}')>"
        )
