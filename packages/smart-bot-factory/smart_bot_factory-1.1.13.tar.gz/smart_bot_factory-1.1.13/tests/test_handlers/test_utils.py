"""Тесты для утилит handlers"""

from unittest.mock import Mock, patch

import pytest

from smart_bot_factory.handlers.utils import (
    apply_send_filters,
    fix_html_markup,
    get_parse_mode_and_fix_html,
    prepare_final_response,
)


class TestFixHTMLMarkup:
    """Тесты для функции fix_html_markup"""

    def test_fix_html_markup_empty(self):
        """Тест исправления пустого текста"""
        assert fix_html_markup("") == ""
        assert fix_html_markup(None) is None

    def test_fix_html_markup_valid_tags(self):
        """Тест что валидные теги не экранируются"""
        text = "<b>bold</b> <i>italic</i> <code>code</code>"
        result = fix_html_markup(text)
        assert "<b>" in result
        assert "</b>" in result
        assert "<i>" in result
        assert "<code>" in result

    def test_fix_html_markup_invalid_tags(self):
        """Тест что невалидные теги экранируются"""
        text = "<invalid>test</invalid> <script>alert('xss')</script>"
        result = fix_html_markup(text)
        assert "&lt;invalid&gt;" in result
        assert "&lt;script&gt;" in result

    def test_fix_html_markup_mixed(self):
        """Тест смешанных валидных и невалидных тегов"""
        text = "<b>bold</b> <invalid>test</invalid> <i>italic</i>"
        result = fix_html_markup(text)
        assert "<b>" in result
        assert "<i>" in result
        assert "&lt;invalid&gt;" in result

    def test_fix_html_markup_link_tag(self):
        """Тест обработки тега ссылки"""
        text = '<a href="https://example.com">link</a>'
        result = fix_html_markup(text)
        assert '<a href="https://example.com">' in result
        assert "</a>" in result

    def test_fix_html_markup_pre_tag(self):
        """Тест обработки тега pre"""
        text = "<pre>code block</pre>"
        result = fix_html_markup(text)
        assert "<pre>" in result
        assert "</pre>" in result


class TestPrepareFinalResponse:
    """Тесты для функции prepare_final_response"""

    def test_prepare_final_response_debug_mode(self):
        """Тест подготовки ответа в режиме отладки"""
        response_text = "User message"
        ai_response = '{"user_message": "User message", "service_info": {}}'

        result = prepare_final_response(response_text, ai_response, debug_mode=True)

        assert result == ai_response

    def test_prepare_final_response_normal_mode(self):
        """Тест подготовки ответа в обычном режиме"""
        response_text = "User message"
        ai_response = '{"user_message": "User message", "service_info": {}}'

        result = prepare_final_response(response_text, ai_response, debug_mode=False)

        assert result == response_text

    def test_prepare_final_response_empty(self):
        """Тест обработки пустого ответа"""
        result = prepare_final_response("", "", debug_mode=False)

        assert len(result) > 0
        assert "ошибка" in result.lower() or "error" in result.lower()


class TestGetParseModeAndFixHTML:
    """Тесты для функции get_parse_mode_and_fix_html"""

    @pytest.fixture
    def mock_config(self):
        """Фикстура для мок конфига"""
        config = Mock()
        config.MESSAGE_PARSE_MODE = "HTML"
        return config

    @pytest.fixture
    def setup_context(self, mock_config):
        """Фикстура для настройки контекста"""
        with patch("smart_bot_factory.handlers.utils.ctx") as mock_ctx:
            mock_ctx.config = mock_config
            yield mock_ctx

    def test_get_parse_mode_html(self, setup_context):
        """Тест получения parse_mode для HTML"""
        text = "<b>test</b>"
        parse_mode, fixed_text = get_parse_mode_and_fix_html(text)

        assert parse_mode == "HTML"
        assert "<b>" in fixed_text

    def test_get_parse_mode_markdown(self, setup_context):
        """Тест получения parse_mode для Markdown"""
        setup_context.config.MESSAGE_PARSE_MODE = "Markdown"
        text = "**test**"
        parse_mode, fixed_text = get_parse_mode_and_fix_html(text)

        assert parse_mode == "Markdown"
        assert fixed_text == text


class TestApplySendFilters:
    """Тесты для функции apply_send_filters"""

    @pytest.fixture
    def setup_context(self):
        """Фикстура для настройки контекста"""
        with patch("smart_bot_factory.handlers.utils.ctx") as mock_ctx:
            mock_ctx.message_hooks = {}
            yield mock_ctx

    @pytest.mark.asyncio
    async def test_apply_send_filters_no_filters(self, setup_context):
        """Тест применения фильтров когда их нет"""
        result = await apply_send_filters(123456789)
        assert result is False

    @pytest.mark.asyncio
    async def test_apply_send_filters_blocked(self, setup_context):
        """Тест блокировки отправки фильтром"""

        async def blocking_filter(user_id):
            return True

        setup_context.message_hooks = {"send_filters": [blocking_filter]}

        result = await apply_send_filters(123456789)
        assert result is True

    @pytest.mark.asyncio
    async def test_apply_send_filters_allowed(self, setup_context):
        """Тест разрешения отправки фильтром"""

        async def allowing_filter(user_id):
            return False

        setup_context.message_hooks = {"send_filters": [allowing_filter]}

        result = await apply_send_filters(123456789)
        assert result is False

    @pytest.mark.asyncio
    async def test_apply_send_filters_multiple(self, setup_context):
        """Тест применения нескольких фильтров"""

        async def filter1(user_id):
            return False

        async def filter2(user_id):
            return True  # Блокирующий фильтр

        setup_context.message_hooks = {"send_filters": [filter1, filter2]}

        result = await apply_send_filters(123456789)
        assert result is True  # Должен заблокировать из-за filter2
