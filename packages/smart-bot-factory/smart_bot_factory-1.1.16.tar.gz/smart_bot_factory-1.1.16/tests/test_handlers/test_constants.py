"""Тесты для констант handlers"""

from smart_bot_factory.handlers.constants import (
    EVENT_EMOJI_MAP,
    FALLBACK_ERROR_MESSAGE,
    MOSCOW_TZ,
    AIMetadataKey,
    HookType,
    MessageRole,
)


class TestConstants:
    """Тесты для констант"""

    def test_message_role_constants(self):
        """Тест констант ролей сообщений"""
        assert MessageRole.SYSTEM == "system"
        assert MessageRole.USER == "user"
        assert MessageRole.ASSISTANT == "assistant"
        assert MessageRole.HUMAN == "human"
        assert MessageRole.AI == "ai"

    def test_hook_type_constants(self):
        """Тест констант типов хуков"""
        assert HookType.VALIDATORS == "validators"
        assert HookType.PROMPT_ENRICHERS == "prompt_enrichers"
        assert HookType.CONTEXT_ENRICHERS == "context_enrichers"
        assert HookType.RESPONSE_PROCESSORS == "response_processors"
        assert HookType.SEND_FILTERS == "send_filters"

    def test_ai_metadata_key_constants(self):
        """Тест констант ключей метаданных AI"""
        assert AIMetadataKey.SERVICE_INFO == "service_info"
        assert AIMetadataKey.USER_MESSAGE == "user_message"
        assert AIMetadataKey.STAGE == "этап"
        assert AIMetadataKey.QUALITY == "качество"
        assert AIMetadataKey.EVENTS == "события"
        assert AIMetadataKey.EVENT_TYPE == "тип"
        assert AIMetadataKey.EVENT_INFO == "инфо"

    def test_fallback_error_message(self):
        """Тест fallback сообщения об ошибке"""
        assert isinstance(FALLBACK_ERROR_MESSAGE, str)
        assert len(FALLBACK_ERROR_MESSAGE) > 0
        assert "ошибка" in FALLBACK_ERROR_MESSAGE.lower()

    def test_event_emoji_map(self):
        """Тест карты эмодзи для событий"""
        assert isinstance(EVENT_EMOJI_MAP, dict)
        assert "телефон" in EVENT_EMOJI_MAP
        assert "email" in EVENT_EMOJI_MAP
        assert "встреча" in EVENT_EMOJI_MAP
        assert EVENT_EMOJI_MAP["телефон"] == "📱"

    def test_moscow_tz(self):
        """Тест временной зоны Москвы"""
        assert MOSCOW_TZ is not None
        assert str(MOSCOW_TZ) == "Europe/Moscow"
