from __future__ import annotations

import logging
from typing import Any, Callable, Iterable, List, Optional

from langchain.tools import tool as langchain_tool
from langchain_core.tools import BaseTool

logger = logging.getLogger(__name__)


class ToolRouter:
    """
    Универсальный роутер для сбора и регистрации LangChain-инструментов.
    """

    def __init__(self, name: str = "tools", bot_id: Optional[str] = None):
        self.name = name
        self.bot_id = bot_id
        self._tools: List[BaseTool] = []

    def set_bot_id(self, bot_id: str):
        """
        Устанавливает bot_id для роутера (вызывается автоматически при регистрации в BotBuilder)

        Args:
            bot_id: ID бота
        """
        self.bot_id = bot_id
        logger.debug(f"🔧 Роутер {self.name}: установлен bot_id = {bot_id}")

    def tool(self, *tool_args: Any, **tool_kwargs: Any):
        """
        Декоратор для регистрации функции как инструмента LangChain.

        Пример:
            tool_router = ToolRouter("common")

            @tool_router.tool
            def ping() -> str:
                return "pong"
        """

        if tool_args and callable(tool_args[0]) and not tool_kwargs:
            func = tool_args[0]
            tool_obj = langchain_tool(func)
            self.add_tool(tool_obj)
            return tool_obj

        def decorator(func: Callable[..., Any]):
            tool_obj = langchain_tool(*tool_args, **tool_kwargs)(func)
            self.add_tool(tool_obj)
            return tool_obj

        return decorator

    def add_tool(self, tool: BaseTool) -> BaseTool:
        if tool not in self._tools:
            self._tools.append(tool)
            logger.debug("🔧 ToolRouter %s: добавлен инструмент %s", self.name, getattr(tool, "name", tool))
        return tool

    def extend(self, tools: Iterable[BaseTool]) -> None:
        for tool in tools:
            self.add_tool(tool)

    def get_tools(self) -> List[BaseTool]:
        return list(self._tools)

    def register_to(self, bot_builder) -> None:
        tools = self.get_tools()
        if not tools:
            logger.warning("⚠️ ToolRouter %s не содержит инструментов для регистрации", self.name)
            return
        bot_builder.register_tool_set(self)
