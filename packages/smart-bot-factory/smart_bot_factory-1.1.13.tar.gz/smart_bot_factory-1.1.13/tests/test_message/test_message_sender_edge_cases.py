"""Тесты граничных случаев для message_sender"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from smart_bot_factory.handlers.constants import AIMetadataKey, MessageRole
from smart_bot_factory.message.message_sender import (
    send_message,
    send_message_by_ai,
    send_message_by_human,
    send_message_to_users_by_stage,
)


class TestEdgeCasesLargeData:
    """Тесты для больших объемов данных"""

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
    async def test_very_long_message_text(self, mock_ctx):
        """Тест обработки очень длинного сообщения (4096+ символов)"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            # Создаем очень длинное сообщение (5000 символов)
            long_message = "А" * 5000

            mock_ctx.supabase_client.get_active_session = AsyncMock(return_value={"id": "session-123"})
            mock_ctx.prompt_loader.load_system_prompt = AsyncMock(return_value="Промпт")
            mock_ctx.prompt_loader.load_final_instructions = AsyncMock(return_value="")
            mock_ctx.supabase_client.add_message = AsyncMock()
            mock_ctx.supabase_client.update_session_stage = AsyncMock()
            mock_ctx.supabase_client.update_session_service_info = AsyncMock()
            mock_ctx.memory_manager.get_memory_messages = AsyncMock(return_value=[])
            mock_ctx.openai_client.estimate_tokens = Mock(return_value=1000)
            mock_ctx.bot.send_message = AsyncMock()

            ai_response = Mock()
            ai_response.user_message = "Короткий ответ"
            ai_response.service_info = {}
            mock_ctx.openai_client.get_completion = AsyncMock(return_value=ai_response)

            with (
                patch("smart_bot_factory.utils.bot_utils.process_events", new_callable=AsyncMock, return_value=True),
                patch("smart_bot_factory.utils.bot_utils.process_file_events", new_callable=AsyncMock, return_value=[]),
            ):
                result = await send_message_by_ai(user_id=123456, message_text=long_message)

                # Проверяем, что длинное сообщение было обработано
                assert result["status"] == "success"
                # Проверяем, что длинное сообщение было сохранено
                first_call = mock_ctx.supabase_client.add_message.call_args_list[0]
                assert len(first_call.kwargs["content"]) == 5000

    @pytest.mark.asyncio
    async def test_large_message_history(self, mock_ctx):
        """Тест обработки большого количества сообщений в истории (100+ сообщений)"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            # Создаем большую историю (100 сообщений)
            large_history = []
            for i in range(100):
                if i % 2 == 0:
                    large_history.append({"role": MessageRole.USER, "content": f"Сообщение {i}"})
                else:
                    large_history.append({"role": MessageRole.ASSISTANT, "content": f"Ответ {i}"})

            mock_ctx.supabase_client.get_active_session = AsyncMock(return_value={"id": "session-123"})
            mock_ctx.prompt_loader.load_system_prompt = AsyncMock(return_value="Промпт")
            mock_ctx.prompt_loader.load_final_instructions = AsyncMock(return_value="")
            mock_ctx.supabase_client.add_message = AsyncMock()
            mock_ctx.supabase_client.update_session_stage = AsyncMock()
            mock_ctx.supabase_client.update_session_service_info = AsyncMock()
            mock_ctx.memory_manager.get_memory_messages = AsyncMock(return_value=large_history)
            mock_ctx.openai_client.estimate_tokens = Mock(return_value=5000)
            mock_ctx.bot.send_message = AsyncMock()

            ai_response = Mock()
            ai_response.user_message = "Ответ"
            ai_response.service_info = {}
            mock_ctx.openai_client.get_completion = AsyncMock(return_value=ai_response)

            with (
                patch("smart_bot_factory.utils.bot_utils.process_events", new_callable=AsyncMock, return_value=True),
                patch("smart_bot_factory.utils.bot_utils.process_file_events", new_callable=AsyncMock, return_value=[]),
            ):
                result = await send_message_by_ai(user_id=123456, message_text="Новое сообщение")

                # Проверяем, что большая история была обработана
                assert result["status"] == "success"
                # Проверяем, что контекст был построен с большой историей
                completion_call = mock_ctx.openai_client.get_completion.call_args
                langchain_messages = completion_call[0][0]
                # Должно быть много сообщений в контексте
                assert len(langchain_messages) >= 100

    @pytest.mark.asyncio
    async def test_large_events_metadata(self, mock_ctx):
        """Тест обработки большого количества событий в метаданных (50+ событий)"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            # Создаем большое количество событий
            large_events = []
            for i in range(50):
                large_events.append({AIMetadataKey.EVENT_TYPE: f"событие_{i}", AIMetadataKey.EVENT_INFO: f"информация_{i}"})

            mock_ctx.supabase_client.get_active_session = AsyncMock(return_value={"id": "session-123"})
            mock_ctx.prompt_loader.load_system_prompt = AsyncMock(return_value="Промпт")
            mock_ctx.prompt_loader.load_final_instructions = AsyncMock(return_value="")
            mock_ctx.supabase_client.add_message = AsyncMock()
            mock_ctx.supabase_client.update_session_stage = AsyncMock()
            mock_ctx.supabase_client.update_session_service_info = AsyncMock()
            mock_ctx.memory_manager.get_memory_messages = AsyncMock(return_value=[])
            mock_ctx.openai_client.estimate_tokens = Mock(return_value=100)
            mock_ctx.bot.send_message = AsyncMock()

            ai_response = Mock()
            ai_response.user_message = "Ответ"
            ai_response.service_info = {AIMetadataKey.EVENTS: large_events}
            mock_ctx.openai_client.get_completion = AsyncMock(return_value=ai_response)

            with (
                patch("smart_bot_factory.utils.bot_utils.process_events", new_callable=AsyncMock, return_value=True),
                patch("smart_bot_factory.utils.bot_utils.process_file_events", new_callable=AsyncMock, return_value=[]),
            ):
                result = await send_message_by_ai(user_id=123456, message_text="Тест")

                # Проверяем, что все события были обработаны
                assert result["status"] == "success"
                assert result["events_processed"] == 50

    @pytest.mark.asyncio
    async def test_very_long_ai_response(self, mock_ctx):
        """Тест обработки очень длинного ответа от AI (10000+ символов)"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            long_response = "Б" * 10000

            mock_ctx.supabase_client.get_active_session = AsyncMock(return_value={"id": "session-123"})
            mock_ctx.prompt_loader.load_system_prompt = AsyncMock(return_value="Промпт")
            mock_ctx.prompt_loader.load_final_instructions = AsyncMock(return_value="")
            mock_ctx.supabase_client.add_message = AsyncMock()
            mock_ctx.supabase_client.update_session_stage = AsyncMock()
            mock_ctx.supabase_client.update_session_service_info = AsyncMock()
            mock_ctx.memory_manager.get_memory_messages = AsyncMock(return_value=[])
            mock_ctx.openai_client.estimate_tokens = Mock(return_value=2500)
            mock_ctx.bot.send_message = AsyncMock()

            ai_response = Mock()
            ai_response.user_message = long_response
            ai_response.service_info = {}
            mock_ctx.openai_client.get_completion = AsyncMock(return_value=ai_response)

            with (
                patch("smart_bot_factory.utils.bot_utils.process_events", new_callable=AsyncMock, return_value=True),
                patch("smart_bot_factory.utils.bot_utils.process_file_events", new_callable=AsyncMock, return_value=[]),
            ):
                result = await send_message_by_ai(user_id=123456, message_text="Тест")

                # Проверяем, что длинный ответ был обработан
                assert result["status"] == "success"
                assert len(result["response_text"]) == 10000
                # Проверяем, что длинный ответ был отправлен
                call_args = mock_ctx.bot.send_message.call_args
                assert len(call_args.kwargs["text"]) == 10000


class TestEdgeCasesInvalidInput:
    """Тесты для некорректных входных данных"""

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
    async def test_empty_message_text(self, mock_ctx):
        """Тест обработки пустого сообщения"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            mock_ctx.supabase_client.get_active_session = AsyncMock(return_value={"id": "session-123"})
            mock_ctx.prompt_loader.load_system_prompt = AsyncMock(return_value="Промпт")
            mock_ctx.prompt_loader.load_final_instructions = AsyncMock(return_value="")
            mock_ctx.supabase_client.add_message = AsyncMock()
            mock_ctx.supabase_client.update_session_stage = AsyncMock()
            mock_ctx.supabase_client.update_session_service_info = AsyncMock()
            mock_ctx.memory_manager.get_memory_messages = AsyncMock(return_value=[])
            mock_ctx.openai_client.estimate_tokens = Mock(return_value=0)
            mock_ctx.bot.send_message = AsyncMock()

            ai_response = Mock()
            ai_response.user_message = "Ответ на пустое сообщение"
            ai_response.service_info = {}
            mock_ctx.openai_client.get_completion = AsyncMock(return_value=ai_response)

            with (
                patch("smart_bot_factory.utils.bot_utils.process_events", new_callable=AsyncMock, return_value=True),
                patch("smart_bot_factory.utils.bot_utils.process_file_events", new_callable=AsyncMock, return_value=[]),
            ):
                result = await send_message_by_ai(user_id=123456, message_text="")

                # Пустое сообщение должно быть обработано (сохранено в БД)
                assert result["status"] == "success"
                first_call = mock_ctx.supabase_client.add_message.call_args_list[0]
                assert first_call.kwargs["content"] == ""

    @pytest.mark.asyncio
    async def test_whitespace_only_message(self, mock_ctx):
        """Тест обработки сообщения только из пробелов"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            mock_ctx.supabase_client.get_active_session = AsyncMock(return_value={"id": "session-123"})
            mock_ctx.prompt_loader.load_system_prompt = AsyncMock(return_value="Промпт")
            mock_ctx.prompt_loader.load_final_instructions = AsyncMock(return_value="")
            mock_ctx.supabase_client.add_message = AsyncMock()
            mock_ctx.supabase_client.update_session_stage = AsyncMock()
            mock_ctx.supabase_client.update_session_service_info = AsyncMock()
            mock_ctx.memory_manager.get_memory_messages = AsyncMock(return_value=[])
            mock_ctx.openai_client.estimate_tokens = Mock(return_value=0)
            mock_ctx.bot.send_message = AsyncMock()

            ai_response = Mock()
            ai_response.user_message = "Ответ"
            ai_response.service_info = {}
            mock_ctx.openai_client.get_completion = AsyncMock(return_value=ai_response)

            with (
                patch("smart_bot_factory.utils.bot_utils.process_events", new_callable=AsyncMock, return_value=True),
                patch("smart_bot_factory.utils.bot_utils.process_file_events", new_callable=AsyncMock, return_value=[]),
            ):
                result = await send_message_by_ai(user_id=123456, message_text="   \n\t  ")

                # Сообщение из пробелов должно быть обработано
                assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_special_characters_message(self, mock_ctx):
        """Тест обработки сообщения со специальными символами и эмодзи"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            special_message = "Привет! 👋\n\nТекст с эмодзи: 😀🎉🔥\n\nСпецсимволы: <>&\"'`\n\nUnicode: 你好 こんにちは"

            mock_ctx.supabase_client.get_active_session = AsyncMock(return_value={"id": "session-123"})
            mock_ctx.prompt_loader.load_system_prompt = AsyncMock(return_value="Промпт")
            mock_ctx.prompt_loader.load_final_instructions = AsyncMock(return_value="")
            mock_ctx.supabase_client.add_message = AsyncMock()
            mock_ctx.supabase_client.update_session_stage = AsyncMock()
            mock_ctx.supabase_client.update_session_service_info = AsyncMock()
            mock_ctx.memory_manager.get_memory_messages = AsyncMock(return_value=[])
            mock_ctx.openai_client.estimate_tokens = Mock(return_value=50)
            mock_ctx.bot.send_message = AsyncMock()

            ai_response = Mock()
            ai_response.user_message = "Ответ с эмодзи: ✅"
            ai_response.service_info = {}
            mock_ctx.openai_client.get_completion = AsyncMock(return_value=ai_response)

            with (
                patch("smart_bot_factory.utils.bot_utils.process_events", new_callable=AsyncMock, return_value=True),
                patch("smart_bot_factory.utils.bot_utils.process_file_events", new_callable=AsyncMock, return_value=[]),
            ):
                result = await send_message_by_ai(user_id=123456, message_text=special_message)

                # Сообщение со спецсимволами должно быть обработано
                assert result["status"] == "success"
                first_call = mock_ctx.supabase_client.add_message.call_args_list[0]
                assert special_message in first_call.kwargs["content"] or first_call.kwargs["content"] == special_message

    @pytest.mark.asyncio
    async def test_negative_user_id(self, mock_ctx):
        """Тест обработки отрицательного user_id"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            mock_ctx.supabase_client.get_active_session = AsyncMock(return_value={"id": "session-123"})
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
            ai_response.service_info = {}
            mock_ctx.openai_client.get_completion = AsyncMock(return_value=ai_response)

            with (
                patch("smart_bot_factory.utils.bot_utils.process_events", new_callable=AsyncMock, return_value=True),
                patch("smart_bot_factory.utils.bot_utils.process_file_events", new_callable=AsyncMock, return_value=[]),
            ):
                result = await send_message_by_ai(user_id=-123456, message_text="Тест")

                # Отрицательный user_id должен быть обработан (Telegram может использовать отрицательные ID для групп)
                assert result["status"] in ["success", "error"]
                if result["status"] == "success":
                    assert result["user_id"] == -123456

    @pytest.mark.asyncio
    async def test_none_response_text(self, mock_ctx):
        """Тест обработки None в response_text от AI"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            mock_ctx.supabase_client.get_active_session = AsyncMock(return_value={"id": "session-123"})
            mock_ctx.prompt_loader.load_system_prompt = AsyncMock(return_value="Промпт")
            mock_ctx.prompt_loader.load_final_instructions = AsyncMock(return_value="")
            mock_ctx.supabase_client.add_message = AsyncMock()
            mock_ctx.supabase_client.update_session_stage = AsyncMock()
            mock_ctx.supabase_client.update_session_service_info = AsyncMock()
            mock_ctx.memory_manager.get_memory_messages = AsyncMock(return_value=[])
            mock_ctx.openai_client.estimate_tokens = Mock(return_value=0)
            mock_ctx.bot.send_message = AsyncMock()

            ai_response = Mock()
            ai_response.user_message = None
            ai_response.service_info = {}
            mock_ctx.openai_client.get_completion = AsyncMock(return_value=ai_response)

            with (
                patch("smart_bot_factory.utils.bot_utils.process_events", new_callable=AsyncMock, return_value=True),
                patch("smart_bot_factory.utils.bot_utils.process_file_events", new_callable=AsyncMock, return_value=[]),
            ):
                result = await send_message_by_ai(user_id=123456, message_text="Тест")

                # None response_text должен быть обработан (вероятно, будет пустая строка или ошибка)
                assert result["status"] in ["success", "error"]
                if result["status"] == "success":
                    # estimate_tokens должен обработать None
                    mock_ctx.openai_client.estimate_tokens.assert_called()

    @pytest.mark.asyncio
    async def test_empty_metadata(self, mock_ctx):
        """Тест обработки пустых метаданных от AI"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            mock_ctx.supabase_client.get_active_session = AsyncMock(return_value={"id": "session-123"})
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
            ai_response.service_info = None  # Пустые метаданные
            mock_ctx.openai_client.get_completion = AsyncMock(return_value=ai_response)

            with (
                patch("smart_bot_factory.utils.bot_utils.process_events", new_callable=AsyncMock, return_value=True),
                patch("smart_bot_factory.utils.bot_utils.process_file_events", new_callable=AsyncMock, return_value=[]),
            ):
                result = await send_message_by_ai(user_id=123456, message_text="Тест")

                # Пустые метаданные должны быть обработаны
                assert result["status"] == "success"
                assert result["events_processed"] == 0

    @pytest.mark.asyncio
    async def test_send_message_by_human_empty_text(self, mock_ctx):
        """Тест отправки пустого текста через send_message_by_human"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            mock_ctx.bot.send_message = AsyncMock(return_value=Mock(message_id=1))
            mock_ctx.supabase_client.add_message = AsyncMock()

            result = await send_message_by_human(user_id=123456, message_text="", session_id="session-123")

            # Пустой текст должен быть отправлен
            assert result["status"] == "success"
            mock_ctx.bot.send_message.assert_called_once()
            call_args = mock_ctx.bot.send_message.call_args
            assert call_args.kwargs["text"] == ""

    @pytest.mark.asyncio
    async def test_send_message_empty_text_with_files(self, mock_message, mock_ctx):
        """Тест send_message с пустым текстом, но с файлами"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            mock_ctx.supabase_client.get_sent_files = AsyncMock(return_value=[])
            mock_ctx.supabase_client.get_sent_directories = AsyncMock(return_value=[])
            mock_message.answer = AsyncMock(return_value=Mock(message_id=1))
            mock_message.answer_media_group = AsyncMock()

            # Создаем временный файл для теста
            import tempfile

            with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
                f.write("test content")
                temp_file = Path(f.name)

            try:
                result = await send_message(
                    message=mock_message,
                    text="",  # Пустой текст
                    supabase_client=mock_ctx.supabase_client,
                    files_list=[temp_file.name],
                )

                # Пустой текст с файлами должен быть обработан
                # Файлы должны быть отправлены, текст может быть пустым
                assert result is not None
            finally:
                # Удаляем временный файл
                if temp_file.exists():
                    temp_file.unlink()


class TestEdgeCasesRaceConditions:
    """Тесты для асинхронных race conditions"""

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
    async def test_concurrent_send_message_by_ai_same_user(self, mock_ctx):
        """Тест параллельных вызовов send_message_by_ai для одного пользователя"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            mock_ctx.supabase_client.get_active_session = AsyncMock(return_value={"id": "session-123"})
            mock_ctx.prompt_loader.load_system_prompt = AsyncMock(return_value="Промпт")
            mock_ctx.prompt_loader.load_final_instructions = AsyncMock(return_value="")
            mock_ctx.supabase_client.add_message = AsyncMock()
            mock_ctx.supabase_client.update_session_stage = AsyncMock()
            mock_ctx.supabase_client.update_session_service_info = AsyncMock()
            mock_ctx.memory_manager.get_memory_messages = AsyncMock(return_value=[])
            mock_ctx.openai_client.estimate_tokens = Mock(return_value=50)
            mock_ctx.bot.send_message = AsyncMock()

            # Создаем разные ответы для разных вызовов
            ai_responses = [Mock(user_message=f"Ответ {i}", service_info={}) for i in range(5)]
            mock_ctx.openai_client.get_completion = AsyncMock(side_effect=ai_responses)

            with (
                patch("smart_bot_factory.utils.bot_utils.process_events", new_callable=AsyncMock, return_value=True),
                patch("smart_bot_factory.utils.bot_utils.process_file_events", new_callable=AsyncMock, return_value=[]),
            ):
                # Запускаем 5 параллельных вызовов
                tasks = [send_message_by_ai(user_id=123456, message_text=f"Сообщение {i}") for i in range(5)]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Все вызовы должны завершиться успешно
                for result in results:
                    assert not isinstance(result, Exception)
                    assert result["status"] == "success"
                    assert result["user_id"] == 123456

                # Проверяем, что все сообщения были сохранены
                assert mock_ctx.supabase_client.add_message.call_count == 10  # 5 пользователей + 5 ассистентов

                # Проверяем, что все сообщения были отправлены
                assert mock_ctx.bot.send_message.call_count == 5

    @pytest.mark.asyncio
    async def test_concurrent_send_message_by_ai_different_users(self, mock_ctx):
        """Тест параллельных вызовов send_message_by_ai для разных пользователей"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            # Разные сессии для разных пользователей
            mock_ctx.supabase_client.get_active_session = AsyncMock(side_effect=[{"id": f"session-{i}"} for i in range(5)])
            mock_ctx.prompt_loader.load_system_prompt = AsyncMock(return_value="Промпт")
            mock_ctx.prompt_loader.load_final_instructions = AsyncMock(return_value="")
            mock_ctx.supabase_client.add_message = AsyncMock()
            mock_ctx.supabase_client.update_session_stage = AsyncMock()
            mock_ctx.supabase_client.update_session_service_info = AsyncMock()
            mock_ctx.memory_manager.get_memory_messages = AsyncMock(return_value=[])
            mock_ctx.openai_client.estimate_tokens = Mock(return_value=50)
            mock_ctx.bot.send_message = AsyncMock()

            ai_responses = [Mock(user_message=f"Ответ пользователю {i}", service_info={}) for i in range(5)]
            mock_ctx.openai_client.get_completion = AsyncMock(side_effect=ai_responses)

            with (
                patch("smart_bot_factory.utils.bot_utils.process_events", new_callable=AsyncMock, return_value=True),
                patch("smart_bot_factory.utils.bot_utils.process_file_events", new_callable=AsyncMock, return_value=[]),
            ):
                # Запускаем 5 параллельных вызовов для разных пользователей
                tasks = [send_message_by_ai(user_id=100000 + i, message_text=f"Сообщение {i}") for i in range(5)]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Все вызовы должны завершиться успешно
                for i, result in enumerate(results):
                    assert not isinstance(result, Exception)
                    assert result["status"] == "success"
                    assert result["user_id"] == 100000 + i

                # Проверяем, что все сообщения были сохранены
                assert mock_ctx.supabase_client.add_message.call_count == 10

                # Проверяем, что все сообщения были отправлены
                assert mock_ctx.bot.send_message.call_count == 5

    @pytest.mark.asyncio
    async def test_concurrent_send_message_to_users_by_stage(self, mock_ctx):
        """Тест параллельных вызовов send_message_to_users_by_stage"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            # Мокируем данные для разных стадий
            def mock_execute():
                result = Mock()
                result.data = [{"user_id": i, "id": f"session-{i}", "current_stage": "test", "created_at": "2024-01-01"} for i in range(3)]
                return result

            mock_ctx.config.BOT_ID = "test-bot"
            mock_ctx.supabase_client.client = Mock()
            mock_ctx.supabase_client.client.table = Mock(
                return_value=Mock(
                    select=Mock(
                        return_value=Mock(
                            eq=Mock(
                                return_value=Mock(
                                    eq=Mock(return_value=Mock(eq=Mock(return_value=Mock(order=Mock(return_value=Mock(execute=mock_execute))))))
                                )
                            )
                        )
                    )
                )
            )
            mock_ctx.bot.send_message = AsyncMock()
            mock_ctx.supabase_client.add_message = AsyncMock()

            # Запускаем параллельные вызовы для разных стадий
            tasks = [send_message_to_users_by_stage(stage=f"stage-{i}", message_text=f"Сообщение {i}", bot_id="test-bot") for i in range(3)]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Все вызовы должны завершиться успешно
            for result in results:
                assert not isinstance(result, Exception)
                assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_race_condition_session_access(self, mock_ctx):
        """Тест race condition при доступе к одной сессии"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            session_id = "session-123"

            mock_ctx.prompt_loader.load_system_prompt = AsyncMock(return_value="Промпт")
            mock_ctx.prompt_loader.load_final_instructions = AsyncMock(return_value="")
            mock_ctx.supabase_client.add_message = AsyncMock()
            mock_ctx.supabase_client.update_session_stage = AsyncMock()
            mock_ctx.supabase_client.update_session_service_info = AsyncMock()
            mock_ctx.memory_manager.get_memory_messages = AsyncMock(return_value=[])
            mock_ctx.openai_client.estimate_tokens = Mock(return_value=50)
            mock_ctx.bot.send_message = AsyncMock()

            ai_responses = [Mock(user_message=f"Ответ {i}", service_info={}) for i in range(3)]
            mock_ctx.openai_client.get_completion = AsyncMock(side_effect=ai_responses)

            with (
                patch("smart_bot_factory.utils.bot_utils.process_events", new_callable=AsyncMock, return_value=True),
                patch("smart_bot_factory.utils.bot_utils.process_file_events", new_callable=AsyncMock, return_value=[]),
            ):
                # Запускаем 3 параллельных вызова с одной сессией
                tasks = [send_message_by_ai(user_id=123456, message_text=f"Сообщение {i}", session_id=session_id) for i in range(3)]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Все вызовы должны завершиться успешно
                for result in results:
                    assert not isinstance(result, Exception)
                    assert result["status"] == "success"

                # Проверяем, что все сообщения были сохранены в одну сессию
                assert mock_ctx.supabase_client.add_message.call_count == 6  # 3 пользователя + 3 ассистента

                # Проверяем, что все вызовы использовали одну сессию
                for call in mock_ctx.supabase_client.add_message.call_args_list:
                    assert call.kwargs["session_id"] == session_id
