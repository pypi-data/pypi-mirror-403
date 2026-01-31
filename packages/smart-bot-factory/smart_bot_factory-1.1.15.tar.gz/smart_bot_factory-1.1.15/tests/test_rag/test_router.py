"""Тесты для RagRouter"""

from unittest.mock import Mock, patch

import pytest
from langchain_core.tools import BaseTool

from smart_bot_factory.rag.router import RagRouter


class TestRagRouter:
    """Тесты для класса RagRouter"""

    @pytest.fixture
    def rag_router(self):
        """Фикстура для RagRouter"""
        return RagRouter("test_rag")

    def test_rag_router_initialization(self, rag_router):
        """Тест инициализации RagRouter"""
        assert rag_router.name == "test_rag"
        assert rag_router.get_tools() == []

    def test_rag_router_tool_decorator_without_params(self, rag_router):
        """Тест декоратора tool без параметров"""

        @rag_router.tool
        def test_tool(query: str) -> str:
            """Тестовый инструмент"""
            return f"Результат: {query}"

        tools = rag_router.get_tools()
        assert len(tools) == 1
        assert isinstance(tools[0], BaseTool)
        assert tools[0].name == "test_tool"

    def test_rag_router_tool_decorator_with_params(self, rag_router):
        """Тест декоратора tool с параметрами"""

        @rag_router.tool(return_direct=True)
        def test_tool_with_params(query: str) -> str:
            """Тестовый инструмент с параметрами"""
            return f"Результат: {query}"

        tools = rag_router.get_tools()
        assert len(tools) == 1
        assert isinstance(tools[0], BaseTool)

    def test_rag_router_multiple_tools(self, rag_router):
        """Тест добавления нескольких инструментов"""

        @rag_router.tool
        def tool1(query: str) -> str:
            """Инструмент 1"""
            return "result1"

        @rag_router.tool
        def tool2(query: str) -> str:
            """Инструмент 2"""
            return "result2"

        tools = rag_router.get_tools()
        assert len(tools) == 2
        assert tools[0].name == "tool1"
        assert tools[1].name == "tool2"

    def test_rag_router_register_to_with_tools(self, rag_router):
        """Тест регистрации роутера с инструментами"""

        @rag_router.tool
        def test_tool(query: str) -> str:
            """Тестовый инструмент"""
            return "result"

        mock_bot_builder = Mock()
        mock_bot_builder.register_rag = Mock()

        rag_router.register_to(mock_bot_builder)

        mock_bot_builder.register_rag.assert_called_once_with(rag_router)

    def test_rag_router_register_to_without_tools(self, rag_router):
        """Тест регистрации роутера без инструментов"""
        mock_bot_builder = Mock()
        mock_bot_builder.register_rag = Mock()

        with patch("smart_bot_factory.rag.router.logger") as mock_logger:
            rag_router.register_to(mock_bot_builder)

            mock_logger.warning.assert_called_once()
            mock_bot_builder.register_rag.assert_not_called()

    def test_rag_router_add_tool_directly(self, rag_router):
        """Тест прямого добавления инструмента"""

        @rag_router.tool
        def test_tool(query: str) -> str:
            """Тестовый инструмент"""
            return "result"

        tool = rag_router.get_tools()[0]

        # Попытка добавить тот же инструмент снова не должна дублировать его
        rag_router.add_tool(tool)
        tools = rag_router.get_tools()
        assert len(tools) == 1

    def test_rag_router_set_bot_id(self, rag_router):
        """Тест установки bot_id"""
        rag_router.set_bot_id("test-bot-id")
        assert rag_router.bot_id == "test-bot-id"
