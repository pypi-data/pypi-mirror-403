"""
Декораторы для регистрации обработчиков и работа с реестрами.
"""

import logging
from functools import wraps
from typing import Any, Callable, Dict, Tuple, Union

from .constants import (
    BaseHandlerConfig,
    GlobalHandlerConfig,
    NotifyTime,
    ScheduledTaskConfig,
)
from .utils import parse_time_string

logger = logging.getLogger(__name__)

# Глобальный реестр обработчиков событий
_event_handlers: Dict[str, BaseHandlerConfig] = {}
_scheduled_tasks: Dict[str, ScheduledTaskConfig] = {}
_global_handlers: Dict[str, GlobalHandlerConfig] = {}

# Глобальный менеджер роутеров
_router_manager = None


def event_handler(
    event_type: str,
    notify: bool = False,
    once_only: bool = True,
    send_ai_response: bool = True,
):
    """
    Декоратор для регистрации обработчика события

    Args:
        event_type: Тип события (например, 'appointment_booking', 'phone_collection')
        notify: Уведомлять ли админов о выполнении события (по умолчанию False)
        once_only: Обрабатывать ли событие только один раз (по умолчанию True)
        send_ai_response: Отправлять ли сообщение от ИИ после обработки события (по умолчанию True)

    Example:
        # Обработчик с отправкой сообщения от ИИ
        @event_handler("appointment_booking", notify=True)
        async def book_appointment(user_id: int, appointment_data: dict):
            # Логика записи на прием
            return {"status": "success", "appointment_id": "123"}

        # Обработчик БЕЗ отправки сообщения от ИИ
        @event_handler("phone_collection", once_only=False, send_ai_response=False)
        async def collect_phone(user_id: int, phone_data: dict):
            # Логика сбора телефона - ИИ не отправит сообщение
            return {"status": "phone_collected"}
    """

    def decorator(func: Callable) -> Callable:
        _event_handlers[event_type] = BaseHandlerConfig(
            handler=func,
            name=func.__name__,
            notify=notify,
            once_only=once_only,
            send_ai_response=send_ai_response,
        )

        logger.info(f"📝 Зарегистрирован обработчик события '{event_type}': {func.__name__}")

        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                logger.info(f"🔧 Выполняем обработчик события '{event_type}'")
                result = await func(*args, **kwargs)
                logger.info(f"✅ Обработчик '{event_type}' выполнен успешно")

                # Автоматически добавляем флаги notify и send_ai_response к результату
                if isinstance(result, dict):
                    result["notify"] = notify
                    result["send_ai_response"] = send_ai_response
                else:
                    # Если результат не словарь, создаем словарь
                    result = {
                        "status": "success",
                        "result": result,
                        "notify": notify,
                        "send_ai_response": send_ai_response,
                    }

                return result
            except Exception as e:
                logger.error(f"❌ Ошибка в обработчике '{event_type}': {e}")
                raise

        return wrapper

    return decorator


def schedule_task(
    task_name: str,
    notify: bool = False,
    notify_time: str = NotifyTime.AFTER,  # 'after' или 'before'
    smart_check: bool = True,
    once_only: bool = True,
    delay: Union[str, int] = None,
    event_type: Union[str, Callable] = None,
    send_ai_response: bool = True,
):
    """
    Декоратор для регистрации задачи, которую можно запланировать на время

    Args:
        task_name: Название задачи (например, 'send_reminder', 'follow_up')
        notify: Уведомлять ли админов о выполнении задачи (по умолчанию False)
        smart_check: Использовать ли умную проверку активности пользователя (по умолчанию True)
        once_only: Выполнять ли задачу только один раз (по умолчанию True)
        delay: Время задержки в удобном формате (например, "1h 30m", "45m", 3600) - ОБЯЗАТЕЛЬНО
        event_type: Источник времени события - ОПЦИОНАЛЬНО:
            - str: Тип события для поиска в БД (например, 'appointment_booking')
            - Callable: Функция для получения datetime (например, async def(user_id, user_data) -> datetime)
        send_ai_response: Отправлять ли сообщение от ИИ после выполнения задачи (по умолчанию True)

    Example:
        # Обычная задача с фиксированным временем
        @schedule_task("send_reminder", delay="1h 30m")
        async def send_reminder(user_id: int, user_data: str):
            # Задача будет запланирована на 1 час 30 минут
            return {"status": "sent", "message": user_data}

        # Напоминание о событии из БД (за delay времени до события)
        @schedule_task("appointment_reminder", delay="2h", event_type="appointment_booking")
        async def appointment_reminder(user_id: int, user_data: str):
            # Ищет событие "appointment_booking" в БД
            # Напоминание будет за 2 часа до времени из события
            return {"status": "sent", "message": user_data}

        # Напоминание с кастомной функцией получения времени
        async def get_yclients_appointment_time(user_id: int, user_data: str) -> datetime:
            '''Получает время записи из YClients API'''
            from yclients_api import get_next_booking
            booking = await get_next_booking(user_id)
            return booking['datetime']  # datetime объект

        @schedule_task("yclients_reminder", delay="1h", event_type=get_yclients_appointment_time)
        async def yclients_reminder(user_id: int, user_data: str):
            # Вызовет get_yclients_appointment_time(user_id, user_data)
            # Напоминание будет за 1 час до возвращенного datetime
            return {"status": "sent"}

        # Форматы времени:
        # delay="1h 30m 45s" - 1 час 30 минут 45 секунд
        # delay="2h" - 2 часа
        # delay="30m" - 30 минут
        # delay=3600 - 3600 секунд (число)

        # ИИ может передавать только данные (текст):
        # {"тип": "send_reminder", "инфо": "Текст напоминания"} - только текст
        # {"тип": "appointment_reminder", "инфо": ""} - пустой текст, время берется из события/функции
    """

    def decorator(func: Callable) -> Callable:
        # Время ОБЯЗАТЕЛЬНО должно быть указано
        if delay is None:
            raise ValueError(f"Для задачи '{task_name}' ОБЯЗАТЕЛЬНО нужно указать параметр delay")

        # Парсим время
        try:
            default_delay_seconds = parse_time_string(delay)
            if event_type:
                logger.info(f"⏰ Задача '{task_name}' настроена как напоминание о событии '{event_type}' за {delay} ({default_delay_seconds}с)")
            else:
                logger.info(f"⏰ Задача '{task_name}' настроена с задержкой: {delay} ({default_delay_seconds}с)")
        except ValueError as e:
            logger.error(f"❌ Ошибка парсинга времени для задачи '{task_name}': {e}")
            raise

        _scheduled_tasks[task_name] = ScheduledTaskConfig(
            handler=func,
            name=func.__name__,
            notify=notify,
            once_only=once_only,
            send_ai_response=send_ai_response,
            smart_check=smart_check,
            notify_time=notify_time,
            default_delay=default_delay_seconds,
            event_type=event_type,  # Новое поле для типа события
        )

        if event_type:
            logger.info(f"⏰ Зарегистрирована задача-напоминание '{task_name}' для события '{event_type}': {func.__name__}")
        else:
            logger.info(f"⏰ Зарегистрирована задача '{task_name}': {func.__name__}")

        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                logger.info(f"⏰ Выполняем запланированную задачу '{task_name}'")
                result = await func(*args, **kwargs)
                logger.info(f"✅ Задача '{task_name}' выполнена успешно")

                # Автоматически добавляем флаги notify и send_ai_response к результату
                if isinstance(result, dict):
                    result["notify"] = notify
                    result["send_ai_response"] = send_ai_response
                else:
                    # Если результат не словарь, создаем словарь
                    result = {
                        "status": "success",
                        "result": result,
                        "notify": notify,
                        "send_ai_response": send_ai_response,
                    }

                return result
            except Exception as e:
                logger.error(f"❌ Ошибка в задаче '{task_name}': {e}")
                raise

        return wrapper

    return decorator


def global_handler(
    handler_type: str,
    notify: bool = False,
    once_only: bool = True,
    delay: Union[str, int] = None,
    event_type: Union[str, Callable] = None,
    send_ai_response: bool = True,
):
    """
    Декоратор для регистрации глобального обработчика (для всех пользователей)

    Args:
        handler_type: Тип глобального обработчика (например, 'global_announcement', 'mass_notification')
        notify: Уведомлять ли админов о выполнении (по умолчанию False)
        once_only: Выполнять ли обработчик только один раз (по умолчанию True)
        delay: Время задержки в удобном формате (например, "1h 30m", "45m", 3600) - ОБЯЗАТЕЛЬНО
        event_type: Источник времени события - ОПЦИОНАЛЬНО:
            - str: Тип события для поиска в БД
            - Callable: Функция для получения datetime (например, async def(handler_data: str) -> datetime)
        send_ai_response: Отправлять ли сообщение от ИИ после выполнения обработчика (по умолчанию True)

    Example:
        # Глобальный обработчик с задержкой
        @global_handler("global_announcement", delay="2h", notify=True)
        async def send_global_announcement(announcement_text: str):
            # Выполнится через 2 часа
            return {"status": "sent", "recipients_count": 150}

        # Глобальный обработчик может выполняться многократно
        @global_handler("daily_report", delay="24h", once_only=False)
        async def send_daily_report(report_data: str):
            # Может запускаться каждый день через 24 часа
            return {"status": "sent", "report_type": "daily"}

        # С кастомной функцией для получения времени
        async def get_promo_end_time(handler_data: str) -> datetime:
            '''Получает время окончания акции из CRM'''
            from crm_api import get_active_promo
            promo = await get_active_promo()
            return promo['end_datetime']

        @global_handler("promo_ending_notification", delay="2h", event_type=get_promo_end_time)
        async def notify_promo_ending(handler_data: str):
            # Уведомление за 2 часа до окончания акции
            return {"status": "sent"}

        # Форматы времени:
        # delay="1h 30m 45s" - 1 час 30 минут 45 секунд
        # delay="2h" - 2 часа
        # delay="45m" - 45 минут
        # delay=3600 - 3600 секунд (число)

        # ИИ может передавать только данные (текст):
        # {"тип": "global_announcement", "инфо": "Важное объявление!"} - только текст
        # {"тип": "global_announcement", "инфо": ""} - пустой текст, время из функции
    """

    def decorator(func: Callable) -> Callable:
        # Время ОБЯЗАТЕЛЬНО должно быть указано
        if delay is None:
            raise ValueError(f"Для глобального обработчика '{handler_type}' ОБЯЗАТЕЛЬНО нужно указать параметр delay")

        # Парсим время
        try:
            default_delay_seconds = parse_time_string(delay)
            logger.info(f"🌍 Глобальный обработчик '{handler_type}' настроен с задержкой: {delay} ({default_delay_seconds}с)")
        except ValueError as e:
            logger.error(f"❌ Ошибка парсинга времени для глобального обработчика '{handler_type}': {e}")
            raise

        _global_handlers[handler_type] = GlobalHandlerConfig(
            handler=func,
            name=func.__name__,
            notify=notify,
            once_only=once_only,
            send_ai_response=send_ai_response,
            default_delay=default_delay_seconds,
            event_type=event_type,  # Добавляем event_type для глобальных обработчиков
        )

        logger.info(f"🌍 Зарегистрирован глобальный обработчик '{handler_type}': {func.__name__}")

        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                logger.info(f"🌍 Выполняем глобальный обработчик '{handler_type}'")
                result = await func(*args, **kwargs)
                logger.info(f"✅ Глобальный обработчик '{handler_type}' выполнен успешно")

                # Автоматически добавляем флаги notify и send_ai_response к результату
                if isinstance(result, dict):
                    result["notify"] = notify
                    result["send_ai_response"] = send_ai_response
                else:
                    # Если результат не словарь, создаем словарь
                    result = {
                        "status": "success",
                        "result": result,
                        "notify": notify,
                        "send_ai_response": send_ai_response,
                    }

                return result
            except Exception as e:
                logger.error(f"❌ Ошибка в глобальном обработчике '{handler_type}': {e}")
                raise

        return wrapper

    return decorator


def get_event_handlers() -> Dict[str, Dict[str, Any]]:
    """Возвращает все зарегистрированные обработчики событий"""
    return _event_handlers.copy()


def get_scheduled_tasks() -> Dict[str, Dict[str, Any]]:
    """Возвращает все зарегистрированные задачи"""
    return _scheduled_tasks.copy()


def get_global_handlers() -> Dict[str, Dict[str, Any]]:
    """Возвращает все зарегистрированные глобальные обработчики"""
    return _global_handlers.copy()


def set_router_manager(router_manager):
    """Устанавливает глобальный менеджер роутеров"""
    global _router_manager
    _router_manager = router_manager
    logger.info("🔄 RouterManager установлен в decorators")


def get_router_manager():
    """Получает глобальный менеджер роутеров"""
    return _router_manager


def _get_registry(kind: str) -> Tuple[Dict[str, Any], str]:
    """
    Унифицированный доступ к реестрам (events / tasks / global).
    Возвращает (registry_dict, source) где source: 'router' или 'legacy'.
    """
    router_manager = get_router_manager()

    if router_manager:
        if kind == "event":
            return router_manager.get_event_handlers(), "router"
        if kind == "task":
            return router_manager.get_scheduled_tasks(), "router"
        if kind == "global":
            return router_manager.get_global_handlers(), "router"

    if kind == "event":
        return _event_handlers, "legacy"
    if kind == "task":
        return _scheduled_tasks, "legacy"
    if kind == "global":
        return _global_handlers, "legacy"

    raise ValueError(f"Неизвестный тип реестра: {kind}")


def get_handlers_for_prompt() -> str:
    """
    Возвращает описание всех обработчиков для добавления в промпт
    """
    # Сначала пробуем получить из роутеров
    if _router_manager:
        return _router_manager.get_handlers_for_prompt()

    # Fallback к старым декораторам
    if not _event_handlers and not _scheduled_tasks and not _global_handlers:
        return ""

    prompt_parts = []

    if _event_handlers:
        prompt_parts.append("ДОСТУПНЫЕ ОБРАБОТЧИКИ СОБЫТИЙ:")
        for event_type, handler_info in _event_handlers.items():
            prompt_parts.append(f"- {event_type}: {handler_info['name']}")

    if _scheduled_tasks:
        prompt_parts.append("\nДОСТУПНЫЕ ЗАДАЧИ ДЛЯ ПЛАНИРОВАНИЯ:")
        for task_name, task_info in _scheduled_tasks.items():
            prompt_parts.append(f"- {task_name}: {task_info['name']}")

    if _global_handlers:
        prompt_parts.append("\nДОСТУПНЫЕ ГЛОБАЛЬНЫЕ ОБРАБОТЧИКИ:")
        for handler_type, handler_info in _global_handlers.items():
            prompt_parts.append(f"- {handler_type}: {handler_info['name']}")

    return "\n".join(prompt_parts)
