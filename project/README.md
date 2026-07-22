# VK Bot — Поиск мероприятий через KudaGo API

Python-бот для VK, который ищет мероприятия в Москве и других городах через публичное API [KudaGo](https://kudago.com/api/).

## Возможности

- 🔍 Поиск мероприятий по городу, дате и категории
- 📋 Детальная информация о каждом мероприятии
- 🎵 Категории: концерты, выставки, кино, фестивали, лекции
- ✏ Пользовательский ввод категории с автопоиском
- 📄 Пагинация результатов
- 🗂 Клавиатурное меню

## Структура проекта

```
project/
├── main.py           # Точка входа
├── config.py         # Настройки (.env)
├── vk_bot.py         # VK LongPoll обработчик
├── kudago_api.py     # KudaGo API клиент
├── event_service.py  # Бизнес-логика
├── keyboards.py      # VK-клавиатуры
├── models.py         # Модели данных
├── utils.py          # Утилиты
├── .env              # Переменные окружения
├── requirements.txt  # Зависимости
└── README.md
```

## Установка

```bash
# Перейти в директорию проекта
cd project

# Создать виртуальное окружение
python -m venv venv

# Активировать
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Установить зависимости
pip install -r requirements.txt
```

## Настройка

1. Скопируйте `.env` и заполните токен:

```bash
cp .env .env.local
```

2. Получите токен в [VK Developer Portal](https://group.dev.vk.com/):
   - Создайте сообщество
   - Настройте бота
   - Получите токен с правами `messages`, `long_poll`

3. Отредактируйте `.env`:
```
VK_TOKEN=your_vk_token_here
```

## Запуск

```bash
python main.py
```

## Использование

1. Напишите боту в личные сообщения
2. Введите `/start` или выберите действие из меню
3. Выберите город, дату и категорию
4. Получите список мероприятий

## Зависимости

- **Python 3.12+**
- **vk-api** — работа с VK API (LongPoll)
- **requests** — HTTP-запросы к KudaGo
- **python-dotenv** — загрузка переменных окружения

## Лицензия

MIT