"""
FileRouter - специализированный роутер для обработки событий связанных с файлами

Пример использования:

    from smart_bot_factory.file_router import FileRouter
    from smart_bot_factory.creation import BotBuilder

    # Создаем файловый роутер
    file_router = FileRouter()

    # Регистрируем обработчик для конкретного типа события
    @file_router.file_handler("send_presentation")
    async def send_presentation(user_id: int):
        # Отправка презентации пользователю
        await send_file_to_user(user_id, "presentation.pdf")
        return {"status": "sent", "file": "presentation.pdf"}

    @file_router.file_handler("send_catalog")
    async def send_catalog(user_id: int):
        # Отправка каталога файлов
        await send_catalog_files(user_id, "catalog_name")
        return {"status": "sent", "catalog": "catalog_name"}

    # Регистрация роутера
    bot_builder = BotBuilder("my_bot")
    bot_builder.register_routers(file_router)

    # ИИ может создать событие:
    # {"тип": "send_presentation", "инфо": "presentation.pdf"}
    # И файловый роутер его обработает!
"""

import logging
from typing import Any, Callable, Dict, Optional, Union

from ..event.router import EventRouter

logger = logging.getLogger(__name__)


class FileRouter(EventRouter):
    """
    Специализированный роутер для обработки событий связанных с отправкой файлов

    Предназначен для:
    - Обработки событий отправки файлов пользователям
    - Управления файлами из каталогов
    - Отправки медиа-контента

    Пример использования:
        from smart_bot_factory.file_router import FileRouter

        file_router = FileRouter()

        @file_router.file_handler("send_presentation")
        async def send_presentation(user_id: int):
            # Отправка презентации пользователю
            await send_file_to_user(user_id, "presentation.pdf")
            return {"status": "sent", "file": "presentation.pdf"}
    """

    def __init__(self, name: str = "FileRouter", bot_id: Optional[str] = None):
        """
        Инициализация файлового роутера

        Args:
            name: Имя роутера для логирования
            bot_id: ID бота (опционально, может быть установлен позже через set_bot_id)
        """
        super().__init__(name=name, bot_id=bot_id)
        self._file_handlers: Dict[str, Dict[str, Any]] = {}

        logger.info(f"📁 Создан файловый роутер: {self.name}")

    def file_handler(
        self,
        name: Union[str, Callable, None] = None,
        once_only: bool = False,
    ):
        """
        Декоратор для регистрации обработчика файлового события

        Args:
            name: Название обработчика (если не указано, берется из имени функции)
            once_only: Выполнять ли только один раз (по умолчанию False - файлы можно отправлять многократно)
        """
        # Если name - это функция (вызов без скобок: @file_router.file_handler)
        if name is not None and callable(name) and not isinstance(name, str):
            func = name
            name = None
            # Регистрируем обработчик напрямую
            func_name = getattr(func, "__name__", "unknown_file_handler")
            actual_event_type = func_name
            self._event_handlers[actual_event_type] = {
                "handler": func,
                "name": func_name,
                "notify": False,
                "once_only": once_only,
                "send_ai_response": False,
                "router": self.name,
                "file_handler": True,
            }
            self._file_handlers[actual_event_type] = {
                "handler": func,
                "name": func_name,
                "once_only": once_only,
            }
            logger.info(f"📁 Файловый роутер {self.name}: " f"зарегистрирован обработчик файлового события '{actual_event_type}': {func_name}")

            from functools import wraps

            @wraps(func)
            async def wrapper(*args, **kwargs):
                try:
                    file_sender = args[0] if args and hasattr(args[0], "user_id") and hasattr(args[0], "send_before") else None
                    if not file_sender:
                        user_id = args[0] if args else kwargs.get("user_id")
                        chat_id = kwargs.get("chat_id", user_id)
                        from .sender import FileSender

                        file_sender = FileSender(user_id=user_id, chat_id=chat_id) if user_id else None
                        result = await func(file_sender, *args[1:], **kwargs)
                    else:
                        result = await func(*args, **kwargs)
                    return {
                        "file_sender": file_sender,
                        "router": self.name,
                        "file_handler": True,
                        "result": result if result else {"status": "success"},
                    }
                except Exception as e:
                    logger.error(f"❌ Ошибка выполнения файлового обработчика '{actual_event_type}': {e}", exc_info=True)
                    raise

            return wrapper

        def decorator(func: Callable) -> Callable:
            # Если name не указан, используем имя функции
            func_name = getattr(func, "__name__", "unknown_file_handler")
            actual_event_type = name if isinstance(name, str) else func_name

            from functools import wraps

            @wraps(func)
            async def wrapper(*args, **kwargs):
                try:
                    # FileSender должен быть передан первым аргументом из execute_file_event_handler
                    file_sender = args[0] if args and hasattr(args[0], "user_id") and hasattr(args[0], "send_before") else None

                    if not file_sender:
                        # FileSender не передан, создаем новый (для обратной совместимости)
                        user_id = args[0] if args else kwargs.get("user_id")
                        chat_id = kwargs.get("chat_id", user_id)
                        from .sender import FileSender

                        file_sender = FileSender(user_id=user_id, chat_id=chat_id) if user_id else None
                        # Вызываем функцию с FileSender первым аргументом
                        result = await func(file_sender, *args[1:], **kwargs)
                    else:
                        # FileSender уже передан, вызываем функцию как есть
                        result = await func(*args, **kwargs)

                    # Возвращаем результат с FileSender
                    return {
                        "file_sender": file_sender,
                        "router": self.name,
                        "file_handler": True,
                        "result": result if result else {"status": "success"},
                    }
                except Exception as e:
                    logger.error(f"❌ Ошибка выполнения файлового обработчика '{actual_event_type}': {e}", exc_info=True)
                    raise

            # Регистрируем wrapper, а не func
            self._event_handlers[actual_event_type] = {
                "handler": wrapper,
                "name": func_name,
                "notify": False,  # Файловые обработчики не уведомляют админов
                "once_only": once_only,
                "send_ai_response": False,  # Файлы отправляются отдельно от ответа ИИ
                "router": self.name,
                "file_handler": True,  # Маркер файлового обработчика
            }

            # Также сохраняем в отдельном словаре для удобства
            self._file_handlers[actual_event_type] = {
                "handler": wrapper,
                "name": func_name,
                "once_only": once_only,
            }

            logger.info(f"📁 Файловый роутер {self.name}: " f"зарегистрирован обработчик файлового события '{actual_event_type}': {func_name}")

            return wrapper

        return decorator

    def get_file_handlers(self) -> Dict[str, Dict[str, Any]]:
        """Получает все файловые обработчики"""
        return self._file_handlers.copy()

    def has_file_handler(self, name: str) -> bool:
        """Проверяет наличие обработчика по имени"""
        return name in self._file_handlers

    def __repr__(self):
        return (
            f"FileRouter(name='{self.name}', "
            f"file_handlers={len(self._file_handlers)}, "
            f"events={len(self._event_handlers)}, "
            f"tasks={len(self._scheduled_tasks)}, "
            f"globals={len(self._global_handlers)})"
        )
