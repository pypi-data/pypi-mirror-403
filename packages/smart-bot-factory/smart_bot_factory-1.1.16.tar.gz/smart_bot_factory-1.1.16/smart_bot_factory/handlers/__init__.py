"""
Модуль обработчиков сообщений для Telegram бота.
"""

from .constants import (
    EVENT_EMOJI_MAP,
    FALLBACK_ERROR_MESSAGE,
    MOSCOW_TZ,
    AIMetadataKey,
    HookType,
    MessageRole,
)
from .converters import MessageConverter
from .handlers import (
    process_user_message,
    router,
)
from .utils import (
    send_message_in_parts,
)

__all__ = [
    # Константы
    "AIMetadataKey",
    "EVENT_EMOJI_MAP",
    "FALLBACK_ERROR_MESSAGE",
    "HookType",
    "MessageRole",
    "MOSCOW_TZ",
    # Классы
    "HandlerContext",
    "MessageConverter",
    # Утилиты
    "send_message_in_parts",
    # Основные функции
    "process_user_message",
    "router",
]
