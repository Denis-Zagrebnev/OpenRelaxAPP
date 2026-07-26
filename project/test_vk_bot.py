"""Focused regression tests for the VK greeting and menu payloads."""

import asyncio
import json
import unittest

import vk_bot


class FakeMessage:
    from_id = 123
    peer_id = 123
    text = "привет"
    payload = None

    def __init__(self):
        self.answers = []
        self.api_sends = []
        self.ctx_api = self
        self.messages = self

    async def answer(self, **kwargs):
        self.answers.append(kwargs)

    async def send(self, **kwargs):
        self.api_sends.append(kwargs)
        return 456


class VkBotMenuTests(unittest.TestCase):
    def test_main_keyboard_contains_intended_russian_labels(self):
        keyboard = json.loads(vk_bot.get_main_keyboard())
        labels = [
            button["action"]["label"]
            for row in keyboard["buttons"]
            for button in row
        ]

        self.assertFalse(keyboard["one_time"])
        self.assertEqual(
            labels,
            [
                "🏙 Выбрать город",
                "📅 Выбрать дату",
                "🎭 Выбрать событие",
                "🔎 Найти мероприятия",
            ],
        )

    def test_greeting_is_sent_with_main_keyboard(self):
        message = FakeMessage()

        asyncio.run(vk_bot.start_handler(message))

        self.assertEqual(message.answers, [])
        self.assertEqual(len(message.api_sends), 1)
        self.assertEqual(message.api_sends[0]["peer_id"], message.peer_id)
        self.assertTrue(message.api_sends[0]["message"].startswith("Привет!"))
        self.assertEqual(
            json.loads(message.api_sends[0]["keyboard"]),
            json.loads(vk_bot.get_main_keyboard()),
        )

    def test_payload_normalization_accepts_dict_and_json(self):
        message = FakeMessage()
        message.payload = {"action": "city_msk"}
        self.assertEqual(vk_bot._get_payload(message), {"action": "city_msk"})

        message.payload = '{"action": "date_26.07"}'
        self.assertEqual(vk_bot._get_payload(message), {"action": "date_26.07"})

        message.payload = "not-json"
        self.assertEqual(vk_bot._get_payload(message), {})


if __name__ == "__main__":
    unittest.main()
