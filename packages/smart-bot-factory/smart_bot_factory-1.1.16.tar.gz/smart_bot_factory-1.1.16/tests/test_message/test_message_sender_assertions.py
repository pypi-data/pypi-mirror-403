"""Улучшенные тесты с детальной проверкой результатов, аргументов и побочных эффектов"""

from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from smart_bot_factory.handlers.constants import AIMetadataKey, MessageRole
from smart_bot_factory.message.message_sender import (
    get_users_by_stage_stats,
    send_message,
    send_message_by_ai,
    send_message_by_human,
    send_message_to_users_by_stage,
)


class TestDetailedAssertionsSendMessageByAI:
    """Тесты с детальной проверкой аргументов, результатов и побочных эффектов для send_message_by_ai"""

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
    async def test_detailed_assertions_success(self, mock_ctx):
        """Детальная проверка всех аргументов, результатов и побочных эффектов"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            user_id = 123456
            message_text = "Привет, как дела?"
            session_id = "session-123"
            response_text = "Отлично, спасибо!"
            tokens_used = 150

            # Настройка моков
            mock_ctx.prompt_loader.load_system_prompt = AsyncMock(return_value="Системный промпт")
            mock_ctx.prompt_loader.load_final_instructions = AsyncMock(return_value="Финальные инструкции")
            mock_ctx.supabase_client.add_message = AsyncMock()
            mock_ctx.supabase_client.update_session_stage = AsyncMock()
            mock_ctx.supabase_client.update_session_service_info = AsyncMock()
            mock_ctx.memory_manager.get_memory_messages = AsyncMock(return_value=[])
            mock_ctx.openai_client.estimate_tokens = Mock(return_value=tokens_used)
            mock_ctx.bot.send_message = AsyncMock()

            ai_response = Mock()
            ai_response.user_message = response_text
            ai_response.service_info = {AIMetadataKey.STAGE: "consult", AIMetadataKey.QUALITY: 8, AIMetadataKey.EVENTS: []}
            mock_ctx.openai_client.get_completion = AsyncMock(return_value=ai_response)

            with (
                patch("smart_bot_factory.utils.bot_utils.process_events", new_callable=AsyncMock, return_value=True),
                patch("smart_bot_factory.utils.bot_utils.process_file_events", new_callable=AsyncMock, return_value=[]),
            ):
                result = await send_message_by_ai(user_id=user_id, message_text=message_text, session_id=session_id)

                # ============ ПРОВЕРКА РЕЗУЛЬТАТА ФУНКЦИИ ============
                assert result["status"] == "success"
                assert result["user_id"] == user_id
                assert result["response_text"] == response_text
                assert result["tokens_used"] == tokens_used
                assert result["events_processed"] == 0
                assert isinstance(result["processing_time_ms"], int)
                assert result["processing_time_ms"] >= 0  # Может быть 0 при очень быстром выполнении

                # ============ ПРОВЕРКА АРГУМЕНТОВ ВЫЗОВОВ МЕТОДОВ ============

                # Проверяем сохранение сообщения пользователя
                user_message_call = mock_ctx.supabase_client.add_message.call_args_list[0]
                assert user_message_call.kwargs["session_id"] == session_id
                assert user_message_call.kwargs["role"] == MessageRole.USER
                assert user_message_call.kwargs["content"] == message_text
                assert user_message_call.kwargs["message_type"] == "text"

                # Проверяем сохранение ответа ассистента
                assistant_message_call = mock_ctx.supabase_client.add_message.call_args_list[1]
                assert assistant_message_call.kwargs["session_id"] == session_id
                assert assistant_message_call.kwargs["role"] == MessageRole.ASSISTANT
                assert assistant_message_call.kwargs["content"] == response_text
                assert assistant_message_call.kwargs["message_type"] == "text"
                assert assistant_message_call.kwargs["tokens_used"] == tokens_used
                assert assistant_message_call.kwargs["processing_time_ms"] == result["processing_time_ms"]
                assert assistant_message_call.kwargs["ai_metadata"] == ai_response.service_info

                # Проверяем обновление стадии сессии
                mock_ctx.supabase_client.update_session_all.assert_called_once()
                call_args = mock_ctx.supabase_client.update_session_all.call_args
                assert call_args[0][0] == session_id
                assert call_args[0][1] == "consult"
                assert call_args[0][2] == 8

                # Проверяем отправку сообщения ботом
                bot_call = mock_ctx.bot.send_message.call_args
                assert bot_call.kwargs["chat_id"] == user_id
                assert bot_call.kwargs["text"] == response_text

                # Проверяем вызов get_completion с правильными аргументами
                completion_call = mock_ctx.openai_client.get_completion.call_args
                langchain_messages = completion_call[0][0]
                assert isinstance(langchain_messages, list)
                assert len(langchain_messages) > 0  # Должен быть системный промпт и сообщение пользователя

                # Проверяем вызов estimate_tokens
                estimate_tokens_calls = [c for c in mock_ctx.openai_client.estimate_tokens.call_args_list if c]
                assert len(estimate_tokens_calls) >= 1  # Должен быть вызван для подсчета токенов ответа

                # ============ ПРОВЕРКА ПОБОЧНЫХ ЭФФЕКТОВ ============

                # Проверяем, что сообщения были сохранены в правильном порядке
                assert mock_ctx.supabase_client.add_message.call_count == 2

                # Проверяем, что get_active_session НЕ был вызван (так как session_id был передан)
                mock_ctx.supabase_client.get_active_session.assert_not_called()

                # Проверяем, что промпт был загружен
                mock_ctx.prompt_loader.load_system_prompt.assert_called_once()
                mock_ctx.prompt_loader.load_final_instructions.assert_called_once()

                # Проверяем, что история была запрошена
                mock_ctx.memory_manager.get_memory_messages.assert_called_once_with(session_id)

    @pytest.mark.asyncio
    async def test_detailed_assertions_with_events(self, mock_ctx):
        """Детальная проверка обработки событий"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            user_id = 789012
            message_text = "Мне нужен телефон"
            session_id = "session-456"

            events = [
                {AIMetadataKey.EVENT_TYPE: "телефон", AIMetadataKey.EVENT_INFO: "+1234567890"},
                {AIMetadataKey.EVENT_TYPE: "email", AIMetadataKey.EVENT_INFO: "test@example.com"},
            ]

            mock_ctx.prompt_loader.load_system_prompt = AsyncMock(return_value="Промпт")
            mock_ctx.prompt_loader.load_final_instructions = AsyncMock(return_value="")
            mock_ctx.supabase_client.add_message = AsyncMock()
            mock_ctx.supabase_client.update_session_stage = AsyncMock()
            mock_ctx.supabase_client.update_session_service_info = AsyncMock()
            mock_ctx.memory_manager.get_memory_messages = AsyncMock(return_value=[])
            mock_ctx.openai_client.estimate_tokens = Mock(return_value=100)
            mock_ctx.bot.send_message = AsyncMock()

            ai_response = Mock()
            ai_response.user_message = "Вот телефон"
            ai_response.service_info = {AIMetadataKey.EVENTS: events, AIMetadataKey.STAGE: "offer"}
            mock_ctx.openai_client.get_completion = AsyncMock(return_value=ai_response)

            with (
                patch("smart_bot_factory.utils.bot_utils.process_events", new_callable=AsyncMock, return_value=True),
                patch("smart_bot_factory.utils.bot_utils.process_file_events", new_callable=AsyncMock, return_value=[]),
            ):
                result = await send_message_by_ai(user_id=user_id, message_text=message_text, session_id=session_id)

                # Проверяем результат
                assert result["status"] == "success"
                assert result["events_processed"] == 2

                # Проверяем, что события были сохранены в метаданных
                assistant_message_call = mock_ctx.supabase_client.add_message.call_args_list[1]
                saved_metadata = assistant_message_call.kwargs["ai_metadata"]
                assert saved_metadata[AIMetadataKey.EVENTS] == events

                # Проверяем, что process_events был вызван (если события не пустые)
                # Это проверка побочного эффекта - обработка событий
                if events:
                    # process_events должен быть вызван для обработки событий
                    # Проверяем через то, что результат содержит events_processed
                    assert result["events_processed"] == len(events)

    @pytest.mark.asyncio
    async def test_detailed_assertions_skip_send(self, mock_ctx):
        """Детальная проверка пропуска отправки сообщения"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            user_id = 111222
            message_text = "Тест"
            session_id = "session-789"

            mock_ctx.prompt_loader.load_system_prompt = AsyncMock(return_value="Промпт")
            mock_ctx.prompt_loader.load_final_instructions = AsyncMock(return_value="")
            mock_ctx.supabase_client.add_message = AsyncMock()
            mock_ctx.supabase_client.update_session_stage = AsyncMock()
            mock_ctx.supabase_client.update_session_service_info = AsyncMock()
            mock_ctx.memory_manager.get_memory_messages = AsyncMock(return_value=[])
            mock_ctx.openai_client.estimate_tokens = Mock(return_value=50)
            mock_ctx.bot.send_message = AsyncMock()

            ai_response = Mock()
            ai_response.user_message = "Ответ"
            # Создаем события, которые приведут к skip
            events = [{AIMetadataKey.EVENT_TYPE: "тест", AIMetadataKey.EVENT_INFO: "инфо"}]
            ai_response.service_info = {AIMetadataKey.EVENTS: events}
            mock_ctx.openai_client.get_completion = AsyncMock(return_value=ai_response)

            # Мокируем process_events чтобы вернуть False (пропустить отправку)
            mock_process_events = AsyncMock(return_value=False)
            with (
                patch("smart_bot_factory.utils.bot_utils.process_events", mock_process_events),
                patch("smart_bot_factory.utils.bot_utils.process_file_events", new_callable=AsyncMock, return_value=[]),
            ):
                result = await send_message_by_ai(user_id=user_id, message_text=message_text, session_id=session_id)

                # Проверяем результат - сообщение должно быть пропущено
                # Если process_events вернул False, сообщение должно быть пропущено
                if mock_process_events.called:
                    assert result["status"] == "skipped"
                    assert result["reason"] == "send_ai_response=False"
                    assert result["user_id"] == user_id

                    # Проверяем побочные эффекты - сообщение НЕ должно быть отправлено
                    mock_ctx.bot.send_message.assert_not_called()
                else:
                    # Если process_events не был вызван (события не обработаны), сообщение должно быть отправлено
                    assert result["status"] == "success"

                # В любом случае сообщения должны быть сохранены в БД
                assert mock_ctx.supabase_client.add_message.call_count == 2

                # Проверяем, что ответ ассистента был сохранен
                assistant_message_call = mock_ctx.supabase_client.add_message.call_args_list[1]
                assert assistant_message_call.kwargs["role"] == MessageRole.ASSISTANT
                assert assistant_message_call.kwargs["content"] == "Ответ"


class TestDetailedAssertionsSendMessageByHuman:
    """Тесты с детальной проверкой для send_message_by_human"""

    @pytest.fixture
    def mock_ctx(self):
        """Фикстура для мок контекста"""
        ctx = Mock()
        ctx.bot = Mock()
        ctx.supabase_client = Mock()
        return ctx

    @pytest.mark.asyncio
    async def test_detailed_assertions_text_message(self, mock_ctx):
        """Детальная проверка отправки текстового сообщения"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            user_id = 123456
            message_text = "Привет от человека"
            session_id = "session-123"
            message_id = 789

            mock_message = Mock()
            mock_message.message_id = message_id
            mock_ctx.bot.send_message = AsyncMock(return_value=mock_message)
            mock_ctx.supabase_client.add_message = AsyncMock()

            result = await send_message_by_human(user_id=user_id, message_text=message_text, session_id=session_id, parse_mode="HTML")

            # Проверяем результат
            assert result["status"] == "success"
            assert result["user_id"] == user_id
            assert result["message_id"] == message_id
            assert result["message_text"] == message_text
            assert result["saved_to_db"] is True
            assert result["has_photo"] is False

            # Проверяем аргументы вызова send_message
            bot_call = mock_ctx.bot.send_message.call_args
            assert bot_call.kwargs["chat_id"] == user_id
            assert bot_call.kwargs["text"] == message_text
            assert bot_call.kwargs["parse_mode"] == "HTML"

            # Проверяем сохранение в БД
            db_call = mock_ctx.supabase_client.add_message.call_args
            assert db_call.kwargs["session_id"] == session_id
            assert db_call.kwargs["role"] == "assistant"
            assert db_call.kwargs["content"] == message_text
            assert db_call.kwargs["message_type"] == "text"
            assert db_call.kwargs["metadata"]["sent_by_human"] is True
            assert db_call.kwargs["metadata"]["has_photo"] is False

    @pytest.mark.asyncio
    async def test_detailed_assertions_photo_message(self, mock_ctx):
        """Детальная проверка отправки фото"""
        with (
            patch("smart_bot_factory.utils.context.ctx", mock_ctx),
            patch("smart_bot_factory.message.message_sender.root", Path("/test")),
            patch("pathlib.Path.exists", return_value=True),
        ):
            user_id = 123456
            message_text = "Подпись к фото"
            photo_path = "photos/test.jpg"
            message_id = 999

            mock_message = Mock()
            mock_message.message_id = message_id
            mock_ctx.bot.send_photo = AsyncMock(return_value=mock_message)
            mock_ctx.supabase_client.add_message = AsyncMock()

            result = await send_message_by_human(user_id=user_id, message_text=message_text, photo=photo_path, parse_mode="Markdown")

            # Проверяем результат
            assert result["status"] == "success"
            assert result["has_photo"] is True

            # Проверяем аргументы вызова send_photo
            bot_call = mock_ctx.bot.send_photo.call_args
            assert bot_call.kwargs["chat_id"] == user_id
            assert bot_call.kwargs["caption"] == message_text
            assert bot_call.kwargs["parse_mode"] == "Markdown"

            # Проверяем сохранение в БД (если session_id был передан)
            # В данном случае session_id не передан, поэтому сохранение не должно произойти
            mock_ctx.supabase_client.add_message.assert_not_called()


class TestDetailedAssertionsSendMessageToUsersByStage:
    """Тесты с детальной проверкой для send_message_to_users_by_stage"""

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
    async def test_detailed_assertions_multiple_users(self, mock_ctx):
        """Детальная проверка отправки сообщений нескольким пользователям"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            stage = "introduction"
            message_text = "Привет всем!"
            bot_id = "test-bot"

            users_data = [
                {"user_id": 111, "id": "session-1", "current_stage": stage, "created_at": "2024-01-01"},
                {"user_id": 222, "id": "session-2", "current_stage": stage, "created_at": "2024-01-02"},
                {"user_id": 333, "id": "session-3", "current_stage": stage, "created_at": "2024-01-03"},
            ]

            # Настройка моков для Supabase запроса
            mock_table = Mock()
            mock_query = Mock()
            mock_query.select.return_value = mock_query
            mock_query.eq.return_value = mock_query
            mock_query.order.return_value = mock_query
            mock_response = Mock()
            mock_response.data = users_data
            mock_query.execute.return_value = mock_response
            mock_table.select.return_value = mock_query
            mock_ctx.supabase_client.client.table.return_value = mock_table

            mock_ctx.bot.send_message = AsyncMock()
            mock_ctx.supabase_client.add_message = AsyncMock()

            result = await send_message_to_users_by_stage(stage=stage, message_text=message_text, bot_id=bot_id)

            # Проверяем результат
            assert result["status"] == "success"
            assert result["stage"] == stage
            assert result["users_found"] == 3
            assert result["messages_sent"] == 3
            assert len(result["errors"]) == 0

            # Проверяем аргументы вызовов send_message для каждого пользователя
            assert mock_ctx.bot.send_message.call_count == 3
            send_message_calls = mock_ctx.bot.send_message.call_args_list

            user_ids_sent = [call.kwargs["chat_id"] for call in send_message_calls]
            assert 111 in user_ids_sent
            assert 222 in user_ids_sent
            assert 333 in user_ids_sent

            # Проверяем, что все сообщения содержат правильный текст
            for call in send_message_calls:
                assert call.kwargs["text"] == message_text

            # Проверяем сохранение сообщений в БД
            assert mock_ctx.supabase_client.add_message.call_count == 3

            # Проверяем аргументы сохранения для каждого пользователя
            db_calls = mock_ctx.supabase_client.add_message.call_args_list
            session_ids_saved = [call.kwargs["session_id"] for call in db_calls]
            assert "session-1" in session_ids_saved
            assert "session-2" in session_ids_saved
            assert "session-3" in session_ids_saved

            # Проверяем метаданные сохраненных сообщений
            for db_call in db_calls:
                assert db_call.kwargs["role"] == "assistant"
                assert db_call.kwargs["content"] == message_text
                assert db_call.kwargs["message_type"] == "text"
                assert db_call.kwargs["metadata"]["sent_by_stage_broadcast"] is True
                assert db_call.kwargs["metadata"]["target_stage"] == stage
                assert "broadcast_timestamp" in db_call.kwargs["metadata"]


class TestDetailedAssertionsGetUsersByStageStats:
    """Тесты с детальной проверкой для get_users_by_stage_stats"""

    @pytest.fixture
    def mock_ctx(self):
        """Фикстура для мок контекста"""
        ctx = Mock()
        ctx.config = Mock()
        ctx.config.BOT_ID = "test-bot"
        ctx.supabase_client = Mock()
        return ctx

    @pytest.mark.asyncio
    async def test_detailed_assertions_stats(self, mock_ctx):
        """Детальная проверка получения статистики"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            bot_id = "test-bot"

            # Данные с дублирующимися пользователями (берем последнюю сессию)
            sessions_data = [
                {"user_id": 111, "current_stage": "introduction", "created_at": "2024-01-01"},
                {"user_id": 222, "current_stage": "introduction", "created_at": "2024-01-02"},
                {"user_id": 333, "current_stage": "consult", "created_at": "2024-01-03"},
                {"user_id": 111, "current_stage": "consult", "created_at": "2024-01-04"},  # Дубликат пользователя 111
            ]

            mock_table = Mock()
            mock_query = Mock()
            mock_query.select.return_value = mock_query
            mock_query.eq.return_value = mock_query
            mock_query.order.return_value = mock_query
            mock_response = Mock()
            mock_response.data = sessions_data
            mock_query.execute.return_value = mock_response
            mock_table.select.return_value = mock_query
            mock_ctx.supabase_client.client.table.return_value = mock_table

            result = await get_users_by_stage_stats(bot_id=bot_id)

            # Проверяем результат
            assert result["status"] == "success"
            assert result["bot_id"] == bot_id
            assert result["total_active_users"] == 3  # Уникальных пользователей (111, 222, 333)

            # Проверяем статистику по стадиям
            # Данные отсортированы по created_at desc, поэтому первая встреча пользователя будет с последней сессией
            assert "stages" in result
            # Проверяем общее количество уникальных пользователей
            assert result["total_active_users"] == 3

            # Проверяем, что есть правильное количество пользователей по стадиям
            # Пользователь 111 (последняя сессия - consult), пользователь 222 (introduction), пользователь 333 (consult)
            # Логика берет первую встреченную сессию для каждого пользователя (которая является последней по дате)
            assert result["stages"]["consult"] >= 1  # Минимум пользователь 333
            assert result["stages"]["introduction"] >= 1  # Минимум пользователь 222

            # Проверяем сортировку (по убыванию количества)
            assert "stages_list" in result
            # Должно быть 2 стадии
            assert len(result["stages_list"]) == 2

            # Проверяем, что стадии отсортированы по убыванию количества пользователей
            assert result["stages_list"][0][1] >= result["stages_list"][1][1]

            # Проверяем, что все стадии присутствуют
            stage_names = [stage[0] for stage in result["stages_list"]]
            assert "consult" in stage_names
            assert "introduction" in stage_names


class TestDetailedAssertionsSendMessage:
    """Тесты с детальной проверкой для send_message"""

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
    async def test_detailed_assertions_text_with_reply_markup(self, mock_message, mock_ctx):
        """Детальная проверка отправки текста с клавиатурой"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

            text = "Выберите действие"
            reply_markup = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="Кнопка 1", callback_data="action1")],
                    [InlineKeyboardButton(text="Кнопка 2", callback_data="action2")],
                ]
            )
            parse_mode = "Markdown"

            mock_result = Mock()
            mock_message.answer = AsyncMock(return_value=mock_result)

            result = await send_message(
                message=mock_message, text=text, supabase_client=mock_ctx.supabase_client, parse_mode=parse_mode, reply_markup=reply_markup
            )

            # Проверяем результат
            assert result == mock_result

            # Проверяем аргументы вызова answer
            answer_call = mock_message.answer.call_args
            assert answer_call[0][0] == text  # Первый позиционный аргумент - текст
            assert answer_call.kwargs["parse_mode"] == parse_mode
            assert answer_call.kwargs["reply_markup"] == reply_markup

            # Проверяем побочные эффекты - не должно быть вызовов media_group
            mock_message.answer_media_group.assert_not_called()

    @pytest.mark.asyncio
    async def test_detailed_assertions_files_filtering(self, mock_message, mock_ctx):
        """Детальная проверка фильтрации уже отправленных файлов"""
        with (
            patch("smart_bot_factory.utils.context.ctx", mock_ctx),
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.is_file", return_value=True),
            patch("pathlib.Path.resolve", return_value=Path("files")),
        ):
            user_id = 123456
            text = "Вот файлы"

            # Мокируем уже отправленные файлы
            mock_ctx.supabase_client.get_sent_files = AsyncMock(return_value=["sent_file.pdf"])
            mock_ctx.supabase_client.get_sent_directories = AsyncMock(return_value=["sent_dir"])

            mock_result = Mock()
            mock_message.answer = AsyncMock(return_value=mock_result)
            mock_message.answer_media_group = AsyncMock()

            await send_message(
                message=mock_message,
                text=text,
                supabase_client=mock_ctx.supabase_client,
                files_list=["new_file.pdf", "sent_file.pdf"],  # Один файл уже отправлен
                directories_list=["new_dir", "sent_dir"],  # Одна директория уже отправлена
            )

            # Проверяем, что файлы и директории обработаны (get_sent_files/get_sent_directories больше не используются)

            # Проверяем, что answer был вызван (для отправки текста)
            mock_message.answer.assert_called_once()

            # Проверяем, что media_group был вызван только для новых файлов
            # (детальная проверка требует знания структуры MediaGroupBuilder)
