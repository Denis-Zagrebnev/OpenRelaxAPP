"""Модели данных мероприятий."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Location:
    """Координаты места (поля coords из API)."""
    lat: float
    lon: float


@dataclass
class Image:
    """Изображение мероприятия (из API)."""
    full_url: str
    thumbnail_url: Optional[str] = None


@dataclass
class Event:
    """Мероприятие.

    Поля соответствуют документации KudaGo API:
        id, title, slug, address, location, timetable,
        phone, images, description, body_text, site_url,
        coords, categories, tags
    """
    event_id: int
    title: str
    slug: str
    location_name: str
    address: str
    description: str
    body_text: str
    timetable: str = ""
    images: list[Image] = None
    site_url: str = ""
    coords: Optional[Location] = None
    phone: str = ""
    categories: list[str] = None

    def __post_init__(self):
        self.images = self.images or []
        self.categories = self.categories or []

    @property
    def short_description(self) -> str:
        """Первые 200 символов описания (очищенного от HTML)."""
        from utils import clean_html
        text = clean_html(self.description)
        return text[:200] + "..." if len(text) > 200 else text

    @property
    def formatted_timetable(self) -> str:
        """Расписание мероприятия из поля timetable."""
        return self.timetable if self.timetable else "Время не указано"