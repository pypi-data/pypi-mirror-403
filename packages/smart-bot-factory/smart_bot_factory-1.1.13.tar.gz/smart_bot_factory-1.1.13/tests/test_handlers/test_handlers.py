"""Тесты для handlers.handlers"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from smart_bot_factory.handlers.handlers import (
    admin_middleware,
    catch_all_handler,
    message_without_state_handler,
    process_user_message,
    setup_handlers,
    start_handler,
    user_in_admin_chat_handler,
    user_message_handler,
)
from smart_bot_factory.handlers.states import UserStates


class TestAdminMiddleware:
    """Тесты для admin_middleware"""

    @pytest.mark.asyncio
    async def test_admin_middleware_with_admin(self):
        """Тест middleware для админа (строки 57-62)"""
        mock_handler = AsyncMock(return_value="result")
        mock_event = Mock()
        mock_event.from_user.id = 789012
        mock_data = {}

        with patch("smart_bot_factory.handlers.handlers.ctx") as mock_ctx:
            mock_ctx.admin_manager = Mock()
            mock_ctx.admin_manager.is_admin = Mock(return_value=True)
            mock_ctx.admin_manager.update_admin_info = AsyncMock()

            result = await admin_middleware(mock_handler, mock_event, mock_data)

            assert result == "result"
            mock_ctx.admin_manager.is_admin.assert_called_once_with(789012)
            mock_ctx.admin_manager.update_admin_info.assert_called_once_with(mock_event.from_user)

    @pytest.mark.asyncio
    async def test_admin_middleware_without_admin(self):
        """Тест middleware для не-админа"""
        mock_handler = AsyncMock(return_value="result")
        mock_event = Mock()
        mock_event.from_user.id = 123456
        mock_data = {}

        with patch("smart_bot_factory.handlers.handlers.ctx") as mock_ctx:
            mock_ctx.admin_manager = Mock()
            mock_ctx.admin_manager.is_admin = Mock(return_value=False)

            result = await admin_middleware(mock_handler, mock_event, mock_data)

            assert result == "result"
            mock_ctx.admin_manager.is_admin.assert_called_once_with(123456)
            # update_admin_info не должен вызываться для не-админа


class TestSetupHandlers:
    """Тесты для setup_handlers"""

    def test_setup_handlers(self):
        """Тест setup_handlers (строки 65-71)"""
        mock_dp = Mock()
        mock_router = Mock()
        mock_router.message = Mock()
        mock_router.message.middleware = Mock()

        with patch("smart_bot_factory.handlers.handlers.router", mock_router):
            setup_handlers(mock_dp)

            mock_router.message.middleware.assert_called()
            mock_dp.include_router.assert_called_once_with(mock_router)


class TestNoStateHandler:
    """Тесты для message_without_state_handler"""

    @pytest.mark.asyncio
    async def test_no_state_handler_with_admin_conversation(self, mock_message, mock_state):
        """Тест message_without_state_handler с диалогом админа (строки 145-179)"""
        conversation = {"id": "conv-123", "admin_id": 789012, "status": "active"}
        session_info = {"id": "session-123"}

        with (
            patch("smart_bot_factory.handlers.handlers.ctx") as mock_ctx,
            patch("smart_bot_factory.utils.debug_routing.debug_user_state"),
        ):
            mock_ctx.conversation_manager = AsyncMock()
            mock_ctx.conversation_manager.is_user_in_admin_chat = AsyncMock(return_value=conversation)
            mock_ctx.conversation_manager.forward_message_to_admin = AsyncMock()
            mock_ctx.supabase_client = AsyncMock()
            mock_ctx.supabase_client.get_active_session = AsyncMock(return_value=session_info)
            mock_ctx.supabase_client.add_message = AsyncMock()

            await message_without_state_handler(mock_message, mock_state)

            mock_state.set_state.assert_called_once_with(UserStates.admin_chat)
            mock_ctx.conversation_manager.forward_message_to_admin.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_state_handler_with_admin(self, mock_message, mock_state):
        """Тест no_state_handler для админа (строки 181-186)"""
        from smart_bot_factory.admin.admin_logic import AdminStates

        with (
            patch("smart_bot_factory.handlers.handlers.ctx") as mock_ctx,
            patch("smart_bot_factory.utils.debug_routing.debug_user_state"),
        ):
            mock_ctx.conversation_manager = AsyncMock()
            mock_ctx.conversation_manager.is_user_in_admin_chat = AsyncMock(return_value=None)
            mock_ctx.admin_manager = Mock()
            mock_ctx.admin_manager.is_admin = Mock(return_value=True)

            await message_without_state_handler(mock_message, mock_state)

            mock_state.set_state.assert_called_once_with(AdminStates.admin_mode)
            mock_message.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_state_handler_with_active_session(self, mock_message, mock_state):
        """Тест no_state_handler с активной сессией (строки 190-205)"""
        session_info = {"id": "session-123"}

        with (
            patch("smart_bot_factory.handlers.handlers.ctx") as mock_ctx,
            patch("smart_bot_factory.utils.debug_routing.debug_user_state"),
            patch("smart_bot_factory.handlers.handlers.process_user_message") as mock_process,
        ):
            mock_ctx.conversation_manager = AsyncMock()
            mock_ctx.conversation_manager.is_user_in_admin_chat = AsyncMock(return_value=None)
            mock_ctx.admin_manager = Mock()
            mock_ctx.admin_manager.is_admin = Mock(return_value=False)
            mock_ctx.supabase_client = AsyncMock()
            mock_ctx.supabase_client.get_active_session = AsyncMock(return_value=session_info)

            await message_without_state_handler(mock_message, mock_state)

            mock_state.update_data.assert_called_once()
            mock_state.set_state.assert_called_once_with(UserStates.waiting_for_message)
            mock_process.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_state_handler_without_session(self, mock_message, mock_state):
        """Тест no_state_handler без активной сессии (строки 206-208)"""
        with (
            patch("smart_bot_factory.handlers.handlers.ctx") as mock_ctx,
            patch("smart_bot_factory.utils.debug_routing.debug_user_state"),
            patch("smart_bot_factory.handlers.handlers.send_message") as mock_send,
        ):
            mock_ctx.conversation_manager = AsyncMock()
            mock_ctx.conversation_manager.is_user_in_admin_chat = AsyncMock(return_value=None)
            mock_ctx.admin_manager = Mock()
            mock_ctx.admin_manager.is_admin = Mock(return_value=False)
            mock_ctx.supabase_client = AsyncMock()
            mock_ctx.supabase_client.get_active_session = AsyncMock(return_value=None)

            await message_without_state_handler(mock_message, mock_state)

            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_state_handler_exception(self, mock_message, mock_state):
        """Тест обработки исключения в no_state_handler (строки 210-212)"""
        with (
            patch("smart_bot_factory.handlers.handlers.ctx") as mock_ctx,
            patch("smart_bot_factory.utils.debug_routing.debug_user_state", side_effect=Exception("Error")),
            patch("smart_bot_factory.handlers.handlers.send_message") as mock_send,
        ):
            mock_ctx.conversation_manager = AsyncMock()
            mock_ctx.conversation_manager.is_user_in_admin_chat = AsyncMock(side_effect=Exception("Error"))

            await message_without_state_handler(mock_message, mock_state)

            mock_send.assert_called_once()


class TestStartHandler:
    """Тесты для start_handler"""

    @pytest.mark.asyncio
    async def test_start_handler_admin_mode(self, mock_message, mock_state):
        """Тест start_handler для админа в режиме администратора (строки 77-98)"""
        with (
            patch("smart_bot_factory.handlers.handlers.ctx") as mock_ctx,
            patch("smart_bot_factory.utils.debug_routing.debug_user_state"),
            patch("smart_bot_factory.admin.admin_logic.admin_start_handler") as mock_admin_start,
        ):
            mock_ctx.admin_manager = Mock()
            mock_ctx.admin_manager.is_admin = Mock(return_value=True)
            mock_ctx.admin_manager.is_in_admin_mode = Mock(return_value=True)

            await start_handler(mock_message, mock_state)

            mock_admin_start.assert_called_once_with(mock_message, mock_state)

    @pytest.mark.asyncio
    async def test_start_handler_user(self, mock_message, mock_state):
        """Тест start_handler для обычного пользователя"""
        with (
            patch("smart_bot_factory.handlers.handlers.ctx") as mock_ctx,
            patch("smart_bot_factory.utils.debug_routing.debug_user_state"),
            patch("smart_bot_factory.handlers.handlers.user_start_handler") as mock_user_start,
        ):
            mock_ctx.admin_manager = Mock()
            mock_ctx.admin_manager.is_admin = Mock(return_value=False)

            await start_handler(mock_message, mock_state)

            mock_user_start.assert_called_once_with(mock_message, mock_state)

    @pytest.mark.asyncio
    async def test_start_handler_exception(self, mock_message, mock_state):
        """Тест обработки исключения в start_handler (строки 96-98)"""
        with (
            patch("smart_bot_factory.handlers.handlers.ctx") as mock_ctx,
            patch("smart_bot_factory.utils.debug_routing.debug_user_state", side_effect=Exception("Error")),
            patch("smart_bot_factory.handlers.handlers.send_message") as mock_send,
        ):
            mock_ctx.admin_manager = Mock()
            mock_ctx.admin_manager.is_admin = Mock(side_effect=Exception("Error"))

            await start_handler(mock_message, mock_state)

            mock_send.assert_called_once()


class TestUserInAdminChatHandler:
    """Тесты для user_in_admin_chat_handler"""

    @pytest.mark.asyncio
    async def test_user_in_admin_chat_handler_with_conversation(self, mock_message, mock_state):
        """Тест user_in_admin_chat_handler с активным диалогом (строки 217-259)"""
        conversation = {"id": "conv-123", "admin_id": 789012, "status": "active"}
        session_info = {"id": "session-123"}

        with (
            patch("smart_bot_factory.handlers.handlers.ctx") as mock_ctx,
            patch("smart_bot_factory.utils.debug_routing.debug_user_state"),
        ):
            mock_ctx.conversation_manager = AsyncMock()
            mock_ctx.conversation_manager.is_user_in_admin_chat = AsyncMock(return_value=conversation)
            mock_ctx.conversation_manager.forward_message_to_admin = AsyncMock()
            mock_ctx.supabase_client = AsyncMock()
            mock_ctx.supabase_client.get_active_session = AsyncMock(return_value=session_info)
            mock_ctx.supabase_client.add_message = AsyncMock()

            await user_in_admin_chat_handler(mock_message, mock_state)

            mock_ctx.conversation_manager.forward_message_to_admin.assert_called_once()
            mock_ctx.supabase_client.add_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_user_in_admin_chat_handler_no_conversation(self, mock_message, mock_state):
        """Тест user_in_admin_chat_handler без диалога (строки 260-272)"""
        with (
            patch("smart_bot_factory.handlers.handlers.ctx") as mock_ctx,
            patch("smart_bot_factory.utils.debug_routing.debug_user_state"),
            patch("smart_bot_factory.handlers.handlers.process_user_message") as mock_process,
        ):
            mock_ctx.conversation_manager = AsyncMock()
            mock_ctx.conversation_manager.is_user_in_admin_chat = AsyncMock(return_value=None)
            mock_state.get_data = AsyncMock(return_value={"session_id": "session-123"})

            await user_in_admin_chat_handler(mock_message, mock_state)

            mock_state.set_state.assert_called_once_with(UserStates.waiting_for_message)
            mock_process.assert_called_once()

    @pytest.mark.asyncio
    async def test_user_in_admin_chat_handler_no_conversation_manager(self, mock_message, mock_state):
        """Тест user_in_admin_chat_handler без conversation_manager (строки 227-230)"""
        with (
            patch("smart_bot_factory.handlers.handlers.ctx") as mock_ctx,
            patch("smart_bot_factory.utils.debug_routing.debug_user_state"),
        ):
            mock_ctx.conversation_manager = None

            await user_in_admin_chat_handler(mock_message, mock_state)

            mock_state.set_state.assert_called_once_with(UserStates.waiting_for_message)

    @pytest.mark.asyncio
    async def test_user_in_admin_chat_handler_exception(self, mock_message, mock_state):
        """Тест обработки исключения в user_in_admin_chat_handler (строки 257-259)"""
        conversation = {"id": "conv-123", "admin_id": 789012}

        with (
            patch("smart_bot_factory.handlers.handlers.ctx") as mock_ctx,
            patch("smart_bot_factory.utils.debug_routing.debug_user_state"),
        ):
            mock_ctx.conversation_manager = AsyncMock()
            mock_ctx.conversation_manager.is_user_in_admin_chat = AsyncMock(return_value=conversation)
            mock_ctx.conversation_manager.forward_message_to_admin = AsyncMock(side_effect=Exception("Error"))
            mock_ctx.supabase_client = AsyncMock()
            mock_ctx.supabase_client.get_active_session = AsyncMock(return_value={"id": "session-123"})

            await user_in_admin_chat_handler(mock_message, mock_state)

            mock_message.answer.assert_called_once()


class TestUserMessageHandler:
    """Тесты для user_message_handler"""

    @pytest.mark.asyncio
    async def test_user_message_handler_with_conversation(self, mock_message, mock_state):
        """Тест user_message_handler с диалогом админа (строки 277-297)"""
        conversation = {"id": "conv-123", "admin_id": 789012}

        with (
            patch("smart_bot_factory.handlers.handlers.ctx") as mock_ctx,
            patch("smart_bot_factory.utils.debug_routing.debug_user_state"),
            patch("smart_bot_factory.handlers.handlers.user_in_admin_chat_handler") as mock_admin_handler,
        ):
            mock_ctx.conversation_manager = AsyncMock()
            mock_ctx.conversation_manager.is_user_in_admin_chat = AsyncMock(return_value=conversation)

            await user_message_handler(mock_message, mock_state)

            mock_state.set_state.assert_called_once_with(UserStates.admin_chat)
            mock_admin_handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_user_message_handler_normal_flow(self, mock_message, mock_state):
        """Тест user_message_handler обычный поток (строки 299-309)"""
        mock_state.get_data = AsyncMock(return_value={"session_id": "session-123"})

        with (
            patch("smart_bot_factory.handlers.handlers.ctx") as mock_ctx,
            patch("smart_bot_factory.utils.debug_routing.debug_user_state"),
            patch("smart_bot_factory.handlers.handlers.process_user_message") as mock_process,
        ):
            mock_ctx.conversation_manager = AsyncMock()
            mock_ctx.conversation_manager.is_user_in_admin_chat = AsyncMock(return_value=None)

            await user_message_handler(mock_message, mock_state)

            # Проверяем что process_user_message был вызван с правильными аргументами
            assert mock_process.called
            call_args = mock_process.call_args
            assert call_args[0][0] == mock_message
            assert call_args[0][1] == mock_state
            assert call_args[0][2] == "session-123"

    @pytest.mark.asyncio
    async def test_user_message_handler_no_session_id(self, mock_message, mock_state):
        """Тест user_message_handler без session_id (строки 303-306)"""
        mock_state.get_data = AsyncMock(return_value={})

        with (
            patch("smart_bot_factory.handlers.handlers.ctx") as mock_ctx,
            patch("smart_bot_factory.utils.debug_routing.debug_user_state"),
            patch("smart_bot_factory.handlers.handlers.send_message") as mock_send,
        ):
            mock_ctx.conversation_manager = AsyncMock()
            mock_ctx.conversation_manager.is_user_in_admin_chat = AsyncMock(return_value=None)

            await user_message_handler(mock_message, mock_state)

            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_user_message_handler_exception(self, mock_message, mock_state):
        """Тест обработки исключения в user_message_handler (строки 311-316)"""
        with (
            patch("smart_bot_factory.handlers.handlers.ctx") as mock_ctx,
            patch("smart_bot_factory.utils.debug_routing.debug_user_state", side_effect=Exception("Error")),
            patch("smart_bot_factory.handlers.handlers.send_message") as mock_send,
        ):
            mock_ctx.conversation_manager = AsyncMock()
            mock_ctx.conversation_manager.is_user_in_admin_chat = AsyncMock(side_effect=Exception("Error"))

            await user_message_handler(mock_message, mock_state)

            mock_send.assert_called_once()


class TestCatchAllHandler:
    """Тесты для catch_all_handler"""

    @pytest.mark.asyncio
    async def test_catch_all_handler_admin(self, mock_message, mock_state):
        """Тест catch_all_handler для админа (строки 319-335)"""
        with (
            patch("smart_bot_factory.handlers.handlers.ctx") as mock_ctx,
            patch("smart_bot_factory.utils.debug_routing.debug_user_state"),
        ):
            mock_ctx.admin_manager = Mock()
            mock_ctx.admin_manager.is_admin = Mock(return_value=True)
            mock_state.get_state = AsyncMock(return_value="some_state")

            await catch_all_handler(mock_message, mock_state)

            mock_message.answer.assert_called_once()
            assert "help" in mock_message.answer.call_args[0][0].lower()

    @pytest.mark.asyncio
    async def test_catch_all_handler_user(self, mock_message, mock_state):
        """Тест catch_all_handler для пользователя"""
        with (
            patch("smart_bot_factory.handlers.handlers.ctx") as mock_ctx,
            patch("smart_bot_factory.utils.debug_routing.debug_user_state"),
        ):
            mock_ctx.admin_manager = Mock()
            mock_ctx.admin_manager.is_admin = Mock(return_value=False)
            mock_state.get_state = AsyncMock(return_value="some_state")

            await catch_all_handler(mock_message, mock_state)

            mock_message.answer.assert_called_once()
            assert "start" in mock_message.answer.call_args[0][0].lower()


class TestProcessUserMessage:
    """Тесты для process_user_message"""

    @pytest.mark.asyncio
    async def test_process_user_message_success(self, mock_message, mock_state):
        """Тест успешной обработки сообщения (строки 341-448)"""
        mock_state.get_data = AsyncMock(return_value={})

        with (
            patch("smart_bot_factory.handlers.handlers.ctx") as mock_ctx,
            patch("smart_bot_factory.handlers.handlers._validate_message", return_value=True),
            patch("smart_bot_factory.handlers.handlers.send_chat_action_for_files"),
            patch("smart_bot_factory.handlers.handlers.send_message_with_files") as mock_send,
            patch("smart_bot_factory.handlers.handlers.send_files_before_message"),
            patch("smart_bot_factory.handlers.handlers.send_files_after_message"),
            patch("smart_bot_factory.handlers.handlers.collect_files_for_message", return_value=([], [], [], [])),
        ):
            # Мокируем только внешние зависимости
            mock_ctx.supabase_client = AsyncMock()
            mock_ctx.supabase_client.add_message = AsyncMock()
            mock_ctx.prompt_loader = AsyncMock()
            mock_ctx.prompt_loader.load_system_prompt = AsyncMock(return_value="system prompt")
            mock_ctx.prompt_loader.load_final_instructions = AsyncMock(return_value="")
            mock_ctx.memory_manager = AsyncMock()
            mock_ctx.memory_manager.get_memory_messages = AsyncMock(return_value=[])
            mock_ctx.openai_client = Mock()
            mock_ctx.openai_client.estimate_tokens = Mock(return_value=10)

            # Мокируем ответ от OpenAI
            ai_response = Mock()
            ai_response.user_message = "response"
            ai_response.service_info = {"события": []}
            mock_ctx.openai_client.get_completion = AsyncMock(return_value=ai_response)

            mock_ctx.message_hooks = {}
            mock_ctx.config = Mock()
            mock_ctx.config.DEBUG_MODE = False
            mock_ctx.config.MESSAGE_PARSE_MODE = "HTML"

            # Мокируем process_events для обработки событий
            with (
                patch("smart_bot_factory.utils.bot_utils.process_events", new_callable=AsyncMock, return_value=True),
                patch("smart_bot_factory.utils.bot_utils.process_file_events", new_callable=AsyncMock, return_value=[]),
                patch("smart_bot_factory.handlers.utils.ctx", mock_ctx),
            ):
                await process_user_message(mock_message, mock_state, "session-123")

                mock_ctx.supabase_client.add_message.assert_called()
                mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_user_message_validation_failed(self, mock_message, mock_state):
        """Тест process_user_message с неудачной валидацией (строки 348-349)"""
        with (
            patch("smart_bot_factory.handlers.handlers.ctx") as mock_ctx,
            patch("smart_bot_factory.handlers.handlers._validate_message", return_value=False),
        ):
            mock_ctx.message_hooks = {}

            await process_user_message(mock_message, mock_state, "session-123")

            # Не должно быть вызовов сохранения сообщения

    @pytest.mark.asyncio
    async def test_process_user_message_skip_send(self, mock_message, mock_state):
        """Тест process_user_message с пропуском отправки (строки 420-422)"""
        with (
            patch("smart_bot_factory.handlers.handlers.ctx") as mock_ctx,
            patch("smart_bot_factory.handlers.handlers._validate_message", return_value=True),
            patch("smart_bot_factory.handlers.handlers.send_chat_action_for_files"),
            patch("smart_bot_factory.handlers.handlers.send_files_before_message"),
            patch("smart_bot_factory.handlers.handlers.send_message_with_files") as mock_send,
        ):
            # Мокируем только внешние зависимости
            mock_ctx.supabase_client = AsyncMock()
            mock_ctx.supabase_client.add_message = AsyncMock()
            mock_ctx.prompt_loader = AsyncMock()
            mock_ctx.prompt_loader.load_system_prompt = AsyncMock(return_value="system prompt")
            mock_ctx.prompt_loader.load_final_instructions = AsyncMock(return_value="")
            mock_ctx.memory_manager = AsyncMock()
            mock_ctx.memory_manager.get_memory_messages = AsyncMock(return_value=[])
            mock_ctx.openai_client = Mock()
            mock_ctx.openai_client.estimate_tokens = Mock(return_value=10)

            # Мокируем ответ от OpenAI с событиями, которые запретят отправку
            ai_response = Mock()
            ai_response.user_message = "response"
            ai_response.service_info = {"события": [{"type": "skip_send"}]}
            mock_ctx.openai_client.get_completion = AsyncMock(return_value=ai_response)

            mock_ctx.message_hooks = {}
            mock_ctx.config = Mock()
            mock_ctx.config.DEBUG_MODE = False
            mock_ctx.config.MESSAGE_PARSE_MODE = "HTML"

            # Мокируем process_events чтобы вернуть False (запретить отправку)
            # Важно: process_events должен быть замокан до вызова _process_metadata
            mock_process_events = AsyncMock(return_value=False)
            with (
                patch("smart_bot_factory.handlers.message_processing.process_events", mock_process_events),
                patch("smart_bot_factory.utils.bot_utils.process_file_events", new_callable=AsyncMock, return_value=[]),
                patch("smart_bot_factory.handlers.utils.ctx", mock_ctx),
            ):
                await process_user_message(mock_message, mock_state, "session-123")

                # send_message_with_files не должен вызываться
                mock_send.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_user_message_exception(self, mock_message, mock_state):
        """Тест обработки исключения в process_user_message (строки 450-453)"""
        with (
            patch("smart_bot_factory.handlers.handlers.ctx") as mock_ctx,
            patch("smart_bot_factory.handlers.handlers._validate_message", side_effect=Exception("Error")),
            patch("smart_bot_factory.handlers.handlers.send_critical_error_message") as mock_error,
        ):
            mock_ctx.message_hooks = {}

            await process_user_message(mock_message, mock_state, "session-123")

            mock_error.assert_called_once_with(mock_message)
