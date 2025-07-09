from datetime import datetime, time
from random import choice, randint
from typing import List, Set, Tuple

import faker
from factory.base import Factory
from factory.declarations import LazyAttribute, LazyFunction
from factory.faker import Faker

from app.appointments.models import Appointment, Doctor, Patient

faker_instance = faker.Faker("ru_RU")


class PatientFactory(Factory[Patient]):
    """Фабрика для генерации экземпляров модели Patient."""

    class Meta:
        model = Patient

    name = Faker("name", locale="ru_RU")
    email = LazyAttribute(lambda o: faker_instance.unique.email())
    phone = LazyAttribute(lambda o: faker_instance.phone_number())


class DoctorFactory(Factory[Doctor]):
    """Фабрика для генерации экземпляров модели Doctor."""

    class Meta:
        model = Doctor

    name = Faker("name", locale="ru_RU")
    specialization = LazyFunction(lambda: choice(["Терапевт", "Хирург", "Кардиолог", "Невролог"]))
    experience_years = LazyFunction(lambda: randint(1, 40))


class AppointmentFactory(Factory[Appointment]):
    """Фабрика для генерации экземпляров модели Appointment."""

    class Meta:
        model = Appointment

    doctor_id = LazyFunction(lambda: randint(1, 5))
    patient_id = LazyFunction(lambda: randint(1, 10))
    start_time = LazyFunction(lambda: faker_instance.date_time_between(start_date="now", end_date="+10d"))


def generate_patients(num_patients: int = 10) -> List[Patient]:
    """
    Генерирует список экземпляров Patient.

    Args:
        num_patients (int): Количество пациентов.

    Returns:
        List[Patient]: Список сгенерированных пациентов.
    """
    out_instance = [PatientFactory() for _ in range(num_patients)]
    return out_instance  # type: ignore


def generate_doctors(num_doctors: int = 5) -> List[Doctor]:
    """
    Генерирует список экземпляров Doctor.

    Args:
        num_doctors (int): Количество врачей.

    Returns:
        List[Doctor]: Список сгенерированных врачей.
    """
    out_instance = [DoctorFactory() for _ in range(num_doctors)]
    return out_instance  # type: ignore


def generate_random_slot(date: datetime) -> datetime:
    """Генерирует случайное время между 8:00 и 18:00 на указанную дату, с шагом 15 минут."""
    hour = randint(8, 17)  # 17, чтобы не выйти за 18:00
    minute = choice([0, 15, 30, 45])
    return datetime.combine(date.date(), time(hour, minute))


def generate_appointments(
    patients: List[Patient],
    doctors: List[Doctor],
    num_appointments: int = 20,
) -> List[Appointment]:
    """
    Генерирует список уникальных записей к врачам с учётом.

    - интервала минимум в 1 час между записями одного врача,
    - уникальности пары doctor-patient (пациент не может записаться дважды к одному врачу),
    - времени приёма только в диапазоне 8:00–18:00.
    """
    appointments: List[Appointment] = []
    doctor_schedule: dict[int, List[datetime]] = {}  # doctor_id -> список времени приёмов
    used_pairs: Set[Tuple[int, int]] = set()  # (doctor_id, patient_id)

    attempts = 0
    max_attempts = num_appointments * 15

    while len(appointments) < num_appointments and attempts < max_attempts:
        doctor = choice(doctors)
        patient = choice(patients)
        if (doctor.id, patient.id) in used_pairs:
            attempts += 1
            continue  # пациент уже записан к этому врачу

        random_date = faker_instance.date_time_between(start_date="now", end_date="+10d")
        start_time = generate_random_slot(random_date)
        doctor_times = doctor_schedule.setdefault(doctor.id, [])

        # Проверка: нет записи у врача в пределах +/- 1 часа
        if all(abs((start_time - t).total_seconds()) >= 3600 for t in doctor_times):
            appointments.append(
                Appointment(
                    doctor_id=doctor.id,
                    patient_id=patient.id,
                    start_time=start_time,
                )
            )
            doctor_times.append(start_time)
            used_pairs.add((doctor.id, patient.id))

        attempts += 1

    return appointments


if __name__ == "__main__":
    patients = generate_patients()
    doctors = generate_doctors()
    appointments = generate_appointments(patients, doctors)

    print(f"Создано пациентов: {len(patients)}")
    print(f"Создано врачей: {len(doctors)}")
    print(f"Создано записей: {len(appointments)}")

    for app in appointments:
        print(app)
