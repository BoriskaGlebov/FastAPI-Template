from pathlib import Path
import sys
from typing import Any, Dict, Mapping, Optional

from loguru import logger
from pydantic import Field, SecretStr, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict  # type: ignore


class Settings(BaseSettings):
    ENV: str = Field(default="db")  # local когда работаю локально
    BASE_DIR: Path = Path(__file__).resolve().parent.parent

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

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def _resolve_host(self) -> str:
        """Определяет правильный хост базы данных в зависимости от значения ENV.

        Returns:
            str: Адрес хоста базы данных.
        """
        if self.ENV == "local":
            return "localhost"
        return self.DB_HOST

    def get_db_url(self) -> str:
        """Формирует URL подключения к основной базе данных.

        Returns:
            str: Строка подключения к основной базе данных в формате postgresql+asyncpg.
        """
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD.get_secret_value()}@"
            f"{self._resolve_host()}:{self.DB_PORT}/{self.DB_NAME}"
        )

    def get_test_db_url(self) -> str:
        """Формирует URL подключения к тестовой базе данных.

        Returns:
            str: Строка подключения к тестовой базе данных в формате postgresql+asyncpg.
        """
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD.get_secret_value()}@"
            f"{self._resolve_host()}:{self.DB_PORT}/{self.DB_TEST}"
        )


class LoggerConfig:
    """Настройка логгирования с использованием loguru.

    Args:
        log_dir (Path): Путь к директории для хранения логов.
        logger_level_stdout (str, optional): Уровень логирования для вывода в stdout. Defaults to "INFO".
        logger_level_file (str, optional): Уровень логирования для основного файла лога. Defaults to "DEBUG".
        logger_error_file (str, optional): Уровень логирования для файла ошибок. Defaults to "ERROR".
        extra_defaults (Optional[Dict[str, Any]], optional): Значения по умолчанию для extra полей. Defaults to None.
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
        """Создает директорию для логов, если она не существует, и устанавливает права доступа."""
        if not self.log_dir.exists():
            self.log_dir.mkdir(parents=True, exist_ok=True, mode=0o755)

    @staticmethod
    def _user_filter(record: Mapping[str, Any]) -> bool:
        """Фильтр для логов с указанным пользователем.

        Args:
            record (Mapping[str, Any]): Запись лога.

        Returns:
            bool: True, если поле 'user' в extra присутствует и не равно "-".
        """
        user = record.get("extra", {}).get("user")
        return bool(user and user != "-")

    @staticmethod
    def _default_filter(record: Mapping[str, Any]) -> bool:
        """Фильтр для логов без данных пользователя.

        Args:
            record (Mapping[str, Any]): Запись лога.

        Returns:
            bool: True, если поле 'user' отсутствует или равно "-".
        """
        user = record.get("extra", {}).get("user")
        return user in (None, "-")

    @staticmethod
    def _exclude_errors(record: Mapping[str, Any]) -> bool:
        """Исключает записи с уровнем WARNING и выше.

        Args:
            record (Mapping[str, Any]): Запись лога.

        Returns:
            bool: True, если уровень лога ниже WARNING.
        """
        return int(record["level"].no) < int(logger.level("WARNING").no)

    def _filter_for_files(self, record: Mapping[str, Any]) -> bool:
        """Объединенный фильтр для файловых логов.

        Args:
            record (Mapping[str, Any]): Запись лога.

        Returns:
            bool: True, если запись подходит по фильтру пользователя и не является ошибкой.
        """
        return (
            self._user_filter(record) or self._default_filter(record)
        ) and self._exclude_errors(record)

    def _setup_logging(self) -> None:
        """Конфигурирует логгирование, удаляя все текущие обработчики и добавляя новые."""
        logger.remove()
        logger.configure(extra=self.extra_defaults)
        self._add_stdout_handler()
        self._add_file_handlers()

    def _add_stdout_handler(self) -> None:
        """Добавляет обработчик для вывода логов в stdout."""
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
        """Добавляет обработчики для записи логов в файлы."""
        log_file_path = self.log_dir / "file.log"
        error_log_file_path = self.log_dir / "error.log"

        logger.add(
            str(log_file_path),
            level=self.logger_level_file,
            format=self._get_format(),
            rotation="1 day",
            retention="30 days",
            catch=True,
            backtrace=True,
            diagnose=True,
            filter=self._filter_for_files,
            enqueue=True,
        )

        logger.add(
            str(error_log_file_path),
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
        """Возвращает формат строки для логов.

        Returns:
            str: Формат строки для loguru.
        """
        return (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> - "
            "<level>{level:^8}</level> - "
            "<cyan>{name}</cyan>:<magenta>{line}</magenta> - "
            "<yellow>{function}</yellow> - "
            "<white>{message}</white> - "
            "<magenta>{extra[user]:^15}</magenta>"
        )


def get_settings() -> Settings:
    """Загружает настройки из окружения, валидируя их.

    Raises:
        RuntimeError: Если есть ошибки валидации при загрузке настроек.

    Returns:
        Settings: Объект настроек приложения.
    """
    try:
        return Settings()
    except ValidationError as e:
        error_messages = []
        for error in e.errors():
            field = error["loc"]
            message = error["msg"]
            error_messages.append(f"Поле '{field[-1]}': {message}")
        raise RuntimeError(f"Ошибки валидации: {', '.join(error_messages)}")


try:
    settings = get_settings()
    # Создание конфигурации логгера
    logger_config = LoggerConfig(
        log_dir=settings.LOG_DIR,
        logger_level_stdout=settings.LOGGER_LEVEL_STDOUT,
        logger_level_file=settings.LOGGER_LEVEL_FILE,
        logger_error_file=settings.LOGGER_ERROR_FILE,
        extra_defaults={"user": "-"},
    )
except RuntimeError as e:
    print(e)

__all__ = ["logger", "get_settings", "settings"]

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
