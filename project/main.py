"""Точка входа в приложение."""

import logging

from vk_bot import VKBot
from config import settings


def setup_logging():
    """Настроить логирование."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def main():
    """Запуск бота."""
    setup_logging()

    if not settings.VK_TOKEN:
        logging.error("Не задан VK_TOKEN в .env")
        return

    bot = VKBot(token=settings.VK_TOKEN)
    bot.run()


if __name__ == "__main__":
    main()