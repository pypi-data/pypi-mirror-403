import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup, Message
from aiogram.utils.media_group import MediaGroupBuilder
from sulguk import SULGUK_PARSE_MODE
from telegramify_markdown import standardize

from ..utils.context import ctx

logger = logging.getLogger(__name__)


# Создаем роутер для общих команд
utils_router = Router()


def _get_event_handlers():
    """Получает все обработчики событий из роутер-менеджера или декораторов"""
    from ..event.decorators.registry import (
        _event_handlers,
        _global_handlers,
        _scheduled_tasks,
        get_router_manager,
    )

    router_manager = get_router_manager()
    if router_manager:
        event_handlers = router_manager.get_event_handlers()
        scheduled_tasks = router_manager.get_scheduled_tasks()
        global_handlers = router_manager.get_global_handlers()
        logger.debug(
            f"🔍 RouterManager найден: {len(event_handlers)} событий, "
            f"{len(scheduled_tasks)} задач, {len(global_handlers)} глобальных обработчиков"
        )
        logger.debug(f"🔍 Доступные scheduled_tasks: {list(scheduled_tasks.keys())}")
    else:
        event_handlers = _event_handlers
        scheduled_tasks = _scheduled_tasks
        global_handlers = _global_handlers
        logger.warning("⚠️ RouterManager не найден, используем старые декораторы")
        logger.debug(f"🔍 Старые scheduled_tasks: {list(scheduled_tasks.keys())}")

    return event_handlers, scheduled_tasks, global_handlers


def _find_handler_for_event(event_type: str, event_handlers: dict, scheduled_tasks: dict):
    """Находит обработчик для события и возвращает его тип и информацию"""
    # 🆕 Оптимизация: используем один поиск вместо двойного (in + get)
    handler_info = event_handlers.get(event_type)
    if handler_info is not None:
        return "event", handler_info

    task_info = scheduled_tasks.get(event_type)
    if task_info is not None:
        return "task", task_info

    return None, None


async def _check_event_already_executed(event_type: str, user_id: int, supabase_client) -> bool:
    """Проверяет, было ли событие уже выполнено для пользователя"""
    check_query = (
        supabase_client.client.table("scheduled_events")
        .select("id, status, session_id")
        .eq("event_type", event_type)
        .eq("user_id", user_id)
        .eq("status", "completed")
    )

    if supabase_client.bot_id:
        check_query = check_query.eq("bot_id", supabase_client.bot_id)

    existing = check_query.execute()
    count = len(existing.data) if existing.data else 0

    logger.debug(f"Проверка БД: найдено {count} выполненных событий '{event_type}' для user_id={user_id}")

    if existing.data:
        logger.debug(f"Событие '{event_type}' уже выполнялось для пользователя {user_id}, пропускаем")
        return True

    return False


def _create_event_record(
    event_type: str,
    event_info: str,
    user_id: int,
    session_id: Optional[str],
    status: str,
    result: Optional[dict] = None,
    error: Optional[str] = None,
    supabase_client=None,
) -> dict:
    """Создает запись события для сохранения в БД"""
    from datetime import datetime, timezone

    event_record = {
        "event_type": event_type,
        "event_category": "user_event",
        "user_id": user_id,
        "event_data": event_info,
        "scheduled_at": None,
        "status": status,
        "session_id": session_id,
    }

    if status == "completed":
        event_record["executed_at"] = datetime.now(timezone.utc).isoformat()
        event_record["result_data"] = json.dumps(result, ensure_ascii=False) if result else None

        # Проверяем наличие поля 'info' для дашборда
        if isinstance(result, dict) and "info" in result:
            event_record["info_dashboard"] = json.dumps(result["info"], ensure_ascii=False)
            logger.debug(f"Дашборд данные добавлены: {result['info'].get('title', 'N/A')}")
    elif status == "failed":
        event_record["last_error"] = error

    if supabase_client and supabase_client.bot_id:
        event_record["bot_id"] = supabase_client.bot_id

    return event_record


async def _execute_and_save_event(
    handler_type: str,
    event_type: str,
    event_info: str,
    user_id: int,
    handler_info: dict,
    supabase_client,
    session_id: Optional[str] = None,
    defer_save: bool = False,  # 🆕 Если True, возвращает event_record вместо сохранения
) -> tuple[str | None | dict, bool]:
    """
    Выполняет обработчик события и сохраняет результат в БД.

    Args:
        defer_save: Если True, возвращает event_record вместо сохранения (для батч-INSERT)

    Returns:
        tuple: (event_id или event_record, should_notify)
    """
    from ..event.decorators.execution import execute_event_handler
    from ..event.decorators.scheduling import execute_scheduled_task_from_event

    logger.debug(f"Немедленно выполняем {handler_type}: '{event_type}'")

    try:
        # Выполняем обработчик в зависимости от типа
        if handler_type == "event":
            result = await execute_event_handler(event_type, user_id, event_info)
        elif handler_type == "task":
            result = await execute_scheduled_task_from_event(user_id, event_type, event_info, session_id)
        else:
            raise ValueError(f"Неизвестный тип обработчика: {handler_type}")

        # Создаем запись события
        event_record = _create_event_record(
            event_type=event_type,
            event_info=event_info,
            user_id=user_id,
            session_id=session_id,
            status="completed",
            result=result,
            supabase_client=supabase_client,
        )

        # 🆕 Если defer_save=True, возвращаем event_record для батч-сохранения
        if defer_save:
            logger.debug(f"Событие '{event_type}' подготовлено для батч-сохранения")
            return event_record, handler_info.get("notify", False)

        # Иначе сохраняем сразу
        response = supabase_client.client.table("scheduled_events").insert(event_record).execute()
        event_id = response.data[0]["id"]

        logger.debug(f"Событие {event_id} выполнено и сохранено как completed")
        return event_id, handler_info.get("notify", False)

    except Exception as e:
        logger.error(f"   ❌ Ошибка выполнения события: {e}")

        # Ошибки всегда сохраняем сразу (критично для диагностики)
        event_record = _create_event_record(
            event_type=event_type,
            event_info=event_info,
            user_id=user_id,
            session_id=session_id,
            status="failed",
            error=str(e),
            supabase_client=supabase_client,
        )

        try:
            supabase_client.client.table("scheduled_events").insert(event_record).execute()
            logger.debug("Ошибка сохранена в БД")
        except Exception as db_error:
            logger.error(f"Не удалось сохранить ошибку в БД: {db_error}")

        raise


async def _handle_scheduled_task(
    event_type: str,
    event_info: str,
    user_id: int,
    session_id: str,
    scheduled_tasks: dict,
    supabase_client,
) -> tuple[bool, bool]:
    """Обрабатывает запланированную задачу"""
    from ..event.decorators.scheduling import execute_scheduled_task_from_event

    task_info = scheduled_tasks.get(event_type, {})
    send_ai_response_flag = task_info.get("send_ai_response", True)

    logger.debug(f"Планируем scheduled_task: '{event_type}', send_ai_response={send_ai_response_flag}")

    if not send_ai_response_flag:
        logger.debug(f"Задача '{event_type}' запретила отправку сообщения от ИИ")

    try:
        result = await execute_scheduled_task_from_event(user_id, event_type, event_info, session_id)
        event_id = result.get("event_id", "unknown")
        should_notify = result.get("notify", False)
        logger.debug(f"Задача запланирована: {event_id}")
        return send_ai_response_flag, should_notify
    except Exception as e:
        if "once_only=True" in str(e):
            logger.debug(f"Задача '{event_type}' уже запланирована, пропускаем")
            return True, False
        else:
            logger.error(f"   ❌ Ошибка планирования scheduled_task '{event_type}': {e}")
            raise


async def _handle_global_handler(event_type: str, event_info: str, global_handlers: dict) -> bool:
    """Обрабатывает глобальный обработчик"""
    from ..event.decorators.scheduling import execute_global_handler_from_event

    logger.debug(f"Планируем global_handler: '{event_type}'")

    try:
        result = await execute_global_handler_from_event(event_type, event_info)
        event_id = result.get("event_id", "unknown")
        should_notify = result.get("notify", False)
        logger.debug(f"Глобальное событие запланировано: {event_id}")
        return should_notify
    except Exception as e:
        if "once_only=True" in str(e):
            logger.debug(f"Глобальное событие '{event_type}' уже запланировано, пропускаем")
            return False
        else:
            logger.error(f"   ❌ Ошибка планирования global_handler '{event_type}': {e}")
            raise


async def _handle_event_notification(
    handler_type: str,
    handler_info: dict,
    should_notify: bool,
    user_id: int,
    event: dict,
):
    """Обрабатывает уведомления админам о событии"""
    if handler_type == "task":
        notify_time = handler_info.get("notify_time", "after")
        if notify_time == "before" and should_notify:
            await notify_admins_about_event(user_id, event)
            logger.debug("Админы уведомлены (notify_time=before)")
        elif notify_time == "after":
            logger.debug("Уведомление будет отправлено после выполнения задачи")
    else:
        if should_notify:
            await notify_admins_about_event(user_id, event)
            logger.debug("Админы уведомлены")


async def _process_single_event(
    event: dict,
    session_id: str,
    user_id: int,
    event_handlers: dict,
    scheduled_tasks: dict,
    global_handlers: dict,
    supabase_client,
    executed_events: Optional[set] = None,  # Множество уже выполненных событий (из батч-проверки)
    defer_save: bool = False,  # 🆕 Если True, возвращает event_record вместо сохранения
) -> tuple[bool, dict | None]:
    """
    Обрабатывает одно событие

    Returns:
        tuple: (should_send_ai_response, event_record или None)
        event_record возвращается только если defer_save=True и событие успешно обработано
    """
    event_type = event.get("тип", "")
    event_info = event.get("инфо", "")

    if not event_type:
        logger.warning(f"⚠️ Событие без типа: {event}")
        return True, None

    logger.debug(f"Обработка события: тип={event_type}, данные={event_info[:100] if len(event_info) > 100 else event_info}")

    should_send_ai_response = True
    handler_type = None
    handler_info = None
    should_notify = False
    event_record = None

    # Инициализируем executed_events если не передан
    if executed_events is None:
        executed_events = set()

    try:
        # Ищем обработчик для события
        handler_type, handler_info = _find_handler_for_event(event_type, event_handlers, scheduled_tasks)

        if handler_info:
            once_only = handler_info.get("once_only", True)
            send_ai_response_flag = handler_info.get("send_ai_response", True)
            should_notify = handler_info.get("notify", False)

            logger.debug(
                f"{handler_type.title()} '{event_type}': "
                f"once_only={once_only}, send_ai_response={send_ai_response_flag}, "
                f"notify={should_notify}"
            )

            if not send_ai_response_flag:
                should_send_ai_response = False
                logger.debug(f"{handler_type.upper()} '{event_type}' запретил отправку сообщения от ИИ")

            # Проверяем, было ли событие уже выполнено (используем батч-результат или делаем отдельный запрос)
            if once_only:
                if event_type in executed_events:
                    logger.debug(f"Событие '{event_type}' уже выполнялось (из батч-проверки), пропускаем")
                    return should_send_ai_response, None
                # Если события нет в батч-результате, делаем отдельную проверку (fallback)
                elif await _check_event_already_executed(event_type, user_id, supabase_client):
                    return should_send_ai_response, None

            # Выполняем и сохраняем событие
            try:
                result = await _execute_and_save_event(
                    handler_type=handler_type,
                    event_type=event_type,
                    event_info=event_info,
                    user_id=user_id,
                    session_id=session_id,
                    handler_info=handler_info,
                    supabase_client=supabase_client,
                    defer_save=defer_save,  # 🆕 Передаем параметр отложенного сохранения
                )

                # Если defer_save=True, result будет (event_record, should_notify)
                # Если defer_save=False, result будет (event_id, should_notify)
                if isinstance(result, tuple):
                    event_data, should_notify = result
                    if defer_save and isinstance(event_data, dict):
                        event_record = event_data
            except Exception:
                return should_send_ai_response, None

        elif event_type in scheduled_tasks:
            # Обрабатываем как запланированную задачу (не найденную в первом поиске)
            try:
                send_ai_response_flag, should_notify = await _handle_scheduled_task(
                    event_type=event_type,
                    event_info=event_info,
                    user_id=user_id,
                    session_id=session_id,
                    scheduled_tasks=scheduled_tasks,
                    supabase_client=supabase_client,
                )
                if not send_ai_response_flag:
                    should_send_ai_response = False
            except Exception:
                return should_send_ai_response, None

        elif event_type in global_handlers:
            # Обрабатываем как глобальный обработчик
            try:
                should_notify = await _handle_global_handler(event_type, event_info, global_handlers)
            except Exception:
                return should_send_ai_response, None

        else:
            logger.warning(f"   ⚠️ Обработчик '{event_type}' не найден среди зарегистрированных")
            logger.debug("   🔍 Доступные обработчики:")
            logger.debug(f"      - event_handlers: {list(event_handlers.keys())}")
            logger.debug(f"      - scheduled_tasks: {list(scheduled_tasks.keys())}")
            logger.debug(f"      - global_handlers: {list(global_handlers.keys())}")

    except ValueError as e:
        logger.warning(f"   ⚠️ Обработчик/задача не найдены: {e}")
    except Exception as e:
        logger.error(f"   ❌ Ошибка в обработчике/задаче: {e}")
        logger.exception("   Стек ошибки:")

    # Обрабатываем уведомления (только если не defer_save, иначе обработаем после батч-INSERT)
    if handler_info and handler_type and not defer_save:
        await _handle_event_notification(handler_type, handler_info, should_notify, user_id, event)

    return should_send_ai_response, event_record


async def process_file_events(
    events: list,
    user_id: int,
    session_id: str,
    chat_id: int,
    supabase_client,
) -> list:
    """
    Обрабатывает файловые события и возвращает список FileSender объектов

    Args:
        events: Список событий из метаданных ИИ
        user_id: ID пользователя
        session_id: ID сессии
        chat_id: ID чата для отправки файлов
        supabase_client: Клиент Supabase

    Returns:
        list: Список FileSender объектов с настроенными файлами для отправки
    """
    from ..file_router.execution import execute_file_event_handler
    from ..file_router.sender import FileSender

    event_handlers, scheduled_tasks, _ = _get_event_handlers()
    file_senders = []

    # 🆕 БАТЧ-ПРОВЕРКА: собираем все файловые события с once_only=True и проверяем одним запросом
    events_to_check = set()  # Используем set для автоматического удаления дубликатов
    for event in events:
        event_type = event.get("тип", "")
        if not event_type:
            continue

        handler_info = event_handlers.get(event_type, {})
        if handler_info.get("file_handler") and handler_info.get("once_only", False):
            events_to_check.add(event_type)

    # Выполняем батч-проверку если есть события для проверки
    executed_events = set()
    if events_to_check:
        executed_events = await supabase_client.batch_check_events_executed(
            event_types=list(events_to_check),
            user_id=user_id,  # Преобразуем set в list для передачи
        )
        logger.debug(f"Батч-проверка файловых событий: {len(executed_events)} из {len(events_to_check)} уже выполнены")

    # 🆕 БАТЧ-СОХРАНЕНИЕ: собираем события для батч-INSERT
    events_to_save = []

    for event in events:
        event_type = event.get("тип", "")
        event_info = event.get("инфо", "")

        if not event_type:
            continue

        # Проверяем, является ли это файловым обработчиком
        handler_info = event_handlers.get(event_type, {})
        if not handler_info.get("file_handler"):
            continue  # Пропускаем не-файловые события

        try:
            # Проверяем once_only (используем батч-результат или делаем отдельный запрос)
            once_only = handler_info.get("once_only", False)
            if once_only:
                if event_type in executed_events:
                    logger.debug(f"📁 Файловое событие '{event_type}' уже выполнялось (из батч-проверки), пропускаем")
                    continue
                # Если события нет в батч-результате, делаем отдельную проверку (fallback)
                elif await _check_event_already_executed(event_type, user_id, supabase_client):
                    logger.debug(f"📁 Файловое событие '{event_type}' уже выполнялось, пропускаем")
                    continue

            # Создаем FileSender
            file_sender = FileSender(user_id=user_id, chat_id=chat_id)

            # Выполняем файловый обработчик через специальную функцию
            await execute_file_event_handler(event_type, file_sender, user_id, event_info)

            # Проверяем, есть ли файлы для отправки
            if file_sender.has_files():
                file_senders.append(file_sender)
                logger.debug(f"📁 FileSender создан для события '{event_type}'")
            else:
                logger.debug(f"📁 FileSender для события '{event_type}' не содержит файлов")

            # 🆕 Собираем событие для батч-сохранения вместо немедленного INSERT
            event_record = _create_event_record(
                event_type=event_type,
                event_info=event_info,
                user_id=user_id,
                session_id=session_id,
                status="completed",
                result={"file_sender": "created"},
                supabase_client=supabase_client,
            )
            events_to_save.append(event_record)

        except Exception as e:
            logger.error(f"❌ Ошибка обработки файлового события '{event_type}': {e}")
            logger.exception("Стек ошибки:")

    # 🆕 БАТЧ-INSERT: сохраняем все файловые события одним запросом
    if events_to_save:
        try:
            event_ids = await supabase_client.batch_insert_events(events_to_save)
            logger.debug(f"Батч-INSERT файловых событий: сохранено {len(event_ids)} событий")
        except Exception as e:
            logger.error(f"❌ Ошибка батч-INSERT файловых событий: {e}")
            logger.exception("Стек ошибки:")

    return file_senders


async def process_events(session_id: str, events: list, user_id: int) -> bool:
    """
    Обрабатывает события из ответа ИИ (исключая файловые события)

    Returns:
        bool: True если нужно отправить сообщение от ИИ, False если не нужно
    """
    # Проверяем кастомный процессор (с fallback на старый атрибут для совместимости)
    custom_processor = getattr(ctx, 'custom_event_processor', None) or getattr(ctx, 'custom_event_proceses', None)
    if custom_processor:
        logger.info(f"🔄 Используется кастомная обработка событий: {custom_processor.__name__}")
        await custom_processor(session_id, events, user_id)
        return True

    # Стандартная обработка
    should_send_ai_response = True

    # Получаем все обработчики один раз
    event_handlers, scheduled_tasks, global_handlers = _get_event_handlers()

    # Фильтруем файловые события - они обрабатываются отдельно
    regular_events = []
    for event in events:
        event_type = event.get("тип", "")
        handler_info = event_handlers.get(event_type, {})
        if not handler_info.get("file_handler"):
            regular_events.append(event)

    # 🆕 БАТЧ-ПРОВЕРКА: собираем все события с once_only=True и проверяем одним запросом
    events_to_check = set()  # Используем set для автоматического удаления дубликатов
    for event in regular_events:
        event_type = event.get("тип", "")
        if not event_type:
            continue

        # 🆕 Оптимизация: используем _find_handler_for_event для поиска в обоих словарях за один проход
        handler_type, handler_info = _find_handler_for_event(event_type, event_handlers, scheduled_tasks)
        if handler_info and handler_info.get("once_only", True):  # По умолчанию once_only=True
            events_to_check.add(event_type)

    # Выполняем батч-проверку если есть события для проверки
    executed_events = set()
    if events_to_check:
        executed_events = await ctx.supabase_client.batch_check_events_executed(
            event_types=list(events_to_check),
            user_id=user_id,  # Преобразуем set в list для передачи
        )
        logger.debug(f"Батч-проверка: {len(executed_events)} из {len(events_to_check)} событий уже выполнены")

    # 🆕 БАТЧ-СОХРАНЕНИЕ: собираем события для батч-INSERT
    events_to_save = []
    events_notifications = []  # Список (event_record, handler_type, handler_info, user_id, event) для уведомлений

    # Обрабатываем только обычные события
    for event in regular_events:
        try:
            event_should_send, event_record = await _process_single_event(
                event=event,
                session_id=session_id,
                user_id=user_id,
                event_handlers=event_handlers,
                scheduled_tasks=scheduled_tasks,
                global_handlers=global_handlers,
                supabase_client=ctx.supabase_client,
                executed_events=executed_events,  # Передаем уже проверенные события
                defer_save=True,  # 🆕 Откладываем сохранение для батч-INSERT
            )

            # Если хотя бы одно событие запретило отправку, устанавливаем флаг
            if not event_should_send:
                should_send_ai_response = False

            # Если событие успешно обработано и есть event_record, добавляем в список для батч-сохранения
            if event_record:
                events_to_save.append(event_record)
                # Сохраняем информацию для уведомлений
                event_type = event.get("тип", "")
                handler_info = event_handlers.get(event_type, {})
                if handler_info and handler_info.get("notify", False):
                    handler_type, _ = _find_handler_for_event(event_type, event_handlers, scheduled_tasks)
                    events_notifications.append((event_record, handler_type, handler_info, user_id, event))

        except Exception as e:
            logger.error(f"❌ Ошибка обработки события {event}: {e}")
            logger.exception("Стек ошибки:")

    # 🆕 БАТЧ-INSERT: сохраняем все события одним запросом
    if events_to_save:
        try:
            event_ids = await ctx.supabase_client.batch_insert_events(events_to_save)
            logger.debug(f"Батч-INSERT: сохранено {len(event_ids)} событий")

            # Обрабатываем уведомления для сохраненных событий
            for event_record, handler_type, handler_info, user_id_notif, event_notif in events_notifications:
                try:
                    await _handle_event_notification(handler_type, handler_info, True, user_id_notif, event_notif)
                except Exception as e:
                    logger.error(f"Ошибка отправки уведомления для события {event_record.get('event_type', 'unknown')}: {e}")
        except Exception as e:
            logger.error(f"❌ Ошибка батч-INSERT событий: {e}")
            logger.exception("Стек ошибки:")

    logger.debug(f"Итоговый флаг send_ai_response: {should_send_ai_response}")
    return should_send_ai_response


async def notify_admins_about_event(user_id: int, event: dict):
    """Отправляем уведомление админам о событии с явным указанием ID пользователя"""

    event_type = event.get("тип", "")
    event_info = event.get("инфо", "")

    if not event_type:
        return

    # Получаем информацию о пользователе для username
    try:
        user_response = (
            ctx.supabase_client.client.table("sales_users").select("first_name", "last_name", "username").eq("telegram_id", user_id).execute()
        )

        user_info = user_response.data[0] if user_response.data else {}

        # Формируем имя пользователя (без ID)
        name_parts = []
        if user_info.get("first_name"):
            name_parts.append(user_info["first_name"])
        if user_info.get("last_name"):
            name_parts.append(user_info["last_name"])

        user_name = " ".join(name_parts) if name_parts else "Без имени"

        # Формируем отображение пользователя с ОБЯЗАТЕЛЬНЫМ ID
        if user_info.get("username"):
            user_display = f"{user_name} (@{user_info['username']})"
        else:
            user_display = user_name

    except Exception as e:
        logger.error(f"Ошибка получения информации о пользователе {user_id}: {e}")
        user_display = "Пользователь"

    emoji_map = {"телефон": "📱", "консультация": "💬", "покупка": "💰", "отказ": "❌"}

    emoji = emoji_map.get(event_type, "🔔")

    # 🆕 ИСПРАВЛЕНИЕ: ID всегда отображается отдельной строкой для удобства копирования
    notification = f"""
{emoji} {event_type.upper()}!
👤 {user_display}
🆔 ID: {user_id}
📝 {event_info}
🕐 {datetime.now().strftime('%H:%M')}
"""

    # Создаем клавиатуру с кнопками
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💬 Чат", callback_data=f"admin_chat_{user_id}"),
                InlineKeyboardButton(text="📋 История", callback_data=f"admin_history_{user_id}"),
            ]
        ]
    )

    try:
        # Отправляем всем активным админам
        active_admins = await ctx.admin_manager.get_active_admins()
        for admin_id in active_admins:
            try:
                await ctx.bot.send_message(admin_id, notification.strip(), reply_markup=keyboard)
            except Exception as e:
                logger.error(f"Ошибка отправки уведомления админу {admin_id}: {e}")

    except Exception as e:
        logger.error(f"Ошибка отправки уведомления админам: {e}")


def _get_parse_mode() -> str | None:
    """Получает parse_mode из конфигурации"""
    parse_mode = ctx.config.MESSAGE_PARSE_MODE if ctx.config.MESSAGE_PARSE_MODE != "None" else None
    
    # Если HTML, возвращаем SULGUK_PARSE_MODE для работы с middleware
    if parse_mode and parse_mode.upper() == "HTML":
        logger.debug(f"Parse mode: SULGUK_PARSE_MODE (для HTML)")
        return SULGUK_PARSE_MODE
    
    logger.debug(f"Parse mode: {parse_mode}")
    return parse_mode


def _get_media_type(file_path: str) -> str:
    """Определяет тип медиа по расширению файла"""
    ext = Path(file_path).suffix.lower()
    # Поддерживаемые форматы изображений в Telegram
    photo_extensions = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff", ".tif", ".svg", ".ico", ".heic", ".heif"}
    # Поддерживаемые форматы видео в Telegram
    video_extensions = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v", ".3gp", ".flv", ".wmv", ".mpg", ".mpeg"}

    if ext in photo_extensions:
        return "photo"
    elif ext in video_extensions:
        return "video"
    else:
        return "document"


async def _filter_sent_files(user_id: int, files_list: list, directories_list: list) -> tuple[list, list]:
    """Возвращает файлы и каталоги без фильтрации (убрана проверка уже отправленных)"""
    logger.debug(f"Передано файлов: {files_list}, каталогов: {directories_list}")
    return files_list, directories_list


def _process_files(actual_files_list: list, actual_directories_list: list) -> tuple[list, list, list]:
    """Обрабатывает файлы и каталоги, разделяя их по типам медиа"""
    video_files = []
    photo_files = []
    document_files = []

    def add_file(file_path: Path, source: str = ""):
        """Добавляет файл в соответствующий список по типу"""
        if not file_path.is_file():
            logger.warning(f"   ⚠️ Файл не найден: {file_path}")
            return

        media_type = _get_media_type(str(file_path))
        source_text = f" из {source}" if source else ""

        if media_type == "video":
            video_files.append(file_path)
            logger.debug(f"Добавлено видео{source_text}: {file_path.name}")
        elif media_type == "photo":
            photo_files.append(file_path)
            logger.debug(f"Добавлено фото{source_text}: {file_path.name}")
        else:
            document_files.append(file_path)
            logger.debug(f"Добавлен документ{source_text}: {file_path.name}")

    # Обрабатываем прямые файлы
    # Определяем путь к папке files относительно рабочей директории
    files_dir = Path("files").resolve()
    if not files_dir.exists():
        # Пробуем найти files относительно директории промптов
        try:
            from ..utils.context import ctx

            if ctx.config and ctx.config.PROMT_FILES_DIR:
                prompts_dir = Path(ctx.config.PROMT_FILES_DIR)
                files_dir = prompts_dir.parent / "files"
        except Exception:
            pass

    for file_name in actual_files_list:
        try:
            file_path = files_dir / file_name
            add_file(file_path)
        except Exception as e:
            logger.error(f"   ❌ Ошибка обработки файла {file_name}: {e}")

    # Обрабатываем файлы из каталогов
    for dir_name in actual_directories_list:
        dir_path = Path(dir_name)
        try:
            if dir_path.is_dir():
                for file_path in dir_path.iterdir():
                    try:
                        add_file(file_path, str(dir_path))
                    except Exception as e:
                        logger.error(f"   ❌ Ошибка обработки файла {file_path}: {e}")
            else:
                logger.warning(f"   ⚠️ Каталог не найден: {dir_path}")
        except Exception as e:
            logger.error(f"   ❌ Ошибка обработки каталога {dir_path}: {e}")

    return video_files, photo_files, document_files


def _get_chat_action_for_file_lists(video_files: list, photo_files: list, document_files: list) -> str:
    """
    Определяет chat action для списков файлов разных типов

    Args:
        video_files: Список видео файлов
        photo_files: Список фото файлов
        document_files: Список документов

    Returns:
        Chat action: 'upload_photo', 'upload_video', 'upload_document' или 'typing'
    """
    # Приоритет: видео > фото > документы (видео загружается дольше)
    if video_files:
        return "upload_video"
    elif photo_files:
        return "upload_photo"
    elif document_files:
        return "upload_document"
    else:
        return "typing"


def _is_parse_error(error: Exception) -> bool:
    """Проверяет, является ли ошибка ошибкой парсинга разметки"""
    error_str = str(error)
    error_type = type(error).__name__
    parse_errors = [
        "can't parse entities",
        "Bad Request",
        "parse",
        "Unexpected end tag",
        "Unclosed tag",
    ]
    return any(parse_err.lower() in error_str.lower() for parse_err in parse_errors) or "TelegramBadRequest" in error_type


async def _send_media_groups(
    message: Message,
    video_files: list,
    photo_files: list,
    document_files: list,
    text: str,
    parse_mode: str | None,
) -> Message:
    """Отправляет медиа группы и текст сообщения"""
    # Определяем и отправляем chat action перед отправкой файлов
    chat_action = _get_chat_action_for_file_lists(video_files, photo_files, document_files)
    if chat_action != "typing":
        try:
            await ctx.bot.send_chat_action(chat_id=message.chat.id, action=chat_action)
            logger.debug(f"📤 Chat action отправлен: {chat_action}")
        except Exception as e:
            logger.warning(f"⚠️ Не удалось отправить chat action '{chat_action}': {e}")

    # 1. Отправляем видео (если есть)
    if video_files:
        video_group = MediaGroupBuilder()
        for file_path in video_files:
            video_group.add_video(media=FSInputFile(str(file_path)))

        videos = video_group.build()
        if videos:
            await message.answer_media_group(media=videos)
            logger.debug(f"Отправлено {len(videos)} видео")

    # 2. Отправляем фото (если есть)
    if photo_files:
        photo_group = MediaGroupBuilder()
        for file_path in photo_files:
            photo_group.add_photo(media=FSInputFile(str(file_path)))

        photos = photo_group.build()
        if photos:
            await message.answer_media_group(media=photos)
            logger.debug(f"Отправлено {len(photos)} фото")

    # 3. Отправляем текст
    # Стандартизируем текст для Markdown/MarkdownV2 и преобразуем в MarkdownV2
    if parse_mode in ("Markdown", "MarkdownV2") and text:
        text_to_send = standardize(text)
        parse_mode = "MarkdownV2"
    else:
        text_to_send = text
    
    try:
        result = await message.answer(text_to_send, parse_mode=parse_mode)
    except Exception as e:
        if _is_parse_error(e):
            result = await message.answer(text_to_send, parse_mode=None)
        else:
            raise

    # 4. Отправляем документы (если есть)
    if document_files:
        doc_group = MediaGroupBuilder()
        for file_path in document_files:
            doc_group.add_document(media=FSInputFile(str(file_path)))

        docs = doc_group.build()
        if docs:
            await message.answer_media_group(media=docs)
            logger.debug(f"Отправлено {len(docs)} документов")

    return result


async def _save_sent_files_to_db(
    user_id: int,
    actual_files_list: list,
    actual_directories_list: list,
    video_files: list,
    photo_files: list,
    document_files: list,
):
    """Заглушка - сохранение файлов в БД отключено"""
    # Сохранение файлов в БД отключено
    pass


def _validate_text(text: str) -> str:
    """Проверяет и валидирует текст сообщения"""
    if not text or not text.strip():
        logger.error("❌ КРИТИЧЕСКАЯ ОШИБКА: final_text пуст после обработки!")
        logger.error(f"   Исходный text: '{text[:200]}...'")
        return "Ошибка формирования ответа. Попробуйте еще раз."
    return text


def _is_bot_blocked_error(error: Exception) -> bool:
    """Проверяет, является ли ошибка блокировкой бота пользователем"""
    error_str = str(error)
    error_type = type(error).__name__
    return "Forbidden: bot was blocked by the user" in error_str or "TelegramForbiddenError" in error_type


async def _handle_send_error(message: Message, error: Exception, user_id: int, original_text: Optional[str] = None):
    """Обрабатывает ошибки при отправке сообщения"""
    if _is_bot_blocked_error(error):
        logger.warning(f"🚫 Бот заблокирован пользователем {user_id}")
        return None

    logger.error(f"❌ ОШИБКА в send_message: {error}")

    # Если ошибка парсинга и есть исходный текст, пытаемся отправить без parse_mode
    if _is_parse_error(error) and original_text:
        logger.warning("⚠️ Ошибка парсинга разметки, пытаемся отправить текст без форматирования")
        try:
            result = await message.answer(original_text, parse_mode=None)
            logger.info("✅ Сообщение отправлено без форматирования")
            return result
        except Exception as e2:
            if _is_bot_blocked_error(e2):
                logger.warning(f"🚫 Бот заблокирован пользователем {user_id} (fallback)")
                return None
            logger.error(f"❌ Не удалось отправить даже без форматирования: {e2}")

    logger.exception("Полный стек ошибки send_message:")

    # Пытаемся отправить простое сообщение без форматирования
    try:
        fallback_text = "Произошла ошибка при отправке ответа. Попробуйте еще раз."
        result = await message.answer(fallback_text)
        logger.info("✅ Запасное сообщение отправлено")
        return result
    except Exception as e2:
        if _is_bot_blocked_error(e2):
            logger.warning(f"🚫 Бот заблокирован пользователем {user_id} (fallback)")
            return None

        logger.error(f"❌ Даже запасное сообщение не отправилось: {e2}")
        raise


async def send_message(
    message: Message,
    text: str,
    files_list: list = [],
    directories_list: list = [],
    parse_mode: str | None = None,
    **kwargs,
):
    """Вспомогательная функция для отправки сообщений с настройкой parse_mode"""
    user_id = message.from_user.id

    logger.debug(f"send_message вызвана: user={user_id}, text_len={len(text)}, debug={ctx.config.DEBUG_MODE}")

    try:
        # Используем переданный parse_mode, или получаем из конфига
        if parse_mode is None:
            parse_mode = _get_parse_mode()
        final_text = _validate_text(text)

        # Стандартизируем текст для Markdown/MarkdownV2 и преобразуем в MarkdownV2
        if parse_mode in ("Markdown", "MarkdownV2"):
            final_text = standardize(final_text)
            parse_mode = "MarkdownV2"

        logger.debug(f"Подготовка сообщения: {len(final_text)} символов")

        # Фильтруем уже отправленные файлы
        actual_files_list, actual_directories_list = await _filter_sent_files(user_id, files_list, directories_list)

        # Если есть файлы для отправки
        if actual_files_list or actual_directories_list:
            logger.debug(f"Файлов для обработки: {len(actual_files_list)}, каталогов: {len(actual_directories_list)}")

            # Обрабатываем файлы
            video_files, photo_files, document_files = _process_files(actual_files_list, actual_directories_list)

            # Отправляем медиа группы и текст (chat action отправляется внутри _send_media_groups)
            result = await _send_media_groups(
                message=message,
                video_files=video_files,
                photo_files=photo_files,
                document_files=document_files,
                text=final_text,
                parse_mode=parse_mode,
            )

            # 🆕 Сохранение названий файлов и каталогов в БД убрано

            return result
        else:
            # Если нет файлов, отправляем просто текст
            logger.debug("Нет файлов для отправки, отправляем как текст")
            result = await message.answer(final_text, parse_mode=parse_mode, **kwargs)
            return result

    except Exception as e:
        return await _handle_send_error(message, e, user_id, final_text)


async def cleanup_expired_conversations():
    """Периодическая очистка просроченных диалогов"""
    while True:
        try:
            await asyncio.sleep(300)  # каждые 5 минут
            await ctx.conversation_manager.cleanup_expired_conversations()
        except Exception:
            pass  # Тихая очистка без логирования


# 🆕 Вспомогательные функции для приветственного файла


async def get_welcome_file_path() -> str | None:
    """Возвращает путь к PDF файлу из папки WELCOME_FILE_DIR из конфига.

    Источник настроек: configs/<bot_id>/.env (переменная WELCOME_FILE_DIR)
    Рабочая директория уже установлена запускалкой на configs/<bot_id>.

    Returns:
        str | None: Путь к PDF файлу или None, если файл не найден
    """
    try:
        if not ctx.config.WELCOME_FILE_DIR:
            return None

        folder = Path(ctx.config.WELCOME_FILE_DIR)
        if not folder.exists():
            logger.info(f"Директория приветственных файлов не существует: {ctx.config.WELCOME_FILE_DIR}")
            return None

        if not folder.is_dir():
            logger.info(f"Путь не является директорией: {ctx.config.WELCOME_FILE_DIR}")
            return None

        # Ищем первый PDF файл в директории
        for path in folder.iterdir():
            if path.is_file() and path.suffix.lower() == ".pdf":
                return str(path)

        logger.info(f"PDF файл не найден в директории: {ctx.config.WELCOME_FILE_DIR}")
        return None

    except Exception as e:
        logger.error(f"Ошибка при поиске приветственного файла: {e}")
        return None


async def get_welcome_msg_path() -> str | None:
    """Возвращает путь к файлу welcome_file_msg.txt из той же директории, где находится PDF файл.

    Returns:
        str | None: Путь к файлу с подписью или None, если файл не найден
    """
    try:
        pdf_path = await get_welcome_file_path()
        if not pdf_path:
            return None

        msg_path = str(Path(pdf_path).parent / "welcome_file_msg.txt")
        if not Path(msg_path).is_file():
            logger.info(f"Файл подписи не найден: {msg_path}")
            return None

        return msg_path

    except Exception as e:
        logger.error(f"Ошибка при поиске файла подписи: {e}")
        return None


async def send_welcome_file(message: Message) -> str:
    """
    Отправляет приветственный файл с подписью из файла welcome_file_msg.txt.
    Если файл подписи не найден, используется пустая подпись.

    Returns:
         str: текст подписи
    """
    try:
        file_path = await get_welcome_file_path()
        if not file_path:
            return ""

        # Получаем путь к файлу с подписью и читаем его
        caption = ""
        msg_path = await get_welcome_msg_path()
        if msg_path:
            try:
                with open(msg_path, "r", encoding="utf-8") as f:
                    caption = f.read().strip()
                    logger.info(f"Подпись загружена из файла: {msg_path}")
            except Exception as e:
                logger.error(f"Ошибка при чтении файла подписи {msg_path}: {e}")

        document = FSInputFile(file_path)

        await message.answer_document(document=document, caption=caption, parse_mode=ctx.config.MESSAGE_PARSE_MODE)

        logger.info(f"Приветственный файл отправлен: {file_path}")
        return caption
    except Exception as e:
        logger.error(f"Ошибка при отправке приветственного файла: {e}")
        return ""


# Общие команды


@utils_router.message(Command("help"))
async def help_handler(message: Message):
    """Справка"""
    try:
        # Разная справка для админов и пользователей
        if ctx.admin_manager.is_admin(message.from_user.id):
            if ctx.admin_manager.is_in_admin_mode(message.from_user.id):
                help_text = """
👑 **Справка для администратора**

**Команды:**
• `/стат` - статистика воронки и событий
• `/дашборд` - ссылка на дашборд аналитики
• `/история <user_id>` - история пользователя
• `/чат <user_id>` - начать диалог с пользователем
• `/чаты` - показать активные диалоги
• `/стоп` - завершить текущий диалог
• `/админ` - переключиться в режим пользователя

**Особенности:**
• Все сообщения пользователей к админу пересылаются
• Ваши сообщения отправляются пользователю как от бота
• Диалоги автоматически завершаются через 30 минут
"""
                await message.answer(help_text, parse_mode="Markdown")
                return

        # Обычная справка для пользователей
        help_text = await ctx.prompt_loader.load_help_message()
        await send_message(message, help_text)

    except Exception as e:
        logger.error(f"Ошибка загрузки справки: {e}")
        # Fallback справка
        await send_message(
            message,
            "🤖 Ваш помощник готов к работе! Напишите /start для начала диалога.",
        )


@utils_router.message(Command("status"))
async def status_handler(message: Message):
    """Проверка статуса системы"""
    try:
        # Проверяем OpenAI
        openai_status = await ctx.openai_client.check_api_health()

        # Проверяем промпты
        prompts_status = await ctx.prompt_loader.validate_prompts()

        # Статистика для админов
        if ctx.admin_manager.is_admin(message.from_user.id):
            status_message = f"""
🔧 **Статус системы:**

OpenAI API: {'✅' if openai_status else '❌'}
Промпты: {'✅ ' + str(sum(prompts_status.values())) + '/' + str(len(prompts_status)) + ' загружено' if any(prompts_status.values()) else '❌'}
База данных: ✅ (соединение активно)

👑 **Админы:** {ctx.admin_manager.get_stats()['active_admins']}/{ctx.admin_manager.get_stats()['total_admins']} активны
🐛 **Режим отладки:** {'Включен' if ctx.config.DEBUG_MODE else 'Выключен'}

Все системы работают нормально!
            """
        else:
            status_message = f"""
🔧 **Статус системы:**

OpenAI API: {'✅' if openai_status else '❌'}
Промпты: {'✅ ' + str(sum(prompts_status.values())) + '/' + str(len(prompts_status)) + ' загружено' if any(prompts_status.values()) else '❌'}
База данных: ✅ (соединение активно)

Все системы работают нормально!
            """

        await send_message(message, status_message)

    except Exception as e:
        logger.error(f"Ошибка проверки статуса: {e}")
        await send_message(message, "❌ Ошибка при проверке статуса системы")


def parse_utm_from_start_param(start_param: str) -> dict:
    """Парсит UTM-метки и сегмент из start параметра в формате source-vk_campaign-summer2025_seg-premium

    Args:
        start_param: строка вида 'source-vk_campaign-summer2025_seg-premium' или полная ссылка

    Returns:
        dict: {'utm_source': 'vk', 'utm_campaign': 'summer2025', 'segment': 'premium'}

    Examples:
        >>> parse_utm_from_start_param('source-vk_campaign-summer2025_seg-premium')
        {'utm_source': 'vk', 'utm_campaign': 'summer2025', 'segment': 'premium'}

        >>> parse_utm_from_start_param('https://t.me/bot?start=source-vk_campaign-summer2025_seg-vip')
        {'utm_source': 'vk', 'utm_campaign': 'summer2025', 'segment': 'vip'}
    """
    import re
    from urllib.parse import unquote

    utm_data = {}

    try:
        # Если это полная ссылка, извлекаем start параметр
        if "t.me/" in start_param or "https://" in start_param:
            match = re.search(r"[?&]start=([^&]+)", start_param)
            if match:
                start_param = unquote(match.group(1))
            else:
                return {}

        # Парсим новый формат: source-vk_campaign-summer2025_seg-premium
        # Поддерживает как комбинированные параметры, так и одиночные (например, только seg-prem)
        if "-" in start_param:
            # Разделяем по _ (если есть несколько параметров) или используем весь параметр
            parts = start_param.split("_") if "_" in start_param else [start_param]

            for part in parts:
                if "-" in part:
                    key, value = part.split("-", 1)
                    # Преобразуем source/medium/campaign/content/term в utm_*
                    if key in ["source", "medium", "campaign", "content", "term"]:
                        key = "utm_" + key
                        utm_data[key] = value
                    # Обрабатываем seg как segment
                    elif key == "seg":
                        utm_data["segment"] = value

    except Exception as e:
        print(f"Ошибка парсинга UTM параметров: {e}")

    return utm_data
