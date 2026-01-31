"""Тесты для utils.tool_router"""

from unittest.mock import Mock, patch

from smart_bot_factory.utils.tool_router import ToolRouter


class TestToolRouter:
    """Тесты для класса ToolRouter"""

    def test_tool_router_init(self):
        """Тест инициализации ToolRouter (строки 17-20)"""
        router = ToolRouter()

        assert router.name == "tools"
        assert router.bot_id is None
        assert router._tools == []

    def test_tool_router_init_with_params(self):
        """Тест инициализации ToolRouter с параметрами"""
        router = ToolRouter(name="custom", bot_id="test-bot")

        assert router.name == "custom"
        assert router.bot_id == "test-bot"

    def test_set_bot_id(self):
        """Тест set_bot_id (строки 22-30)"""
        router = ToolRouter()
        router.set_bot_id("test-bot")

        assert router.bot_id == "test-bot"

    def test_tool_decorator_without_args(self):
        """Тест декоратора tool без аргументов (строки 32-55)"""
        router = ToolRouter()

        with patch("smart_bot_factory.utils.tool_router.langchain_tool") as mock_tool:
            mock_tool_obj = Mock()
            mock_tool.return_value = mock_tool_obj

            @router.tool
            def test_tool() -> str:
                """Test tool description"""
                return "test"

            tools = router.get_tools()
            assert len(tools) == 1
            mock_tool.assert_called_once()

    def test_tool_decorator_with_args(self):
        """Тест декоратора tool с аргументами"""
        router = ToolRouter()

        with patch("smart_bot_factory.utils.tool_router.langchain_tool") as mock_tool:
            mock_tool_obj = Mock()
            mock_tool.return_value = Mock(return_value=mock_tool_obj)

            @router.tool(description="Test tool")
            def test_tool() -> str:
                """Test tool"""
                return "test"

            tools = router.get_tools()
            assert len(tools) == 1

    def test_add_tool(self):
        """Тест add_tool (строки 57-61)"""
        router = ToolRouter()
        mock_tool = Mock()
        mock_tool.name = "test_tool"

        router.add_tool(mock_tool)

        assert len(router._tools) == 1
        assert router._tools[0] == mock_tool

    def test_add_tool_duplicate(self):
        """Тест add_tool для дубликата"""
        router = ToolRouter()
        mock_tool = Mock()
        mock_tool.name = "test_tool"

        router.add_tool(mock_tool)
        router.add_tool(mock_tool)  # Дубликат

        assert len(router._tools) == 1  # Не должен добавиться дважды

    def test_extend(self):
        """Тест extend (строки 63-65)"""
        router = ToolRouter()
        mock_tool1 = Mock()
        mock_tool2 = Mock()

        router.extend([mock_tool1, mock_tool2])

        assert len(router._tools) == 2

    def test_get_tools(self):
        """Тест get_tools (строки 67-68)"""
        router = ToolRouter()
        mock_tool = Mock()
        router.add_tool(mock_tool)

        tools = router.get_tools()

        assert len(tools) == 1
        assert tools[0] == mock_tool
        # Проверяем что возвращается копия списка
        assert tools is not router._tools

    def test_register_to(self):
        """Тест register_to (строки 70-75)"""
        router = ToolRouter()
        mock_tool = Mock()
        router.add_tool(mock_tool)

        mock_bot_builder = Mock()
        router.register_to(mock_bot_builder)

        mock_bot_builder.register_tool_set.assert_called_once_with(router)

    def test_register_to_empty(self):
        """Тест register_to без инструментов (строки 72-74)"""
        router = ToolRouter()

        mock_bot_builder = Mock()
        router.register_to(mock_bot_builder)

        # Не должен вызывать register_tool_set если нет инструментов
        mock_bot_builder.register_tool_set.assert_not_called()
