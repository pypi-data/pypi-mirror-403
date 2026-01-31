"""Расширенные тесты для handlers.utils - непокрытые функции"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from smart_bot_factory.handlers.utils import (
    apply_send_filters,
    fix_html_markup,
    get_parse_mode_and_fix_html,
    prepare_final_response,
    send_critical_error_message,
    send_message_in_parts,
)


class TestFixHtmlMarkup:
    """Тесты для fix_html_markup"""

    def test_fix_html_markup_empty(self):
        """Тест fix_html_markup для пустой строки (строки 17-70)"""
        result = fix_html_markup("")
        assert result == ""

    def test_fix_html_markup_none(self):
        """Тест fix_html_markup для None"""
        result = fix_html_markup(None)
        assert result is None

    def test_fix_html_markup_valid_tags(self):
        """Тест fix_html_markup с валидными тегами"""
        text = "<b>Bold</b> <i>Italic</i> <code>Code</code>"
        result = fix_html_markup(text)

        # Валидные теги должны остаться
        assert "<b>" in result
        assert "</b>" in result
        assert "<i>" in result
        assert "<code>" in result

    def test_fix_html_markup_invalid_tags(self):
        """Тест fix_html_markup с невалидными тегами"""
        text = "<invalid>Test</invalid> <div>Content</div>"
        result = fix_html_markup(text)

        # Невалидные теги должны быть экранированы
        assert "&lt;invalid&gt;" in result
        assert "&lt;div&gt;" in result

    def test_fix_html_markup_link_tag(self):
        """Тест fix_html_markup с тегом ссылки (строки 38-40)"""
        text = '<a href="https://example.com">Link</a>'
        result = fix_html_markup(text)

        # Тег ссылки должен остаться
        assert '<a href="https://example.com">' in result
        assert "</a>" in result

    def test_fix_html_markup_mixed(self):
        """Тест fix_html_markup со смешанными тегами"""
        text = "<b>Bold</b> <invalid>Invalid</invalid> <i>Italic</i>"
        result = fix_html_markup(text)

        assert "<b>" in result
        assert "&lt;invalid&gt;" in result
        assert "<i>" in result


class TestSendMessageInParts:
    """Тесты для send_message_in_parts"""

    @pytest.mark.asyncio
    async def test_send_message_in_parts_short(self, mock_message):
        """Тест send_message_in_parts для короткого сообщения (строки 73-177)"""
        text = "Short message"

        with patch("smart_bot_factory.handlers.utils.send_message") as mock_send:
            result = await send_message_in_parts(mock_message, text)

            assert result == 1
            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_message_in_parts_empty(self, mock_message):
        """Тест send_message_in_parts для пустого сообщения (строки 94-96)"""
        with patch("smart_bot_factory.handlers.utils.send_message"):
            result = await send_message_in_parts(mock_message, "")

            assert result == 0

    @pytest.mark.asyncio
    async def test_send_message_in_parts_long(self, mock_message):
        """Тест send_message_in_parts для длинного сообщения (строки 109-169)"""
        # Создаем длинное сообщение
        long_text = "\n".join([f"Line {i}" for i in range(1000)])

        with patch("smart_bot_factory.handlers.utils.send_message") as mock_send:
            result = await send_message_in_parts(mock_message, long_text, max_length=100)

            assert result > 1
            assert mock_send.call_count == result

    @pytest.mark.asyncio
    async def test_send_message_in_parts_with_files(self, mock_message):
        """Тест send_message_in_parts с файлами (строки 156-163)"""
        text = "Test message"
        files_list = ["file1.pdf"]

        with patch("smart_bot_factory.handlers.utils.send_message") as mock_send:
            await send_message_in_parts(mock_message, text, files_list=files_list)

            # Проверяем что файлы переданы в первый вызов
            call_args = mock_send.call_args
            assert call_args[1]["files_list"] == files_list

    @pytest.mark.asyncio
    async def test_send_message_in_parts_exception(self, mock_message):
        """Тест обработки исключения в send_message_in_parts (строки 170-177)"""
        text = "Test message"

        with patch("smart_bot_factory.handlers.utils.send_message", side_effect=Exception("Error")):
            with pytest.raises(Exception):
                await send_message_in_parts(mock_message, text)

    @pytest.mark.asyncio
    async def test_send_message_in_parts_long_line(self, mock_message):
        """Тест send_message_in_parts с очень длинной строкой (строки 131-145)"""
        # Создаем очень длинную строку без переносов
        long_line = " ".join(["word"] * 1000)

        with patch("smart_bot_factory.handlers.utils.send_message") as mock_send:
            result = await send_message_in_parts(mock_message, long_line, max_length=100)

            assert result > 1
            assert mock_send.call_count == result


class TestPrepareFinalResponse:
    """Тесты для prepare_final_response"""

    def test_prepare_final_response_debug_mode(self):
        """Тест prepare_final_response в режиме отладки (строки 180-206)"""
        response_text = "Clean text"
        ai_response = '{"text": "Clean text", "metadata": {}}'

        result = prepare_final_response(response_text, ai_response, debug_mode=True)

        assert result == ai_response

    def test_prepare_final_response_normal_mode(self):
        """Тест prepare_final_response в обычном режиме"""
        response_text = "Clean text"
        ai_response = '{"text": "Clean text", "metadata": {}}'

        result = prepare_final_response(response_text, ai_response, debug_mode=False)

        assert result == response_text

    def test_prepare_final_response_empty(self):
        """Тест prepare_final_response для пустого ответа (строки 202-204)"""
        result = prepare_final_response("", "", debug_mode=False)

        assert "ошибка" in result.lower() or "error" in result.lower()


class TestGetParseModeAndFixHtml:
    """Тесты для get_parse_mode_and_fix_html"""

    def test_get_parse_mode_and_fix_html_html_mode(self):
        """Тест get_parse_mode_and_fix_html для HTML режима (строки 209-225)"""
        with patch("smart_bot_factory.handlers.utils.ctx") as mock_ctx:
            mock_ctx.config = Mock()
            mock_ctx.config.MESSAGE_PARSE_MODE = "HTML"

            parse_mode, fixed = get_parse_mode_and_fix_html("<invalid>Test</invalid>")

            assert parse_mode == "HTML"
            assert "&lt;invalid&gt;" in fixed

    def test_get_parse_mode_and_fix_html_markdown_mode(self):
        """Тест get_parse_mode_and_fix_html для Markdown режима"""
        with patch("smart_bot_factory.handlers.utils.ctx") as mock_ctx:
            mock_ctx.config = Mock()
            mock_ctx.config.MESSAGE_PARSE_MODE = "Markdown"

            parse_mode, fixed = get_parse_mode_and_fix_html("Test text")

            assert parse_mode == "Markdown"
            assert fixed == "Test text"


class TestSendCriticalErrorMessage:
    """Тесты для send_critical_error_message"""

    @pytest.mark.asyncio
    async def test_send_critical_error_message_success(self, mock_message):
        """Тест send_critical_error_message успешно (строки 228-238)"""
        await send_critical_error_message(mock_message)

        mock_message.answer.assert_called_once()
        assert "ошибка" in mock_message.answer.call_args[0][0].lower() or "error" in mock_message.answer.call_args[0][0].lower()

    @pytest.mark.asyncio
    async def test_send_critical_error_message_exception(self, mock_message):
        """Тест обработки исключения в send_critical_error_message (строки 237-238)"""
        mock_message.answer = AsyncMock(side_effect=Exception("Error"))

        # Не должно упасть
        await send_critical_error_message(mock_message)


class TestApplySendFilters:
    """Тесты для apply_send_filters"""

    @pytest.mark.asyncio
    async def test_apply_send_filters_no_filters(self):
        """Тест apply_send_filters без фильтров (строки 241-260)"""
        with patch("smart_bot_factory.handlers.utils.ctx") as mock_ctx:
            mock_ctx.message_hooks = {}

            result = await apply_send_filters(123456)

            assert result is False

    @pytest.mark.asyncio
    async def test_apply_send_filters_blocked(self):
        """Тест apply_send_filters когда фильтр блокирует"""
        from smart_bot_factory.handlers.constants import HookType

        async def blocking_filter(user_id):
            return True

        with patch("smart_bot_factory.handlers.utils.ctx") as mock_ctx:
            mock_ctx.message_hooks = {HookType.SEND_FILTERS: [blocking_filter]}

            result = await apply_send_filters(123456)

            assert result is True

    @pytest.mark.asyncio
    async def test_apply_send_filters_not_blocked(self):
        """Тест apply_send_filters когда фильтр не блокирует"""
        from smart_bot_factory.handlers.constants import HookType

        async def non_blocking_filter(user_id):
            return False

        with patch("smart_bot_factory.handlers.utils.ctx") as mock_ctx:
            mock_ctx.message_hooks = {HookType.SEND_FILTERS: [non_blocking_filter]}

            result = await apply_send_filters(123456)

            assert result is False

    @pytest.mark.asyncio
    async def test_apply_send_filters_exception(self):
        """Тест обработки исключения в apply_send_filters (строки 257-258)"""
        from smart_bot_factory.handlers.constants import HookType

        async def error_filter(user_id):
            raise Exception("Filter error")

        with patch("smart_bot_factory.handlers.utils.ctx") as mock_ctx:
            mock_ctx.message_hooks = {HookType.SEND_FILTERS: [error_filter]}

            # Не должно упасть, должно вернуть False
            result = await apply_send_filters(123456)

            assert result is False
