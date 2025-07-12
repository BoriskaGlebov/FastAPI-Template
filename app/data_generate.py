from datetime import datetime, time
from random import choice, randint
from typing import List, Set, Tuple

from factory.base import Factory
from factory.declarations import LazyAttribute, LazyFunction
from factory.faker import Faker
import faker

from app.appointments.models import Appointment, Doctor, Patient

faker_instance = faker.Faker("ru_RU")


class PatientFactory(Factory[Patient]):
    """Фабрика для генерации экземпляров модели Patient."""

    class Meta:
        model = Patient

    name = Faker("name", locale="ru_RU")
    email = LazyAttribute(lambda _: faker_instance.unique.email())
    phone = LazyAttribute(lambda _: faker_instance.phone_number())


class DoctorFactory(Factory[Doctor]):
    """Фабрика для генерации экземпляров модели Doctor."""

    class Meta:
        model = Doctor

    name = Faker("name", locale="ru_RU")
    specialization = LazyFunction(
        lambda: choice(["Терапевт", "Хирург", "Кардиолог", "Невролог"])
    )
    experience_years = LazyFunction(lambda: randint(1, 40))


class AppointmentFactory(Factory[Appointment]):
    """Фабрика для генерации экземпляров модели Appointment."""

    class Meta:
        model = Appointment

    doctor_id = LazyFunction(lambda: randint(1, 5))
    patient_id = LazyFunction(lambda: randint(1, 10))
    start_time = LazyFunction(
        lambda: faker_instance.date_time_between(start_date="now", end_date="+10d")
    )


def generate_patients(num_patients: int = 10) -> List[Patient]:
    """Генерирует список экземпляров Patient.

    Args:
        num_patients (int): Количество пациентов для генерации.

    Returns:
        List[Patient]: Список сгенерированных пациентов.
    """
    return [PatientFactory() for _ in range(num_patients)]  # type: ignore


def generate_doctors(num_doctors: int = 5) -> List[Doctor]:
    """Генерирует список экземпляров Doctor.

    Args:
        num_doctors (int): Количество врачей для генерации.

    Returns:
        List[Doctor]: Список сгенерированных врачей.
    """
    return [DoctorFactory() for _ in range(num_doctors)]  # type: ignore


def generate_random_slot(date: datetime) -> datetime:
    """Генерирует случайное время на указанную дату в интервале 08:00–18:00 с шагом 15 минут.

    Args:
        date (datetime): Дата, на которую нужно сгенерировать время.

    Returns:
        datetime: Объект datetime с выбранной датой и случайным временем.
    """
    hour = randint(8, 17)  # До 17:45, чтобы не выйти за 18:00
    minute = choice([0, 15, 30, 45])
    return datetime.combine(date.date(), time(hour, minute))


def generate_appointments(
    patients: List[Patient],
    doctors: List[Doctor],
    num_appointments: int = 20,
) -> List[Appointment]:
    """Генерирует уникальные записи к врачам с учетом ограничений.

    - Интервал между записями одного врача должен быть минимум 1 час.
    - Один пациент не может быть записан к одному врачу более одного раза.
    - Время приёма находится в пределах 08:00–18:00.

    Args:
        patients (List[Patient]): Список доступных пациентов.
        doctors (List[Doctor]): Список доступных врачей.
        num_appointments (int): Количество записей, которые нужно создать.

    Returns:
        List[Appointment]: Список сгенерированных уникальных записей.
    """
    appointments: List[Appointment] = []
    doctor_schedule: dict[int, List[datetime]] = {}
    used_pairs: Set[Tuple[int, int]] = set()

    attempts = 0
    max_attempts = num_appointments * 15

    while len(appointments) < num_appointments and attempts < max_attempts:
        doctor = choice(doctors)
        patient = choice(patients)

        if (doctor.id, patient.id) in used_pairs:
            attempts += 1
            continue

        random_date = faker_instance.date_time_between(
            start_date="now", end_date="+10d"
        )
        start_time = generate_random_slot(random_date)
        doctor_times = doctor_schedule.setdefault(doctor.id, [])

        if all(abs((start_time - t).total_seconds()) >= 3600 for t in doctor_times):
            appointment = Appointment(
                doctor_id=doctor.id,
                patient_id=patient.id,
                start_time=start_time,
            )
            appointments.append(appointment)
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
