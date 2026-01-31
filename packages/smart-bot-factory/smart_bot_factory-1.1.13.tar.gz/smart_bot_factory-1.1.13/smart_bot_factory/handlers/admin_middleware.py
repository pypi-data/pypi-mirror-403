from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from ..utils.context import ctx


class AdminMiddleware(BaseMiddleware):
    """Middleware для обновления информации об админах"""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """Обработка middleware"""
        if isinstance(event, Message) and ctx.admin_manager and event.from_user:
            if ctx.admin_manager.is_admin(event.from_user.id):
                await ctx.admin_manager.update_admin_info(event.from_user)

        return await handler(event, data)
