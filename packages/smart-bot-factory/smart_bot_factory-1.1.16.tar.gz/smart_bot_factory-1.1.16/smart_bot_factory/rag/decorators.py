from typing import Any, Callable

from langchain.tools import tool as langchain_tool


def rag(*tool_args: Any, **tool_kwargs: Any):
    """
    Wrapper around langchain.tools.tool to keep rag-related tooling imports localized.

    Usage:
        @rag
        def my_tool(...):
            ...

        @rag(return_direct=True)
        def my_other_tool(...):
            ...
    """

    if tool_args and callable(tool_args[0]) and not tool_kwargs:
        # Called without params: @rag
        func = tool_args[0]
        return langchain_tool(func)

    def decorator(func: Callable[..., Any]):
        return langchain_tool(*tool_args, **tool_kwargs)(func)

    return decorator
