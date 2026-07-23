"""Точка входа в приложение."""

import logging

from vk_bot import main


def setup_logging():
    """Настроить логирование."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


if __name__ == "__main__":
    setup_logging()
    main()