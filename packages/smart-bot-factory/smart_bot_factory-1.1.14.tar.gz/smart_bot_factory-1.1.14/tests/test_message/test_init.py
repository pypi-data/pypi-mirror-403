"""Тесты для __init__.py модуля message"""

from unittest.mock import Mock, patch

import pytest

from smart_bot_factory.message import get_bot


class TestGetBot:
    """Тесты для функции get_bot"""

    def test_get_bot_success(self):
        """Тест успешного получения бота"""
        mock_bot = Mock()
        mock_ctx = Mock()
        mock_ctx.bot = mock_bot

        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            result = get_bot()

            assert result == mock_bot

    def test_get_bot_not_initialized(self):
        """Тест получения бота когда он не инициализирован"""
        mock_ctx = Mock()
        mock_ctx.bot = None

        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            with pytest.raises(RuntimeError, match="Bot еще не инициализирован"):
                get_bot()
