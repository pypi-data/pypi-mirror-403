"""
Выполнение обработчиков событий, задач и глобальных обработчиков.
"""

import logging
from typing import Any

from .registry import _get_registry

logger = logging.getLogger(__name__)


async def execute_event_handler(event_type: str, *args, **kwargs) -> Any:
    """Выполняет обработчик события по типу"""
    event_handlers, source = _get_registry("event")

    if event_type not in event_handlers:
        available = list(event_handlers.keys())
        logger.error(f"❌ Обработчик события '{event_type}' не найден (источник: {source}). Доступные: {available}")
        raise ValueError(f"Обработчик события '{event_type}' не найден")

    handler_info = event_handlers[event_type]
    return await handler_info["handler"](*args, **kwargs)


async def execute_scheduled_task(task_name: str, user_id: int, user_data: str) -> Any:
    """Выполняет запланированную задачу по имени (без планирования, только выполнение)"""
    scheduled_tasks, source = _get_registry("task")

    if task_name not in scheduled_tasks:
        available = list(scheduled_tasks.keys())
        logger.error(f"❌ Задача '{task_name}' не найдена (источник: {source}). Доступные: {available}")
        raise ValueError(f"Задача '{task_name}' не найдена")

    task_info = scheduled_tasks[task_name]
    return await task_info["handler"](user_id, user_data)


async def execute_global_handler(handler_type: str, *args, **kwargs) -> Any:
    """Выполняет глобальный обработчик по типу"""
    global_handlers, source = _get_registry("global")

    if handler_type not in global_handlers:
        available = list(global_handlers.keys())
        logger.error(f"❌ Глобальный обработчик '{handler_type}' не найден (источник: {source}). Доступные: {available}")
        raise ValueError(f"Глобальный обработчик '{handler_type}' не найден")

    handler_info = global_handlers[handler_type]
    return await handler_info["handler"](*args, **kwargs)
