"""
Планирование задач и глобальных обработчиков.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from ...utils.context import ctx
from .db import save_global_event, save_scheduled_task
from .execution import execute_global_handler, execute_scheduled_task
from .registry import _get_registry
from .utils import format_seconds_to_human, parse_appointment_data

logger = logging.getLogger(__name__)


async def schedule_task_for_later(task_name: str, delay_seconds: int, user_id: int, user_data: str):
    """
    Планирует выполнение задачи через указанное время

    Args:
        task_name: Название задачи
        delay_seconds: Задержка в секундах
        user_id: ID пользователя
        user_data: Простой текст для задачи
    """
    scheduled_tasks, source = _get_registry("task")
    logger.debug(f"🔍 Поиск задачи '{task_name}' через источник: {source}")

    if task_name not in scheduled_tasks:
        available_tasks = list(scheduled_tasks.keys())
        logger.error(f"❌ Задача '{task_name}' не найдена. Доступные задачи: {available_tasks}")
        raise ValueError(f"Задача '{task_name}' не найдена. Доступные: {available_tasks}")

    logger.info(f"⏰ Планируем задачу '{task_name}' через {delay_seconds} секунд")

    async def delayed_task():
        await asyncio.sleep(delay_seconds)
        await execute_scheduled_task(task_name, user_id, user_data)

    asyncio.create_task(delayed_task())

    return {
        "status": "scheduled",
        "task_name": task_name,
        "delay_seconds": delay_seconds,
        "scheduled_at": datetime.now().isoformat(),
    }


async def execute_scheduled_task_from_event(user_id: int, task_name: str, event_info: str, session_id: Optional[str] = None):
    """
    Выполняет запланированную задачу на основе события от ИИ

    Args:
        user_id: ID пользователя
        task_name: Название задачи
        event_info: Информация от ИИ (только текст, время задается в декораторе или событии)
        session_id: ID сессии для отслеживания
    """
    scheduled_tasks, source = _get_registry("task")
    logger.debug(f"🔍 Источник задач: {source}, доступные задачи: {list(scheduled_tasks.keys())}")

    if task_name not in scheduled_tasks:
        available_tasks = list(scheduled_tasks.keys())
        logger.error(f"❌ Задача '{task_name}' не найдена. Доступные задачи: {available_tasks}")
        raise ValueError(f"Задача '{task_name}' не найдена. Доступные задачи: {available_tasks}")

    task_info = scheduled_tasks[task_name]
    default_delay = task_info.get("default_delay")
    event_type = task_info.get("event_type")

    if default_delay is None:
        raise ValueError(f"Для задачи '{task_name}' не указано время в декораторе (параметр delay)")

    user_data = event_info.strip() if event_info else ""

    if event_type:
        event_datetime = None

        if callable(event_type):
            logger.info(f"⏰ Задача '{task_name}' - вызываем функцию для получения времени события")

            try:
                event_datetime = await event_type(user_id, user_data)

                if not isinstance(event_datetime, datetime):
                    raise ValueError(f"Функция event_type должна вернуть datetime, получен {type(event_datetime)}")

                logger.info(f"✅ Функция вернула время события: {event_datetime}")

            except Exception as e:
                logger.error(f"❌ Ошибка в функции event_type: {e}")
                result = await schedule_task_for_later_with_db(task_name, user_id, user_data, default_delay, session_id)
                return result

        else:
            logger.info(f"⏰ Задача '{task_name}' - напоминание о событии '{event_type}' за {default_delay}с")

            if not ctx.supabase_client:
                raise RuntimeError("Supabase клиент не найден для получения времени события")

            try:
                event_data_str = await ctx.supabase_client.get_last_event_info_by_user_and_type(user_id, event_type)

                if not event_data_str:
                    logger.warning(f"Событие '{event_type}' не найдено для пользователя {user_id}")
                    result = await schedule_task_for_later_with_db(task_name, user_id, user_data, default_delay, session_id)
                    return result

                event_data = parse_appointment_data(event_data_str)

                if "datetime" not in event_data:
                    logger.warning(f"Не удалось распарсить дату/время из события '{event_type}'")
                    result = await schedule_task_for_later_with_db(task_name, user_id, user_data, default_delay, session_id)
                    return result

                event_datetime = event_data["datetime"]
                logger.info(f"✅ Получено время события из БД: {event_datetime}")

            except Exception as e:
                logger.error(f"❌ Ошибка получения события из БД: {e}")
                result = await schedule_task_for_later_with_db(task_name, user_id, user_data, default_delay, session_id)
                return result

        now = datetime.now()
        reminder_datetime = event_datetime - timedelta(seconds=default_delay)

        if reminder_datetime <= now:
            logger.warning("Напоминание уже в прошлом, отправляем немедленно")
            result = await execute_scheduled_task(task_name, user_id, user_data)
            return {
                "status": "executed_immediately",
                "task_name": task_name,
                "reason": "reminder_time_passed",
                "event_datetime": event_datetime.isoformat(),
                "result": result,
            }

        delay_seconds = int((reminder_datetime - now).total_seconds())

        event_source = "функции" if callable(task_info.get("event_type")) else f"события '{event_type}'"
        human_time = format_seconds_to_human(delay_seconds)
        logger.info(
            f"""⏰ Планируем напоминание '{task_name}' за
            {format_seconds_to_human(default_delay)} 
            до {event_source} (через {human_time} / {delay_seconds}с)"""
        )

        result = await schedule_task_for_later_with_db(task_name, user_id, user_data, delay_seconds, session_id)
        result["event_datetime"] = event_datetime.isoformat()
        result["reminder_type"] = "event_reminder"

        return result
    else:
        human_time = format_seconds_to_human(default_delay)
        logger.info(f"⏰ Планируем задачу '{task_name}' через {human_time} ({default_delay}с) с текстом: '{user_data}'")

        result = await schedule_task_for_later_with_db(task_name, user_id, user_data, default_delay, session_id)

        return result


async def schedule_global_handler_for_later(handler_type: str, delay_seconds: int, handler_data: str):
    """
    Планирует выполнение глобального обработчика через указанное время

    Args:
        handler_type: Тип глобального обработчика
        delay_seconds: Задержка в секундах
        handler_data: Данные для обработчика
    """
    global_handlers, source = _get_registry("global")
    logger.debug(f"🔍 Поиск глобального обработчика '{handler_type}' через источник: {source}")

    if handler_type not in global_handlers:
        available_handlers = list(global_handlers.keys())
        logger.error(f"❌ Глобальный обработчик '{handler_type}' не найден. Доступные: {available_handlers}")
        raise ValueError(f"Глобальный обработчик '{handler_type}' не найден. Доступные: {available_handlers}")

    logger.info(f"🌍 Планируем глобальный обработчик '{handler_type}' через {delay_seconds} секунд")

    async def delayed_global_handler():
        await asyncio.sleep(delay_seconds)
        await execute_global_handler(handler_type, handler_data)

    asyncio.create_task(delayed_global_handler())

    return {
        "status": "scheduled",
        "handler_type": handler_type,
        "delay_seconds": delay_seconds,
        "scheduled_at": datetime.now().isoformat(),
    }


async def execute_global_handler_from_event(handler_type: str, event_info: str):
    """
    Выполняет глобальный обработчик на основе события от ИИ

    Args:
        handler_type: Тип глобального обработчика
        event_info: Информация от ИИ (только текст, время задается в декораторе или функции)
    """
    global_handlers, source = _get_registry("global")

    if handler_type not in global_handlers:
        available = list(global_handlers.keys())
        logger.error(f"❌ Глобальный обработчик '{handler_type}' не найден (источник: {source}). Доступные: {available}")
        raise ValueError(f"Глобальный обработчик '{handler_type}' не найден")

    handler_info = global_handlers[handler_type]
    default_delay = handler_info.get("default_delay")
    event_type = handler_info.get("event_type")

    if default_delay is None:
        raise ValueError(f"Для глобального обработчика '{handler_type}' не указано время в декораторе (параметр delay)")

    handler_data = event_info.strip() if event_info else ""

    if event_type:
        event_datetime = None

        if callable(event_type):
            logger.info(f"🌍 Глобальный обработчик '{handler_type}' - вызываем функцию для получения времени")

            try:
                event_datetime = await event_type(handler_data)

                if not isinstance(event_datetime, datetime):
                    raise ValueError(f"Функция event_type должна вернуть datetime, получен {type(event_datetime)}")

                logger.info(f"✅ Функция вернула время события: {event_datetime}")

            except Exception as e:
                logger.error(f"❌ Ошибка в функции event_type: {e}")
                result = await schedule_global_handler_for_later_with_db(handler_type, default_delay, handler_data)
                return result

        else:
            logger.info(f"🌍 Глобальный обработчик '{handler_type}' - event_type '{event_type}' (строка)")
            result = await schedule_global_handler_for_later_with_db(handler_type, default_delay, handler_data)
            return result

        now = datetime.now()
        reminder_datetime = event_datetime - timedelta(seconds=default_delay)

        if reminder_datetime <= now:
            logger.warning("Напоминание глобального события уже в прошлом, выполняем немедленно")
            result = await execute_global_handler(handler_type, handler_data)
            return {
                "status": "executed_immediately",
                "handler_type": handler_type,
                "reason": "reminder_time_passed",
                "event_datetime": event_datetime.isoformat(),
                "result": result,
            }

        delay_seconds = int((reminder_datetime - now).total_seconds())

        human_time = format_seconds_to_human(delay_seconds)
        logger.info(
            f"""🌍 Планируем глобальный обработчик '{handler_type}' за
            {format_seconds_to_human(default_delay)} до события (через
            {human_time} / {delay_seconds}с)"""
        )

        result = await schedule_global_handler_for_later_with_db(handler_type, delay_seconds, handler_data)
        result["event_datetime"] = event_datetime.isoformat()
        result["reminder_type"] = "global_event_reminder"

        return result

    else:
        logger.info(f"🌍 Планируем глобальный обработчик '{handler_type}' через {default_delay}с с данными: '{handler_data}'")

        result = await schedule_global_handler_for_later_with_db(handler_type, default_delay, handler_data)

        return result


async def schedule_task_for_later_with_db(
    task_name: str,
    user_id: int,
    user_data: str,
    delay_seconds: int,
    session_id: Optional[str] = None,
):
    """Планирует выполнение задачи через указанное время с сохранением в БД (без asyncio.sleep)"""

    scheduled_tasks, _ = _get_registry("task")

    if task_name not in scheduled_tasks:
        import inspect

        frame = inspect.currentframe()
        line_no = frame.f_lineno if frame else "unknown"
        available_tasks = list(scheduled_tasks.keys())
        logger.error(f"❌ [decorators_scheduling.py:{line_no}] Задача '{task_name}' не найдена. Доступные: {available_tasks}")
        raise ValueError(f"Задача '{task_name}' не найдена")

    human_time = format_seconds_to_human(delay_seconds)
    logger.info(f"⏰ Планируем задачу '{task_name}' через {human_time} ({delay_seconds}с) для user_id={user_id}")

    event_id = await save_scheduled_task(task_name, user_id, user_data, delay_seconds, session_id)

    logger.info(f"💾 Задача '{task_name}' сохранена в БД с ID {event_id}, будет обработана фоновым процессором")

    return {
        "status": "scheduled",
        "task_name": task_name,
        "delay_seconds": delay_seconds,
        "event_id": event_id,
        "scheduled_at": datetime.now(timezone.utc).isoformat(),
    }


async def schedule_global_handler_for_later_with_db(handler_type: str, delay_seconds: int, handler_data: str):
    """Планирует выполнение глобального обработчика через указанное время с сохранением в БД (без asyncio.sleep)"""

    global_handlers, _ = _get_registry("global")

    if handler_type not in global_handlers:
        raise ValueError(f"Глобальный обработчик '{handler_type}' не найден")

    logger.info(f"🌍 Планируем глобальный обработчик '{handler_type}' через {delay_seconds} секунд")

    event_id = await save_global_event(handler_type, handler_data, delay_seconds)

    logger.info(f"💾 Глобальный обработчик '{handler_type}' сохранен в БД с ID {event_id}, будет обработан фоновым процессором")

    return {
        "status": "scheduled",
        "handler_type": handler_type,
        "delay_seconds": delay_seconds,
        "event_id": event_id,
        "scheduled_at": datetime.now(timezone.utc).isoformat(),
    }
