"""Тесты для модуля file_router.router"""

from unittest.mock import Mock

import pytest

from smart_bot_factory.file_router import FileRouter, FileSender


class TestFileRouter:
    """Тесты для класса FileRouter"""

    def test_file_router_init(self):
        """Тест инициализации файлового роутера"""
        router = FileRouter()
        assert router.name == "FileRouter"
        assert router._file_handlers == {}
        assert router._event_handlers == {}

    def test_file_router_init_with_name(self):
        """Тест инициализации файлового роутера с именем"""
        router = FileRouter(name="CustomFileRouter", bot_id="test-bot")
        assert router.name == "CustomFileRouter"
        assert router.bot_id == "test-bot"

    def test_file_handler_with_name(self):
        """Тест декоратора file_handler с явным указанием name"""
        router = FileRouter()

        @router.file_handler(name="send_presentation")
        async def send_presentation(file_sender: FileSender):
            return {"status": "sent"}

        handlers = router.get_file_handlers()
        assert "send_presentation" in handlers
        assert handlers["send_presentation"]["name"] == "send_presentation"
        assert handlers["send_presentation"]["once_only"] is False

    def test_file_handler_without_name(self):
        """Тест декоратора file_handler без указания name (автоматическое имя из функции)"""
        router = FileRouter()

        @router.file_handler()
        async def send_catalog(file_sender: FileSender):
            return {"status": "sent"}

        handlers = router.get_file_handlers()
        assert "send_catalog" in handlers
        assert handlers["send_catalog"]["name"] == "send_catalog"

    def test_file_handler_without_parentheses(self):
        """Тест декоратора file_handler без скобок (автоматическое имя из функции)"""
        router = FileRouter()

        @router.file_handler
        async def send_files(file_sender: FileSender):
            return {"status": "sent"}

        handlers = router.get_file_handlers()
        assert "send_files" in handlers
        assert handlers["send_files"]["name"] == "send_files"

    def test_file_handler_with_once_only(self):
        """Тест file_handler с параметром once_only"""
        router = FileRouter()

        @router.file_handler(name="send_once", once_only=True)
        async def send_once(file_sender: FileSender):
            return {"status": "sent"}

        handlers = router.get_file_handlers()
        assert "send_once" in handlers
        assert handlers["send_once"]["once_only"] is True

    def test_file_handler_registers_in_event_handlers(self):
        """Тест что file_handler регистрируется также в event_handlers"""
        router = FileRouter()

        @router.file_handler(name="test_event")
        async def test_handler(file_sender: FileSender):
            return {"status": "ok"}

        event_handlers = router.get_event_handlers()
        assert "test_event" in event_handlers
        assert event_handlers["test_event"]["file_handler"] is True
        assert event_handlers["test_event"]["notify"] is False
        assert event_handlers["test_event"]["send_ai_response"] is False

    def test_has_file_handler(self):
        """Тест метода has_file_handler"""
        router = FileRouter()

        @router.file_handler(name="test_handler")
        async def test_handler(file_sender: FileSender):
            return {"status": "ok"}

        assert router.has_file_handler("test_handler") is True
        assert router.has_file_handler("non_existent") is False

    def test_get_file_handlers(self):
        """Тест получения всех файловых обработчиков"""
        router = FileRouter()

        @router.file_handler(name="handler1")
        async def handler1(file_sender: FileSender):
            pass

        @router.file_handler(name="handler2")
        async def handler2(file_sender: FileSender):
            pass

        handlers = router.get_file_handlers()
        assert len(handlers) == 2
        assert "handler1" in handlers
        assert "handler2" in handlers

    @pytest.mark.asyncio
    async def test_file_handler_wrapper_execution(self):
        """Тест выполнения wrapper функции file_handler"""
        router = FileRouter()

        call_result = None

        @router.file_handler(name="test_execution")
        async def test_handler(file_sender: FileSender):
            nonlocal call_result
            call_result = file_sender
            return {"result": "success"}

        # Создаем mock FileSender с нужными атрибутами для проверки в wrapper
        mock_file_sender = Mock()
        mock_file_sender.user_id = 123
        mock_file_sender.chat_id = 123
        mock_file_sender.send_before = Mock()

        # Получаем wrapper функцию из event_handlers (там она обернута)
        handler_info = router.get_event_handlers()["test_execution"]
        handler = handler_info["handler"]

        # Вызываем wrapper - он должен вернуть словарь с результатом
        result = await handler(mock_file_sender)

        # Проверяем что функция была вызвана с правильным file_sender
        assert call_result == mock_file_sender

        # Проверяем структуру результата wrapper
        assert isinstance(result, dict)
        assert "file_sender" in result
        assert result["file_sender"] == mock_file_sender
        assert result["router"] == "FileRouter"
        assert result["file_handler"] is True
        assert result["result"]["result"] == "success"

    def test_file_handler_multiple_without_name(self):
        """Тест нескольких file_handler без указания name"""
        router = FileRouter()

        @router.file_handler()
        async def handler_one(file_sender: FileSender):
            pass

        @router.file_handler()
        async def handler_two(file_sender: FileSender):
            pass

        handlers = router.get_file_handlers()
        assert "handler_one" in handlers
        assert "handler_two" in handlers
        assert len(handlers) == 2

    def test_file_handler_inherits_from_event_router(self):
        """Тест что FileRouter наследуется от EventRouter"""
        router = FileRouter()

        # Проверяем что методы EventRouter доступны
        assert hasattr(router, "event_handler")
        assert hasattr(router, "schedule_task")
        assert hasattr(router, "global_handler")
        assert hasattr(router, "get_event_handlers")
        assert hasattr(router, "get_scheduled_tasks")
        assert hasattr(router, "get_global_handlers")
