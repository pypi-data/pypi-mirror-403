"""Тесты для message_sender"""

from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from smart_bot_factory.message.message_sender import (
    get_users_by_stage_stats,
    send_message,
    send_message_by_ai,
    send_message_by_human,
    send_message_to_users_by_stage,
)


class TestSendMessageByAI:
    """Тесты для функции send_message_by_ai"""

    @pytest.fixture
    def mock_ctx(self):
        """Фикстура для мок контекста"""
        ctx = Mock()
        ctx.supabase_client = Mock()
        ctx.prompt_loader = Mock()
        ctx.openai_client = Mock()
        ctx.memory_manager = Mock()
        ctx.config = Mock()
        ctx.config.DEBUG_MODE = False
        ctx.bot = Mock()
        ctx.message_hooks = {}
        return ctx

    @pytest.mark.asyncio
    async def test_send_message_by_ai_success(self, mock_ctx):
        """Тест успешной отправки сообщения через ИИ"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            # Мокируем только внешние зависимости
            mock_ctx.supabase_client.get_active_session = AsyncMock(return_value={"id": "session-123"})
            mock_ctx.prompt_loader.load_system_prompt = AsyncMock(return_value="Системный промпт")
            mock_ctx.prompt_loader.load_final_instructions = AsyncMock(return_value="")
            mock_ctx.supabase_client.add_message = AsyncMock()
            mock_ctx.supabase_client.update_session_stage = AsyncMock()
            mock_ctx.memory_manager.get_memory_messages = AsyncMock(return_value=[])
            mock_ctx.openai_client.estimate_tokens = Mock(return_value=100)
            mock_ctx.bot.send_message = AsyncMock()

            # Мокируем ответ от OpenAI
            ai_response = Mock()
            ai_response.user_message = "Ответ ИИ"
            ai_response.service_info = {"события": []}
            mock_ctx.openai_client.get_completion = AsyncMock(return_value=ai_response)

            # Мокируем process_events для обработки событий
            with (
                patch("smart_bot_factory.utils.bot_utils.process_events", new_callable=AsyncMock, return_value=True),
                patch("smart_bot_factory.utils.bot_utils.process_file_events", new_callable=AsyncMock, return_value=[]),
            ):
                result = await send_message_by_ai(user_id=123456, message_text="Привет")

                assert result["status"] == "success"
                assert result["user_id"] == 123456
                assert result["response_text"] == "Ответ ИИ"
                assert result["tokens_used"] == 100
                assert result["events_processed"] == 0
                assert "processing_time_ms" in result

                # Проверяем, что сообщение было отправлено
                mock_ctx.bot.send_message.assert_called_once()
                call_args = mock_ctx.bot.send_message.call_args
                assert call_args.kwargs["chat_id"] == 123456
                assert call_args.kwargs["text"] == "Ответ ИИ"

                # Проверяем, что сообщения были сохранены в БД
                assert mock_ctx.supabase_client.add_message.call_count == 2  # Пользователь и ассистент

    @pytest.mark.asyncio
    async def test_send_message_by_ai_no_session(self, mock_ctx):
        """Тест отправки сообщения без активной сессии"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            mock_ctx.supabase_client.get_active_session = AsyncMock(return_value=None)

            result = await send_message_by_ai(user_id=123456, message_text="Привет")

            assert result["status"] == "error"
            assert "Активная сессия не найдена" in result["error"]

    @pytest.mark.asyncio
    async def test_send_message_by_ai_with_session_id(self, mock_ctx):
        """Тест отправки сообщения с указанным session_id"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            # Мокируем только внешние зависимости
            mock_ctx.prompt_loader.load_system_prompt = AsyncMock(return_value="Системный промпт")
            mock_ctx.prompt_loader.load_final_instructions = AsyncMock(return_value="")
            mock_ctx.supabase_client.add_message = AsyncMock()
            mock_ctx.supabase_client.update_session_stage = AsyncMock()
            mock_ctx.supabase_client.update_session_service_info = AsyncMock()
            mock_ctx.memory_manager.get_memory_messages = AsyncMock(return_value=[])
            mock_ctx.openai_client.estimate_tokens = Mock(return_value=100)
            mock_ctx.bot.send_message = AsyncMock()

            # Мокируем ответ от OpenAI
            ai_response = Mock()
            ai_response.user_message = "Ответ ИИ"
            ai_response.service_info = {}
            mock_ctx.openai_client.get_completion = AsyncMock(return_value=ai_response)

            # Мокируем process_events
            with (
                patch("smart_bot_factory.utils.bot_utils.process_events", new_callable=AsyncMock, return_value=True),
                patch("smart_bot_factory.utils.bot_utils.process_file_events", new_callable=AsyncMock, return_value=[]),
            ):
                result = await send_message_by_ai(user_id=123456, message_text="Привет", session_id="session-123")

                # Не должен вызывать get_active_session
                mock_ctx.supabase_client.get_active_session.assert_not_called()

                assert result["status"] == "success"
                assert result["user_id"] == 123456

    @pytest.mark.asyncio
    async def test_send_message_by_ai_with_events(self, mock_ctx):
        """Тест отправки сообщения с событиями"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            # Мокируем только внешние зависимости
            mock_ctx.supabase_client.get_active_session = AsyncMock(return_value={"id": "session-123"})
            mock_ctx.prompt_loader.load_system_prompt = AsyncMock(return_value="Системный промпт")
            mock_ctx.prompt_loader.load_final_instructions = AsyncMock(return_value="")
            mock_ctx.supabase_client.add_message = AsyncMock()
            mock_ctx.supabase_client.update_session_stage = AsyncMock()
            mock_ctx.supabase_client.update_session_service_info = AsyncMock()
            mock_ctx.memory_manager.get_memory_messages = AsyncMock(return_value=[])
            mock_ctx.openai_client.estimate_tokens = Mock(return_value=100)
            mock_ctx.bot.send_message = AsyncMock()

            # Мокируем ответ от OpenAI с событиями
            ai_response = Mock()
            ai_response.user_message = "Ответ ИИ"
            ai_response.service_info = {"события": [{"тип": "телефон", "инфо": "+1234567890"}], "этап": "consult"}
            mock_ctx.openai_client.get_completion = AsyncMock(return_value=ai_response)

            # Мокируем process_events - события обрабатываются, но ответ отправляется
            with (
                patch("smart_bot_factory.utils.bot_utils.process_events", new_callable=AsyncMock, return_value=True),
                patch("smart_bot_factory.utils.bot_utils.process_file_events", new_callable=AsyncMock, return_value=[]),
            ):
                result = await send_message_by_ai(user_id=123456, message_text="Привет")

                assert result["status"] == "success"
                assert result["user_id"] == 123456
                assert result["events_processed"] == 1  # Одно событие обработано
                mock_ctx.bot.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_message_by_ai_error(self, mock_ctx):
        """Тест обработки ошибки"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            mock_ctx.supabase_client.get_active_session = AsyncMock(side_effect=Exception("Ошибка"))

            result = await send_message_by_ai(user_id=123456, message_text="Привет")

            assert result["status"] == "error"
            assert "error" in result


class TestSendMessageByHuman:
    """Тесты для функции send_message_by_human"""

    @pytest.fixture
    def mock_ctx(self):
        """Фикстура для мок контекста"""
        ctx = Mock()
        ctx.bot = Mock()
        ctx.supabase_client = Mock()
        return ctx

    @pytest.mark.asyncio
    async def test_send_message_by_human_text(self, mock_ctx):
        """Тест отправки текстового сообщения"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            mock_message = Mock()
            mock_message.message_id = 123
            mock_ctx.bot.send_message = AsyncMock(return_value=mock_message)
            mock_ctx.supabase_client.add_message = AsyncMock()

            result = await send_message_by_human(user_id=123456, message_text="Привет от человека")

            assert result["status"] == "success"
            assert result["user_id"] == 123456
            assert result["message_id"] == 123
            assert result["saved_to_db"] is False  # session_id не указан

    @pytest.mark.asyncio
    async def test_send_message_by_human_with_session(self, mock_ctx):
        """Тест отправки сообщения с сохранением в БД"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            mock_message = Mock()
            mock_message.message_id = 123
            mock_ctx.bot.send_message = AsyncMock(return_value=mock_message)
            mock_ctx.supabase_client.add_message = AsyncMock()

            result = await send_message_by_human(user_id=123456, message_text="Привет", session_id="session-123")

            assert result["status"] == "success"
            assert result["saved_to_db"] is True
            mock_ctx.supabase_client.add_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_message_by_human_with_photo(self, mock_ctx):
        """Тест отправки фото с подписью"""
        with (
            patch("smart_bot_factory.utils.context.ctx", mock_ctx),
            patch("smart_bot_factory.message.message_sender.root", Path("/test")),
            patch("pathlib.Path.exists", return_value=True),
        ):
            mock_message = Mock()
            mock_message.message_id = 123
            mock_ctx.bot.send_photo = AsyncMock(return_value=mock_message)
            mock_ctx.supabase_client.add_message = AsyncMock()

            result = await send_message_by_human(user_id=123456, message_text="Подпись к фото", photo="test.jpg")

            assert result["status"] == "success"
            assert result["has_photo"] is True
            mock_ctx.bot.send_photo.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_message_by_human_photo_not_found(self, mock_ctx):
        """Тест отправки фото когда файл не найден"""
        with (
            patch("smart_bot_factory.utils.context.ctx", mock_ctx),
            patch("smart_bot_factory.message.message_sender.root", Path("/test")),
            patch("pathlib.Path.exists", return_value=False),
        ):
            result = await send_message_by_human(user_id=123456, message_text="Подпись", photo="nonexistent.jpg")

            assert result["status"] == "error"
            assert "не найден" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_send_message_by_human_error(self, mock_ctx):
        """Тест обработки ошибки"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            mock_ctx.bot.send_message = AsyncMock(side_effect=Exception("Ошибка"))

            result = await send_message_by_human(user_id=123456, message_text="Привет")

            assert result["status"] == "error"
            assert "error" in result


class TestSendMessageToUsersByStage:
    """Тесты для функции send_message_to_users_by_stage"""

    @pytest.fixture
    def mock_ctx(self):
        """Фикстура для мок контекста"""
        ctx = Mock()
        ctx.config = Mock()
        ctx.config.BOT_ID = "test-bot"
        ctx.supabase_client = Mock()
        ctx.bot = Mock()
        return ctx

    @pytest.mark.asyncio
    async def test_send_message_to_users_by_stage_no_users(self, mock_ctx):
        """Тест отправки когда пользователей не найдено"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            mock_table = Mock()
            mock_query = Mock()
            mock_query.select.return_value = mock_query
            mock_query.eq.return_value = mock_query
            mock_query.order.return_value = mock_query
            mock_response = Mock()
            mock_response.data = []
            mock_query.execute.return_value = mock_response
            mock_table.select.return_value = mock_query
            mock_ctx.supabase_client.client.table.return_value = mock_table

            result = await send_message_to_users_by_stage(stage="introduction", message_text="Привет", bot_id="test-bot")

            assert result["status"] == "success"
            assert result["users_found"] == 0
            assert result["messages_sent"] == 0

    @pytest.mark.asyncio
    async def test_send_message_to_users_by_stage_with_users(self, mock_ctx):
        """Тест отправки сообщений пользователям"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            mock_table = Mock()
            mock_query = Mock()
            mock_query.select.return_value = mock_query
            mock_query.eq.return_value = mock_query
            mock_query.order.return_value = mock_query
            mock_response = Mock()
            mock_response.data = [
                {"user_id": 123456, "id": "session-1", "current_stage": "introduction"},
                {"user_id": 789012, "id": "session-2", "current_stage": "introduction"},
            ]
            mock_query.execute.return_value = mock_response
            mock_table.select.return_value = mock_query
            mock_ctx.supabase_client.client.table.return_value = mock_table
            mock_ctx.bot.send_message = AsyncMock()
            mock_ctx.supabase_client.add_message = AsyncMock()

            result = await send_message_to_users_by_stage(stage="introduction", message_text="Привет", bot_id="test-bot")

            assert result["status"] == "success"
            assert result["users_found"] == 2
            assert result["messages_sent"] == 2

    @pytest.mark.asyncio
    async def test_send_message_to_users_by_stage_with_photo(self, mock_ctx):
        """Тест отправки фото пользователям"""
        with (
            patch("smart_bot_factory.utils.context.ctx", mock_ctx),
            patch("smart_bot_factory.message.message_sender.root", Path("/test")),
            patch("pathlib.Path.exists", return_value=True),
        ):
            mock_table = Mock()
            mock_query = Mock()
            mock_query.select.return_value = mock_query
            mock_query.eq.return_value = mock_query
            mock_query.order.return_value = mock_query
            mock_response = Mock()
            mock_response.data = [
                {"user_id": 123456, "id": "session-1", "current_stage": "introduction"},
            ]
            mock_query.execute.return_value = mock_response
            mock_table.select.return_value = mock_query
            mock_ctx.supabase_client.client.table.return_value = mock_table
            mock_ctx.bot.send_photo = AsyncMock()
            mock_ctx.supabase_client.add_message = AsyncMock()

            result = await send_message_to_users_by_stage(stage="introduction", message_text="Подпись", bot_id="test-bot", photo="test.jpg")

            assert result["status"] == "success"
            mock_ctx.bot.send_photo.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_message_to_users_by_stage_error(self, mock_ctx):
        """Тест обработки ошибки"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            mock_ctx.supabase_client.client.table.side_effect = Exception("Ошибка")

            result = await send_message_to_users_by_stage(stage="introduction", message_text="Привет", bot_id="test-bot")

            assert result["status"] == "error"
            assert "error" in result


class TestGetUsersByStageStats:
    """Тесты для функции get_users_by_stage_stats"""

    @pytest.fixture
    def mock_ctx(self):
        """Фикстура для мок контекста"""
        ctx = Mock()
        ctx.config = Mock()
        ctx.config.BOT_ID = "test-bot"
        ctx.supabase_client = Mock()
        return ctx

    @pytest.mark.asyncio
    async def test_get_users_by_stage_stats_success(self, mock_ctx):
        """Тест получения статистики по стадиям"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            mock_table = Mock()
            mock_query = Mock()
            mock_query.select.return_value = mock_query
            mock_query.eq.return_value = mock_query
            mock_query.order.return_value = mock_query
            mock_response = Mock()
            mock_response.data = [
                {"user_id": 123456, "current_stage": "introduction"},
                {"user_id": 789012, "current_stage": "introduction"},
                {"user_id": 345678, "current_stage": "consult"},
            ]
            mock_query.execute.return_value = mock_response
            mock_table.select.return_value = mock_query
            mock_ctx.supabase_client.client.table.return_value = mock_table

            result = await get_users_by_stage_stats(bot_id="test-bot")

            assert result["status"] == "success"
            assert result["total_active_users"] == 3
            assert "stages" in result
            assert result["stages"]["introduction"] == 2
            assert result["stages"]["consult"] == 1

    @pytest.mark.asyncio
    async def test_get_users_by_stage_stats_no_bot_id(self, mock_ctx):
        """Тест получения статистики без bot_id"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            mock_ctx.config = None

            result = await get_users_by_stage_stats()

            assert result["status"] == "error"
            assert "bot_id" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_get_users_by_stage_stats_error(self, mock_ctx):
        """Тест обработки ошибки"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            mock_ctx.supabase_client.client.table.side_effect = Exception("Ошибка")

            result = await get_users_by_stage_stats(bot_id="test-bot")

            assert result["status"] == "error"
            assert "error" in result


class TestSendMessage:
    """Тесты для функции send_message"""

    @pytest.fixture
    def mock_message(self):
        """Фикстура для мок сообщения"""
        message = Mock()
        message.from_user.id = 123456
        message.answer = AsyncMock()
        message.answer_media_group = AsyncMock()
        return message

    @pytest.fixture
    def mock_ctx(self):
        """Фикстура для мок контекста"""
        ctx = Mock()
        ctx.config = Mock()
        ctx.config.PROMT_FILES_DIR = Path("bots/test/prompts")
        ctx.supabase_client = Mock()
        ctx.supabase_client.get_sent_files = AsyncMock(return_value=[])
        ctx.supabase_client.get_sent_directories = AsyncMock(return_value=[])
        return ctx

    @pytest.mark.asyncio
    async def test_send_message_text_only(self, mock_message, mock_ctx):
        """Тест отправки только текста"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            mock_result = Mock()
            mock_message.answer = AsyncMock(return_value=mock_result)

            result = await send_message(message=mock_message, text="Привет", supabase_client=mock_ctx.supabase_client)

            assert result == mock_result
            mock_message.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_message_with_files(self, mock_message, mock_ctx):
        """Тест отправки сообщения с файлами"""
        with (
            patch("smart_bot_factory.utils.context.ctx", mock_ctx),
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.is_file", return_value=True),
            patch("pathlib.Path.resolve", return_value=Path("files")),
        ):
            mock_result = Mock()
            mock_message.answer = AsyncMock(return_value=mock_result)
            mock_message.answer_media_group = AsyncMock()

            result = await send_message(message=mock_message, text="Привет", supabase_client=mock_ctx.supabase_client, files_list=["test.jpg"])

            assert result == mock_result

    @pytest.mark.asyncio
    async def test_send_message_with_directories(self, mock_message, mock_ctx):
        """Тест отправки сообщения с каталогами"""
        with (
            patch("smart_bot_factory.utils.context.ctx", mock_ctx),
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.is_dir", return_value=True),
            patch("pathlib.Path.iterdir", return_value=[Path("file1.jpg"), Path("file2.jpg")]),
            patch("pathlib.Path.is_file", return_value=True),
            patch("pathlib.Path.resolve", return_value=Path("files")),
        ):
            mock_result = Mock()
            mock_message.answer = AsyncMock(return_value=mock_result)
            mock_message.answer_media_group = AsyncMock()

            result = await send_message(message=mock_message, text="Привет", supabase_client=mock_ctx.supabase_client, directories_list=["photos"])

            assert result == mock_result

    @pytest.mark.asyncio
    async def test_send_message_empty_text(self, mock_message, mock_ctx):
        """Тест отправки сообщения с пустым текстом"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            mock_result = Mock()
            mock_message.answer = AsyncMock(return_value=mock_result)

            await send_message(message=mock_message, text="", supabase_client=mock_ctx.supabase_client)

            # Должен быть установлен fallback текст
            # Проверяем что answer был вызван
            assert mock_message.answer.called
            # Проверяем что был вызван с fallback текстом
            call_args = mock_message.answer.call_args
            if call_args:
                # Получаем текст из аргументов
                if call_args.kwargs and "text" in call_args.kwargs:
                    call_text = call_args.kwargs["text"]
                elif call_args.args and len(call_args.args) > 0:
                    call_text = call_args.args[0]
                else:
                    call_text = ""
                # Проверяем что текст содержит fallback сообщение
                assert "Ошибка" in call_text or "ошибка" in call_text.lower()

    @pytest.mark.asyncio
    async def test_send_message_bot_blocked(self, mock_message, mock_ctx):
        """Тест обработки блокировки бота"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            mock_message.answer = AsyncMock(side_effect=Exception("Forbidden: bot was blocked by the user"))

            result = await send_message(message=mock_message, text="Привет", supabase_client=mock_ctx.supabase_client)

            assert result is None

    @pytest.mark.asyncio
    async def test_send_message_error(self, mock_message, mock_ctx):
        """Тест обработки ошибки"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            mock_message.answer = AsyncMock(side_effect=Exception("Ошибка"))
            mock_message.answer.side_effect = [Exception("Ошибка"), Mock()]  # Первый вызов - ошибка, второй - успех

            # Мокаем fallback вызов
            mock_fallback = Mock()
            mock_message.answer = AsyncMock(side_effect=[Exception("Ошибка"), mock_fallback])

            await send_message(message=mock_message, text="Привет", supabase_client=mock_ctx.supabase_client)

            # Должен быть вызван fallback
            assert mock_message.answer.call_count >= 1
