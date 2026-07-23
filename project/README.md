# OpenRelaxAPP

VK-бот для поиска мероприятий через API сервиса KudaGo.

## Возможности

- Выбор города
- Выбор даты мероприятия
- Выбор категории:
  - Концерты
  - Выставки
  - Кино
  - Фестивали
  - Лекции
- Поиск мероприятий через KudaGo API
- Вывод списка найденных событий

## Технологии

- Python 3.12
- VKBottle
- KudaGo API
- python-dotenv

## Установка

Клонировать репозиторий:

```bash
git clone https://github.com/Denis-Zagrebnev/OpenRelaxAPP.git

## Перейти в папку проекта:

cd OpenRelaxAPP

## Создать виртуальное окружение:

python -m venv venv

## Активировать окружение:

Windows:

venv\Scripts\activate

## Установить зависимости:

pip install -r requirements.txt

## Настройка

Создать файл .env:

VK_TOKEN=ваш_токен_сообщества_VK
DEFAULT_CITY=msk

## Запуск

python main.py

## Структура проекта

project/
│
├── main.py              # запуск бота
├── vk_bot.py            # логика VKBottle бота
├── kudago_api.py        # работа с API KudaGo
├── event_service.py     # бизнес-логика поиска
├── models.py            # модели данных
├── config.py            # настройки
├── requirements.txt     # зависимости
└── .env                 # переменные окружения

## Работа бота

Пользователь запускает бота.
Выбирает город.
Выбирает дату.
Выбирает категорию мероприятия.
Бот получает данные из KudaGo API и выводит найденные события.

## Автор

Denis Zagrebnev