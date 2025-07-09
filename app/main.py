from contextlib import asynccontextmanager
import os
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import uvicorn

from app.appointments.dao import AppointmentDAO, DoctorDAO, PatientDAO
from app.appointments.router import router as router_appointment
from app.config import logger
from app.data_generate import generate_appointments, generate_doctors, generate_patients
from app.database import Base, engine
from app.dependencies import get_session
from app.exceptions.exceptions_methods import (
    http_exception_handler,
    integrity_error_exception_handler,
    validation_exception_handler,
)

tags_metadata: List[Dict[str, Any]] = [
    {
        "name": "Appointments",
        "description": "Логика записи пациентов",
    },
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Жизненный цикл приложения FastAPI.

    Если переменная окружения RESET_DB установлена в "1", то при запуске:
    - Пересоздаётся база данных (drop_all + create_all).
    - Добавляются тестовые врачи и пациенты.
    - Создаются тестовые записи приёмов.

    Args:
        app (FastAPI): Экземпляр приложения FastAPI.

    Yields:
        None: Управляет жизненным циклом приложения.
    """
    if os.getenv("RESET_DB", "0") == "1":
        logger.warning("Пересоздание БД (drop_all + create_all) включено!")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

        async for session in get_session():
            for doctor in generate_doctors(5):
                await DoctorDAO.add(session, **doctor.to_dict())

            for patient in generate_patients(5):
                await PatientDAO.add(session, **patient.to_dict())

            doctors = list(await DoctorDAO.find_all(async_session=session))
            patients = list(await PatientDAO.find_all(async_session=session))

            for appointment in generate_appointments(
                patients=patients, doctors=doctors, num_appointments=20
            ):
                try:
                    await AppointmentDAO.add(session, **appointment.to_dict())
                except (ValueError, SQLAlchemyError) as e:
                    logger.warning(f"Ошибка при создании приёма: {e}")

    yield


app = FastAPI(
    debug=True,
    title="Girumed Test API",
    summary="Микросервис для записи пациентов с возможностью быстрого развёртывания и тестирования.",
    description="""
## Эндпойнты
- `POST /appointments` — создать запись.
- `GET /appointments/{id}` — получить запись по ID.
- Ограничение: уникальность пары doctor_id + start_time.

""",
    openapi_tags=tags_metadata,
    contact={
        "name": "Boriska Glebov",
        "url": "http://localhost:8000/docs",
        "email": "BorisTheBlade.glebov@yandex.ru",
    },
    lifespan=lifespan,
)

app.include_router(router_appointment)

app.add_exception_handler(HTTPException, http_exception_handler)  # type: ignore[arg-type]
app.add_exception_handler(IntegrityError, integrity_error_exception_handler)  # type: ignore[arg-type]
app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]


@app.get("/health")
async def health_check():
    """Эндпойнт для проверки состояния сервиса.

    Returns:
        dict: {"status": "ok"} — если сервис работает.
    """
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app="main:app", host="0.0.0.0", port=8000, reload=True)
