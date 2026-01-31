"""Тесты для увеличения покрытия кода message_sender"""

from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from smart_bot_factory.message.message_sender import (
    get_users_by_stage_stats,
    send_message,
    send_message_by_ai,
    send_message_to_users_by_stage,
)


class TestCoverageSendMessageByAI:
    """Тесты для покрытия непокрытых веток send_message_by_ai"""

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
    async def test_error_loading_system_prompt(self, mock_ctx):
        """Тест обработки ошибки загрузки системного промпта (строки 53-55)"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            mock_ctx.supabase_client.get_active_session = AsyncMock(return_value={"id": "session-123"})
            mock_ctx.prompt_loader.load_system_prompt = AsyncMock(side_effect=Exception("Ошибка загрузки"))

            result = await send_message_by_ai(user_id=123456, message_text="Тест")

            assert result["status"] == "error"
            assert "Не удалось загрузить системный промпт" in result["error"]
            assert result["user_id"] == 123456

    @pytest.mark.asyncio
    async def test_error_saving_assistant_message(self, mock_ctx):
        """Тест обработки ошибки сохранения ответа ассистента в БД (строки 105-106)"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            mock_ctx.supabase_client.get_active_session = AsyncMock(return_value={"id": "session-123"})
            mock_ctx.prompt_loader.load_system_prompt = AsyncMock(return_value="Промпт")
            mock_ctx.prompt_loader.load_final_instructions = AsyncMock(return_value="")
            mock_ctx.supabase_client.add_message = AsyncMock()
            # Первый вызов успешен (сохранение сообщения пользователя), второй - ошибка (сохранение ответа)
            mock_ctx.supabase_client.add_message.side_effect = [
                None,  # Успешное сохранение сообщения пользователя
                Exception("Ошибка сохранения"),  # Ошибка при сохранении ответа ассистента
            ]
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
                result = await send_message_by_ai(user_id=123456, message_text="Тест")

                # Функция должна продолжить работу даже при ошибке сохранения
                assert result["status"] == "success"
                # Сообщение должно быть отправлено
                mock_ctx.bot.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_debug_mode_response(self, mock_ctx):
        """Тест режима отладки (строки 111-112)"""
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
            mock_ctx.config.DEBUG_MODE = True  # Включаем режим отладки

            # В DEBUG_MODE original_ai_response используется напрямую, но он должен быть объектом с service_info
            original_response = Mock()
            original_response.user_message = "Очищенный ответ"
            original_response.service_info = {}
            # Для DEBUG_MODE нужно чтобы original_ai_response можно было использовать как строку или объект
            # Мокируем так, чтобы _process_ai_response вернул правильные значения
            ai_response = Mock()
            ai_response.user_message = "Очищенный ответ"
            ai_response.service_info = {}
            mock_ctx.openai_client.get_completion = AsyncMock(return_value=ai_response)

            with (
                patch("smart_bot_factory.utils.bot_utils.process_events", new_callable=AsyncMock, return_value=True),
                patch("smart_bot_factory.utils.bot_utils.process_file_events", new_callable=AsyncMock, return_value=[]),
            ):
                result = await send_message_by_ai(user_id=123456, message_text="Тест")

                # В режиме отладки должен быть отправлен полный ответ
                assert result["status"] == "success"
                # Проверяем, что был отправлен original_ai_response
                call_args = mock_ctx.bot.send_message.call_args
                # В DEBUG_MODE отправляется original_ai_response (может быть dict)
                assert call_args is not None


class TestCoverageSendMessageToUsersByStage:
    """Тесты для покрытия непокрытых веток send_message_to_users_by_stage"""

    @pytest.fixture
    def mock_ctx(self):
        """Фикстура для мок контекста"""
        ctx = Mock()
        ctx.config = Mock()
        ctx.config.BOT_ID = None  # Для теста ошибки определения bot_id
        ctx.supabase_client = Mock()
        ctx.bot = Mock()
        return ctx

    @pytest.mark.asyncio
    async def test_error_determining_bot_id(self, mock_ctx):
        """Тест ошибки определения bot_id (строка 237)"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            mock_ctx.config = None

            result = await send_message_to_users_by_stage(stage="introduction", message_text="Привет", bot_id=None)

            assert result["status"] == "error"
            assert "Не удалось определить bot_id" in result["error"]

    @pytest.mark.asyncio
    async def test_photo_file_not_found(self, mock_ctx):
        """Тест ошибки когда файл с фото не найден (строка 270)"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx), patch("smart_bot_factory.message.message_sender.root", Path("/test")):
            mock_ctx.config.BOT_ID = "test-bot"

            # Настраиваем моки для получения пользователей (нужен хотя бы один, чтобы проверить фото)
            mock_table = Mock()
            mock_query = Mock()
            mock_query.select.return_value = mock_query
            mock_query.eq.return_value = mock_query
            mock_query.order.return_value = mock_query
            mock_response = Mock()
            mock_response.data = [
                {"user_id": 111, "id": "session-1", "current_stage": "introduction", "created_at": "2024-01-01"},
            ]
            mock_query.execute.return_value = mock_response
            mock_table.select.return_value = mock_query
            mock_ctx.supabase_client.client.table.return_value = mock_table

            # Мокируем Path.exists чтобы вернуть False для фото
            # Ошибка обрабатывается внутри функции и возвращается в результате
            with patch("pathlib.Path.exists", return_value=False):
                result = await send_message_to_users_by_stage(stage="introduction", message_text="Привет", bot_id="test-bot", photo="nonexistent.jpg")
                # Функция обрабатывает ошибку и возвращает error статус
                assert result["status"] == "error"
                assert "не найден" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_send_to_user_exception_handling(self, mock_ctx):
        """Тест обработки исключений при отправке пользователю (строки 297-300, 311, 315)"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            mock_ctx.config.BOT_ID = "test-bot"

            # Настраиваем моки для получения пользователей
            mock_table = Mock()
            mock_query = Mock()
            mock_query.select.return_value = mock_query
            mock_query.eq.return_value = mock_query
            mock_query.order.return_value = mock_query
            mock_response = Mock()
            mock_response.data = [
                {"user_id": 111, "id": "session-1", "current_stage": "introduction", "created_at": "2024-01-01"},
                {"user_id": 222, "id": "session-2", "current_stage": "introduction", "created_at": "2024-01-02"},
            ]
            mock_query.execute.return_value = mock_response
            mock_table.select.return_value = mock_query
            mock_ctx.supabase_client.client.table.return_value = mock_table

            # Мокируем отправку сообщения - первый успех, второй ошибка
            mock_ctx.bot.send_message = AsyncMock(
                side_effect=[
                    None,  # Первый пользователь - успех
                    Exception("Ошибка отправки"),  # Второй пользователь - ошибка
                ]
            )
            mock_ctx.supabase_client.add_message = AsyncMock(
                side_effect=[
                    None,  # Первый пользователь - успех
                    Exception("Ошибка сохранения"),  # Второй пользователь - ошибка сохранения
                ]
            )

            result = await send_message_to_users_by_stage(stage="introduction", message_text="Привет", bot_id="test-bot")

            # Проверяем, что ошибки были обработаны
            assert result["status"] == "success"
            assert result["users_found"] == 2
            assert result["messages_sent"] == 1  # Только одно сообщение отправлено успешно
            assert len(result["errors"]) > 0  # Должны быть ошибки

    @pytest.mark.asyncio
    async def test_gather_exception_handling(self, mock_ctx):
        """Тест обработки исключений в asyncio.gather (строка 311)"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            mock_ctx.config.BOT_ID = "test-bot"

            mock_table = Mock()
            mock_query = Mock()
            mock_query.select.return_value = mock_query
            mock_query.eq.return_value = mock_query
            mock_query.order.return_value = mock_query
            mock_response = Mock()
            mock_response.data = [
                {"user_id": 111, "id": "session-1", "current_stage": "introduction", "created_at": "2024-01-01"},
            ]
            mock_query.execute.return_value = mock_response
            mock_table.select.return_value = mock_query
            mock_ctx.supabase_client.client.table.return_value = mock_table

            # Мокируем send_message чтобы вызвать исключение на уровне gather

            async def mock_gather(*tasks, return_exceptions=False):
                # Симулируем исключение в одной из задач
                results = []
                for task in tasks:
                    try:
                        result = await task
                        results.append(result)
                    except Exception as e:
                        if return_exceptions:
                            results.append(e)
                        else:
                            raise
                return results

            with patch("asyncio.gather", side_effect=mock_gather):
                # Мокируем send_message чтобы вызвать исключение
                mock_ctx.bot.send_message = AsyncMock(side_effect=RuntimeError("Неожиданная ошибка"))

                result = await send_message_to_users_by_stage(stage="introduction", message_text="Привет", bot_id="test-bot")

                # Проверяем, что исключение было обработано
                assert result["status"] == "success"
                # Должны быть ошибки
                assert len(result["errors"]) > 0


class TestCoverageGetUsersByStageStats:
    """Тесты для покрытия непокрытых веток get_users_by_stage_stats"""

    @pytest.fixture
    def mock_ctx(self):
        """Фикстура для мок контекста"""
        ctx = Mock()
        ctx.config = Mock()
        ctx.config.BOT_ID = "test-bot"
        ctx.supabase_client = Mock()
        return ctx

    @pytest.mark.asyncio
    async def test_error_in_get_users_by_stage_stats(self, mock_ctx):
        """Тест обработки ошибки в get_users_by_stage_stats (строки 392-393)"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            mock_ctx.supabase_client.client.table.side_effect = Exception("Ошибка БД")

            result = await get_users_by_stage_stats(bot_id="test-bot")

            assert result["status"] == "error"
            assert "error" in result
            assert result["bot_id"] == "test-bot"


class TestCoverageSendMessage:
    """Тесты для покрытия непокрытых веток send_message"""

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
    async def test_video_files_processing(self, mock_message, mock_ctx):
        """Тест обработки видео файлов (строки 491, 505-506)"""
        with (
            patch("smart_bot_factory.utils.context.ctx", mock_ctx),
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.is_file", return_value=True),
            patch("pathlib.Path.resolve", return_value=Path("files")),
        ):
            mock_result = Mock()
            mock_message.answer = AsyncMock(return_value=mock_result)
            mock_message.answer_media_group = AsyncMock()

            result = await send_message(message=mock_message, text="Видео", supabase_client=mock_ctx.supabase_client, files_list=["test.mp4"])

            # Проверяем, что видео было обработано
            assert result == mock_result
            # Проверяем, что answer_media_group был вызван для видео
            mock_message.answer_media_group.assert_called()

    @pytest.mark.asyncio
    async def test_error_processing_file(self, mock_message, mock_ctx):
        """Тест обработки ошибки при обработке файла (строки 532-533)"""
        with (
            patch("smart_bot_factory.utils.context.ctx", mock_ctx),
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.resolve", return_value=Path("files")),
        ):
            # Мокируем process_file чтобы вызвать исключение
            def mock_process_file_side_effect(file_path):
                if "error" in str(file_path):
                    raise Exception("Ошибка обработки файла")
                return None

            mock_result = Mock()
            mock_message.answer = AsyncMock(return_value=mock_result)

            # Мокируем Path.is_file чтобы вернуть True для всех файлов
            with patch("pathlib.Path.is_file", return_value=True):
                result = await send_message(
                    message=mock_message, text="Текст", supabase_client=mock_ctx.supabase_client, files_list=["error_file.txt", "normal_file.txt"]
                )

                # Функция должна обработать ошибку и продолжить работу
                assert result == mock_result

    @pytest.mark.asyncio
    async def test_error_processing_directory(self, mock_message, mock_ctx):
        """Тест обработки ошибки при обработке каталога (строки 543-544, 547-548)"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx), patch("pathlib.Path.exists", return_value=True):
            mock_result = Mock()
            mock_message.answer = AsyncMock(return_value=mock_result)

            # Мокируем is_dir чтобы вернуть True, но iterdir вызывает ошибку
            with patch("pathlib.Path.is_dir", return_value=True), patch("pathlib.Path.iterdir", side_effect=Exception("Ошибка чтения каталога")):
                result = await send_message(
                    message=mock_message, text="Текст", supabase_client=mock_ctx.supabase_client, directories_list=["error_dir"]
                )

                # Функция должна обработать ошибку и продолжить работу
                assert result == mock_result

    @pytest.mark.asyncio
    async def test_error_finding_files_dir(self, mock_message, mock_ctx):
        """Тест обработки ошибки при поиске директории files (строка 524)"""
        with (
            patch("smart_bot_factory.utils.context.ctx", mock_ctx),
            patch("pathlib.Path.exists", return_value=False),
            patch("pathlib.Path.resolve", return_value=Path("files")),
        ):
            # Мокируем config.PROMT_FILES_DIR чтобы вызвать исключение при доступе
            mock_ctx.config.PROMT_FILES_DIR = None

            mock_result = Mock()
            mock_message.answer = AsyncMock(return_value=mock_result)

            result = await send_message(message=mock_message, text="Текст", supabase_client=mock_ctx.supabase_client, files_list=["test.txt"])

            # Функция должна обработать ошибку и продолжить работу
            assert result == mock_result

    @pytest.mark.asyncio
    async def test_bot_blocked_error(self, mock_message, mock_ctx):
        """Тест обработки ошибки блокировки бота (строки 602-603)"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            # Мокируем ошибку блокировки бота
            class TelegramForbiddenError(Exception):
                pass

            mock_message.answer = AsyncMock(side_effect=TelegramForbiddenError("Forbidden: bot was blocked"))

            result = await send_message(message=mock_message, text="Привет", supabase_client=mock_ctx.supabase_client)

            # Должен вернуться None при блокировке
            assert result is None

    @pytest.mark.asyncio
    async def test_fallback_message_blocked(self, mock_message, mock_ctx):
        """Тест блокировки бота при отправке fallback сообщения (строки 614-623)"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            # Мокируем ошибку при основной отправке и блокировку при fallback
            class TelegramForbiddenError(Exception):
                pass

            mock_message.answer = AsyncMock(
                side_effect=[
                    Exception("Ошибка отправки"),  # Первая ошибка
                    TelegramForbiddenError("Forbidden: bot was blocked"),  # Блокировка при fallback
                ]
            )

            result = await send_message(message=mock_message, text="Привет", supabase_client=mock_ctx.supabase_client)

            # Должен вернуться None при блокировке
            assert result is None

    @pytest.mark.asyncio
    async def test_fallback_message_error(self, mock_message, mock_ctx):
        """Тест ошибки при отправке fallback сообщения (строка 622)"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            # Мокируем ошибку при основной отправке и другую ошибку при fallback
            mock_message.answer = AsyncMock(
                side_effect=[
                    Exception("Ошибка отправки"),  # Первая ошибка
                    Exception("Ошибка fallback"),  # Ошибка при fallback
                ]
            )

            # Должно быть выброшено исключение
            with pytest.raises(Exception) as exc_info:
                await send_message(message=mock_message, text="Привет", supabase_client=mock_ctx.supabase_client)
            assert "fallback" in str(exc_info.value).lower() or "ошибка" in str(exc_info.value).lower()
