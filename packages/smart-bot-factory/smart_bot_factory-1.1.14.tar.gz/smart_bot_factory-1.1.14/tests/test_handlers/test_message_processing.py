"""Тесты для message_processing"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from aiogram.types import Message, User

from smart_bot_factory.handlers.constants import AIMetadataKey, HookType, MessageRole
from smart_bot_factory.handlers.message_processing import (
    _build_context,
    _enrich_prompt,
    _process_ai_response,
    _process_metadata,
    _validate_message,
)


class TestValidateMessage:
    """Тесты для функции _validate_message"""

    @pytest.fixture
    def mock_message(self):
        """Фикстура для мок сообщения"""
        message = Mock(spec=Message)
        message.text = "Test message"
        message.from_user = Mock(spec=User)
        message.from_user.id = 123456789
        return message

    @pytest.mark.asyncio
    async def test_validate_message_no_validators(self, mock_message):
        """Тест валидации без валидаторов"""
        result = await _validate_message("test", mock_message, {})
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_message_passed(self, mock_message):
        """Тест успешной валидации"""

        async def validator(text, message):
            return True

        message_hooks = {HookType.VALIDATORS: [validator]}
        result = await _validate_message("test", mock_message, message_hooks)
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_message_blocked(self, mock_message):
        """Тест блокировки валидатором"""

        async def validator(text, message):
            return False

        message_hooks = {HookType.VALIDATORS: [validator]}
        result = await _validate_message("test", mock_message, message_hooks)
        assert result is False

    @pytest.mark.asyncio
    async def test_validate_message_error(self, mock_message):
        """Тест обработки ошибки в валидаторе"""

        async def validator(text, message):
            raise ValueError("Test error")

        message_hooks = {HookType.VALIDATORS: [validator]}
        # Должен продолжить выполнение несмотря на ошибку
        result = await _validate_message("test", mock_message, message_hooks)
        assert result is True


class TestEnrichPrompt:
    """Тесты для функции _enrich_prompt"""

    @pytest.mark.asyncio
    async def test_enrich_prompt_basic(self):
        """Тест базового обогащения промпта"""
        system_prompt = "System prompt"
        result_prompt, time_info = await _enrich_prompt(system_prompt, 123456789, {})

        assert "System prompt" in result_prompt
        assert "ТЕКУЩЕЕ ВРЕМЯ" in result_prompt
        assert time_info is not None

    @pytest.mark.asyncio
    async def test_enrich_prompt_with_enricher(self):
        """Тест обогащения промпта через хук"""

        async def enricher(prompt, user_id):
            return prompt + "\n\nEnriched content"

        message_hooks = {HookType.PROMPT_ENRICHERS: [enricher]}
        result_prompt, time_info = await _enrich_prompt("System prompt", 123456789, message_hooks)

        assert "Enriched content" in result_prompt

    @pytest.mark.asyncio
    async def test_enrich_prompt_time_info(self):
        """Тест что time_info содержит время"""
        _, time_info = await _enrich_prompt("System prompt", 123456789, {})

        assert time_info is not None
        assert isinstance(time_info, str)
        assert len(time_info) > 0


class TestBuildContext:
    """Тесты для функции _build_context"""

    @pytest.fixture
    def mock_prompt_loader(self):
        """Фикстура для мок загрузчика промптов"""
        loader = Mock()
        loader.load_final_instructions = AsyncMock(return_value="Final instructions")
        return loader

    @pytest.fixture
    def mock_memory_manager(self):
        """Фикстура для мок менеджера памяти"""
        manager = Mock()
        manager.get_memory_messages = AsyncMock(
            return_value=[
                {"role": MessageRole.USER, "content": "User message"},
                {"role": MessageRole.ASSISTANT, "content": "AI response"},
            ]
        )
        return manager

    @pytest.mark.asyncio
    async def test_build_context_basic(self, mock_prompt_loader, mock_memory_manager):
        """Тест построения базового контекста"""
        messages = await _build_context("System prompt", "session-123", mock_prompt_loader, mock_memory_manager, {}, "12:00, 01.01.2024, Monday")

        assert len(messages) >= 3  # system + history + final instructions
        assert messages[0]["role"] == MessageRole.SYSTEM
        assert "System prompt" in messages[0]["content"]

    @pytest.mark.asyncio
    async def test_build_context_with_history(self, mock_prompt_loader, mock_memory_manager):
        """Тест построения контекста с историей"""
        messages = await _build_context("System prompt", "session-123", mock_prompt_loader, mock_memory_manager, {}, "12:00, 01.01.2024, Monday")

        # Проверяем что история добавлена
        user_messages = [m for m in messages if m.get("role") == MessageRole.USER]
        assert len(user_messages) > 0

    @pytest.mark.asyncio
    async def test_build_context_with_enricher(self, mock_prompt_loader, mock_memory_manager):
        """Тест построения контекста с обогатителем"""

        async def enricher(messages):
            messages.append({"role": MessageRole.SYSTEM, "content": "Enriched"})
            return messages

        message_hooks = {HookType.CONTEXT_ENRICHERS: [enricher]}
        messages = await _build_context(
            "System prompt", "session-123", mock_prompt_loader, mock_memory_manager, message_hooks, "12:00, 01.01.2024, Monday"
        )

        # Проверяем что обогащение применено
        enriched = [m for m in messages if m.get("content") == "Enriched"]
        assert len(enriched) > 0


class TestProcessAIResponse:
    """Тесты для функции _process_ai_response"""

    @pytest.fixture
    def mock_openai_client(self):
        """Фикстура для мок OpenAI клиента"""
        client = Mock()

        # Мокаем ответ от OpenAI
        response = Mock()
        response.user_message = "AI response"
        response.service_info = {"этап": "test"}

        client.get_completion = AsyncMock(return_value=response)
        return client

    @pytest.mark.asyncio
    async def test_process_ai_response_basic(self, mock_openai_client):
        """Тест базовой обработки ответа AI"""
        messages = [
            {"role": MessageRole.SYSTEM, "content": "System"},
            {"role": MessageRole.USER, "content": "User"},
        ]

        response_text, ai_metadata, processing_time, ai_response = await _process_ai_response(messages, mock_openai_client, {}, 123456789)

        assert response_text == "AI response"
        assert ai_metadata == {"этап": "test"}
        assert processing_time >= 0  # Может быть 0 если выполнение очень быстрое
        assert ai_response is not None

    @pytest.mark.asyncio
    async def test_process_ai_response_empty(self, mock_openai_client):
        """Тест обработки пустого ответа"""
        response = Mock()
        response.user_message = ""
        response.service_info = {}
        mock_openai_client.get_completion = AsyncMock(return_value=response)

        messages = [{"role": MessageRole.USER, "content": "User"}]
        response_text, ai_metadata, _, _ = await _process_ai_response(messages, mock_openai_client, {}, 123456789)

        assert "ошибка" in response_text.lower() or "error" in response_text.lower()

    @pytest.mark.asyncio
    async def test_process_ai_response_with_processor(self, mock_openai_client):
        """Тест обработки ответа через процессор"""

        async def processor(response_text, metadata, user_id):
            return f"Processed: {response_text}", metadata

        message_hooks = {HookType.RESPONSE_PROCESSORS: [processor]}
        messages = [{"role": MessageRole.USER, "content": "User"}]

        response_text, _, _, _ = await _process_ai_response(messages, mock_openai_client, message_hooks, 123456789)

        assert "Processed:" in response_text


class TestProcessMetadata:
    """Тесты для функции _process_metadata"""

    @pytest.fixture
    def mock_supabase_client(self):
        """Фикстура для мок Supabase клиента"""
        client = Mock()
        client.update_session_all = AsyncMock()
        client.update_session_service_info = AsyncMock()
        return client

    @pytest.mark.asyncio
    async def test_process_metadata_empty(self, mock_supabase_client):
        """Тест обработки пустых метаданных"""
        should_send, file_senders = await _process_metadata({}, "session-123", 123456789, mock_supabase_client, "Response")

        assert should_send is True
        assert file_senders == []

    @pytest.mark.asyncio
    async def test_process_metadata_stage(self, mock_supabase_client):
        """Тест обработки этапа"""
        ai_metadata = {AIMetadataKey.STAGE: "introduction"}

        should_send, _ = await _process_metadata(ai_metadata, "session-123", 123456789, mock_supabase_client, "Response")

        assert should_send is True
        mock_supabase_client.update_session_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_metadata_quality(self, mock_supabase_client):
        """Тест обработки качества"""
        ai_metadata = {AIMetadataKey.QUALITY: 8}

        should_send, _ = await _process_metadata(ai_metadata, "session-123", 123456789, mock_supabase_client, "Response")

        assert should_send is True
        mock_supabase_client.update_session_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_metadata_events(self, mock_supabase_client):
        """Тест обработки событий"""

        async def mock_process_events(session_id, events, user_id):
            return True

        with patch("smart_bot_factory.handlers.message_processing.process_events", side_effect=mock_process_events):
            ai_metadata = {AIMetadataKey.EVENTS: [{AIMetadataKey.EVENT_TYPE: "телефон", AIMetadataKey.EVENT_INFO: "+1234567890"}]}

            should_send, _ = await _process_metadata(ai_metadata, "session-123", 123456789, mock_supabase_client, "Response")

            assert should_send is True
