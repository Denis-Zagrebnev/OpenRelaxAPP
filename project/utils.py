"""Вспомогательные функции."""

import logging
import re

logger = logging.getLogger(__name__)


def clean_html(text: str) -> str:
    """Удалить HTML-теги из строки."""
    if not text:
        return ""
    clean = re.sub(r"<[^>]+>", "", text)
    clean = clean.replace("&nbsp;", " ").replace("&amp;", "&")
    clean = clean.replace("&lt;", "<").replace("&gt;", ">")
    return clean.strip()


def format_event_preview(event) -> str:
    """Сформировать короткое превью мероприятия для вывода в чат."""
    lines = [
        f"🎭 <b>{event.title}</b>",
        f"📅 {event.formatted_timetable}",
        f"📍 {event.address or event.location_name}",
    ]
    if event.short_description:
        lines.append(f"📝 {event.short_description}")
    if event.site_url:
        lines.append(f"🔗 <a href='{event.site_url}'>Подробнее</a>")

    return "\n".join(lines)