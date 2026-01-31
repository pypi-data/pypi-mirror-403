from __future__ import annotations

import logging
from typing import Any, Callable

from langchain_core.tools import BaseTool

from ..utils.tool_router import ToolRouter
from .decorators import rag

logger = logging.getLogger(__name__)


class RagRouter(ToolRouter):
    """
    Упрощенный роутер для регистрации RAG-инструментов.

    Позволяет описывать инструменты через декоратор `@rag_router.tool`
    и потом одним вызовом подключать их к `BotBuilder`.
    """

    def tool(self, *tool_args: Any, **tool_kwargs: Any) -> Callable[[Callable[..., Any]], BaseTool]:
        """
        Декоратор для регистрации функции как RAG-инструмента.

        Пример:
            rag_router = RagRouter("mdclinica_rag")

            @rag_router.tool
            async def get_service(...):
                ...
        """

        if tool_args and callable(tool_args[0]) and not tool_kwargs:
            func = tool_args[0]
            tool_obj = rag(func)
            self.add_tool(tool_obj)
            return tool_obj

        def decorator(func: Callable[..., Any]) -> BaseTool:
            tool_obj = rag(*tool_args, **tool_kwargs)(func)
            self.add_tool(tool_obj)
            return tool_obj

        return decorator

    def register_to(self, bot_builder) -> None:
        tools = self.get_tools()
        if not tools:
            logger.warning("⚠️ RagRouter %s не содержит инструментов для регистрации", self.name)
            return
        bot_builder.register_rag(self)
        logger.info("✅ RagRouter %s: зарегистрировано %d инструментов", self.name, len(tools))
