"""Тесты для MessageConverter"""

import pytest
from langchain.messages import AIMessage, HumanMessage, SystemMessage

from smart_bot_factory.handlers.constants import MessageRole
from smart_bot_factory.handlers.converters import MessageConverter


class TestMessageConverter:
    """Тесты для класса MessageConverter"""

    def test_langchain_to_openai_system_message(self):
        """Тест конвертации SystemMessage в формат OpenAI"""
        message = SystemMessage(content="System prompt")
        result = MessageConverter.langchain_to_openai(message)

        assert result["role"] == MessageRole.SYSTEM
        assert result["content"] == "System prompt"

    def test_langchain_to_openai_ai_message(self):
        """Тест конвертации AIMessage в формат OpenAI"""
        message = AIMessage(content="AI response")
        result = MessageConverter.langchain_to_openai(message)

        assert result["role"] == MessageRole.ASSISTANT
        assert result["content"] == "AI response"

    def test_langchain_to_openai_human_message(self):
        """Тест конвертации HumanMessage в формат OpenAI"""
        message = HumanMessage(content="User message")
        result = MessageConverter.langchain_to_openai(message)

        assert result["role"] == MessageRole.USER
        assert result["content"] == "User message"

    def test_openai_to_langchain_system(self):
        """Тест конвертации словаря OpenAI в SystemMessage"""
        message_dict = {"role": MessageRole.SYSTEM, "content": "System prompt"}
        result = MessageConverter.openai_to_langchain(message_dict)

        assert isinstance(result, SystemMessage)
        assert result.content == "System prompt"

    def test_openai_to_langchain_assistant(self):
        """Тест конвертации словаря OpenAI в AIMessage"""
        message_dict = {"role": MessageRole.ASSISTANT, "content": "AI response"}
        result = MessageConverter.openai_to_langchain(message_dict)

        assert isinstance(result, AIMessage)
        assert result.content == "AI response"

    def test_openai_to_langchain_user(self):
        """Тест конвертации словаря OpenAI в HumanMessage"""
        message_dict = {"role": MessageRole.USER, "content": "User message"}
        result = MessageConverter.openai_to_langchain(message_dict)

        assert isinstance(result, HumanMessage)
        assert result.content == "User message"

    def test_openai_to_langchain_human_synonym(self):
        """Тест конвертации с синонимом human"""
        message_dict = {"role": "human", "content": "User message"}
        result = MessageConverter.openai_to_langchain(message_dict)

        assert isinstance(result, HumanMessage)
        assert result.content == "User message"

    def test_openai_to_langchain_ai_synonym(self):
        """Тест конвертации с синонимом ai"""
        message_dict = {"role": "ai", "content": "AI response"}
        result = MessageConverter.openai_to_langchain(message_dict)

        assert isinstance(result, AIMessage)
        assert result.content == "AI response"

    def test_langchain_messages_to_openai_mixed(self):
        """Тест конвертации смешанного списка сообщений"""
        messages = [
            SystemMessage(content="System"),
            {"role": MessageRole.USER, "content": "User"},
            AIMessage(content="AI"),
        ]

        result = MessageConverter.langchain_messages_to_openai(messages)

        assert len(result) == 3
        assert result[0]["role"] == MessageRole.SYSTEM
        assert result[1]["role"] == MessageRole.USER
        assert result[2]["role"] == MessageRole.ASSISTANT

    def test_openai_messages_to_langchain_mixed(self):
        """Тест конвертации смешанного списка словарей в LangChain"""
        messages = [
            {"role": MessageRole.SYSTEM, "content": "System"},
            HumanMessage(content="User"),
            {"role": MessageRole.ASSISTANT, "content": "AI"},
        ]

        result = MessageConverter.openai_messages_to_langchain(messages)

        assert len(result) == 3
        assert isinstance(result[0], SystemMessage)
        assert isinstance(result[1], HumanMessage)
        assert isinstance(result[2], AIMessage)

    def test_langchain_messages_to_openai_empty(self):
        """Тест конвертации пустого списка"""
        result = MessageConverter.langchain_messages_to_openai([])
        assert result == []

    def test_openai_messages_to_langchain_empty(self):
        """Тест конвертации пустого списка"""
        result = MessageConverter.openai_messages_to_langchain([])
        assert result == []

    def test_langchain_to_openai_invalid_type(self):
        """Тест ошибки при неверном типе сообщения"""
        with pytest.raises(ValueError):
            MessageConverter.langchain_to_openai("invalid")

    def test_openai_to_langchain_invalid_role(self):
        """Тест ошибки при неверном role"""
        message_dict = {"role": "invalid", "content": "test"}
        with pytest.raises(ValueError):
            MessageConverter.openai_to_langchain(message_dict)

    def test_langchain_messages_to_openai_invalid_type(self):
        """Тест ошибки при неверном типе в массиве"""
        messages = [SystemMessage(content="test"), "invalid"]
        with pytest.raises(ValueError):
            MessageConverter.langchain_messages_to_openai(messages)
