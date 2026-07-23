"""Модуль для работы с KudaGo API."""

import logging
from datetime import datetime

import requests

from config import settings
from models import Event, Image, Location

logger = logging.getLogger(__name__)


class KudaGoAPIError(Exception):
    """Ошибка при запросе к KudaGo API."""


class KudaGoAPI:
    """Клиент для работы с публичным API KudaGo.

    Эндпоинты:
        - GET /events/          — список мероприятий
        - GET /events/{id}/     — детальная информация
    """

    def __init__(self, version: str = None, timeout: int = None):
        self.version = version or settings.KUDAGO_API_VERSION
        self.timeout = timeout or settings.REQUEST_TIMEOUT
        self.base_url = f"{settings.KUDAGO_BASE_URL}/{self.version}"
        self.session = requests.Session()

    # ------------------------------------------------------------------
    # Внутренние методы
    # ------------------------------------------------------------------

    def _get(self, endpoint: str, params: dict = None) -> dict:
        """Выполнить GET-запрос к API."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        params = params or {}

        try:
            response = self.session.get(
                url, params=params, timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response else None
            if status == 404:
                raise KudaGoAPIError("Ресурс не найден")
            raise KudaGoAPIError(f"HTTP ошибка: {status}") from exc
        except requests.RequestException as exc:
            raise KudaGoAPIError(f"Ошибка сети: {exc}") from exc

    # ------------------------------------------------------------------
    # Публичные методы
    # ------------------------------------------------------------------

    def get_events(
        self,
        city: str = None,
        date: datetime = None,
        categories: list[str] = None,
        page: int = 1,
        page_size: int = None,
    ) -> dict:
        """
        Получить список мероприятий.

        Args:
            city: Код города (msk, spb, ...). Обязательный параметр.
            date: Дата в формате datetime (фильтр showing_since/showing_until).
            categories: Список категорий для фильтрации.
            page: Номер страницы пагинатора.
            page_size: Размер страницы (макс. 100).

        Returns:
            Словарь с ключами: count, next, previous, results (список Event).
        """
        page_size = page_size or settings.DEFAULT_PAGE_SIZE
        city = city or settings.DEFAULT_CITY

        params: dict = {
            "location": city,
            "page": page,
            "page_size": min(page_size, settings.MAX_PAGE_SIZE),
            "lang": settings.DEFAULT_LANG,
            "fields": (
                "id,title,slug,address,location,description,site_url,"
                "timetable,images,categories"
            ),
        }

        if date:
            params["showing_since"] = int(date.timestamp())
            params["showing_until"] = int(date.timestamp()) + 86400

        if categories:
            params["categories"] = ",".join(categories)

        data = self._get("events", params)
        results = [self._parse_event(item) for item in data.get("results", [])]

        return {
            "count": data.get("count", 0),
            "next": data.get("next"),
            "previous": data.get("previous"),
            "results": results,
        }

    def get_event_details(self, event_id: int) -> Event:
        """
        Получить детальную информацию о мероприятии.

        Args:
            event_id: ID мероприятия.

        Returns:
            Объект Event с полным описанием.
        """
        params = {
            "lang": settings.DEFAULT_LANG,
            "fields": (
                "id,title,slug,address,location,description,body_text,"
                "site_url,timetable,images,categories,phone"
            ),
            "expand": "images",
        }

        data = self._get(f"events/{event_id}", params)
        return self._parse_event(data, detailed=True)

    # ------------------------------------------------------------------
    # Парсеры
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_event(data: dict, detailed: bool = False) -> Event:
        """Спарсить JSON-объект KudaGo в Event.

        Поля API (из документации):
            id, title, short_title, slug, address, location,
            timetable, phone, images, description, body_text,
            site_url, coords, subway, categories, tags
        """
        images = []
        for img in data.get("images", []):
            full_url = img.get("image", "")
            thumbnails = img.get("thumbnails", {})
            thumb_url = thumbnails.get("640x384", thumbnails.get("144x96", ""))
            images.append(Image(full_url=full_url, thumbnail_url=thumb_url))

        coords_data = data.get("coords")
        coords = None
        if coords_data:
            coords = Location(
                lat=coords_data.get("lat", 0),
                lon=coords_data.get("lon", 0),
            )

        # description — краткое описание, body_text — полное (только в детализации)
        description = data.get("description", "")
        body_text = ""
        if detailed:
            body_text = data.get("body_text", "") or description

        location_name = data.get("location", "")

        return Event(
            event_id=data.get("id"),
            title=data.get("title", "Без названия"),
            slug=data.get("slug", ""),
            location_name=location_name,
            address=data.get("address", ""),
            description=description,
            body_text=body_text,
            timetable=data.get("timetable", ""),
            images=images,
            site_url=data.get("site_url", ""),
            coords=coords,
            phone=data.get("phone", ""),
            categories=data.get("categories", []),
        )