"""Тестовый скрипт для проверки работы с KudaGo API.

Запуск: python test_api.py
Не требует VK-токена, работает отдельно от бота.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

# Добавляем родительскую директорию в путь для импорта
sys.path.insert(0, str(Path(__file__).resolve().parent))

from kudago_api import KudaGoAPI, KudaGoAPIError
from event_service import EventService, EventNotFoundError


def print_header(title: str):
    """Вывести заголовок секции."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def print_event(event, index: int = 0):
    """Красиво вывести одно мероприятие."""
    prefix = f"  [{index + 1}] " if index >= 0 else "  - "
    print(f"{prefix}{event.title}")
    print(f"      Расписание: {event.formatted_timetable}")
    print(f"      Адрес: {event.address or event.location_name}")
    if event.short_description:
        print(f"      Описание: {event.short_description[:120]}...")
    print(f"      Ссылка: {event.site_url}")
    print(f"      Категории: {event.categories}")
    print()


def test_get_events_moscow():
    """Тест 1: Получить 5 мероприятий Москвы."""
    print_header("Тест 1: 5 мероприятий Москвы")

    service = EventService()
    
    try:
        result = service.search_events(
            city="msk",
            date=None,
            page=1,
            page_size=5,
        )
        print(f"  Найдено: {result['count']} мероприятий")
        print(f"  Страница: {result.get('next')}")
        print()
        for i, event in enumerate(result["results"]):
            print_event(event, i)
        print(f"  OK — {len(result['results'])} мероприятий получено")
    except EventNotFoundError:
        print("  Нет мероприятий, попробуйте изменить параметры поиска")
    except KudaGoAPIError as exc:
        print(f"  Ошибка API: {exc}")


def test_get_events_concerts():
    """Тест 2: Получить 5 концертов."""
    print_header("Тест 2: 5 концертов (Казань, сегодня)")

    service = EventService()
    
    try:
        result = service.search_events(
            city="kzn",
            date=None,
            categories=["concert"],
            page=1,
            page_size=5,
        )
        print(f"  Найдено: {result['count']} концертов")
        print()
        for i, event in enumerate(result["results"]):
            print_event(event, i)
        print(f"  OK — {len(result['results'])} концертов получено")
    except EventNotFoundError:
        print("  Концертов не найдено, попробуйте изменить параметры")
    except KudaGoAPIError as exc:
        print(f"  Ошибка API: {exc}")


def test_get_events_exhibitions():
    """Тест 3: Получить 5 выставок."""
    print_header("Тест 3: 5 выставок (Москва, сегодня)")

    service = EventService()
    
    try:
        result = service.search_events(
            city="msk",
            date=None,
            categories=["exhibition"],
            page=1,
            page_size=5,
        )
        print(f"  Найдено: {result['count']} выставок")
        print()
        for i, event in enumerate(result["results"]):
            print_event(event, i)
        print(f"  OK — {len(result['results'])} выставок получено")
    except EventNotFoundError:
        print("  Выставок не найдено, попробуйте изменить параметры")
    except KudaGoAPIError as exc:
        print(f"  Ошибка API: {exc}")


def test_get_event_details():
    """Тест 4: Получить подробную информацию о первом найденном мероприятии."""
    print_header("Тест 4: Детали первого мероприятия (Москва)")

    service = EventService()
    
    try:
        # Сначала получим список
        result = service.search_events(
            city="msk",
            date=None,
            page=1,
            page_size=1,
        )

        if not result["results"]:
            print("  Нет мероприятий для получения деталей")
            return

        first_event = result["results"][0]
        print(f"  ID мероприятия: {first_event.event_id}")
        print(f"  Название: {first_event.title}")
        print()

        # Теперь получим детали
        details = service.get_event_details(first_event.event_id)
        print(f"  <b>{details.title}</b>")
        print(f"  Расписание: {details.formatted_timetable}")
        print(f"  Адрес: {details.address}")
        print(f"  Телефон: {details.phone}")
        print(f"  Короткое описание: {details.short_description}")
        print(f"  Полное описание: {details.body_text[:300]}...")
        print(f"  Ссылка: {details.site_url}")
        print(f"  Категории: {details.categories}")
        print(f"  Изображений: {len(details.images)}")
        if details.images:
            print(f"    Первое: {details.images[0].full_url}")
        print()
        print("  OK — детали получены")
    except EventNotFoundError:
        print("  Мероприятие не найдено")
    except KudaGoAPIError as exc:
        print(f"  Ошибка API: {exc}")


def test_category_mapping():
    """Тест 5: Проверка маппинга категорий."""
    print_header("Тест 5: Маппинг категорий (CATEGORY_MAP)")

    from event_service import CATEGORY_MAP

    print(f"  CATEGORY_MAP = {CATEGORY_MAP}")
    print()

    service = EventService()

    for display_name in CATEGORY_MAP.keys():
        result = service.find_category(display_name)
        print(f"  '{display_name}' -> {result}")

    # Проверим несуществующую категорию
    result = service.find_category("Неизвестное")
    print(f"  'Неизвестное' -> {result}")
    print()
    print("  OK — маппинг проверен")


def main():
    """Запустить все тесты."""
    print("=" * 60)
    print("  Tестирование KudaGo API")
    print("=" * 60)

    test_get_events_moscow()
    test_get_events_concerts()
    test_get_events_exhibitions()
    test_get_event_details()
    test_category_mapping()

    print("\n" + "=" * 60)
    print("  Тестирование завершено")
    print("=" * 60)


if __name__ == "__main__":
    main()