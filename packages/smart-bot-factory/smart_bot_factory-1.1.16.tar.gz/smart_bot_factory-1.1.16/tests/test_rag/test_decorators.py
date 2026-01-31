"""Тесты для декораторов RAG"""

from langchain_core.tools import BaseTool

from smart_bot_factory.rag.decorators import rag


class TestRagDecorator:
    """Тесты для декоратора rag"""

    def test_rag_decorator_without_params(self):
        """Тест декоратора rag без параметров"""

        @rag
        def test_tool(query: str) -> str:
            """Тестовый инструмент"""
            return f"Результат: {query}"

        assert isinstance(test_tool, BaseTool)
        assert test_tool.name == "test_tool"
        assert test_tool.description == "Тестовый инструмент"

    def test_rag_decorator_with_params(self):
        """Тест декоратора rag с параметрами"""

        @rag(return_direct=True)
        def test_tool_with_params(query: str) -> str:
            """Тестовый инструмент с параметрами"""
            return f"Результат: {query}"

        assert isinstance(test_tool_with_params, BaseTool)
        assert test_tool_with_params.name == "test_tool_with_params"

    def test_rag_decorator_async_function(self):
        """Тест декоратора rag с асинхронной функцией"""

        @rag
        async def async_test_tool(query: str) -> str:
            """Асинхронный тестовый инструмент"""
            return f"Асинхронный результат: {query}"

        assert isinstance(async_test_tool, BaseTool)
        assert async_test_tool.name == "async_test_tool"

    def test_rag_decorator_with_metadata(self):
        """Тест декоратора rag с метаданными"""

        @rag(return_direct=True)
        def test_tool(query: str) -> str:
            """Тестовый инструмент"""
            return f"Результат: {query}"

        assert isinstance(test_tool, BaseTool)
        assert test_tool.name == "test_tool"
        assert test_tool.description == "Тестовый инструмент"

    def test_rag_decorator_callable(self):
        """Тест вызова декорированной функции"""

        @rag
        def test_tool(query: str) -> str:
            """Тестовый инструмент"""
            return f"Результат: {query}"

        # Проверяем, что инструмент можно вызвать
        result = test_tool.invoke({"query": "test"})
        assert result == "Результат: test"
