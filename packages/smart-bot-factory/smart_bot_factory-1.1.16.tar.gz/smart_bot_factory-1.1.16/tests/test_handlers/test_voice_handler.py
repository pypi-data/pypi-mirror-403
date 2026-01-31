"""Тесты для voice_handler"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, User, Voice

from smart_bot_factory.handlers.states import UserStates
from smart_bot_factory.handlers.voice_handler import (
    voice_edit_handler,
    voice_edit_text_handler,
    voice_handler,
    voice_retry_handler,
    voice_send_handler,
)


class TestVoiceHandler:
    """Тесты для обработчика голосовых сообщений"""

    @pytest.fixture
    def mock_message(self):
        """Фикстура для мок сообщения"""
        message = Mock(spec=Message)
        message.from_user = Mock(spec=User)
        message.from_user.id = 123456789
        message.voice = Mock(spec=Voice)
        message.voice.file_id = "voice_file_id"
        message.voice.duration = 10
        message.answer = AsyncMock()
        return message

    @pytest.fixture
    def mock_state(self):
        """Фикстура для мок состояния FSM"""
        state = AsyncMock(spec=FSMContext)
        state.get_state = AsyncMock(return_value=UserStates.waiting_for_message)
        state.get_data = AsyncMock(return_value={"session_id": "session-123"})
        state.update_data = AsyncMock()
        state.set_state = AsyncMock()
        return state

    @pytest.fixture
    def setup_context(self):
        """Фикстура для настройки контекста"""
        with patch("smart_bot_factory.handlers.voice_handler.ctx") as mock_ctx:
            mock_ctx.admin_manager = Mock()
            mock_ctx.admin_manager.is_admin = Mock(return_value=False)
            mock_ctx.bot = Mock()
            mock_ctx.bot.get_file = AsyncMock(return_value=Mock(file_path="test.ogg"))
            mock_ctx.bot.download_file = AsyncMock()
            mock_ctx.openai_client = Mock()
            mock_ctx.openai_client.transcribe_audio = AsyncMock(return_value="Распознанный текст")
            mock_ctx.supabase_client = Mock()
            mock_ctx.supabase_client.get_active_session = AsyncMock(return_value={"id": "session-123"})
            yield mock_ctx

    @pytest.mark.asyncio
    async def test_voice_handler_basic(self, mock_message, mock_state, setup_context):
        """Тест базового обработчика голосового сообщения"""
        processing_msg = Mock()
        processing_msg.delete = AsyncMock()
        mock_message.answer.return_value = processing_msg

        with (
            patch("smart_bot_factory.handlers.voice_handler.tempfile") as mock_tempfile,
            patch("smart_bot_factory.handlers.voice_handler.Path") as mock_path_class,
        ):
            mock_tempfile.gettempdir.return_value = "C:\\temp"

            # Создаем мок для Path объекта
            mock_path_instance = Mock()
            mock_path_instance.mkdir = Mock()
            mock_path_instance.exists = Mock(return_value=False)
            mock_path_instance.iterdir = Mock(return_value=iter([]))
            mock_path_instance.rmdir = Mock()
            mock_path_instance.unlink = Mock()
            mock_path_instance.__str__ = Mock(return_value="C:\\temp\\smart_bot_factory_audio\\123456789_1234567890.ogg")

            # Мокируем операцию / (__truediv__)
            mock_path_instance.__truediv__ = Mock(return_value=mock_path_instance)

            # Path() возвращает мок-объект
            mock_path_class.return_value = mock_path_instance
            await voice_handler(mock_message, mock_state)

        setup_context.openai_client.transcribe_audio.assert_called_once()
        mock_state.set_state.assert_called_with(UserStates.voice_confirmation)

    @pytest.mark.asyncio
    async def test_voice_handler_admin_mode(self, mock_message, mock_state, setup_context):
        """Тест что админ в режиме админа не обрабатывает голос"""
        setup_context.admin_manager.is_admin.return_value = True
        setup_context.admin_manager.is_in_admin_mode.return_value = True

        await voice_handler(mock_message, mock_state)

        setup_context.openai_client.transcribe_audio.assert_not_called()

    @pytest.mark.asyncio
    async def test_voice_handler_no_recognition(self, mock_message, mock_state, setup_context):
        """Тест обработки когда распознавание не удалось"""
        setup_context.openai_client.transcribe_audio = AsyncMock(return_value="")

        processing_msg = Mock()
        processing_msg.edit_text = AsyncMock()
        mock_message.answer.return_value = processing_msg

        with (
            patch("smart_bot_factory.handlers.voice_handler.tempfile") as mock_tempfile,
            patch("smart_bot_factory.handlers.voice_handler.Path") as mock_path_class,
        ):
            mock_tempfile.gettempdir.return_value = "C:\\temp"

            # Создаем мок для Path объекта
            mock_path_instance = Mock()
            mock_path_instance.mkdir = Mock()
            mock_path_instance.exists = Mock(return_value=False)
            mock_path_instance.iterdir = Mock(return_value=iter([]))
            mock_path_instance.rmdir = Mock()
            mock_path_instance.unlink = Mock()
            mock_path_instance.__str__ = Mock(return_value="C:\\temp\\smart_bot_factory_audio\\123456789_1234567890.ogg")

            # Мокируем операцию / (__truediv__)
            mock_path_instance.__truediv__ = Mock(return_value=mock_path_instance)

            # Path() возвращает мок-объект
            mock_path_class.return_value = mock_path_instance
            await voice_handler(mock_message, mock_state)

        processing_msg.edit_text.assert_called()
        call_args = processing_msg.edit_text.call_args[0][0]
        assert "не удалось" in call_args.lower() or "распознать" in call_args.lower()


class TestVoiceSendHandler:
    """Тесты для обработчика отправки голосового сообщения"""

    @pytest.fixture
    def mock_callback(self):
        """Фикстура для мок callback"""
        callback = Mock()
        callback.from_user = Mock(spec=User)
        callback.from_user.id = 123456789
        callback.answer = AsyncMock()
        callback.message = Mock(spec=Message)
        callback.message.delete = AsyncMock()
        return callback

    @pytest.fixture
    def mock_state(self):
        """Фикстура для мок состояния FSM"""
        state = AsyncMock(spec=FSMContext)
        state.get_data = AsyncMock(return_value={"voice_recognized_text": "Распознанный текст", "session_id": "session-123"})
        state.set_state = AsyncMock()
        state.update_data = AsyncMock()
        return state

    @pytest.mark.asyncio
    async def test_voice_send_handler(self, mock_callback, mock_state):
        """Тест обработчика отправки голосового сообщения"""
        with patch("smart_bot_factory.handlers.handlers.process_user_message") as mock_process:
            await voice_send_handler(mock_callback, mock_state)

            mock_process.assert_called_once()
            mock_state.set_state.assert_called_with(UserStates.waiting_for_message)

    @pytest.mark.asyncio
    async def test_voice_send_handler_no_text(self, mock_callback, mock_state):
        """Тест обработчика когда текст не найден"""
        mock_state.get_data.return_value = {"session_id": "session-123"}

        await voice_send_handler(mock_callback, mock_state)

        mock_callback.answer.assert_called()


class TestVoiceEditHandler:
    """Тесты для обработчика редактирования голосового сообщения"""

    @pytest.fixture
    def mock_callback(self):
        """Фикстура для мок callback"""
        callback = Mock()
        callback.answer = AsyncMock()
        callback.message = Mock(spec=Message)
        callback.message.edit_text = AsyncMock()
        return callback

    @pytest.fixture
    def mock_state(self):
        """Фикстура для мок состояния FSM"""
        state = AsyncMock(spec=FSMContext)
        state.get_data = AsyncMock(return_value={"voice_recognized_text": "Распознанный текст"})
        state.set_state = AsyncMock()
        return state

    @pytest.mark.asyncio
    async def test_voice_edit_handler(self, mock_callback, mock_state):
        """Тест обработчика редактирования"""
        await voice_edit_handler(mock_callback, mock_state)

        mock_state.set_state.assert_called_with(UserStates.voice_editing)
        mock_callback.message.edit_text.assert_called_once()


class TestVoiceRetryHandler:
    """Тесты для обработчика повтора голосового сообщения"""

    @pytest.fixture
    def mock_callback(self):
        """Фикстура для мок callback"""
        callback = Mock()
        callback.answer = AsyncMock()
        callback.message = Mock(spec=Message)
        callback.message.delete = AsyncMock()
        callback.message.answer = AsyncMock()
        return callback

    @pytest.fixture
    def mock_state(self):
        """Фикстура для мок состояния FSM"""
        state = AsyncMock(spec=FSMContext)
        state.set_state = AsyncMock()
        state.update_data = AsyncMock()
        return state

    @pytest.mark.asyncio
    async def test_voice_retry_handler(self, mock_callback, mock_state):
        """Тест обработчика повтора"""
        await voice_retry_handler(mock_callback, mock_state)

        mock_state.set_state.assert_called_with(UserStates.waiting_for_message)
        mock_callback.message.answer.assert_called_once()


class TestVoiceEditTextHandler:
    """Тесты для обработчика отредактированного текста"""

    @pytest.fixture
    def mock_message(self):
        """Фикстура для мок сообщения"""
        message = Mock(spec=Message)
        message.text = "Отредактированный текст"
        message.answer = AsyncMock()
        return message

    @pytest.fixture
    def mock_state(self):
        """Фикстура для мок состояния FSM"""
        state = AsyncMock(spec=FSMContext)
        state.get_data = AsyncMock(return_value={"session_id": "session-123"})
        state.set_state = AsyncMock()
        state.update_data = AsyncMock()
        return state

    @pytest.mark.asyncio
    async def test_voice_edit_text_handler(self, mock_message, mock_state):
        """Тест обработчика отредактированного текста"""
        with patch("smart_bot_factory.handlers.handlers.process_user_message") as mock_process:
            await voice_edit_text_handler(mock_message, mock_state)

            mock_process.assert_called_once()
            mock_state.set_state.assert_called_with(UserStates.waiting_for_message)

    @pytest.mark.asyncio
    async def test_voice_edit_text_handler_empty(self, mock_message, mock_state):
        """Тест обработчика с пустым текстом"""
        mock_message.text = "   "

        await voice_edit_text_handler(mock_message, mock_state)

        mock_message.answer.assert_called()
        call_args = mock_message.answer.call_args[0][0]
        assert "пустым" in call_args.lower()
