"""Тесты для utils.debug_routing"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from smart_bot_factory.utils.debug_routing import (
    debug_admin_conversation_creation,
    debug_user_state,
    setup_debug_handlers,
)
from smart_bot_factory.utils.debug_routing import (
    test_message_routing as debug_test_message_routing,
)


class TestDebugUserState:
    """Тесты для функции debug_user_state"""

    @pytest.fixture
    def mock_message(self):
        """Фикстура для мок сообщения"""
        message = Mock()
        message.from_user.id = 123456
        message.text = "Test message"
        return message

    @pytest.fixture
    def mock_state(self):
        """Фикстура для мок состояния"""
        state = AsyncMock()
        state.get_state = AsyncMock(return_value="waiting_for_message")
        state.get_data = AsyncMock(return_value={"session_id": "test-session"})
        return state

    @pytest.mark.asyncio
    async def test_debug_user_state_basic(self, mock_message, mock_state):
        """Тест базовой работы debug_user_state (строки 22-48)"""
        with patch("smart_bot_factory.utils.debug_routing.ctx") as mock_ctx:
            mock_ctx.conversation_manager = AsyncMock()
            mock_ctx.conversation_manager.is_user_in_admin_chat = AsyncMock(return_value=None)
            mock_ctx.supabase_client = AsyncMock()
            mock_ctx.supabase_client.get_active_session = AsyncMock(return_value=None)

            await debug_user_state(mock_message, mock_state, "TEST_CONTEXT")

            mock_state.get_state.assert_called_once()
            mock_state.get_data.assert_called_once()
            mock_ctx.conversation_manager.is_user_in_admin_chat.assert_called_once_with(123456)
            mock_ctx.supabase_client.get_active_session.assert_called_once_with(123456)

    @pytest.mark.asyncio
    async def test_debug_user_state_with_conversation(self, mock_message, mock_state):
        """Тест debug_user_state с диалогом админа (строки 37-39)"""
        conversation = {"id": "conv-123", "admin_id": 789012, "status": "active"}

        with patch("smart_bot_factory.utils.debug_routing.ctx") as mock_ctx:
            mock_ctx.conversation_manager = AsyncMock()
            mock_ctx.conversation_manager.is_user_in_admin_chat = AsyncMock(return_value=conversation)
            mock_ctx.supabase_client = AsyncMock()
            mock_ctx.supabase_client.get_active_session = AsyncMock(return_value=None)

            await debug_user_state(mock_message, mock_state, "TEST_CONTEXT")

            mock_ctx.conversation_manager.is_user_in_admin_chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_debug_user_state_with_session(self, mock_message, mock_state):
        """Тест debug_user_state с активной сессией (строки 42-46)"""
        session_info = {"id": "session-123", "created_at": "2024-01-01T00:00:00Z"}

        with patch("smart_bot_factory.utils.debug_routing.ctx") as mock_ctx:
            mock_ctx.conversation_manager = AsyncMock()
            mock_ctx.conversation_manager.is_user_in_admin_chat = AsyncMock(return_value=None)
            mock_ctx.supabase_client = AsyncMock()
            mock_ctx.supabase_client.get_active_session = AsyncMock(return_value=session_info)

            await debug_user_state(mock_message, mock_state, "TEST_CONTEXT")

            mock_ctx.supabase_client.get_active_session.assert_called_once_with(123456)


class TestDebugAdminConversationCreation:
    """Тесты для функции debug_admin_conversation_creation"""

    @pytest.mark.asyncio
    async def test_debug_admin_conversation_creation_basic(self):
        """Тест базовой работы debug_admin_conversation_creation (строки 51-73)"""
        with patch("smart_bot_factory.utils.debug_routing.ctx") as mock_ctx:
            mock_ctx.supabase_client = Mock()
            mock_ctx.supabase_client.get_active_session = AsyncMock(return_value=None)
            mock_ctx.supabase_client.client = Mock()
            mock_ctx.supabase_client.client.table = Mock()

            # Мокируем цепочку вызовов для запроса к БД
            mock_query = Mock()
            mock_query.select = Mock(return_value=mock_query)
            mock_query.eq = Mock(return_value=mock_query)
            mock_query.execute = Mock(return_value=Mock(data=[]))
            mock_ctx.supabase_client.client.table.return_value = mock_query

            await debug_admin_conversation_creation(admin_id=789012, user_id=123456)

            mock_ctx.supabase_client.get_active_session.assert_called_once_with(123456)

    @pytest.mark.asyncio
    async def test_debug_admin_conversation_creation_with_session(self):
        """Тест debug_admin_conversation_creation с активной сессией (строки 58-63)"""
        session_info = {"id": "session-123", "created_at": "2024-01-01T00:00:00Z"}

        with patch("smart_bot_factory.utils.debug_routing.ctx") as mock_ctx:
            mock_ctx.supabase_client = Mock()
            mock_ctx.supabase_client.get_active_session = AsyncMock(return_value=session_info)
            mock_ctx.supabase_client.client = Mock()
            mock_ctx.supabase_client.client.table = Mock()

            mock_query = Mock()
            mock_query.select = Mock(return_value=mock_query)
            mock_query.eq = Mock(return_value=mock_query)
            mock_query.execute = Mock(return_value=Mock(data=[]))
            mock_ctx.supabase_client.client.table.return_value = mock_query

            await debug_admin_conversation_creation(admin_id=789012, user_id=123456)

            mock_ctx.supabase_client.get_active_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_debug_admin_conversation_creation_with_existing_conversations(self):
        """Тест debug_admin_conversation_creation с существующими диалогами (строки 65-71)"""
        existing_conversations = [{"id": "conv-1", "admin_id": 789012, "status": "active"}, {"id": "conv-2", "admin_id": 789013, "status": "active"}]

        with patch("smart_bot_factory.utils.debug_routing.ctx") as mock_ctx:
            mock_ctx.supabase_client = Mock()
            mock_ctx.supabase_client.get_active_session = AsyncMock(return_value=None)
            mock_ctx.supabase_client.client = Mock()
            mock_ctx.supabase_client.client.table = Mock()

            mock_query = Mock()
            mock_query.select = Mock(return_value=mock_query)
            mock_query.eq = Mock(return_value=mock_query)
            mock_query.execute = Mock(return_value=Mock(data=existing_conversations))
            mock_ctx.supabase_client.client.table.return_value = mock_query

            await debug_admin_conversation_creation(admin_id=789012, user_id=123456)

            # Проверяем что запрос был выполнен
            assert mock_query.execute.called

    @pytest.mark.asyncio
    async def test_debug_admin_conversation_creation_exception(self):
        """Тест обработки исключения в debug_admin_conversation_creation (строки 72-73)"""
        with patch("smart_bot_factory.utils.debug_routing.ctx") as mock_ctx:
            mock_ctx.supabase_client = Mock()
            mock_ctx.supabase_client.get_active_session = AsyncMock(return_value=None)
            mock_ctx.supabase_client.client = Mock()
            mock_ctx.supabase_client.client.table = Mock(side_effect=Exception("DB Error"))

            # Функция должна обработать исключение и не упасть
            await debug_admin_conversation_creation(admin_id=789012, user_id=123456)


class TestTestMessageRouting:
    """Тесты для функции test_message_routing"""

    @pytest.mark.asyncio
    async def test_message_routing_with_conversation(self):
        """Тест test_message_routing с диалогом админа (строки 76-94)"""
        conversation = {"id": "conv-123", "admin_id": 789012, "started_at": "2024-01-01T00:00:00Z"}

        with patch("smart_bot_factory.utils.debug_routing.ctx") as mock_ctx:
            mock_ctx.conversation_manager = AsyncMock()
            mock_ctx.conversation_manager.is_user_in_admin_chat = AsyncMock(return_value=conversation)

            result = await debug_test_message_routing(user_id=123456, test_message="Test message")

            assert result == "admin_chat"
            mock_ctx.conversation_manager.is_user_in_admin_chat.assert_called_once_with(123456)

    @pytest.mark.asyncio
    async def test_message_routing_without_conversation(self):
        """Тест test_message_routing без диалога админа"""
        with patch("smart_bot_factory.utils.debug_routing.ctx") as mock_ctx:
            mock_ctx.conversation_manager = AsyncMock()
            mock_ctx.conversation_manager.is_user_in_admin_chat = AsyncMock(return_value=None)

            result = await debug_test_message_routing(user_id=123456, test_message="Test message")

            assert result == "bot_chat"
            mock_ctx.conversation_manager.is_user_in_admin_chat.assert_called_once_with(123456)


class TestSetupDebugHandlers:
    """Тесты для функции setup_debug_handlers"""

    def test_setup_debug_handlers(self):
        """Тест setup_debug_handlers (строки 17-19)"""
        mock_dp = Mock()

        setup_debug_handlers(mock_dp)

        mock_dp.include_router.assert_called_once()
