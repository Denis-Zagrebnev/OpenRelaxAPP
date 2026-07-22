"""Клавиатуры и меню для VK-бота."""

import json

from event_service import CATEGORY_MAP
from vk_api.keyboard import VkKeyboard, VkKeyboardButtonColor


class VKKeyboards:
    """Набор клавиатур для бота."""

    @staticmethod
    def get_main_keyboard() -> VkKeyboard:
        """Главное меню бота."""
        keyboard = VkKeyboard(one_time=False)

        keyboard.add_button(
            "🏙 Выбрать город", VkKeyboardButtonColor.SECONDARY
        )
        keyboard.add_line()
        keyboard.add_button(
            "📅 Выбрать дату", VkKeyboardButtonColor.SECONDARY
        )
        keyboard.add_line()
        keyboard.add_button(
            "🎭 Выбрать событие", VkKeyboardButtonColor.POSITIVE
        )
        keyboard.add_line()
        keyboard.add_button(
            "🔎 Найти мероприятия", VkKeyboardButtonColor.POSITIVE
        )

        return keyboard

    @staticmethod
    def get_city_keyboard(cities: dict) -> VkKeyboard:
        """Клавиатура выбора города."""
        keyboard = VkKeyboard(one_time=False)

        for code, name in cities.items():
            keyboard.add_button(name, VkKeyboardButtonColor.SECONDARY)

        keyboard.add_line()
        keyboard.add_button("← Назад", VkKeyboardButtonColor.SECONDARY)
        return keyboard

    @staticmethod
    def get_date_keyboard() -> VkKeyboard:
        """Клавиатура выбора даты (ближайшие 7 дней)."""
        keyboard = VkKeyboard(one_time=False)

        from datetime import datetime, timedelta
        for i in range(7):
            day = datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            ) + timedelta(days=i)
            label = day.strftime("%d.%m")
            keyboard.add_button(label, VkKeyboardButtonColor.SECONDARY)

        keyboard.add_line()
        keyboard.add_button("← Назад", VkKeyboardButtonColor.SECONDARY)
        return keyboard

    @staticmethod
    def get_category_keyboard() -> VkKeyboard:
        """Клавиатура выбора категории мероприятия."""
        keyboard = VkKeyboard(one_time=False)

        for display_name, _ in CATEGORY_MAP.items():
            keyboard.add_button(display_name, VkKeyboardButtonColor.POSITIVE)

        keyboard.add_line()
        keyboard.add_button("✏ Свой вариант", VkKeyboardButtonColor.SECONDARY)
        keyboard.add_line()
        keyboard.add_button("← Назад", VkKeyboardButtonColor.SECONDARY)
        return keyboard

    @staticmethod
    def get_event_actions_keyboard(event_id: int) -> VkKeyboard:
        """Клавиатура действий с конкретным мероприятием."""
        keyboard = VkKeyboard(one_time=False)

        keyboard.add_button(
            "Подробнее",
            VkKeyboardButtonColor.POSITIVE,
            payload=json.dumps({"action": "event_details", "event_id": event_id}),
        )
        keyboard.add_line()
        keyboard.add_button(
            "Другие мероприятия",
            VkKeyboardButtonColor.SECONDARY,
            payload=json.dumps({"action": "other_events", "event_id": event_id}),
        )
        keyboard.add_line()
        keyboard.add_button(
            "Главное меню",
            VkKeyboardButtonColor.SECONDARY,
            payload=json.dumps({"action": "main_menu"}),
        )
        return keyboard

    @staticmethod
    def get_pagination_keyboard(current_page: int, has_next: bool) -> VkKeyboard:
        """Клавиатура пагинации."""
        keyboard = VkKeyboard(one_time=False)

        if has_next:
            keyboard.add_button(
                "➡ Далее",
                VkKeyboardButtonColor.POSITIVE,
                payload=json.dumps({"action": "next_page", "page": current_page + 1}),
            )
        keyboard.add_line()
        keyboard.add_button(
            "← Назад в меню",
            VkKeyboardButtonColor.SECONDARY,
            payload=json.dumps({"action": "main_menu"}),
        )
        return keyboard