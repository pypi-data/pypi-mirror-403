"""
Выполнение файловых обработчиков событий
"""

from __future__ import annotations

import inspect
import logging
from typing import TYPE_CHECKING, Any, Optional

from ..event.decorators.registry import _get_registry

if TYPE_CHECKING:
    from .sender import FileSender

logger = logging.getLogger(__name__)


async def execute_file_event_handler(name: str, file_sender: FileSender, user_id: Optional[int] = None, event_info: Optional[str] = None) -> Any:
    """
    Выполняет файловый обработчик события по имени

    Args:
        name: Название обработчика
        file_sender: FileSender объект для управления отправкой файлов
        user_id: ID пользователя (опционально, для обратной совместимости)
        event_info: Информация о событии (опционально, для обратной совместимости)

    Returns:
        Any: Результат выполнения обработчика
    """
    event_handlers, source = _get_registry("event")

    if name not in event_handlers:
        available = list(event_handlers.keys())
        logger.error(f"❌ Файловый обработчик события '{name}' не найден (источник: {source}). Доступные: {available}")
        raise ValueError(f"Файловый обработчик события '{name}' не найден")

    handler_info = event_handlers[name]

    # Проверяем, что это действительно файловый обработчик
    if not handler_info.get("file_handler"):
        raise ValueError(f"Обработчик '{name}' не является файловым обработчиком")

    handler = handler_info["handler"]

    # Анализируем сигнатуру функции для правильного вызова
    try:
        sig = inspect.signature(handler)
        params = list(sig.parameters.keys())

        # Определяем количество обязательных параметров (без значений по умолчанию)
        required_params = [p for p, param in sig.parameters.items() if param.default == inspect.Parameter.empty]

        logger.debug(f"📁 Вызов файлового обработчика '{name}': сигнатура {params}, обязательные: {required_params}")

        # Вызываем обработчик в зависимости от сигнатуры
        if len(required_params) == 1:
            # Обработчик принимает только file_sender
            return await handler(file_sender)
        elif len(required_params) == 2 and params[1] == "user_id":
            # Обработчик принимает file_sender и user_id
            return await handler(file_sender, user_id)
        elif len(params) >= 2:
            # Обработчик принимает file_sender и другие параметры
            # Пробуем передать user_id и event_info если они есть
            if user_id is not None and event_info is not None:
                return await handler(file_sender, user_id, event_info)
            elif user_id is not None:
                return await handler(file_sender, user_id)
            else:
                return await handler(file_sender)
        else:
            # Неожиданная сигнатура, пробуем просто с file_sender
            return await handler(file_sender)

    except TypeError as e:
        # Если не получилось вызвать с параметрами, пробуем просто с file_sender
        logger.debug(f"⚠️ Не удалось вызвать обработчик '{name}' с параметрами, пробуем только с file_sender: {e}")
        try:
            return await handler(file_sender)
        except Exception as e2:
            logger.error(f"❌ Ошибка вызова файлового обработчика '{name}': {e2}")
            raise
    except Exception as e:
        logger.error(f"❌ Ошибка выполнения файлового обработчика '{name}': {e}")
        raise
