"""Тесты для admin_logic"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Chat, Message, User

from smart_bot_factory.admin.states import AdminStates


class TestAdminLogic:
    """Тесты для обработчиков admin_logic"""

    @pytest.fixture
    def mock_admin_manager(self):
        """Фикстура для мок AdminManager"""
        manager = Mock()
        manager.is_admin = Mock(return_value=True)
        manager.toggle_admin_mode = Mock(return_value=True)
        manager.get_admin_mode_text = Mock(return_value="👑 Режим администратора")
        return manager

    @pytest.fixture
    def mock_analytics_manager(self):
        """Фикстура для мок AnalyticsManager"""
        manager = Mock()
        manager.get_funnel_stats = AsyncMock(return_value={})
        manager.get_events_stats = AsyncMock(return_value={})
        manager.get_user_journey = AsyncMock(return_value=[])
        manager.format_funnel_stats = Mock(return_value="Funnel stats")
        manager.format_events_stats = Mock(return_value="Events stats")
        manager.format_user_journey = Mock(return_value="User journey")
        return manager

    @pytest.fixture
    def mock_conversation_manager(self):
        """Фикстура для мок ConversationManager"""
        manager = Mock()
        manager.start_admin_conversation = AsyncMock(return_value=True)
        manager.end_admin_conversation = AsyncMock(return_value=True)
        manager.get_active_conversations = AsyncMock(return_value=[])
        manager.get_admin_active_conversation = AsyncMock(return_value=None)
        manager.format_active_conversations = Mock(return_value="Active conversations")
        manager.route_admin_message = AsyncMock(return_value=False)
        manager.is_user_in_admin_chat = AsyncMock(return_value=None)
        return manager

    @pytest.fixture
    def mock_supabase_client(self):
        """Фикстура для мок Supabase клиента"""
        client = Mock()
        client.get_active_session = AsyncMock(return_value={"id": "session-123"})
        return client

    @pytest.fixture
    def mock_message(self):
        """Фикстура для мок сообщения"""
        message = Mock(spec=Message)
        message.from_user = Mock(spec=User)
        message.from_user.id = 123456789
        message.text = "/admin"
        message.answer = AsyncMock()
        message.chat = Mock(spec=Chat)
        message.chat.id = 123456789
        return message

    @pytest.fixture
    def mock_state(self):
        """Фикстура для мок состояния FSM"""
        state = AsyncMock(spec=FSMContext)
        state.set_state = AsyncMock()
        state.update_data = AsyncMock()
        state.get_data = AsyncMock(return_value={})
        state.get_state = AsyncMock(return_value=None)
        state.clear = AsyncMock()
        return state

    @pytest.fixture
    def setup_context(self, mock_admin_manager, mock_analytics_manager, mock_conversation_manager, mock_supabase_client):
        """Фикстура для настройки контекста"""
        with patch("smart_bot_factory.admin.admin_logic.ctx") as mock_ctx:
            mock_ctx.admin_manager = mock_admin_manager
            mock_ctx.analytics_manager = mock_analytics_manager
            mock_ctx.conversation_manager = mock_conversation_manager
            mock_ctx.supabase_client = mock_supabase_client
            yield mock_ctx

    @pytest.mark.asyncio
    async def test_cancel_handler(self, mock_message, mock_state, setup_context):
        """Тест обработчика отмены"""
        from smart_bot_factory.admin.admin_logic import cancel_handler

        await cancel_handler(mock_message, mock_state)

        mock_state.clear.assert_called_once()
        mock_message.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_cancel_handler_with_event_state(self, mock_message, mock_state, setup_context):
        """Тест обработчика отмены при создании события"""
        mock_state.get_state = AsyncMock(return_value="AdminStates:create_event_name")

        with patch("smart_bot_factory.admin.admin_events.cleanup_temp_files") as mock_cleanup:
            from smart_bot_factory.admin.admin_logic import cancel_handler

            await cancel_handler(mock_message, mock_state)

            mock_cleanup.assert_called_once_with(mock_state)
            mock_state.clear.assert_called_once()

    @pytest.mark.asyncio
    async def test_admin_stats_handler(self, mock_message, mock_state, setup_context):
        """Тест обработчика статистики"""
        from smart_bot_factory.admin.admin_logic import admin_stats_handler

        await admin_stats_handler(mock_message, mock_state)

        setup_context.analytics_manager.get_funnel_stats.assert_called_once_with(7)
        setup_context.analytics_manager.get_events_stats.assert_called_once_with(7)
        mock_message.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_admin_stats_not_admin(self, mock_message, mock_state, setup_context):
        """Тест что не-админ не может получить статистику"""
        setup_context.admin_manager.is_admin.return_value = False

        from smart_bot_factory.admin.admin_logic import admin_stats_handler

        await admin_stats_handler(mock_message, mock_state)

        mock_message.answer.assert_not_called()

    @pytest.mark.asyncio
    async def test_admin_history_handler(self, mock_message, mock_state, setup_context):
        """Тест обработчика истории пользователя"""
        mock_message.text = "/история 987654321"

        from smart_bot_factory.admin.admin_logic import admin_history_handler

        await admin_history_handler(mock_message, mock_state)

        setup_context.analytics_manager.get_user_journey.assert_called_once_with(987654321)
        mock_message.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_admin_history_no_user_id(self, mock_message, mock_state, setup_context):
        """Тест истории без указания user_id"""
        mock_message.text = "/история"

        from smart_bot_factory.admin.admin_logic import admin_history_handler

        await admin_history_handler(mock_message, mock_state)

        assert mock_message.answer.called
        call_args = mock_message.answer.call_args[0][0]
        assert "id пользователя" in call_args.lower()

    @pytest.mark.asyncio
    async def test_admin_chat_handler(self, mock_message, mock_state, setup_context):
        """Тест обработчика начала диалога"""
        mock_message.text = "/чат 987654321"

        from smart_bot_factory.admin.admin_logic import admin_chat_handler

        await admin_chat_handler(mock_message, mock_state)

        setup_context.conversation_manager.start_admin_conversation.assert_called_once_with(123456789, 987654321)
        mock_state.set_state.assert_called_with(AdminStates.in_conversation)
        mock_message.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_admin_chat_no_session(self, mock_message, mock_state, setup_context):
        """Тест начала диалога без активной сессии"""
        mock_message.text = "/чат 987654321"
        setup_context.supabase_client.get_active_session = AsyncMock(return_value=None)

        from smart_bot_factory.admin.admin_logic import admin_chat_handler

        await admin_chat_handler(mock_message, mock_state)

        assert mock_message.answer.called
        call_args = mock_message.answer.call_args[0][0]
        assert "нет активной сессии" in call_args.lower()

    @pytest.mark.asyncio
    async def test_admin_active_chats_command(self, mock_message, mock_state, setup_context):
        """Тест команды активных чатов"""
        from smart_bot_factory.admin.admin_logic import admin_active_chats_command

        await admin_active_chats_command(mock_message, mock_state)

        setup_context.conversation_manager.get_active_conversations.assert_called_once()
        mock_message.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_admin_stop_handler(self, mock_message, mock_state, setup_context):
        """Тест обработчика завершения диалога"""
        setup_context.conversation_manager.get_admin_active_conversation = AsyncMock(return_value={"user_id": 987654321})

        from smart_bot_factory.admin.admin_logic import admin_stop_handler

        await admin_stop_handler(mock_message, mock_state)

        setup_context.conversation_manager.end_admin_conversation.assert_called_once_with(123456789)
        mock_state.set_state.assert_called_with(AdminStates.admin_mode)
        mock_message.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_admin_stop_no_conversation(self, mock_message, mock_state, setup_context):
        """Тест завершения диалога когда его нет"""
        setup_context.conversation_manager.get_admin_active_conversation = AsyncMock(return_value=None)

        from smart_bot_factory.admin.admin_logic import admin_stop_handler

        await admin_stop_handler(mock_message, mock_state)

        assert mock_message.answer.called
        call_args = mock_message.answer.call_args[0][0]
        assert "нет активного диалога" in call_args.lower()

    @pytest.mark.asyncio
    async def test_admin_toggle_handler(self, mock_message, mock_state, setup_context):
        """Тест переключения режима админа"""
        from smart_bot_factory.admin.admin_logic import admin_toggle_handler

        await admin_toggle_handler(mock_message, mock_state)

        setup_context.admin_manager.toggle_admin_mode.assert_called_once_with(123456789)
        mock_message.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_admin_message_handler(self, mock_message, mock_state, setup_context):
        """Тест обработчика сообщений админа"""
        mock_message.text = "Test message"
        setup_context.conversation_manager.route_admin_message = AsyncMock(return_value=True)

        from smart_bot_factory.admin.admin_logic import admin_message_handler

        await admin_message_handler(mock_message, mock_state)

        setup_context.conversation_manager.route_admin_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_admin_message_handler_not_handled(self, mock_message, mock_state, setup_context):
        """Тест обработчика сообщений когда сообщение не обработано"""
        mock_message.text = "Test message"
        setup_context.conversation_manager.route_admin_message = AsyncMock(return_value=False)

        from smart_bot_factory.admin.admin_logic import admin_message_handler

        await admin_message_handler(mock_message, mock_state)

        assert mock_message.answer.called
        call_args = mock_message.answer.call_args[0][0]
        assert "администратора" in call_args.lower() or "команды" in call_args.lower()

    @pytest.mark.asyncio
    async def test_admin_callback_handler_stats(self, setup_context):
        """Тест callback обработчика для статистики"""
        callback = Mock(spec=CallbackQuery)
        callback.from_user = Mock(spec=User)
        callback.from_user.id = 123456789
        callback.data = "admin_stats"
        callback.message = Mock()
        callback.message.answer = AsyncMock()
        callback.answer = AsyncMock()

        mock_state = AsyncMock()

        from smart_bot_factory.admin.admin_logic import admin_callback_handler

        await admin_callback_handler(callback, mock_state)

        setup_context.analytics_manager.get_funnel_stats.assert_called_once_with(7)
        callback.message.answer.assert_called_once()
        callback.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_admin_callback_handler_toggle_mode(self, setup_context):
        """Тест callback обработчика для переключения режима"""
        callback = Mock(spec=CallbackQuery)
        callback.from_user = Mock(spec=User)
        callback.from_user.id = 123456789
        callback.data = "admin_toggle_mode"
        callback.message = Mock()
        callback.message.answer = AsyncMock()
        callback.answer = AsyncMock()

        mock_state = AsyncMock()

        from smart_bot_factory.admin.admin_logic import admin_callback_handler

        await admin_callback_handler(callback, mock_state)

        setup_context.admin_manager.toggle_admin_mode.assert_called_once_with(123456789)
        # answer вызывается дважды - один раз с текстом, второй раз в конце функции
        assert callback.answer.call_count >= 1

    @pytest.mark.asyncio
    async def test_admin_callback_handler_not_admin(self, setup_context):
        """Тест callback обработчика для не-админа"""
        callback = Mock(spec=CallbackQuery)
        callback.from_user = Mock(spec=User)
        callback.from_user.id = 111111111
        callback.data = "admin_stats"
        callback.answer = AsyncMock()

        setup_context.admin_manager.is_admin.return_value = False

        mock_state = AsyncMock()

        from smart_bot_factory.admin.admin_logic import admin_callback_handler

        await admin_callback_handler(callback, mock_state)

        callback.answer.assert_called_once_with("Нет доступа")
