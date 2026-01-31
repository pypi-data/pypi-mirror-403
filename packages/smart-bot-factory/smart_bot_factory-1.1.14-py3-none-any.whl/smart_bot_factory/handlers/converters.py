"""
Конвертация сообщений между форматами LangChain и OpenAI.
"""

from langchain.messages import AIMessage, HumanMessage, SystemMessage

from .constants import MessageRole


class MessageConverter:
    """
    Класс для конвертации сообщений между форматами LangChain и OpenAI.
    Объединяет все функции конвертации в один класс.
    """

    @staticmethod
    def _is_langchain_message(message):
        """Проверяет, является ли сообщение LangChain сообщением"""
        return isinstance(message, (SystemMessage, AIMessage, HumanMessage))

    @staticmethod
    def _is_openai_dict(message):
        """Проверяет, является ли сообщение словарем OpenAI"""
        return isinstance(message, dict) and "role" in message and "content" in message

    @staticmethod
    def langchain_to_openai(message):
        """
        Конвертирует одно LangChain сообщение в формат OpenAI (словарь).

        Args:
            message: SystemMessage, AIMessage или HumanMessage из LangChain

        Returns:
            dict: Словарь в формате OpenAI {"role": "...", "content": "..."}
        """
        # Сначала проверяем тип через isinstance
        if isinstance(message, SystemMessage):
            role = MessageRole.SYSTEM
        elif isinstance(message, AIMessage):
            role = MessageRole.ASSISTANT
        elif isinstance(message, HumanMessage):
            role = MessageRole.USER
        else:
            # Если не распознали по типу, проверяем атрибут type (может быть "human", "ai", "system")
            message_type = getattr(message, "type", None)
            if message_type == MessageRole.SYSTEM:
                role = MessageRole.SYSTEM
            elif message_type in (MessageRole.AI, MessageRole.ASSISTANT):
                role = MessageRole.ASSISTANT
            elif message_type in (MessageRole.HUMAN, MessageRole.USER):
                role = MessageRole.USER
            else:
                raise ValueError(f"Неподдерживаемый тип сообщения: {type(message)}, type={message_type}")

        content = message.content if hasattr(message, "content") else str(message)

        return {"role": role, "content": content}

    @staticmethod
    def openai_to_langchain(message_dict):
        """
        Конвертирует один словарь OpenAI в LangChain сообщение.

        Args:
            message_dict: Словарь в формате OpenAI {"role": "...", "content": "..."}

        Returns:
            SystemMessage, AIMessage или HumanMessage в зависимости от role
        """
        role = message_dict.get("role", "").lower() if message_dict.get("role") else ""
        content = message_dict.get("content", "")

        # Обрабатываем синонимы: human -> user, ai -> assistant
        if role == MessageRole.SYSTEM:
            return SystemMessage(content=content)
        elif role in (MessageRole.ASSISTANT, MessageRole.AI):
            return AIMessage(content=content)
        elif role in (MessageRole.USER, MessageRole.HUMAN):
            return HumanMessage(content=content)
        else:
            raise ValueError(f"Неподдерживаемый role: {role}")

    @staticmethod
    def langchain_messages_to_openai(messages):
        """
        Конвертирует массив сообщений в массив словарей OpenAI.
        Поддерживает смешанные типы: LangChain сообщения и словари OpenAI.

        Args:
            messages: Список сообщений (LangChain сообщения или словари OpenAI)

        Returns:
            list: Список словарей в формате OpenAI
        """
        result = []
        for msg in messages:
            if MessageConverter._is_openai_dict(msg):
                # Уже в формате OpenAI, оставляем как есть
                result.append(msg)
            elif MessageConverter._is_langchain_message(msg):
                # LangChain сообщение, конвертируем
                result.append(MessageConverter.langchain_to_openai(msg))
            else:
                raise ValueError(f"Неподдерживаемый тип сообщения в массиве: {type(msg)}")
        return result

    @staticmethod
    def openai_messages_to_langchain(messages_list):
        """
        Конвертирует массив сообщений в массив LangChain сообщений.
        Поддерживает смешанные типы: словари OpenAI и LangChain сообщения.

        Args:
            messages_list: Список сообщений (словари OpenAI или LangChain сообщения)

        Returns:
            list: Список LangChain сообщений (SystemMessage, AIMessage, HumanMessage)
        """
        result = []
        for msg in messages_list:
            if MessageConverter._is_langchain_message(msg):
                # Уже LangChain сообщение, оставляем как есть
                result.append(msg)
            elif MessageConverter._is_openai_dict(msg):
                # Словарь OpenAI, конвертируем
                result.append(MessageConverter.openai_to_langchain(msg))
            else:
                raise ValueError(f"Неподдерживаемый тип сообщения в массиве: {type(msg)}")
        return result
