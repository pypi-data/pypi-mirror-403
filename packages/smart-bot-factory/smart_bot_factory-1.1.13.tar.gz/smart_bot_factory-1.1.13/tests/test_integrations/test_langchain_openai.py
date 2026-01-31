"""Тесты для langchain_openai"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from langchain.messages import AIMessage, HumanMessage, SystemMessage

from smart_bot_factory.integrations.openai.langchain_openai import LangChainOpenAIClient
from smart_bot_factory.integrations.openai.responce_models import MainResponseModel


class TestLangChainOpenAIClient:
    """Тесты для LangChainOpenAIClient"""

    @pytest.fixture
    def mock_client(self):
        """Фикстура для мок клиента"""
        with patch("smart_bot_factory.integrations.openai.langchain_openai.AsyncOpenAI") as mock:
            client = Mock()
            client.audio = Mock()
            client.audio.transcriptions = Mock()
            client.audio.transcriptions.create = AsyncMock(return_value=Mock(text="Распознанный текст"))
            mock.return_value = client
            yield client

    @pytest.fixture
    def openai_client(self, mock_client):
        """Фикстура для LangChainOpenAIClient"""
        with patch("smart_bot_factory.integrations.openai.langchain_openai.ChatOpenAI") as mock_chat:
            with patch("smart_bot_factory.integrations.openai.langchain_openai.create_agent") as mock_agent:
                mock_chat_instance = Mock()
                mock_chat.return_value = mock_chat_instance

                mock_agent_instance = Mock()
                mock_agent_instance.ainvoke = AsyncMock(
                    return_value={"messages": [AIMessage(content='{"user_message": "Тест", "service_info": {}}')]}
                )
                mock_agent.return_value = mock_agent_instance

                client = LangChainOpenAIClient(api_key="test-key", model="gpt-4", max_tokens=1000, temperature=0.7)
                client.chat_model = mock_agent_instance
                yield client

    def test_init(self, mock_client):
        """Тест инициализации клиента"""
        with patch("smart_bot_factory.integrations.openai.langchain_openai.ChatOpenAI"):
            with patch("smart_bot_factory.integrations.openai.langchain_openai.create_agent"):
                client = LangChainOpenAIClient(api_key="test-key", model="gpt-4", max_tokens=1000)

                assert client.api_key == "test-key"
                assert client.model == "gpt-4"
                assert client.max_tokens == 1000

    def test_is_gpt5(self, openai_client):
        """Тест определения GPT-5"""
        openai_client.model = "gpt-5"
        assert openai_client.is_gpt5 is True

        openai_client.model = "gpt-4"
        assert openai_client.is_gpt5 is False

    def test_get_model_limits(self, openai_client):
        """Тест получения лимитов модели"""
        limits = openai_client._get_model_limits()

        assert "total_context" in limits
        assert "max_input_tokens" in limits
        assert "completion_reserve" in limits
        assert limits["total_context"] > 0

    def test_get_model_limits_gpt5(self, openai_client):
        """Тест лимитов для GPT-5"""
        openai_client.model = "gpt-5"
        limits = openai_client._get_model_limits()

        assert limits["total_context"] == 200000

    def test_convert_messages_to_langchain(self, openai_client):
        """Тест конвертации сообщений в LangChain формат"""
        messages = [
            {"role": "system", "content": "System"},
            {"role": "user", "content": "User"},
            {"role": "assistant", "content": "AI"},
        ]

        result = openai_client._convert_messages_to_langchain(messages)

        assert len(result) == 3
        assert isinstance(result[0], SystemMessage)
        assert isinstance(result[1], HumanMessage)
        assert isinstance(result[2], AIMessage)

    def test_add_tool(self, openai_client):
        """Тест добавления инструмента"""
        mock_tool = Mock()
        mock_tool.name = "test_tool"
        mock_tool.description = "Test tool description"

        openai_client.add_tool(mock_tool, update_agent=False)

        assert len(openai_client._tools) == 1
        assert openai_client._tools[0] == mock_tool

    def test_add_tools(self, openai_client):
        """Тест добавления нескольких инструментов"""
        tool1 = Mock()
        tool1.name = "tool1"
        tool1.description = "Description 1"
        tool2 = Mock()
        tool2.name = "tool2"
        tool2.description = "Description 2"

        openai_client.add_tools([tool1, tool2])

        assert len(openai_client._tools) == 2

    def test_get_tools(self, openai_client):
        """Тест получения списка инструментов"""
        tool1 = Mock()
        openai_client._tools = [tool1]

        tools = openai_client.get_tools()

        assert len(tools) == 1
        assert tools[0] == tool1
        # Проверяем что возвращается копия
        assert tools is not openai_client._tools

    def test_get_tools_description_for_prompt(self, openai_client):
        """Тест получения описания инструментов для промпта"""
        tool = Mock()
        tool.name = "test_tool"
        tool.description = "Test description"
        tool.args_schema = None

        openai_client._tools = [tool]

        description = openai_client.get_tools_description_for_prompt()

        assert "ДОСТУПНЫЕ ИНСТРУМЕНТЫ" in description
        assert "test_tool" in description
        assert "Test description" in description

    def test_get_tools_description_empty(self, openai_client):
        """Тест получения описания когда нет инструментов"""
        description = openai_client.get_tools_description_for_prompt()

        assert description == ""

    @pytest.mark.asyncio
    async def test_get_completion(self, openai_client):
        """Тест получения ответа от AI"""
        messages = [HumanMessage(content="Тест")]

        result = await openai_client.get_completion(messages)

        assert isinstance(result, MainResponseModel)
        assert result.user_message == "Тест"

    @pytest.mark.asyncio
    async def test_get_completion_validation_error(self, openai_client):
        """Тест обработки ошибки валидации JSON"""
        openai_client.chat_model.ainvoke = AsyncMock(return_value={"messages": [AIMessage(content="Невалидный JSON")]})

        result = await openai_client.get_completion([HumanMessage(content="Тест")])

        assert isinstance(result, MainResponseModel)
        assert result.user_message == ""

    def test_estimate_tokens(self, openai_client):
        """Тест оценки токенов"""
        text = "Тестовый текст для оценки токенов"
        tokens = openai_client.estimate_tokens(text)

        assert tokens > 0
        assert isinstance(tokens, int)

    @pytest.mark.asyncio
    async def test_transcribe_audio(self, openai_client, mock_client):
        """Тест распознавания аудио"""
        audio_path = "test.ogg"

        # Мокаем открытие файла
        with patch("builtins.open", create=True) as mock_open:
            mock_file = Mock()
            mock_file.__enter__ = Mock(return_value=mock_file)
            mock_file.__exit__ = Mock(return_value=None)
            mock_file.read = Mock(return_value=b"audio data")
            mock_open.return_value = mock_file

            text = await openai_client.transcribe_audio(audio_path)

            assert text == "Распознанный текст"
            mock_client.audio.transcriptions.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_transcribe_audio_error(self, openai_client, mock_client):
        """Тест обработки ошибки при распознавании"""
        mock_client.audio.transcriptions.create = AsyncMock(side_effect=Exception("Error"))

        text = await openai_client.transcribe_audio("test.ogg")

        assert text == ""

    @pytest.mark.asyncio
    async def test_check_api_health(self, openai_client):
        """Тест проверки здоровья API"""
        with patch("smart_bot_factory.integrations.openai.langchain_openai.ChatOpenAI") as mock_chat:
            mock_model = Mock()
            mock_model.ainvoke = AsyncMock()
            mock_chat.return_value.__or__ = Mock(return_value=mock_model)

            result = await openai_client.check_api_health()

            assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_get_available_models(self, openai_client):
        """Тест получения списка доступных моделей"""
        models = await openai_client.get_available_models()

        assert isinstance(models, list)
        assert len(models) > 0
        assert "gpt-4" in models
        assert "gpt-5" in models
