"""Тесты для file_router.execution"""

import inspect
from unittest.mock import AsyncMock, Mock, patch

import pytest

from smart_bot_factory.file_router.execution import execute_file_event_handler
from smart_bot_factory.file_router.sender import FileSender


class TestExecuteFileEventHandler:
    """Тесты для функции execute_file_event_handler"""

    @pytest.fixture
    def mock_file_sender(self):
        """Фикстура для мок FileSender"""
        sender = Mock(spec=FileSender)
        sender.user_id = 123456
        sender.chat_id = 123456
        return sender

    @pytest.mark.asyncio
    async def test_handler_not_found(self, mock_file_sender):
        """Тест ошибки когда обработчик не найден (строки 34-37)"""
        with patch("smart_bot_factory.file_router.execution._get_registry") as mock_get_registry:
            mock_get_registry.return_value = ({}, "test_source")

            with pytest.raises(ValueError) as exc_info:
                await execute_file_event_handler("nonexistent", mock_file_sender)

            assert "не найден" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_handler_not_file_handler(self, mock_file_sender):
        """Тест ошибки когда обработчик не является файловым (строки 42-43)"""
        with patch("smart_bot_factory.file_router.execution._get_registry") as mock_get_registry:
            mock_get_registry.return_value = (
                {
                    "test_handler": {
                        "handler": AsyncMock(),
                        "file_handler": False,  # Не файловый обработчик
                    }
                },
                "test_source",
            )

            with pytest.raises(ValueError) as exc_info:
                await execute_file_event_handler("test_handler", mock_file_sender)

            assert "не является файловым обработчиком" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_handler_with_only_file_sender(self, mock_file_sender):
        """Тест обработчика с одним параметром file_sender (строки 58-60)"""

        async def handler(file_sender: FileSender):
            return {"status": "ok", "file_sender": file_sender}

        with patch("smart_bot_factory.file_router.execution._get_registry") as mock_get_registry:
            mock_get_registry.return_value = ({"test_handler": {"handler": handler, "file_handler": True}}, "test_source")

            result = await execute_file_event_handler("test_handler", mock_file_sender)

            assert result["status"] == "ok"
            assert result["file_sender"] == mock_file_sender

    @pytest.mark.asyncio
    async def test_handler_with_file_sender_and_user_id(self, mock_file_sender):
        """Тест обработчика с file_sender и user_id (строки 61-63)"""

        async def handler(file_sender: FileSender, user_id: int):
            return {"status": "ok", "user_id": user_id}

        with patch("smart_bot_factory.file_router.execution._get_registry") as mock_get_registry:
            mock_get_registry.return_value = ({"test_handler": {"handler": handler, "file_handler": True}}, "test_source")

            result = await execute_file_event_handler("test_handler", mock_file_sender, user_id=789012)

            assert result["status"] == "ok"
            assert result["user_id"] == 789012

    @pytest.mark.asyncio
    async def test_handler_with_file_sender_user_id_and_event_info(self, mock_file_sender):
        """Тест обработчика с file_sender, user_id и event_info (строки 67-68)"""

        async def handler(file_sender: FileSender, user_id: int, event_info: str):
            return {"status": "ok", "user_id": user_id, "event_info": event_info}

        with patch("smart_bot_factory.file_router.execution._get_registry") as mock_get_registry:
            mock_get_registry.return_value = ({"test_handler": {"handler": handler, "file_handler": True}}, "test_source")

            result = await execute_file_event_handler("test_handler", mock_file_sender, user_id=789012, event_info="test_info")

            assert result["status"] == "ok"
            assert result["user_id"] == 789012
            assert result["event_info"] == "test_info"

    @pytest.mark.asyncio
    async def test_handler_with_file_sender_and_user_id_only(self, mock_file_sender):
        """Тест обработчика с file_sender и user_id (без event_info) (строки 69-70)"""

        async def handler(file_sender: FileSender, user_id: int):
            return {"status": "ok", "user_id": user_id}

        with patch("smart_bot_factory.file_router.execution._get_registry") as mock_get_registry:
            mock_get_registry.return_value = ({"test_handler": {"handler": handler, "file_handler": True}}, "test_source")

            result = await execute_file_event_handler("test_handler", mock_file_sender, user_id=789012)

            assert result["status"] == "ok"
            assert result["user_id"] == 789012

    @pytest.mark.asyncio
    async def test_handler_fallback_to_file_sender_only(self, mock_file_sender):
        """Тест fallback на вызов только с file_sender (строки 71-72)"""

        async def handler(file_sender: FileSender):
            return {"status": "ok"}

        with patch("smart_bot_factory.file_router.execution._get_registry") as mock_get_registry:
            mock_get_registry.return_value = ({"test_handler": {"handler": handler, "file_handler": True}}, "test_source")

            result = await execute_file_event_handler("test_handler", mock_file_sender)

            assert result["status"] == "ok"

    @pytest.mark.asyncio
    async def test_handler_unexpected_signature_fallback(self, mock_file_sender):
        """Тест обработки неожиданной сигнатуры (строки 73-75)"""

        async def handler(file_sender: FileSender):
            return {"status": "ok"}

        with patch("smart_bot_factory.file_router.execution._get_registry") as mock_get_registry:
            mock_get_registry.return_value = ({"test_handler": {"handler": handler, "file_handler": True}}, "test_source")

            result = await execute_file_event_handler("test_handler", mock_file_sender)

            assert result["status"] == "ok"

    @pytest.mark.asyncio
    async def test_handler_typeerror_fallback(self, mock_file_sender):
        """Тест обработки TypeError с fallback на file_sender (строки 77-84)"""
        call_count = {"attempts": 0}

        async def handler(*args, **kwargs):
            call_count["attempts"] += 1
            if call_count["attempts"] == 1:
                # Первый вызов вызывает TypeError
                raise TypeError("Wrong arguments")
            return {"status": "ok"}

        with patch("smart_bot_factory.file_router.execution._get_registry") as mock_get_registry:
            mock_get_registry.return_value = ({"test_handler": {"handler": handler, "file_handler": True}}, "test_source")

            # Мокируем inspect.signature чтобы вернуть сигнатуру, которая вызовет TypeError
            with patch("inspect.signature") as mock_signature:
                # Первый вызов вызывает TypeError при попытке вызвать с параметрами
                mock_sig = Mock()
                mock_sig.parameters = {
                    "file_sender": Mock(default=inspect.Parameter.empty),
                    "user_id": Mock(default=inspect.Parameter.empty),
                    "event_info": Mock(default=inspect.Parameter.empty),
                }
                mock_signature.return_value = mock_sig

                result = await execute_file_event_handler("test_handler", mock_file_sender, user_id=789012, event_info="test")

                assert result["status"] == "ok"
                assert call_count["attempts"] == 2  # Два вызова: первый с ошибкой, второй успешный

    @pytest.mark.asyncio
    async def test_handler_exception_propagation(self, mock_file_sender):
        """Тест распространения исключения при ошибке (строки 85-87)"""

        async def handler(file_sender: FileSender):
            raise ValueError("Handler error")

        with patch("smart_bot_factory.file_router.execution._get_registry") as mock_get_registry:
            mock_get_registry.return_value = ({"test_handler": {"handler": handler, "file_handler": True}}, "test_source")

            with pytest.raises(ValueError) as exc_info:
                await execute_file_event_handler("test_handler", mock_file_sender)

            assert "Handler error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_handler_with_optional_parameters(self, mock_file_sender):
        """Тест обработчика с опциональными параметрами"""

        async def handler(file_sender: FileSender, user_id: int = None, event_info: str = None):
            return {"status": "ok", "user_id": user_id, "event_info": event_info}

        with patch("smart_bot_factory.file_router.execution._get_registry") as mock_get_registry:
            mock_get_registry.return_value = ({"test_handler": {"handler": handler, "file_handler": True}}, "test_source")

            # Обработчик имеет только один обязательный параметр (file_sender)
            result = await execute_file_event_handler("test_handler", mock_file_sender)

            assert result["status"] == "ok"
