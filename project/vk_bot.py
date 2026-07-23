"""VK LongPoll бот для поиска мероприятий через KudaGo API (VKBottle)."""

import logging
from datetime import datetime, timedelta

from vkbottle import Bot, Keyboard, KeyboardButtonColor, Text
from vkbottle.bot import BotLabeler, Message, rules

from config import settings
from event_service import CATEGORY_MAP, EventNotFoundError, EventService
from kudago_api import KudaGoAPI, KudaGoAPIError

logger = logging.getLogger(__name__)

# Словари состояния пользователей: user_id -> state_data
user_states: dict[int, dict[str, ...]] = {}

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
START_COMMANDS = ["начать", "привет", "меню"]

# Глобальный лейблер
bl = BotLabeler()

# Сервис (инициализируется в create_bot)
service: EventService | None = None


# ======================================================================
# Клавиатуры
# ======================================================================

def get_main_keyboard() -> str:
    """Главное меню бота."""
    kb = Keyboard(one_time=True)

    kb.add(
        Text("🏙 Выбрать город", payload={"action": "city"}),
        color=KeyboardButtonColor.SECONDARY,
    )

    kb.add(
        Text("📅 Выбрать дату", payload={"action": "date"}),
        color=KeyboardButtonColor.SECONDARY,
    )

    kb.row()

    kb.add(
        Text("🎭 Выбрать событие", payload={"action": "category"}),
        color=KeyboardButtonColor.POSITIVE,
    )

    kb.add(
        Text("🔎 Найти мероприятия", payload={"action": "search"}),
        color=KeyboardButtonColor.POSITIVE,
    )

    return kb.get_json()


def get_city_keyboard() -> str:
    """Клавиатура выбора города."""
    kb = Keyboard(one_time=True)

    for index, (code, name) in enumerate(CITIES.items()):
        kb.add(
            Text(
                name,
                payload={"action": f"city_{code}"}
            ),
            color=KeyboardButtonColor.SECONDARY
        )

        if (index + 1) % 4 == 0:
            kb.row()

    kb.row()

    kb.add(
        Text(
            "← Назад",
            payload={"action": "main_menu"}
        ),
        color=KeyboardButtonColor.SECONDARY
    )

    return kb.get_json()


def get_date_keyboard() -> str:
    """Клавиатура выбора даты (ближайшие 7 дней)."""
    kb = Keyboard(one_time=True)

    for i in range(7):
        day = datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        ) + timedelta(days=i)

        label = day.strftime("%d.%m")

        kb.add(
            Text(label, payload={"action": f"date_{label}"}),
            color=KeyboardButtonColor.SECONDARY
        )

        if (i + 1) % 4 == 0:
            kb.row()

    kb.row()

    kb.add(
        Text("← Назад", payload={"action": "main_menu"}),
        color=KeyboardButtonColor.SECONDARY
    )

    return kb.get_json()

def get_category_keyboard() -> str:
    """Клавиатура выбора категории мероприятия."""
    kb = Keyboard(one_time=True)

    buttons = list(CATEGORY_MAP.items())

    for index, (display_name, code) in enumerate(buttons):
        kb.add(
            Text(
                display_name,
                payload={"action": f"category_{code}"}
            ),
            color=KeyboardButtonColor.POSITIVE,
        )

        if (index + 1) % 4 == 0:
            kb.row()

    kb.row()

    kb.add(
        Text("✏ Свой вариант", payload={"action": "custom_category"}),
        color=KeyboardButtonColor.SECONDARY,
    )

    kb.add(
        Text("← Назад", payload={"action": "main_menu"}),
        color=KeyboardButtonColor.SECONDARY,
    )

    return kb.get_json()


def get_event_actions_keyboard(event_id: int) -> str:
    """Клавиатура действий с конкретным мероприятием."""
    kb = Keyboard(one_time=False)
    kb.add(
        Text("Подробнее", payload={"action": "event_details", "event_id": event_id}),
        color=KeyboardButtonColor.POSITIVE,
        )
    kb.add(
        Text("Программа", payload={"action": "event_program", "event_id": event_id}),
        color=KeyboardButtonColor.SECONDARY,
        )
    kb.add(
        Text("Другие мероприятия", payload={"action": "other_events", "event_id": event_id}),
        color=KeyboardButtonColor.SECONDARY,
        )
    kb.add(
        Text("Главное меню", payload={"action": "main_menu"}),
        color=KeyboardButtonColor.SECONDARY,
        )
    return kb.get_json()


def get_pagination_keyboard(page: int, has_next: bool) -> str:
    """Клавиатура пагинации."""
    kb = Keyboard(one_time=False)
    if has_next:
        kb.add(
            Text("➡ Далее", payload={"action": "next_page", "page": page + 1}),
            color=KeyboardButtonColor.POSITIVE,
            )
    kb.add(
        Text("← Назад в меню", payload={"action": "main_menu"}),
        color=KeyboardButtonColor.SECONDARY,
        )
    return kb.get_json()


# ======================================================================
# Вспомогательные функции
# ======================================================================


async def send_message(
    message: Message, text: str, keyboard: str | None = None
):
    """Отправить сообщение через VKBottle."""
    kwargs: dict = {"message": text}
    if keyboard:
        kwargs["keyboard"] = keyboard
    await message.answer(**kwargs)
 

def get_user_state(user_id: int) -> dict:
    """Получить или создать состояние пользователя."""
    return user_states.setdefault(user_id, {"city": settings.DEFAULT_CITY})


# ======================================================================
# Текстовые команды
# ======================================================================


@bl.message(text=START_COMMANDS)
async def start_handler(message: Message):
    """Команды: начать, привет, меню."""
    state = get_user_state(message.from_id)
    state.pop("waiting_for", None)
    state.pop("categories", None)
    await send_message(
        message,
        "Привет! Я бот для поиска мероприятий.\n\n"
        "Выберите действие из меню или введите команду.",
        keyboard=get_main_keyboard(),
    )

@bl.message(text="🏙 Выбрать город")
async def city_selection_handler(message: Message):
    """Выбор города."""
    await send_message(message, "Выберите город:", keyboard=get_city_keyboard())


@bl.message(text="📅 Выбрать дату")
async def date_selection_handler(message: Message):
    """Выбор даты."""
    await send_message(message, "Выберите дату:", keyboard=get_date_keyboard())


@bl.message(text="🎭 Выбрать событие")
async def category_selection_handler(message: Message):
    """Выбор категории."""
    await send_message(
        message, "Выберите категорию:", keyboard=get_category_keyboard()
    )


@bl.message(text="🔎 Найти мероприятия")
async def search_handler(message: Message):
    """Поиск мероприятий."""
    state = get_user_state(message.from_id)
    city = state.get("city", settings.DEFAULT_CITY)
    date = state.get("date")
    if not date:
        date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    try:
        result = service.search_events(city=city, date=date, page=1)
    except EventNotFoundError:
        await send_message(
            message,
            "Мероприятия не найдены. Попробуйте изменить параметры поиска.",
        )
        return
    except KudaGoAPIError as exc:
        logger.error("Ошибка API при поиске: %s", exc)
        await send_message(message, "Ошибка при поиске. Попробуйте позже.")
        return

    await display_events(message, result["results"], state)


@bl.message(text="✏ Свой вариант")
async def custom_category_trigger(message: Message):
    """Запрос пользовательского ввода категории."""
    state = get_user_state(message.from_id)
    state["waiting_for"] = "custom_category"
    await send_message(
        message, "Введите название категории текстом (например: Концерты)"
    )


@bl.message(text="← назад в меню")
@bl.message(text="← назад")
async def back_to_menu_handler(message: Message):
    """Возврат в главное меню."""
    user_states.pop(message.from_id, None)
    await send_message(message, "Главное меню:", keyboard=get_main_keyboard())


# ======================================================================
# Пользовательский ввод категории (через FuncRule)
# ======================================================================


def _waiting_for_custom_category(message: Message) -> bool:
    """Проверить, ожидает ли пользователь ввод категории."""
    state = get_user_state(message.from_id)
    return state.get("waiting_for") == "custom_category"


@bl.message(rules.FuncRule(_waiting_for_custom_category))
async def custom_category_input_handler(message: Message):
    """Обработка пользовательского ввода категории."""
    state = get_user_state(message.from_id)
    state.pop("waiting_for", None)
    text = message.text.strip()

    categories = service.find_category(text)
    if not categories:
        await send_message(
            message,
            "Категория не найдена. Выберите категорию из меню.",
        )
        await send_message(message, keyboard=get_category_keyboard())
        return

    state["categories"] = categories
    city = state.get("city", settings.DEFAULT_CITY)
    date = state.get("date")
    if not date:
        date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    try:
        result = service.search_events(
            city=city, date=date, categories=categories, page=1
        )
    except EventNotFoundError:
        await send_message(
            message,
            "Мероприятия не найдены. Попробуйте изменить параметры поиска.",
        )
        return
    except KudaGoAPIError:
        await send_message(message, "Ошибка при поиске. Попробуйте позже.")
        return

    await display_events(message, result["results"], state)


# ======================================================================
# Обработчики кнопок (payload)
# ======================================================================


@bl.message(payload={"action": "main_menu"})
async def payload_main_menu(message: Message):
    """Главное меню."""
    user_states.pop(message.from_id, None)
    await send_message(message, "Главное меню:", keyboard=get_main_keyboard())


@bl.message(payload={"action": "event_details"})
async def payload_event_details(message: Message):
    """Детали мероприятия."""
    event_id = message.payload.get("event_id")
    if not event_id:
        return
    try:
        event = service.get_event_details(event_id)
    except EventNotFoundError:
        await send_message(message, "Не удалось загрузить детали.")
        return

    text = (
        f"Мероприятие: {event.title}\n\n"
        f"Расписание: {event.formatted_timetable}\n"
        f"Адрес: {event.address or event.location_name}\n\n"
        f"{event.body_text or event.description}\n\n"
        f"Ссылка: {event.site_url}"
    )
    await send_message(message, text)


@bl.message(payload={"action": "event_program"})
async def payload_event_program(message: Message):
    """Программа мероприятия."""
    event_id = message.payload.get("event_id")
    if not event_id:
        return
    try:
        event = service.get_event_details(event_id)
    except EventNotFoundError:
        await send_message(message, "Не удалось загрузить программу.")
        return

    text = f"Программа: {event.title}\n\n"
    if event.body_text:
        text += event.body_text
    else:
        text += "Программа не указана."
    await send_message(message, text)


@bl.message(payload={"action": "other_events"})
async def payload_other_events(message: Message):
    """Другие мероприятия."""
    state = get_user_state(message.from_id)
    event_id = message.payload.get("event_id")
    if not event_id:
        return

    city = state.get("city", settings.DEFAULT_CITY)
    date = state.get("date")
    if not date:
        date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    try:
        result = service.get_similar_events(
            city=city, date=date, exclude_id=event_id, page=1
        )
    except KudaGoAPIError:
        await send_message(message, "Ошибка при загрузке событий.")
        return

    if not result["results"]:
        await send_message(message, "Других событий в этот день не найдено.")
        return

    await display_events(message, result["results"][:5], state)
    await send_message(message, "", keyboard=get_main_keyboard())


@bl.message(payload={"action": "next_page"})
async def payload_next_page(message: Message):
    """Следующая страница."""
    state = get_user_state(message.from_id)
    page = message.payload.get("page", 1)
    city = state.get("city", settings.DEFAULT_CITY)
    date = state.get("date")
    if not date:
        date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    try:
        result = service.search_events(city=city, date=date, page=page)
    except EventNotFoundError:
        await send_message(
            message,
            "Мероприятия не найдены. Попробуйте изменить параметры поиска.",
        )
        return
    except KudaGoAPIError:
        await send_message(message, "Ошибка при поиске. Попробуйте позже.")
        return

    await display_events(message, result["results"], state)
    has_next = result.get("next") is not None
    await send_message(
        message, "", keyboard=get_pagination_keyboard(page, has_next)
    )


# Единый обработчик для city_, date_, category_ префиксов
def _payload_city_rule(message: Message) -> bool:
    payload = message.payload
    return isinstance(payload, dict) and payload.get("action", "").startswith("city_")


def _payload_date_rule(message: Message) -> bool:
    payload = message.payload
    return isinstance(payload, dict) and payload.get("action", "").startswith("date_")


def _payload_category_rule(message: Message) -> bool:
    payload = message.payload
    return isinstance(payload, dict) and payload.get("action", "").startswith("category_")


@bl.message(rules.FuncRule(_payload_city_rule))
# async def payload_city(message: Message):
async def payload_city(message: Message):
    print("CITY PAYLOAD:", message.payload)
    """Выбор города."""
    action = message.payload.get("action", "")
    city_code = action.replace("city_", "")
    city_name = CITIES.get(city_code, city_code)
    state = get_user_state(message.from_id)
    state["city"] = city_code
    await send_message(
        message,
        f"Город: {city_name}. Выберите действие.",
        keyboard=get_main_keyboard(),
    )


@bl.message(rules.FuncRule(_payload_date_rule))
async def payload_date(message: Message):
    """Выбор даты."""
    action = message.payload.get("action", "")
    date_str = action.replace("date_", "")
    try:
        date = datetime.strptime(date_str, "%d.%m")
        state = get_user_state(message.from_id)
        state["date"] = date
        await send_message(
            message,
            f"Дата: {date.strftime('%d.%m.%Y')}. Выберите категорию.",
            keyboard=get_category_keyboard(),
        )
    except ValueError:
        await send_message(message, "Произошла ошибка. Попробуйте позже.")


@bl.message(rules.FuncRule(_payload_category_rule))
async def payload_category(message: Message):
    """Выбор категории."""
    action = message.payload.get("action", "")
    category_code = action.replace("category_", "")
    state = get_user_state(message.from_id)
    state["categories"] = [category_code]
    city = state.get("city", settings.DEFAULT_CITY)
    date = state.get("date")
    if not date:
        date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    try:
        result = service.search_events(
            city=city, date=date, categories=[category_code], page=1
        )
    except EventNotFoundError:
        await send_message(
            message,
            "Мероприятия не найдены. Попробуйте изменить параметры поиска.",
        )
        return
    except KudaGoAPIError:
        await send_message(message, "Ошибка при поиске. Попробуйте позже.")
        return

    await display_events(message, result["results"], state)


# ======================================================================
# Отображение мероприятий
# ======================================================================


async def display_events(message: Message, events, state: dict):
    """Отобразить список мероприятий с кнопками."""
    for event in events[:5]:
        text = service.get_event_preview_text(event)
        await send_message(
            message, text, keyboard=get_event_actions_keyboard(event.event_id)
        )


# ======================================================================
# Инициализация бота
# ======================================================================


def create_bot() -> Bot:
    """Создать и настроить бота VKBottle."""
    global service

    bot = Bot(token=settings.VK_TOKEN)
    service = EventService(KudaGoAPI())
    bot.labeler.load(bl)
    return bot


def main():
    """Запуск бота."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    if not settings.VK_TOKEN:
        logger.error("Не задан VK_TOKEN в .env")
        return

    bot = create_bot()
    logger.info("Бот запущен...")
    bot.run()


if __name__ == "__main__":
    main()
