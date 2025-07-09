from typing import Awaitable, Union, Callable

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from app.config import logger


async def http_exception_handler(
        request: Request,
        exc: HTTPException,
) -> Union[JSONResponse, Awaitable[JSONResponse]]:
    """
    Обработчик исключений HTTPException для FastAPI.

    Args:
        request (Request): HTTP-запрос, вызвавший исключение.
        exc (HTTPException): Объект исключения HTTPException.

    Returns:
        Union[JSONResponse, Awaitable[JSONResponse]]: JSON-ответ с HTTP-кодом ошибки и описанием.
    """
    logger.error(f"HTTPException: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "result": False,
            "error_type": "HTTPException",
            "error_message": exc.detail,
        },
    )


async def integrity_error_exception_handler(
        request: Request,
        exc: IntegrityError,
) -> Union[JSONResponse, Awaitable[JSONResponse]]:
    """
    Обработчик ошибок целостности данных (IntegrityError) из SQLAlchemy.

    Args:
        request (Request): HTTP-запрос, вызвавший исключение.
        exc (IntegrityError): Объект исключения IntegrityError.

    Returns:
        Union[JSONResponse, Awaitable[JSONResponse]]: JSON-ответ с кодом 409 и подробностями ошибки.
    """
    logger.error(f"IntegrityError: {repr(exc.orig)}")
    return JSONResponse(
        status_code=409,
        content={
            "result": False,
            "error_type": "sqlalchemy.exc.IntegrityError",
            "error_message": repr(exc.orig),
        },
    )


async def validation_exception_handler(
        request: Request,
        exc: ValidationError,
) -> Union[JSONResponse, Awaitable[JSONResponse]]:
    """
    Обработчик ошибок валидации Pydantic (ValidationError).

    Args:
        request (Request): HTTP-запрос, вызвавший исключение.
        exc (ValidationError): Объект исключения ValidationError.

    Returns:
        Union[JSONResponse, Awaitable[JSONResponse]]: JSON-ответ с кодом 400 и деталями ошибки валидации.
    """
    logger.error(f"ValidationError: {exc.errors()}")
    return JSONResponse(
        status_code=400,
        content={
            "result": False,
            "error_type": "ValidationError",
            "error_message": exc.errors(),
        },
    )
