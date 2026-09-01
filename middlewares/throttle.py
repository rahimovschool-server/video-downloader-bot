import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

logger = logging.getLogger(__name__)

# Chat_id → oxirgi so'rov vaqti
_throttle_data: dict[int, float] = {}


class ThrottleMiddleware(BaseMiddleware):
    """
    Anti-spam middleware.
    Bir foydalanuvchi `rate` sekunddan tez xabar yubora olmaydi.
    """

    def __init__(self, rate: float = 5.0):
        self.rate = rate
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        import time

        if isinstance(event, Message):
            user_id = event.from_user.id if event.from_user else None
            if user_id:
                last_time = _throttle_data.get(user_id, 0)
                now = time.time()
                diff = now - last_time

                if diff < self.rate:
                    remaining = round(self.rate - diff, 1)
                    await event.answer(
                        f"⏳ Iltimos, <b>{remaining}</b> soniya kuting!\n"
                        f"Spam himoyasi ishlamoqda.",
                        parse_mode="HTML"
                    )
                    return

                _throttle_data[user_id] = now

        return await handler(event, data)
