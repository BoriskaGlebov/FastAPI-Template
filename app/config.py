import os
import sys
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

from loguru import logger
from pydantic import Field, SecretStr, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

env_file_local: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
env_file_docker: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env.docker")


class Settings(BaseSettings):
    """
    Схема с конфигурацией приложения.

    Атрибуты:
        DB_USER (str): Пользователь базы данных.
        DB_PASSWORD (SecretStr): Пароль базы данных (секрет).
        DB_HOST (str): Хост базы данных.
        DB_PORT (int): Порт базы данных.
        DB_NAME (str): Имя основной базы данных.
        DB_TEST (str): Имя тестовой базы данных.
        PYTHONPATH (str): Путь к Python.
    """

    ENV: str = Field(default="db")  # default = local, но может быть 'container' или 'prod'

    DB_USER: str
    DB_PASSWORD: SecretStr
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_TEST: str
    PYTHONPATH: str
    LOGGER_LEVEL_STDOUT: str
    LOGGER_LEVEL_FILE: str
    LOGGER_ERROR_FILE: str
    LOG_DIR: Path = Path(__file__).resolve().parent / "logs"

    model_config = SettingsConfigDict(extra="ignore")

    def _resolve_host(self) -> str:
        """Возвращает правильный хост базы данных в зависимости от ENV."""
        if self.ENV == "local":
            return "localhost"
        return self.DB_HOST  # обычно "db" в docker-compose

    def get_db_url(self) -> str:
        """
        Получает URL для основной базы данных.

        :return: URL базы данных в формате строки.
        """
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD.get_secret_value()}@"
            f"{self._resolve_host()}:{self.DB_PORT}/{self.DB_NAME}"
        )

    def get_test_db_url(self) -> str:
        """
        Получает URL для тестовой базы данных.

        :return: URL тестовой базы данных в формате строки.
        """
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD.get_secret_value()}@"
            f"{self._resolve_host()}:{self.DB_PORT}/{self.DB_TEST}"
        )

    @classmethod
    def static_path(cls) -> str:
        """Путь к директории для статических файлов."""
        return os.path.join(os.path.dirname(__file__), "static")

    @classmethod
    def template_path(cls) -> str:
        """Возвращает путь к директории для файлов HTML."""
        return os.path.join(os.path.dirname(__file__), "templates")


def get_settings() -> Settings:
    """Возвращает путь к директории для файлов HTML."""
    env_file = env_file_docker if os.getenv("ENV") == "docker" else env_file_local
    try:
        return Settings(_env_file=env_file)
    except ValidationError as e:
        # Извлечение сообщений об ошибках с указанием полей
        error_messages = []
        for error in e.errors():
            field = error["loc"]  # Получаем местоположение ошибки
            message = error["msg"]  # Получаем сообщение об ошибке
            error_messages.append(f"Field '{field[-1]}' error: {message}")  # Указываем поле и сообщение

        raise RuntimeError(f"Validation errors: {', '.join(error_messages)}")


try:
    settings = get_settings()
except RuntimeError as e:
    print(e)


class LoggerConfig:
    """
    Класс для настройки логирования с помощью loguru.

    Параметры:
        log_dir: Директория для хранения логов
        logger_level_stdout: Уровень логирования для stdout
        logger_level_file: Уровень логирования для файлового лога
        logger_error_file: Уровень логирования для файла ошибок
        extra_defaults: Значения по умолчанию для extra полей
    """

    def __init__(
        self,
        log_dir: Path,
        logger_level_stdout: str = "INFO",
        logger_level_file: str = "DEBUG",
        logger_error_file: str = "ERROR",
        extra_defaults: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.log_dir = log_dir
        self.logger_level_stdout = logger_level_stdout
        self.logger_level_file = logger_level_file
        self.logger_error_file = logger_error_file
        self.extra_defaults = extra_defaults or {"user": "-"}

        self._ensure_log_dir_exists()
        self._setup_logging()

    def _ensure_log_dir_exists(self) -> None:
        """Создает директорию для логов если она не существует."""
        if not self.log_dir.exists():
            self.log_dir.mkdir(parents=True)
            # Дать права: rwx для владельца, rx для группы и других (755)
            os.chmod(self.log_dir, 0o777)

    @staticmethod
    def _user_filter(record: Mapping[str, Any]) -> bool:
        """Фильтр для логов с указанным пользователем."""
        user = record["extra"].get("user")
        return bool(user and user != "-")

    @staticmethod
    def _default_filter(record: Mapping[str, Any]) -> bool:
        """Фильтр для логов без данных пользователя."""
        user = record["extra"].get("user")
        return user in (None, "-")

    @staticmethod
    def _exclude_errors(record: Mapping[str, Any]) -> bool:
        """Фильтр для исключения ошибок из обычного файла логов."""
        return record["level"].no < logger.level("WARNING").no

    def _setup_logging(self) -> None:
        """Настраивает обработчики логирования."""
        logger.remove()
        logger.configure(extra=self.extra_defaults)
        self._add_stdout_handler()
        self._add_file_handlers()

    def _add_stdout_handler(self) -> None:
        """Добавляет обработчик для вывода в stdout."""
        logger.add(
            sys.stdout,
            level=self.logger_level_stdout,
            format=self._get_format(),
            filter=lambda r: self._user_filter(r) or self._default_filter(r),
            catch=True,
            diagnose=True,
            enqueue=True,
        )

    def _add_file_handlers(self) -> None:
        """Добавляет обработчики для записи в файлы."""
        log_file_path = self.log_dir / "file.log"
        log_error_file_path = self.log_dir / "error.log"

        logger.add(
            str(log_file_path),
            level=self.logger_level_file,
            format=self._get_format(),
            rotation="1 day",
            retention="30 days",
            catch=True,
            backtrace=True,
            diagnose=True,
            filter=lambda r: (self._user_filter(r) or self._default_filter(r)) and self._exclude_errors(r),
            enqueue=True,
        )

        logger.add(
            str(log_error_file_path),
            level=self.logger_error_file,
            format=self._get_format(),
            rotation="1 day",
            retention="30 days",
            catch=True,
            backtrace=True,
            diagnose=True,
            filter=lambda r: self._user_filter(r) or self._default_filter(r),
            enqueue=True,
        )

    @staticmethod
    def _get_format() -> str:
        """Возвращает формат строки логов."""
        return (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> - "
            "<level>{level:^8}</level> - "
            "<cyan>{name}</cyan>:<magenta>{line}</magenta> - "
            "<yellow>{function}</yellow> - "
            "<white>{message}</white> - "
            "<magenta>{extra[user]:^15}</magenta>"
        )


# Создание конфигурации логгера
logger_config = LoggerConfig(
    log_dir=settings.LOG_DIR,
    logger_level_stdout=settings.LOGGER_LEVEL_STDOUT,
    logger_level_file=settings.LOGGER_LEVEL_FILE,
    logger_error_file=settings.LOGGER_ERROR_FILE,
    extra_defaults={"user": "-"},
)
# Теперь вы можете использовать logger в других модулях
# Явный экспорт для того что б mypy не ругался
__all__ = ["logger"]

if __name__ == "__main__":
    logger.bind(user="Boris").debug("Сообщение")
    logger.bind(filename="Boris_file.txt").debug("Сообщение")
    logger.bind(user="Boris", filename="Boris_file.txt").warning("Сообщение")
    logger.debug("Сообщение")
    logger.error("asdasd")
    logger.bind(user="Boris").warning("Сообщение")
    logger.bind(filename="Boris_file.txt").error("Сообщение")
    print(settings.get_db_url())
    print(settings.get_test_db_url())
