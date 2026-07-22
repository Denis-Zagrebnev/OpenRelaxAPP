"""Бизнес-логика поиска мероприятий."""

import logging
from datetime import datetime
from typing import Optional

from kudago_api import KudaGoAPI, KudaGoAPIError
from models import Event
from utils import format_event_preview

logger = logging.getLogger(__name__)

# Маппинг пользовательских категорий -> категории KudaGo API
CATEGORY_MAP = {
    "Концерты": "concert",
    "Выставки": "exhibition",
    "Кино": "cinema",
    "Фестивали": "festival",
    "Лекции": "lecture",
}


class EventNotFoundError(Exception):
    """Мероприятие не найдено."""


class EventService:
    """Сервис для поиска и обработки мероприятий."""

    def __init__(self, api: KudaGoAPI = None):
        self.api = api or KudaGoAPI()

    # ------------------------------------------------------------------
    # Поиск мероприятий
    # ------------------------------------------------------------------

    def search_events(
        self,
        city: str,
        date: datetime,
        categories: list[str] = None,
        page: int = 1,
        page_size: int = None,
    ) -> dict:
        """
        Выполнить поиск мероприятий с заданными параметрами.

        Args:
            city: Код города (msk, spb, ...).
            date: Дата поиска.
            categories: Список категорий KudaGo.
            page: Номер страницы.
            page_size: Размер страницы.

        Returns:
            Словарь с результатами поиска.
        """
        try:
            result = self.api.get_events(
                city=city,
                date=date,
                categories=categories,
                page=page,
                page_size=page_size,
            )
        except KudaGoAPIError as exc:
            logger.error(f"Ошибка при поиске мероприятий: {exc}")
            raise

        if not result["results"]:
            raise EventNotFoundError(
                "Мероприятия не найдены. Попробуйте изменить параметры поиска."
            )

        return result

    # ------------------------------------------------------------------
    # Детали мероприятия
    # ------------------------------------------------------------------

    def get_event_details(self, event_id: int) -> Event:
        """Получить детальную информацию о мероприятии."""
        try:
            return self.api.get_event_details(event_id)
        except KudaGoAPIError as exc:
            logger.error(f"Ошибка при получении деталей события {event_id}: {exc}")
            raise EventNotFoundError(
                f"Не удалось получить информацию о мероприятии: {exc}"
            )

    # ------------------------------------------------------------------
    # Категории
    # ------------------------------------------------------------------

    def find_category(self, query: str) -> list[str]:
        """
        Найти категорию KudaGo по пользовательскому запросу.

        Args:
            query: Строка от пользователя (например, "Концерты").

        Returns:
            Список категорий KudaGo (один элемент или пустой список).
        """
        query_stripped = query.strip()
        for display_name, kategory in CATEGORY_MAP.items():
            if display_name.lower() == query_stripped.lower():
                return [kategory]
        return []

    def get_event_preview_text(self, event: Event) -> str:
        """Сформировать текст превью мероприятия."""
        return format_event_preview(event)

    # ------------------------------------------------------------------
    # Связанные события
    # ------------------------------------------------------------------

    def get_similar_events(
        self,
        city: str,
        date: datetime,
        exclude_id: int,
        page: int = 1,
        page_size: int = None,
    ) -> dict:
        """
        Найти другие события в тот же день, исключая указанное.

        Args:
            city: Код города.
            date: Дата поиска.
            exclude_id: ID события для исключения.
            page: Номер страницы.
            page_size: Размер страницы.

        Returns:
            Словарь с результатами поиска.
        """
        result = self.api.get_events(
            city=city,
            date=date,
            page=page,
            page_size=page_size,
        )

        # Исключаем указанное событие
        result["results"] = [
            e for e in result["results"] if e.event_id != exclude_id
        ]

        return result