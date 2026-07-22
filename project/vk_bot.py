"""VK LongPoll бот для поиска мероприятий через KudaGo API."""

import json
import logging
import random
from datetime import datetime, timedelta
from typing import Any

import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType

from config import settings
from event_service import CATEGORY_MAP, EventNotFoundError, EventService
from keyboards import VKKeyboards
from kudago_api import KudaGoAPI, KudaGoAPIError

logger = logging.getLogger(__name__)

# Словари состояния пользователей: user_id -> state_data
user_states: dict[int, dict[str, Any]] = {}

# Словарь городов: код -> название
CITIES = {
    "msk": "Москва",
    "spb": "Санкт-Петербург",
    "nsk": "Новосибирск",
    "ekb": "Екатеринбург",
    "kzn": "Казань",
    "sochi": "Сочи",
    "ufa": "Уфа",
    "krasnoyarsk": "Красноярск",
    "krd": "Краснодар",
    "nnv": "Нижний Новгород",
    "new-york": "Нью-Йорк",
}

# Команды для запуска бота
START_COMMANDS = ("начать", "привет", "меню")


class VKBot:
    """VK LongPoll бот."""

    def __init__(self, token: str):
        self.vk_session = vk_api.VkApi(token=token)
        self.longpoll = VkLongPoll(self.vk_session)
        self.api = self.vk_session.get_api()
        self.service = EventService(KudaGoAPI())
        self.keyboards = VKKeyboards()

    # ------------------------------------------------------------------
    # Обработка сообщений
    # ------------------------------------------------------------------

    def run(self):
        """Запуск бота."""
        logger.info("Бот запущен...")

        for event in self.longpoll.listen():
            if not event.type == VkEventType.MESSAGE_NEW:
                continue
            if not event.to_me:
                continue

            try:
                self._handle_message(event)
            except Exception:
                logger.exception("Необработанная ошибка в боте")
                self._send_error(event.chat_id)

    def _handle_message(self, event):
        """Обработать входящее сообщение."""
        user_id = event.user_id
        chat_id = event.chat_id
        text = event.text.strip().lower() if event.text else ""

        # Состояние пользователя
        state = user_states.setdefault(user_id, {"city": settings.DEFAULT_CITY})

        # Обработка кнопок через payload
        if event.payload:
            self._handle_button(event, user_id, chat_id, state)
            return

        # Обработка текстовых команд
        if text in START_COMMANDS:
            self._send_start(chat_id)
            return

        # Обработка по состоянию
        if state.get("waiting_for"):
            self._handle_state_command(
                event, chat_id, state, text
            )
            return

        # Обработка текстовых команд
        if text == "🏙 выбрать город":
            self._send_city_selection(chat_id)
        elif text == "📅 выбрать дату":
            self._send_date_selection(chat_id)
        elif text == "🎭 выбрать событие":
            self._send_category_selection(chat_id)
        elif text == "🔎 найти мероприятия":
            self._search_events(chat_id, state)
        elif text == "← назад в меню" or text == "← назад":
            self._send_main_menu(chat_id)
        else:
            self._send_main_menu(chat_id)

    # ------------------------------------------------------------------
    # Обработка кнопок
    # ------------------------------------------------------------------

    def _handle_button(
        self, event, user_id: int, chat_id: int, state: dict
    ):
        """Обработать нажатие кнопки через payload."""
        try:
            payload = json.loads(event.payload)
        except (json.JSONDecodeError, TypeError):
            return

        action = payload.get("action", "")

        if action == "main_menu":
            self._send_main_menu(chat_id)
            user_states.pop(user_id, None)

        elif action == "event_details":
            event_id = payload.get("event_id")
            if event_id:
                self._show_event_details(chat_id, event_id)

        elif action == "event_program":
            event_id = payload.get("event_id")
            if event_id:
                self._show_event_program(chat_id, event_id)

        elif action == "other_events":
            event_id = payload.get("event_id")
            if event_id:
                self._show_other_events(chat_id, event_id, state)

        elif action == "next_page":
            page = payload.get("page", 1)
            self._search_events(chat_id, state, page=page)

        elif action.startswith("city_"):
            city_code = action.replace("city_", "")
            city_name = CITIES.get(city_code, city_code)
            state["city"] = city_code
            self._send_message(
                chat_id, f"Город: {city_name}. Выберите действие."
            )
            self._send_main_menu(chat_id)

        elif action.startswith("date_"):
            date_str = action.replace("date_", "")
            try:
                date = datetime.strptime(date_str, "%d.%m")
                state["date"] = date
                self._send_message(
                    chat_id, f"Дата: {date.strftime('%d.%m.%Y')}. "
                             "Выберите категорию."
                )
                self._send_category_selection(chat_id)
            except ValueError:
                self._send_error(chat_id)

        elif action.startswith("category_"):
            category_code = action.replace("category_", "")
            self._search_events(chat_id, state, categories=[category_code])

    # ------------------------------------------------------------------
    # Обработка команд по состоянию
    # ------------------------------------------------------------------

    def _handle_state_command(
        self, event, chat_id: int, state: dict, text: str
    ):
        """Обработать команду, ожидающую ввод пользователя."""
        waiting = state.get("waiting_for")

        if waiting == "custom_category":
            self._handle_custom_category(chat_id, state, text)

    def _handle_custom_category(
        self, chat_id: int, state: dict, text: str
    ):
        """Обработать пользовательский ввод категории."""
        state.pop("waiting_for", None)

        # Ищем совпадение с CATEGORY_MAP без учёта регистра
        categories = self.service.find_category(text)

        if not categories:
            self._send_message(
                chat_id,
                "Категория не найдена. Выберите категорию из меню.",
            )
            self._send_category_selection(chat_id)
            return

        state["categories"] = categories
        self._search_events(chat_id, state)

    # ------------------------------------------------------------------
    # Основные сценарии
    # ------------------------------------------------------------------

    def _send_start(self, chat_id: int):
        """Отправить стартовое сообщение."""
        self._send_message(
            chat_id,
            "👋 Привет! Я бот для поиска мероприятий.\n\n"
            "Выберите действие из меню или введите команду.",
        )
        self._send_main_menu(chat_id)

    def _send_main_menu(self, chat_id: int):
        """Отправить главное меню."""
        self._send_message(chat_id, "Главное меню:", keyboard=self.keyboards.get_main_keyboard())

    def _send_city_selection(self, chat_id: int):
        """Отправить выбор города."""
        self._send_message(
            chat_id, "Выберите город:",
            keyboard=self.keyboards.get_city_keyboard(CITIES),
        )

    def _send_date_selection(self, chat_id: int):
        """Отправить выбор даты."""
        self._send_message(
            chat_id, "Выберите дату:",
            keyboard=self.keyboards.get_date_keyboard(),
        )

    def _send_category_selection(self, chat_id: int):
        """Отправить выбор категории."""
        self._send_message(
            chat_id, "Выберите категорию:",
            keyboard=self.keyboards.get_category_keyboard(),
        )

    def _search_events(
        self,
        chat_id: int,
        state: dict,
        page: int = 1,
        categories: list[str] = None,
    ):
        """Выполнить поиск и показать мероприятия."""
        city = state.get("city", settings.DEFAULT_CITY)
        date = state.get("date")

        if not date:
            # Если дата не выбрана, берём сегодня
            date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        try:
            result = self.service.search_events(
                city=city,
                date=date,
                categories=categories,
                page=page,
            )
        except EventNotFoundError:
            self._send_message(
                chat_id,
                "Мероприятия не найдены. "
                "Попробуйте изменить параметры поиска.",
            )
            self._send_main_menu(chat_id)
            return
        except KudaGoAPIError as exc:
            logger.error(f"Ошибка API при поиске: {exc}")
            self._send_message(chat_id, "Ошибка при поиске. Попробуйте позже.")
            return

        # Показываем первые 5 мероприятий с клавиатурой
        for event in result["results"][:5]:
            text = self.service.get_event_preview_text(event)
            self._send_message(chat_id, text)

            # Клавиатура для каждого мероприятия
            event_keyboard = self.keyboards.get_event_actions_keyboard(event.event_id)
            self._send_message(chat_id, "", keyboard=event_keyboard)

        # Пагинация
        has_next = result.get("next") is not None
        self._send_message(
            chat_id, "",
            keyboard=self.keyboards.get_pagination_keyboard(page, has_next),
        )

    def _show_event_details(self, chat_id: int, event_id: int):
        """Показать детали мероприятия."""
        try:
            event = self.service.get_event_details(event_id)
        except EventNotFoundError:
            self._send_message(chat_id, "Не удалось загрузить детали.")
            return

        text = (
            f"Мероприятие: {event.title}\n\n"
            f"Расписание: {event.formatted_timetable}\n"
            f"Адрес: {event.address or event.location_name}\n\n"
            f"{event.body_text or event.description}\n\n"
            f"Ссылка: {event.site_url}"
        )
        self._send_message(chat_id, text)

    def _show_event_program(self, chat_id: int, event_id: int):
        """Показать программу мероприятия."""
        try:
            event = self.service.get_event_details(event_id)
        except EventNotFoundError:
            self._send_message(chat_id, "Не удалось загрузить программу.")
            return

        text = f"Программа: {event.title}\n\n"
        if event.body_text:
            text += event.body_text
        else:
            text += "Программа не указана."

        self._send_message(chat_id, text)

    def _show_other_events(
        self, chat_id: int, event_id: int, state: dict
    ):
        """Показать другие события в тот же день."""
        city = state.get("city", settings.DEFAULT_CITY)
        date = state.get("date")

        if not date:
            date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        try:
            result = self.service.get_similar_events(
                city=city, date=date, exclude_id=event_id
            )
        except KudaGoAPIError:
            self._send_message(chat_id, "Ошибка при загрузке событий.")
            return

        if not result["results"]:
            self._send_message(chat_id, "Других событий в этот день не найдено.")
            return

        for event in result["results"][:5]:
            text = self.service.get_event_preview_text(event)
            self._send_message(chat_id, text)

        self._send_main_menu(chat_id)

    # ------------------------------------------------------------------
    # Отправка сообщений
    # ------------------------------------------------------------------

    def _send_message(
        self,
        chat_id: int,
        text: str,
        keyboard: Any = None,
    ):
        """Отправить сообщение через VK API."""
        try:
            self.api.messages.send(
                chat_id=chat_id,
                message=text,
                keyboard=keyboard.get_keyboard() if keyboard else None,
                random_id=random.randint(0, 2147483647),
            )
        except Exception:
            logger.exception(f"Ошибка при отправке сообщения в чат {chat_id}")

    def _send_error(self, chat_id: int):
        """Отправить сообщение об ошибке."""
        self._send_message(
            chat_id,
            "Произошла ошибка. Пожалуйста, попробуйте позже.",
        )