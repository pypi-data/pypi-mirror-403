"""
Функции для работы с БД событий.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from ...utils.context import ctx
from .checks import check_event_already_processed
from .constants import EventCategory, EventStatus
from .registry import _get_registry

logger = logging.getLogger(__name__)


async def save_immediate_event(event_type: str, user_id: int, event_data: str, session_id: Optional[str] = None) -> str:
    """Сохраняет событие для немедленного выполнения"""

    if not ctx.supabase_client:
        logger.error("❌ Supabase клиент не найден")
        raise RuntimeError("Supabase клиент не инициализирован")

    # Проверяем, нужно ли предотвращать дублирование
    event_handlers, _ = _get_registry("event")

    event_handler_info = event_handlers.get(event_type, {})
    once_only = event_handler_info.get("once_only", True)

    if once_only:
        # Проверяем, было ли уже обработано аналогичное событие для этого пользователя
        already_processed = await check_event_already_processed(event_type, user_id, session_id)
        if already_processed:
            logger.info(f"🔄 Событие '{event_type}' уже обрабатывалось для пользователя {user_id}, пропускаем")
            raise ValueError(f"Событие '{event_type}' уже обрабатывалось (once_only=True)")

    # Получаем bot_id
    if not ctx.supabase_client.bot_id:
        logger.warning("⚠️ bot_id не указан при создании immediate_event")

    event_record = {
        "event_type": event_type,
        "event_category": EventCategory.USER_EVENT,
        "user_id": user_id,
        "event_data": event_data,
        "scheduled_at": None,  # Немедленное выполнение
        "status": EventStatus.IMMEDIATE,
        "session_id": session_id,
        "bot_id": ctx.supabase_client.bot_id,  # Всегда добавляем bot_id
    }

    try:
        response = ctx.supabase_client.client.table("scheduled_events").insert(event_record).execute()
        event_id = response.data[0]["id"]
        logger.info(f"💾 Событие сохранено в БД: {event_id}")
        return event_id
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения события в БД: {e}")
        raise


async def save_scheduled_task(
    task_name: str,
    user_id: int,
    user_data: str,
    delay_seconds: int,
    session_id: Optional[str] = None,
) -> str:
    """Сохраняет запланированную задачу"""

    if not ctx.supabase_client:
        logger.error("❌ Supabase клиент не найден")
        raise RuntimeError("Supabase клиент не инициализирован")

    # Проверяем, нужно ли предотвращать дублирование
    scheduled_tasks, _ = _get_registry("task")

    task_info = scheduled_tasks.get(task_name, {})
    once_only = task_info.get("once_only", True)

    if once_only:
        # Проверяем, была ли уже запланирована аналогичная задача для этого пользователя
        already_processed = await check_event_already_processed(task_name, user_id, session_id)
        if already_processed:
            logger.info(f"🔄 Задача '{task_name}' уже запланирована для пользователя {user_id}, пропускаем")
            raise ValueError(f"Задача '{task_name}' уже запланирована (once_only=True)")

    scheduled_at = datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)

    # Получаем bot_id
    if not ctx.supabase_client.bot_id:
        logger.warning("⚠️ bot_id не указан при создании scheduled_task")

    event_record = {
        "event_type": task_name,
        "event_category": EventCategory.SCHEDULED_TASK,
        "user_id": user_id,
        "event_data": user_data,
        "scheduled_at": scheduled_at.isoformat(),
        "status": EventStatus.PENDING,
        "session_id": session_id,
        "bot_id": ctx.supabase_client.bot_id,  # Всегда добавляем bot_id
    }

    try:
        response = ctx.supabase_client.client.table("scheduled_events").insert(event_record).execute()
        event_id = response.data[0]["id"]
        logger.info(f"⏰ Запланированная задача сохранена в БД: {event_id} (через {delay_seconds}с)")
        return event_id
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения запланированной задачи в БД: {e}")
        raise


async def save_global_event(handler_type: str, handler_data: str, delay_seconds: int = 0) -> str:
    """Сохраняет глобальное событие"""

    if not ctx.supabase_client:
        logger.error("❌ Supabase клиент не найден")
        raise RuntimeError("Supabase клиент не инициализирован")

    # Проверяем, нужно ли предотвращать дублирование
    global_handlers, _ = _get_registry("global")

    handler_info = global_handlers.get(handler_type, {})
    once_only = handler_info.get("once_only", True)

    if once_only:
        # Проверяем, было ли уже запланировано аналогичное глобальное событие
        already_processed = await check_event_already_processed(handler_type, user_id=None)
        if already_processed:
            logger.info(f"🔄 Глобальное событие '{handler_type}' уже запланировано, пропускаем")
            raise ValueError(f"Глобальное событие '{handler_type}' уже запланировано (once_only=True)")

    scheduled_at = None
    status = EventStatus.IMMEDIATE

    if delay_seconds > 0:
        scheduled_at = datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)
        status = EventStatus.PENDING

    # Получаем bot_id
    if not ctx.supabase_client.bot_id:
        logger.warning("⚠️ bot_id не указан при создании global_event")

    event_record = {
        "event_type": handler_type,
        "event_category": EventCategory.GLOBAL_HANDLER,
        "user_id": None,  # Глобальное событие
        "event_data": handler_data,
        "scheduled_at": scheduled_at.isoformat() if scheduled_at else None,
        "status": status,
        "bot_id": ctx.supabase_client.bot_id,  # Всегда добавляем bot_id (глобальные события тоже привязаны к боту)
    }

    try:
        response = ctx.supabase_client.client.table("scheduled_events").insert(event_record).execute()
        event_id = response.data[0]["id"]
        logger.info(f"🌍 Глобальное событие сохранено в БД: {event_id}")
        return event_id
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения глобального события в БД: {e}")
        raise


async def update_event_result(event_id: str, status: str, result_data: Any = None, error_message: Optional[str] = None):
    """Обновляет результат выполнения события"""

    if not ctx.supabase_client:
        logger.error("❌ Supabase клиент не найден")
        return

    update_data = {
        "status": status,
        "executed_at": datetime.now(timezone.utc).isoformat(),
    }

    if result_data:
        import json

        update_data["result_data"] = json.dumps(result_data, ensure_ascii=False)

        # Проверяем наличие поля 'info' для дашборда
        if isinstance(result_data, dict) and "info" in result_data:
            update_data["info_dashboard"] = json.dumps(result_data["info"], ensure_ascii=False)
            logger.info(f"📊 Дашборд данные добавлены в событие {event_id}")

    if error_message:
        update_data["last_error"] = error_message
        # Получаем текущее количество попыток
        try:
            query = ctx.supabase_client.client.table("scheduled_events").select("retry_count").eq("id", event_id)

            # Добавляем фильтр по bot_id если указан
            if ctx.supabase_client.bot_id:
                query = query.eq("bot_id", ctx.supabase_client.bot_id)

            current_retry = query.execute().data[0]["retry_count"]
            update_data["retry_count"] = current_retry + 1
        except Exception:
            logger.debug("Не удалось получить текущее количество попыток, устанавливаем 1")
            update_data["retry_count"] = 1

    try:
        query = ctx.supabase_client.client.table("scheduled_events").update(update_data).eq("id", event_id)

        # Добавляем фильтр по bot_id если указан
        if ctx.supabase_client.bot_id:
            query = query.eq("bot_id", ctx.supabase_client.bot_id)

        query.execute()
        logger.info(f"📝 Результат события {event_id} обновлен: {status}")
    except Exception as e:
        logger.error(f"❌ Ошибка обновления результата события {event_id}: {e}")


async def get_pending_events(limit: int = 50) -> list:
    """Получает события готовые к выполнению СЕЙЧАС"""

    if not ctx.supabase_client:
        logger.error("❌ Supabase клиент не найден")
        return []

    try:
        now = datetime.now(timezone.utc).isoformat()

        query = (
            ctx.supabase_client.client.table("scheduled_events")
            .select("*")
            .in_("status", [EventStatus.PENDING, EventStatus.IMMEDIATE])
            .or_(f"scheduled_at.is.null,scheduled_at.lte.{now}")
            .order("created_at")
            .limit(limit)
        )

        # 🆕 Фильтруем по bot_id если указан
        if ctx.supabase_client.bot_id:
            query = query.eq("bot_id", ctx.supabase_client.bot_id)

        response = query.execute()

        return response.data
    except Exception as e:
        logger.error(f"❌ Ошибка получения событий из БД: {e}")
        return []


async def get_pending_events_in_next_minute(limit: int = 100) -> list:
    """Получает события готовые к выполнению в течение следующей минуты"""

    if not ctx.supabase_client:
        logger.error("❌ Supabase клиент не найден")
        return []

    try:
        now = datetime.now(timezone.utc)
        next_minute = now + timedelta(seconds=60)

        query = (
            ctx.supabase_client.client.table("scheduled_events")
            .select("*")
            .in_("status", [EventStatus.PENDING, EventStatus.IMMEDIATE])
            .or_(f"scheduled_at.is.null,scheduled_at.lte.{next_minute.isoformat()}")
            .order("created_at")
            .limit(limit)
        )

        # 🆕 Фильтруем по bot_id если указан
        if ctx.supabase_client.bot_id:
            query = query.eq("bot_id", ctx.supabase_client.bot_id)

        response = query.execute()

        return response.data
    except Exception as e:
        logger.error(f"❌ Ошибка получения событий из БД: {e}")
        return []
