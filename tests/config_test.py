import os
from unittest.mock import patch

import pytest

from app.config import get_settings


def test_invalid_settings():
    with patch.dict(
        os.environ,
        {
            "DB_USER": "",
            "DB_PASSWORD": "",
            "DB_HOST": "localhost",
            "DB_PORT": "invalid_port",
            "DB_NAME": "test_db",
            "DB_TEST": "test_db_test",
            "UPLOAD_DIRECTORY": "/uploads",
            "PYTHONPATH": "/app",
        },
    ):
        with pytest.raises(RuntimeError):
            get_settings()
