import os
from contextlib import asynccontextmanager
from typing import Any, Dict, List

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

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
from migrations_script import run_alembic_command

# API теги и их описание
tags_metadata: List[Dict[str, Any]] = [
    {
        "name": "Appointments",
        "description": "Логика записи пациентов",
    },
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Действия перед запуском приложения.

    :param app:
    :return:
    """
    logger.info("Перед первым запуском необходимо убедиться в актуальности версии миграции")
    if os.path.split(os.getcwd())[1] == "app":
        run_alembic_command("cd ..; alembic upgrade head;alembic current")
    elif os.path.split(os.getcwd())[1] == "girumed":
        run_alembic_command("alembic upgrade head;alembic current")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async for session in get_session():
        [await DoctorDAO.add(session, **user.to_dict()) for user in generate_doctors(5)]
        [await PatientDAO.add(session, **user.to_dict()) for user in generate_patients(5)]
        doctors = await DoctorDAO.find_all(async_session=session)
        patients = await PatientDAO.find_all(async_session=session)
        # Генерируем приёмы
        for user in generate_appointments(patients=patients, doctors=doctors, num_appointments=20):  # type: ignore
            try:
                await AppointmentDAO.add(session, **user.to_dict())
            except ValueError as e:
                logger.warning(f"⚠️ Не удалось создать приём: {e}")
            except SQLAlchemyError as e:
                logger.error(f"❌ Ошибка базы данных при создании приёма: {e}")
    yield


app = FastAPI(
    debug=True,
    title="Girumed Test API",
    summary="Соберите минимальный, но полноценный микросервис для записи пациентов и "
    "подготовьте его так, чтобы коллега мог развернуть проект за пару "
    "минут и сразу увидеть живой API.",
    description="""
---
# Girumed Test API

## Сервис и бизнес-логика
1. Напишите приложение на FastAPI или Flask.
2. Создайте модель Appointment и два эндпойнта:
3. POST /appointments — создать запись;
4. GET /appointments/{id} — получить запись по ID.
5. В базе должна быть уникальная пара doctor_id + start_time, чтобы один врач не принимал двух пациентов одновременно.


---

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


# Определение обработчиков исключений
app.add_exception_handler(HTTPException, http_exception_handler)  # type: ignore[arg-type]
app.add_exception_handler(IntegrityError, integrity_error_exception_handler)  # type: ignore[arg-type]
app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]


@app.get("/health")
async def health_check():
    """Проверка статуса контейнера."""
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app="main:app", host="0.0.0.0", port=8000, reload=True)
