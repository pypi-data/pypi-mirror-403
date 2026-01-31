"""
Константы для обработчиков сообщений.
"""

import pytz

# Временная зона
MOSCOW_TZ = pytz.timezone("Europe/Moscow")


# Роли сообщений
class MessageRole:
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    HUMAN = "human"
    AI = "ai"


# Типы хуков для обработки сообщений
class HookType:
    VALIDATORS = "validators"
    PROMPT_ENRICHERS = "prompt_enrichers"
    CONTEXT_ENRICHERS = "context_enrichers"
    RESPONSE_PROCESSORS = "response_processors"
    SEND_FILTERS = "send_filters"


# Ключи метаданных AI ответа
class AIMetadataKey:
    SERVICE_INFO = "service_info"
    USER_MESSAGE = "user_message"
    STAGE = "этап"
    QUALITY = "качество"
    EVENTS = "события"
    EVENT_TYPE = "тип"
    EVENT_INFO = "инфо"


# Fallback сообщения
FALLBACK_ERROR_MESSAGE = "Извините, произошла техническая ошибка. " "Попробуйте переформулировать вопрос или напишите /start для перезапуска."

# Эмодзи для типов событий
EVENT_EMOJI_MAP = {
    "телефон": "📱",
    "email": "📧",
    "встреча": "📅",
    "заказ": "🛍️",
    "вопрос": "❓",
    "консультация": "💬",
    "жалоба": "⚠️",
    "отзыв": "💭",
}
