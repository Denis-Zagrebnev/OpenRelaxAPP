"""Конфигурация приложения и переменные окружения."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Загрузка .env из корня проекта
_project_dir = Path(__file__).resolve().parent
load_dotenv(_project_dir / ".env")


class Settings:
    """Настройки приложения из переменных окружения."""

    VK_TOKEN: str = os.getenv("VK_TOKEN", "")
    KUDAGO_API_VERSION: str = os.getenv("KUDAGO_API_VERSION", "v1.4")
    KUDAGO_BASE_URL: str = "https://kudago.com/public-api"
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "15"))
    DEFAULT_PAGE_SIZE: int = int(os.getenv("DEFAULT_PAGE_SIZE", "20"))
    MAX_PAGE_SIZE: int = int(os.getenv("MAX_PAGE_SIZE", "100"))
    DEFAULT_CITY: str = os.getenv("DEFAULT_CITY", "msk")
    DEFAULT_LANG: str = os.getenv("DEFAULT_LANG", "ru")


settings = Settings()