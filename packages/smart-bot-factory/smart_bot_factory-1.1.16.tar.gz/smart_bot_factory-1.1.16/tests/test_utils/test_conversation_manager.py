"""Тесты для модуля conversation_manager"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from smart_bot_factory.utils.conversation_manager import ConversationManager


class TestConversationManager:
    """Тесты для класса ConversationManager"""

    def test_conversation_manager_init(self, mock_supabase_client, mock_admin_manager):
        """Тест инициализации ConversationManager"""
        manager = ConversationManager(
            supabase_client=mock_supabase_client, admin_manager=mock_admin_manager, parse_mode="Markdown", admin_session_timeout_minutes=30
        )
        assert manager.supabase == mock_supabase_client
        assert manager.admin_manager == mock_admin_manager
        assert manager.parse_mode == "Markdown"
        assert manager.admin_session_timeout_minutes == 30

    @pytest.mark.asyncio
    async def test_start_admin_conversation_success(self, mock_supabase_client, mock_admin_manager):
        """Тест успешного начала диалога админа"""
        mock_admin_manager.is_admin.return_value = True
        mock_supabase_client.get_active_session = AsyncMock(return_value={"id": "session_123"})
        mock_supabase_client.start_admin_conversation = AsyncMock(return_value=1)

        manager = ConversationManager(
            supabase_client=mock_supabase_client, admin_manager=mock_admin_manager, parse_mode="Markdown", admin_session_timeout_minutes=30
        )

        # Мокаем debug_admin_conversation_creation из правильного модуля
        with patch("smart_bot_factory.utils.debug_routing.debug_admin_conversation_creation", new_callable=AsyncMock):
            with patch.object(manager, "_show_recent_messages", new_callable=AsyncMock):
                result = await manager.start_admin_conversation(123456, 789012)
                assert result is True

    @pytest.mark.asyncio
    async def test_start_admin_conversation_not_admin(self, mock_supabase_client, mock_admin_manager):
        """Тест начала диалога не-админом"""
        mock_admin_manager.is_admin.return_value = False

        manager = ConversationManager(
            supabase_client=mock_supabase_client, admin_manager=mock_admin_manager, parse_mode="Markdown", admin_session_timeout_minutes=30
        )

        result = await manager.start_admin_conversation(123456, 789012)
        assert result is False

    @pytest.mark.asyncio
    async def test_start_admin_conversation_no_session(self, mock_supabase_client, mock_admin_manager):
        """Тест начала диалога без активной сессии"""
        mock_admin_manager.is_admin.return_value = True
        mock_supabase_client.get_active_session = AsyncMock(return_value=None)

        manager = ConversationManager(
            supabase_client=mock_supabase_client, admin_manager=mock_admin_manager, parse_mode="Markdown", admin_session_timeout_minutes=30
        )

        result = await manager.start_admin_conversation(123456, 789012)
        assert result is False

    @pytest.mark.asyncio
    async def test_end_admin_conversation(self, mock_supabase_client, mock_admin_manager):
        """Тест завершения диалога админа"""
        mock_supabase_client.end_admin_conversations = AsyncMock(return_value=1)

        manager = ConversationManager(
            supabase_client=mock_supabase_client, admin_manager=mock_admin_manager, parse_mode="Markdown", admin_session_timeout_minutes=30
        )

        result = await manager.end_admin_conversation(123456)
        assert result is True

    @pytest.mark.asyncio
    async def test_get_user_display_name(self, mock_supabase_client, mock_admin_manager):
        """Тест получения отображаемого имени пользователя"""
        # Настраиваем правильную цепочку вызовов для Supabase
        mock_table = Mock()
        mock_query = Mock()
        mock_response = Mock()
        mock_response.data = [{"first_name": "Test", "last_name": "User", "username": "testuser"}]
        mock_query.execute.return_value = mock_response

        # Настраиваем цепочку: table().select().eq().eq() (два eq для bot_id)
        mock_table.select.return_value.eq.return_value.eq.return_value = mock_query

        mock_supabase_client.client = Mock()
        mock_supabase_client.client.table.return_value = mock_table
        mock_supabase_client.bot_id = "test-bot"

        manager = ConversationManager(
            supabase_client=mock_supabase_client, admin_manager=mock_admin_manager, parse_mode="Markdown", admin_session_timeout_minutes=30
        )

        name = await manager.get_user_display_name(123456)
        assert "Test" in name
        assert "testuser" in name

    def test_truncate_message(self, mock_supabase_client, mock_admin_manager):
        """Тест сокращения длинного сообщения"""
        manager = ConversationManager(
            supabase_client=mock_supabase_client, admin_manager=mock_admin_manager, parse_mode="Markdown", admin_session_timeout_minutes=30
        )

        long_text = "\n".join([f"Line {i}" for i in range(10)])
        truncated = manager._truncate_message(long_text, max_lines=6)
        assert "..." in truncated
        assert len(truncated.split("\n")) <= 7  # 3 + ... + 3

    def test_escape_markdown(self, mock_supabase_client, mock_admin_manager):
        """Тест экранирования Markdown символов"""
        manager = ConversationManager(
            supabase_client=mock_supabase_client, admin_manager=mock_admin_manager, parse_mode="Markdown", admin_session_timeout_minutes=30
        )

        text = "Test *bold* _italic_ `code`"
        escaped = manager._escape_markdown(text)
        assert "\\*" in escaped or "*" not in escaped
        assert "\\_" in escaped or "_" not in escaped
