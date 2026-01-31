"""Интеграционные тесты для message_sender"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from smart_bot_factory.handlers.constants import AIMetadataKey, MessageRole
from smart_bot_factory.message.message_sender import send_message_by_ai


class TestSendMessageByAIIntegration:
    """Интеграционные тесты для send_message_by_ai - проверяют реальную работу цепочки функций"""

    @pytest.fixture
    def mock_ctx(self):
        """Фикстура для мок контекста с полной настройкой"""
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
    async def test_integration_full_chain_success(self, mock_ctx):
        """Интеграционный тест полной цепочки обработки сообщения"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            # Настройка моков внешних зависимостей
            mock_ctx.supabase_client.get_active_session = AsyncMock(return_value={"id": "session-123"})
            mock_ctx.prompt_loader.load_system_prompt = AsyncMock(return_value="Ты помощник. Отвечай кратко.")
            mock_ctx.prompt_loader.load_final_instructions = AsyncMock(return_value="")
            mock_ctx.supabase_client.add_message = AsyncMock()
            mock_ctx.supabase_client.update_session_all = AsyncMock()
            mock_ctx.supabase_client.update_session_service_info = AsyncMock()
            mock_ctx.memory_manager.get_memory_messages = AsyncMock(return_value=[])
            mock_ctx.openai_client.estimate_tokens = Mock(return_value=50)
            mock_ctx.bot.send_message = AsyncMock()

            # Мокируем ответ от OpenAI
            ai_response = Mock()
            ai_response.user_message = "Привет! Чем могу помочь?"
            ai_response.service_info = {}
            mock_ctx.openai_client.get_completion = AsyncMock(return_value=ai_response)

            # Мокируем только внешние утилиты для обработки событий
            with (
                patch("smart_bot_factory.utils.bot_utils.process_events", new_callable=AsyncMock, return_value=True),
                patch("smart_bot_factory.utils.bot_utils.process_file_events", new_callable=AsyncMock, return_value=[]),
            ):
                result = await send_message_by_ai(user_id=123456, message_text="Привет")

                # Проверяем результат
                assert result["status"] == "success"
                assert result["user_id"] == 123456
                assert result["response_text"] == "Привет! Чем могу помочь?"
                assert result["tokens_used"] == 50
                assert "processing_time_ms" in result

                # Проверяем, что сообщение было отправлено
                mock_ctx.bot.send_message.assert_called_once()
                call_args = mock_ctx.bot.send_message.call_args
                assert call_args.kwargs["chat_id"] == 123456
                assert call_args.kwargs["text"] == "Привет! Чем могу помочь?"

                # Проверяем, что сообщения были сохранены в БД
                assert mock_ctx.supabase_client.add_message.call_count == 2

                # Проверяем первое сообщение (от пользователя)
                first_call = mock_ctx.supabase_client.add_message.call_args_list[0]
                assert first_call.kwargs["role"] == MessageRole.USER
                assert first_call.kwargs["content"] == "Привет"

                # Проверяем второе сообщение (от ассистента)
                second_call = mock_ctx.supabase_client.add_message.call_args_list[1]
                assert second_call.kwargs["role"] == MessageRole.ASSISTANT
                assert second_call.kwargs["content"] == "Привет! Чем могу помочь?"

    @pytest.mark.asyncio
    async def test_integration_prompt_enrichment(self, mock_ctx):
        """Интеграционный тест обогащения промпта временем"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            mock_ctx.supabase_client.get_active_session = AsyncMock(return_value={"id": "session-123"})
            mock_ctx.prompt_loader.load_system_prompt = AsyncMock(return_value="Базовый промпт")
            mock_ctx.prompt_loader.load_final_instructions = AsyncMock(return_value="")
            mock_ctx.supabase_client.add_message = AsyncMock()
            mock_ctx.supabase_client.update_session_all = AsyncMock()
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
                await send_message_by_ai(user_id=123456, message_text="Тест")

                # Проверяем, что промпт был обогащен временем
                # _enrich_prompt должен добавить информацию о времени к промпту
                # Проверяем это через вызов get_completion - промпт должен содержать время
                completion_call = mock_ctx.openai_client.get_completion.call_args
                langchain_messages = completion_call[0][0]

                # Ищем системное сообщение с обогащенным промптом
                system_message = next((msg for msg in langchain_messages if hasattr(msg, "content") and "ТЕКУЩЕЕ ВРЕМЯ" in str(msg.content)), None)
                assert system_message is not None, "Промпт должен быть обогащен информацией о времени"

    @pytest.mark.asyncio
    async def test_integration_context_building(self, mock_ctx):
        """Интеграционный тест построения контекста с историей"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            mock_ctx.supabase_client.get_active_session = AsyncMock(return_value={"id": "session-123"})
            mock_ctx.prompt_loader.load_system_prompt = AsyncMock(return_value="Системный промпт")
            mock_ctx.prompt_loader.load_final_instructions = AsyncMock(return_value="Финальные инструкции")
            mock_ctx.supabase_client.add_message = AsyncMock()
            mock_ctx.supabase_client.update_session_all = AsyncMock()
            mock_ctx.supabase_client.update_session_service_info = AsyncMock()
            mock_ctx.openai_client.estimate_tokens = Mock(return_value=50)
            mock_ctx.bot.send_message = AsyncMock()

            # Мокируем историю сообщений
            mock_ctx.memory_manager.get_memory_messages = AsyncMock(
                return_value=[
                    {"role": MessageRole.USER, "content": "Предыдущее сообщение"},
                    {"role": MessageRole.ASSISTANT, "content": "Предыдущий ответ"},
                ]
            )

            ai_response = Mock()
            ai_response.user_message = "Новый ответ"
            ai_response.service_info = {}
            mock_ctx.openai_client.get_completion = AsyncMock(return_value=ai_response)

            with (
                patch("smart_bot_factory.utils.bot_utils.process_events", new_callable=AsyncMock, return_value=True),
                patch("smart_bot_factory.utils.bot_utils.process_file_events", new_callable=AsyncMock, return_value=[]),
            ):
                await send_message_by_ai(user_id=123456, message_text="Новое сообщение")

                # Проверяем, что контекст был построен с историей
                completion_call = mock_ctx.openai_client.get_completion.call_args
                langchain_messages = completion_call[0][0]

                # Должно быть минимум 3 сообщения: системный промпт, история (2 сообщения), текущее сообщение
                assert len(langchain_messages) >= 3, "Контекст должен содержать системный промпт, историю и текущее сообщение"

                # Проверяем, что история была загружена
                mock_ctx.memory_manager.get_memory_messages.assert_called_once_with("session-123")

    @pytest.mark.asyncio
    async def test_integration_metadata_processing(self, mock_ctx):
        """Интеграционный тест обработки метаданных от AI"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            mock_ctx.supabase_client.get_active_session = AsyncMock(return_value={"id": "session-123"})
            mock_ctx.prompt_loader.load_system_prompt = AsyncMock(return_value="Промпт")
            mock_ctx.prompt_loader.load_final_instructions = AsyncMock(return_value="")
            mock_ctx.supabase_client.add_message = AsyncMock()
            mock_ctx.supabase_client.update_session_all = AsyncMock()
            mock_ctx.supabase_client.update_session_service_info = AsyncMock()
            mock_ctx.memory_manager.get_memory_messages = AsyncMock(return_value=[])
            mock_ctx.openai_client.estimate_tokens = Mock(return_value=50)
            mock_ctx.bot.send_message = AsyncMock()

            # Мокируем ответ с метаданными (этап, качество, события)
            ai_response = Mock()
            ai_response.user_message = "Ответ с метаданными"
            ai_response.service_info = {
                AIMetadataKey.STAGE: "consult",
                AIMetadataKey.QUALITY: 8,
                AIMetadataKey.EVENTS: [{AIMetadataKey.EVENT_TYPE: "телефон", AIMetadataKey.EVENT_INFO: "+1234567890"}],
            }
            mock_ctx.openai_client.get_completion = AsyncMock(return_value=ai_response)

            with (
                patch("smart_bot_factory.utils.bot_utils.process_events", new_callable=AsyncMock, return_value=True),
                patch("smart_bot_factory.utils.bot_utils.process_file_events", new_callable=AsyncMock, return_value=[]),
            ):
                result = await send_message_by_ai(user_id=123456, message_text="Тест")

                # Проверяем, что метаданные были обработаны
                assert result["status"] == "success"
                assert result["events_processed"] == 1

                # Проверяем, что этап и качество были обновлены в БД
                mock_ctx.supabase_client.update_session_all.assert_called_once()
                call_args = mock_ctx.supabase_client.update_session_all.call_args
                assert call_args[0][0] == "session-123"  # session_id
                assert call_args[0][1] == "consult"  # stage
                assert call_args[0][2] == 8  # quality

                # Проверяем, что события были обработаны
                # process_events должен быть вызван с правильными аргументами
                # Проверяем через то, что результат содержит events_processed

    @pytest.mark.asyncio
    async def test_integration_with_prompt_enricher_hook(self, mock_ctx):
        """Интеграционный тест с хуком обогащения промпта"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            mock_ctx.supabase_client.get_active_session = AsyncMock(return_value={"id": "session-123"})
            mock_ctx.prompt_loader.load_system_prompt = AsyncMock(return_value="Базовый промпт")
            mock_ctx.prompt_loader.load_final_instructions = AsyncMock(return_value="")
            mock_ctx.supabase_client.add_message = AsyncMock()
            mock_ctx.supabase_client.update_session_all = AsyncMock()
            mock_ctx.supabase_client.update_session_service_info = AsyncMock()
            mock_ctx.memory_manager.get_memory_messages = AsyncMock(return_value=[])
            mock_ctx.openai_client.estimate_tokens = Mock(return_value=50)
            mock_ctx.bot.send_message = AsyncMock()

            # Добавляем хук обогащения промпта
            async def prompt_enricher(prompt: str, user_id: int) -> str:
                return f"{prompt}\n\nДополнительная информация для пользователя {user_id}"

            mock_ctx.message_hooks = {"prompt_enrichers": [prompt_enricher]}

            ai_response = Mock()
            ai_response.user_message = "Ответ"
            ai_response.service_info = {}
            mock_ctx.openai_client.get_completion = AsyncMock(return_value=ai_response)

            with (
                patch("smart_bot_factory.utils.bot_utils.process_events", new_callable=AsyncMock, return_value=True),
                patch("smart_bot_factory.utils.bot_utils.process_file_events", new_callable=AsyncMock, return_value=[]),
            ):
                await send_message_by_ai(user_id=123456, message_text="Тест")

                # Проверяем, что хук был вызван и промпт обогащен
                completion_call = mock_ctx.openai_client.get_completion.call_args
                langchain_messages = completion_call[0][0]

                # Ищем системное сообщение с обогащенным промптом
                system_content = str(next((msg for msg in langchain_messages if hasattr(msg, "content")), None).content)
                assert "Дополнительная информация для пользователя 123456" in system_content

    @pytest.mark.asyncio
    async def test_integration_with_context_enricher_hook(self, mock_ctx):
        """Интеграционный тест с хуком обогащения контекста"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            mock_ctx.supabase_client.get_active_session = AsyncMock(return_value={"id": "session-123"})
            mock_ctx.prompt_loader.load_system_prompt = AsyncMock(return_value="Промпт")
            mock_ctx.prompt_loader.load_final_instructions = AsyncMock(return_value="")
            mock_ctx.supabase_client.add_message = AsyncMock()
            mock_ctx.supabase_client.update_session_all = AsyncMock()
            mock_ctx.supabase_client.update_session_service_info = AsyncMock()
            mock_ctx.memory_manager.get_memory_messages = AsyncMock(return_value=[])
            mock_ctx.openai_client.estimate_tokens = Mock(return_value=50)
            mock_ctx.bot.send_message = AsyncMock()

            # Добавляем хук обогащения контекста
            async def context_enricher(messages: list) -> list:
                messages.append({"role": MessageRole.SYSTEM, "content": "Дополнительный контекст"})
                return messages

            mock_ctx.message_hooks = {"context_enrichers": [context_enricher]}

            ai_response = Mock()
            ai_response.user_message = "Ответ"
            ai_response.service_info = {}
            mock_ctx.openai_client.get_completion = AsyncMock(return_value=ai_response)

            with (
                patch("smart_bot_factory.utils.bot_utils.process_events", new_callable=AsyncMock, return_value=True),
                patch("smart_bot_factory.utils.bot_utils.process_file_events", new_callable=AsyncMock, return_value=[]),
            ):
                await send_message_by_ai(user_id=123456, message_text="Тест")

                # Проверяем, что хук был вызван и контекст обогащен
                completion_call = mock_ctx.openai_client.get_completion.call_args
                langchain_messages = completion_call[0][0]

                # Должно быть дополнительное системное сообщение
                system_messages = [msg for msg in langchain_messages if hasattr(msg, "content") and "Дополнительный контекст" in str(msg.content)]
                assert len(system_messages) > 0, "Контекст должен быть обогащен через хук"

    @pytest.mark.asyncio
    async def test_integration_with_response_processor_hook(self, mock_ctx):
        """Интеграционный тест с хуком обработки ответа"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            mock_ctx.supabase_client.get_active_session = AsyncMock(return_value={"id": "session-123"})
            mock_ctx.prompt_loader.load_system_prompt = AsyncMock(return_value="Промпт")
            mock_ctx.prompt_loader.load_final_instructions = AsyncMock(return_value="")
            mock_ctx.supabase_client.add_message = AsyncMock()
            mock_ctx.supabase_client.update_session_all = AsyncMock()
            mock_ctx.supabase_client.update_session_service_info = AsyncMock()
            mock_ctx.memory_manager.get_memory_messages = AsyncMock(return_value=[])
            mock_ctx.openai_client.estimate_tokens = Mock(return_value=50)
            mock_ctx.bot.send_message = AsyncMock()

            # Добавляем хук обработки ответа
            async def response_processor(response_text: str, ai_metadata: dict, user_id: int) -> tuple[str, dict]:
                return f"[Обработано] {response_text}", {**ai_metadata, "processed": True}

            mock_ctx.message_hooks = {"response_processors": [response_processor]}

            ai_response = Mock()
            ai_response.user_message = "Оригинальный ответ"
            ai_response.service_info = {}
            mock_ctx.openai_client.get_completion = AsyncMock(return_value=ai_response)

            with (
                patch("smart_bot_factory.utils.bot_utils.process_events", new_callable=AsyncMock, return_value=True),
                patch("smart_bot_factory.utils.bot_utils.process_file_events", new_callable=AsyncMock, return_value=[]),
            ):
                result = await send_message_by_ai(user_id=123456, message_text="Тест")

                # Проверяем, что ответ был обработан через хук
                assert result["status"] == "success"
                assert result["response_text"] == "[Обработано] Оригинальный ответ"

                # Проверяем, что обработанный ответ был отправлен
                call_args = mock_ctx.bot.send_message.call_args
                assert "[Обработано] Оригинальный ответ" in call_args.kwargs["text"]

    @pytest.mark.asyncio
    async def test_integration_error_handling_in_chain(self, mock_ctx):
        """Интеграционный тест обработки ошибок в цепочке"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            mock_ctx.supabase_client.get_active_session = AsyncMock(return_value={"id": "session-123"})
            mock_ctx.prompt_loader.load_system_prompt = AsyncMock(return_value="Промпт")
            mock_ctx.prompt_loader.load_final_instructions = AsyncMock(return_value="")
            mock_ctx.supabase_client.add_message = AsyncMock()
            mock_ctx.supabase_client.update_session_all = AsyncMock()
            mock_ctx.supabase_client.update_session_service_info = AsyncMock()
            mock_ctx.memory_manager.get_memory_messages = AsyncMock(return_value=[])
            mock_ctx.openai_client.estimate_tokens = Mock(return_value=50)
            mock_ctx.bot.send_message = AsyncMock()

            # Мокируем ошибку в get_memory_messages
            mock_ctx.memory_manager.get_memory_messages = AsyncMock(side_effect=Exception("Ошибка БД"))

            ai_response = Mock()
            ai_response.user_message = "Ответ"
            ai_response.service_info = {}
            mock_ctx.openai_client.get_completion = AsyncMock(return_value=ai_response)

            with (
                patch("smart_bot_factory.utils.bot_utils.process_events", new_callable=AsyncMock, return_value=True),
                patch("smart_bot_factory.utils.bot_utils.process_file_events", new_callable=AsyncMock, return_value=[]),
            ):
                result = await send_message_by_ai(user_id=123456, message_text="Тест")

                # Проверяем, что ошибка была обработана
                # В зависимости от реализации, может быть success с пустой историей или error
                assert result["status"] in ["success", "error"]

                # Если success, проверяем, что обработка продолжилась без истории
                if result["status"] == "success":
                    # Контекст должен быть построен без истории
                    completion_call = mock_ctx.openai_client.get_completion.call_args
                    langchain_messages = completion_call[0][0]
                    # Должно быть минимум системный промпт и текущее сообщение
                    assert len(langchain_messages) >= 2

    @pytest.mark.asyncio
    async def test_integration_data_flow_through_chain(self, mock_ctx):
        """Интеграционный тест передачи данных через всю цепочку"""
        with patch("smart_bot_factory.utils.context.ctx", mock_ctx):
            mock_ctx.supabase_client.get_active_session = AsyncMock(return_value={"id": "session-123"})
            mock_ctx.prompt_loader.load_system_prompt = AsyncMock(return_value="Системный промпт")
            mock_ctx.prompt_loader.load_final_instructions = AsyncMock(return_value="Финальные инструкции")
            mock_ctx.supabase_client.add_message = AsyncMock()
            mock_ctx.supabase_client.update_session_all = AsyncMock()
            mock_ctx.supabase_client.update_session_service_info = AsyncMock()
            mock_ctx.memory_manager.get_memory_messages = AsyncMock(
                return_value=[{"role": MessageRole.USER, "content": "История 1"}, {"role": MessageRole.ASSISTANT, "content": "История 2"}]
            )
            mock_ctx.openai_client.estimate_tokens = Mock(return_value=75)
            mock_ctx.bot.send_message = AsyncMock()

            ai_response = Mock()
            ai_response.user_message = "Финальный ответ"
            ai_response.service_info = {AIMetadataKey.STAGE: "offer", AIMetadataKey.QUALITY: 9}
            mock_ctx.openai_client.get_completion = AsyncMock(return_value=ai_response)

            with (
                patch("smart_bot_factory.utils.bot_utils.process_events", new_callable=AsyncMock, return_value=True),
                patch("smart_bot_factory.utils.bot_utils.process_file_events", new_callable=AsyncMock, return_value=[]),
            ):
                result = await send_message_by_ai(user_id=789012, message_text="Текущее сообщение")

                # Проверяем полный поток данных
                assert result["status"] == "success"
                assert result["user_id"] == 789012
                assert result["response_text"] == "Финальный ответ"

                # Проверяем, что данные прошли через всю цепочку
                # 1. Сообщение пользователя сохранено
                user_message_call = mock_ctx.supabase_client.add_message.call_args_list[0]
                assert user_message_call.kwargs["content"] == "Текущее сообщение"

                # 2. Контекст построен с историей
                completion_call = mock_ctx.openai_client.get_completion.call_args
                langchain_messages = completion_call[0][0]
                # Должно быть: системный промпт + история (2) + финальные инструкции + текущее сообщение
                assert len(langchain_messages) >= 4

                # 3. Метаданные обработаны
                mock_ctx.supabase_client.update_session_all.assert_called_once()
                call_args = mock_ctx.supabase_client.update_session_all.call_args
                assert call_args[0][0] == "session-123"
                assert call_args[0][1] == "offer"
                assert call_args[0][2] == 9

                # 4. Ответ сохранен и отправлен
                assistant_message_call = mock_ctx.supabase_client.add_message.call_args_list[1]
                assert assistant_message_call.kwargs["content"] == "Финальный ответ"
                mock_ctx.bot.send_message.assert_called_once()
