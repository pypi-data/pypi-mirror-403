"""Тесты для commands"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.types import Chat, Message, User

from smart_bot_factory.handlers.commands import timeup_handler, user_start_handler
from smart_bot_factory.handlers.states import UserStates


class TestUserStartHandler:
    """Тесты для обработчика user_start_handler"""

    @pytest.fixture
    def mock_message(self):
        """Фикстура для мок сообщения"""
        message = Mock(spec=Message)
        message.from_user = Mock(spec=User)
        message.from_user.id = 123456789
        message.from_user.username = "testuser"
        message.from_user.first_name = "Test"
        message.from_user.last_name = "User"
        message.from_user.language_code = "ru"
        message.text = "/start"
        message.answer = AsyncMock()
        message.chat = Mock(spec=Chat)
        message.chat.id = 123456789
        return message

    @pytest.fixture
    def mock_state(self):
        """Фикстура для мок состояния FSM"""
        state = AsyncMock(spec=FSMContext)
        state.clear = AsyncMock()
        state.update_data = AsyncMock()
        state.set_state = AsyncMock()
        state.get_data = AsyncMock(return_value={})
        return state

    @pytest.fixture
    def setup_context(self):
        """Фикстура для настройки контекста"""
        with patch("smart_bot_factory.handlers.commands.ctx") as mock_ctx:
            mock_ctx.prompt_loader = Mock()
            mock_ctx.prompt_loader.load_welcome_message = AsyncMock(return_value="Добро пожаловать!")
            mock_ctx.supabase_client = Mock()
            mock_ctx.supabase_client.create_chat_session = AsyncMock(return_value="session-123")
            mock_ctx.supabase_client.add_message = AsyncMock()
            mock_ctx.utm_triggers = None
            mock_ctx.start_handlers = []
            mock_ctx.config = Mock()
            mock_ctx.config.BOT_ID = "test-bot"
            yield mock_ctx

    @pytest.mark.asyncio
    async def test_user_start_handler_basic(self, mock_message, mock_state, setup_context):
        """Тест базового обработчика /start"""
        with patch("smart_bot_factory.handlers.commands.send_message"):
            with patch("smart_bot_factory.handlers.commands.send_welcome_file") as mock_send_file:
                mock_send_file.return_value = None

                await user_start_handler(mock_message, mock_state)

                mock_state.clear.assert_called_once()
                setup_context.supabase_client.create_chat_session.assert_called_once()
                mock_state.set_state.assert_called_with(UserStates.waiting_for_message)

    @pytest.mark.asyncio
    async def test_user_start_handler_with_utm(self, mock_message, mock_state, setup_context):
        """Тест обработчика /start с UTM параметрами"""
        mock_message.text = "/start utm_source=test&utm_medium=email"

        with patch("smart_bot_factory.handlers.commands.parse_utm_from_start_param") as mock_parse:
            mock_parse.return_value = {"utm_source": "test", "utm_medium": "email"}

            with patch("smart_bot_factory.handlers.commands.send_message"):
                with patch("smart_bot_factory.handlers.commands.send_welcome_file") as mock_send_file:
                    mock_send_file.return_value = None

                    await user_start_handler(mock_message, mock_state)

                    mock_parse.assert_called_once()
                    setup_context.supabase_client.create_chat_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_user_start_handler_with_start_handlers(self, mock_message, mock_state, setup_context):
        """Тест обработчика /start с пользовательскими обработчиками"""

        async def start_handler(user_id, session_id, message, state):
            pass

        setup_context.start_handlers = [start_handler]

        with patch("smart_bot_factory.handlers.commands.send_message"):
            with patch("smart_bot_factory.handlers.commands.send_welcome_file") as mock_send_file:
                mock_send_file.return_value = None

                await user_start_handler(mock_message, mock_state)

                setup_context.supabase_client.create_chat_session.assert_called_once()


class TestTimeupHandler:
    """Тесты для обработчика timeup_handler"""

    @pytest.fixture
    def mock_message(self):
        """Фикстура для мок сообщения"""
        message = Mock(spec=Message)
        message.from_user = Mock(spec=User)
        message.from_user.id = 123456789
        message.text = "/timeup"
        message.answer = AsyncMock()
        return message

    @pytest.fixture
    def mock_state(self):
        """Фикстура для мок состояния FSM"""
        state = AsyncMock(spec=FSMContext)
        return state

    @pytest.fixture
    def setup_context(self):
        """Фикстура для настройки контекста"""
        with patch("smart_bot_factory.handlers.commands.ctx") as mock_ctx:
            mock_ctx.supabase_client = Mock()
            mock_ctx.supabase_client.bot_id = "test-bot"
            mock_ctx.supabase_client.client = Mock()
            mock_table = mock_ctx.supabase_client.client.table.return_value
            mock_table.select.return_value.in_.return_value.eq.return_value.or_.return_value.execute.return_value.data = []
            yield mock_ctx

    @pytest.mark.asyncio
    async def test_timeup_handler_no_events(self, mock_message, mock_state, setup_context):
        """Тест обработчика /timeup когда нет событий"""
        await timeup_handler(mock_message, mock_state)

        mock_message.answer.assert_called()
        call_args = mock_message.answer.call_args[0][0]
        assert "нет запланированных" in call_args.lower() or "нет событий" in call_args.lower()

    @pytest.mark.asyncio
    async def test_timeup_handler_with_event(self, mock_message, mock_state, setup_context):
        """Тест обработчика /timeup с событием"""
        from datetime import timezone

        event_data = {
            "id": "event-123",
            "event_type": "test_event",
            "event_category": "user_event",
            "user_id": 123456789,
            "scheduled_at": datetime.now(timezone.utc).isoformat(),
            "status": "pending",
        }

        mock_table = setup_context.supabase_client.client.table.return_value
        mock_table.select.return_value.in_.return_value.eq.return_value.or_.return_value.execute.return_value.data = [
            event_data
        ]

        with patch("smart_bot_factory.event.decorators.processor.process_scheduled_event") as mock_process:
            mock_process.return_value = {"status": "success"}

            with patch("smart_bot_factory.event.decorators.db.update_event_result") as mock_update:
                await timeup_handler(mock_message, mock_state)

                mock_process.assert_called_once()
                mock_update.assert_called_once()
