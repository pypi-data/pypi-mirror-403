"""
Константы и базовые конфиги для decorators.
"""

from typing import Callable, Union


class EventStatus:
    """Статусы событий в БД."""

    PENDING = "pending"
    IMMEDIATE = "immediate"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class EventCategory:
    """Категории событий."""

    USER_EVENT = "user_event"
    SCHEDULED_TASK = "scheduled_task"
    GLOBAL_HANDLER = "global_handler"
    ADMIN_EVENT = "admin_event"


class NotifyTime:
    """Время уведомлений."""

    BEFORE = "before"
    AFTER = "after"


class SmartCheckAction:
    """Действия умной проверки."""

    EXECUTE = "execute"
    CANCEL = "cancel"
    RESCHEDULE = "reschedule"


class BaseHandlerConfig(dict):
    """Базовый конфиг обработчика: доступ и по ключам, и как к атрибутам."""

    def __init__(
        self,
        handler: Callable,
        name: str,
        notify: bool = False,
        once_only: bool = True,
        send_ai_response: bool = True,
    ):
        super().__init__(
            handler=handler,
            name=name,
            notify=notify,
            once_only=once_only,
            send_ai_response=send_ai_response,
        )
        self.__dict__ = self


class ScheduledTaskConfig(BaseHandlerConfig):
    """Конфиг для запланированных задач."""

    def __init__(
        self,
        handler: Callable,
        name: str,
        notify: bool,
        once_only: bool,
        send_ai_response: bool,
        smart_check: bool,
        notify_time: str,
        default_delay: int,
        event_type: Union[str, Callable, None],
    ):
        super().__init__(
            handler=handler,
            name=name,
            notify=notify,
            once_only=once_only,
            send_ai_response=send_ai_response,
        )
        self.update(
            smart_check=smart_check,
            notify_time=notify_time,
            default_delay=default_delay,
            event_type=event_type,
        )


class GlobalHandlerConfig(BaseHandlerConfig):
    """Конфиг для глобальных обработчиков."""

    def __init__(
        self,
        handler: Callable,
        name: str,
        notify: bool,
        once_only: bool,
        send_ai_response: bool,
        default_delay: int,
        event_type: Union[str, Callable, None],
    ):
        super().__init__(
            handler=handler,
            name=name,
            notify=notify,
            once_only=once_only,
            send_ai_response=send_ai_response,
        )
        self.update(default_delay=default_delay, event_type=event_type)
