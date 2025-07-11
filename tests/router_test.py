from datetime import datetime, timedelta
from random import randint

from fastapi import status
from httpx import AsyncClient
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.appointments.models import Appointment, Doctor, Patient


@pytest.mark.asyncio(loop_scope="session")
async def test_get_appointment_by_id_success(
    async_client: AsyncClient,
    test_db: AsyncSession,
    test_appointment: Appointment,
) -> None:
    response = await async_client.get(f"/api/appointments/{test_appointment.id}")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["id"] == test_appointment.id
    assert data["doctor_id"] == test_appointment.doctor_id
    assert data["patient_id"] == test_appointment.patient_id


@pytest.mark.asyncio(loop_scope="session")
async def test_get_appointment_not_found(
    async_client: AsyncClient,
    test_db: AsyncSession,
) -> None:
    response = await async_client.get("/api/appointments/999999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["error_message"] == "Запись не найдена"


@pytest.mark.asyncio(loop_scope="session")
async def test_create_appointment_success(
    test_doctor: Doctor,
    test_patient2: Patient,
    async_client: AsyncClient,
    test_db: AsyncSession,
) -> None:

    start_base = datetime.now().replace(microsecond=0, second=0) + timedelta(days=1)
    hour = randint(8, 17)
    minute = randint(0, 1) * 30

    start_time = start_base.replace(hour=hour, minute=minute)
    payload = {
        "doctor_id": test_doctor.id,
        "patient_id": test_patient2.id,
        "start_time": start_time.strftime("%Y-%m-%d %H:%M"),
    }

    response = await async_client.post("/api/appointments", json=payload)
    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()
    assert data["doctor_id"] == payload["doctor_id"]
    assert data["patient_id"] == payload["patient_id"]


@pytest.mark.asyncio(loop_scope="session")
async def test_create_appointment_conflict(
    test_doctor: Doctor,
    test_patient1: Patient,
    test_appointment: Appointment,
    async_client: AsyncClient,
    test_db: AsyncSession,
) -> None:
    payload = {
        "doctor_id": test_appointment.doctor_id,
        "patient_id": test_appointment.patient_id,
        "start_time": test_appointment.start_time.strftime("%Y-%m-%d %H:%M"),
    }

    response = await async_client.post("/api/appointments", json=payload)
    assert response.status_code == status.HTTP_409_CONFLICT
    assert "занято" in response.json()["error_message"]


@pytest.mark.asyncio(loop_scope="session")
async def test_create_appointment_doctor_not_found(
    test_patient1: Patient,
    async_client: AsyncClient,
    test_db: AsyncSession,
) -> None:
    start_base = datetime.now().replace(microsecond=0, second=0) + timedelta(days=1)
    hour = randint(8, 17)  # 17 чтобы последнее возможное время было 17:00
    minute = randint(0, 1) * 30  # например, только 00 или 30 минут

    start_time = start_base.replace(hour=hour, minute=minute)
    payload = {
        "doctor_id": 999999,
        "patient_id": test_patient1.id,
        "start_time": start_time.strftime("%Y-%m-%d %H:%M"),
    }

    response = await async_client.post("/api/appointments", json=payload)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Доктор" in response.json()["error_message"]


@pytest.mark.asyncio(loop_scope="session")
async def test_create_appointment_patient_not_found(
    test_doctor: Doctor,
    async_client: AsyncClient,
    test_db: AsyncSession,
) -> None:
    start_base = datetime.now().replace(microsecond=0, second=0) + timedelta(days=1)
    hour = randint(8, 17)
    minute = randint(0, 1) * 30

    start_time = start_base.replace(hour=hour, minute=minute)
    payload = {
        "doctor_id": test_doctor.id,
        "patient_id": 999999,
        "start_time": start_time.strftime("%Y-%m-%d %H:%M"),
    }

    response = await async_client.post("/api/appointments", json=payload)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Пациент" in response.json()["error_message"]
