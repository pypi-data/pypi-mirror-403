"""
Проверки и валидация для обработчиков событий.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from ...utils.context import ctx
from .constants import EventStatus, SmartCheckAction

logger = logging.getLogger(__name__)


async def check_event_already_processed(event_type: str, user_id: Optional[int] = None, session_id: Optional[str] = None) -> bool:
    """
    Проверяет, был ли уже обработан аналогичный event_type для пользователя/сессии

    Args:
        event_type: Тип события
        user_id: ID пользователя (для user_event и scheduled_task)
        session_id: ID сессии (для дополнительной проверки)

    Returns:
        True если событие уже обрабатывалось или в процессе
    """
    if not ctx.supabase_client:
        logger.error("❌ Supabase клиент не найден для проверки дублирования")
        return False

    try:
        # Строим запрос для поиска аналогичных событий
        query = ctx.supabase_client.client.table("scheduled_events").select("id").eq("event_type", event_type)

        # Для глобальных событий (user_id = None)
        if user_id is None:
            query = query.is_("user_id", "null")
        else:
            query = query.eq("user_id", user_id)

        # Добавляем фильтр по статусам (pending, immediate, completed)
        query = query.in_("status", [EventStatus.PENDING, EventStatus.IMMEDIATE, EventStatus.COMPLETED])

        # Если есть session_id, добавляем его в фильтр
        if session_id:
            query = query.eq("session_id", session_id)

        # 🆕 Фильтруем по bot_id если указан
        if ctx.supabase_client.bot_id:
            query = query.eq("bot_id", ctx.supabase_client.bot_id)

        response = query.execute()

        if response.data:
            logger.info(f"🔄 Найдено {len(response.data)} аналогичных событий для '{event_type}'")
            return True

        return False

    except Exception as e:
        logger.error(f"❌ Ошибка проверки дублирования для '{event_type}': {e}")
        return False


async def ensure_not_processed_once(
    event_type: str,
    user_id: Optional[int] = None,
    session_id: Optional[str] = None,
    current_event_id: Optional[str] = None,
) -> bool:
    """
    Проверяет, завершалось ли событие (status=COMPLETED) с теми же параметрами.
    Возвращает True, если уже выполнено и повторять нельзя (once_only).
    """
    if not ctx.supabase_client:
        logger.error("❌ Supabase клиент не найден для проверки once_only")
        return False

    try:
        query = ctx.supabase_client.client.table("scheduled_events").select("id").eq("event_type", event_type).eq("status", EventStatus.COMPLETED)

        if user_id is None:
            query = query.is_("user_id", "null")
        else:
            query = query.eq("user_id", user_id)

        if session_id:
            query = query.eq("session_id", session_id)

        if current_event_id:
            query = query.neq("id", current_event_id)

        if ctx.supabase_client.bot_id:
            query = query.eq("bot_id", ctx.supabase_client.bot_id)

        existing = query.execute()
        if existing.data:
            logger.info(
                f"🔄 Найдено завершённое событие '{event_type}' " f"для user_id={user_id} session_id={session_id}, once_only блокирует повтор"
            )
            return True

        return False
    except Exception as e:
        logger.error(f"❌ Ошибка проверки once_only для '{event_type}': {e}")
        return False


async def smart_execute_check(event_id: str, user_id: int, session_id: str, task_name: str, user_data: str) -> Dict[str, Any]:
    """
    Умная проверка перед выполнением запланированной задачи

    Логика:
    1. Если пользователь перешел на новый этап - отменяем событие
    2. Если прошло меньше времени чем планировалось - переносим на разницу
    3. Если прошло достаточно времени - выполняем

    Returns:
        Dict с action: 'execute', 'cancel', 'reschedule'
    """
    if not ctx.supabase_client:
        logger.error("❌ Supabase клиент не найден для умной проверки")
        return {"action": SmartCheckAction.EXECUTE, "reason": "no_supabase_client"}

    try:
        # Получаем информацию о последнем сообщении пользователя
        user_info = await ctx.supabase_client.get_user_last_message_info(user_id)

        if not user_info:
            logger.info(f"🔄 Пользователь {user_id} не найден, выполняем задачу")
            return {"action": SmartCheckAction.EXECUTE, "reason": "user_not_found"}

        # Проверяем, изменился ли этап
        stage_changed = await ctx.supabase_client.check_user_stage_changed(user_id, session_id)
        if stage_changed:
            logger.info(f"🔄 Пользователь {user_id} перешел на новый этап, отменяем задачу {task_name}")
            return {"action": SmartCheckAction.CANCEL, "reason": "user_stage_changed"}

        # Получаем информацию о событии из БД
        event_response = ctx.supabase_client.client.table("scheduled_events").select("created_at", "scheduled_at").eq("id", event_id).execute()

        if not event_response.data:
            logger.error(f"❌ Событие {event_id} не найдено в БД")
            return {"action": SmartCheckAction.EXECUTE, "reason": "event_not_found"}

        event = event_response.data[0]
        created_at = datetime.fromisoformat(event["created_at"].replace("Z", "+00:00"))
        scheduled_at = datetime.fromisoformat(event["scheduled_at"].replace("Z", "+00:00"))
        last_message_at = datetime.fromisoformat(user_info["last_message_at"].replace("Z", "+00:00"))

        # Вычисляем разницу во времени
        now = datetime.now(timezone.utc)
        time_since_creation = (now - created_at).total_seconds()
        time_since_last_message = (now - last_message_at).total_seconds()
        planned_delay = (scheduled_at - created_at).total_seconds()

        # Проверяем, писал ли пользователь после создания события
        time_between_creation_and_last_message = (last_message_at - created_at).total_seconds()

        logger.info(f"🔄 Анализ для пользователя {user_id}:")
        logger.info(f"   Время с создания события: {time_since_creation:.0f}с")
        logger.info(f"   Время с последнего сообщения: {time_since_last_message:.0f}с")
        logger.info(f"   Запланированная задержка: {planned_delay:.0f}с")
        logger.info(f"   Пользователь писал после создания события: {time_between_creation_and_last_message > 0}")

        # Если пользователь писал ПОСЛЕ создания события (недавно активен)
        # И с момента его последнего сообщения прошло меньше planned_delay
        if time_between_creation_and_last_message > 0 and time_since_last_message < planned_delay:
            # Пересчитываем время - отправляем через planned_delay после последнего сообщения
            new_delay = max(0, planned_delay - time_since_last_message)
            logger.info(f"🔄 Переносим задачу на {new_delay:.0f}с (пользователь был активен, через {planned_delay:.0f}с после последнего сообщения)")
            return {
                "action": SmartCheckAction.RESCHEDULE,
                "new_delay": new_delay,
                "reason": f"user_active_after_event_creation_{new_delay:.0f}s_delay",
            }

        # Если прошло достаточно времени с последнего сообщения - выполняем
        if time_since_last_message >= planned_delay:
            logger.info(f"🔄 Выполняем задачу {task_name} для пользователя {user_id} (прошло {time_since_last_message:.0f}с с последнего сообщения)")
            return {"action": SmartCheckAction.EXECUTE, "reason": "time_expired_since_last_message"}

        # Если что-то пошло не так - выполняем
        logger.info(f"🔄 Неожиданная ситуация, выполняем задачу {task_name}")
        return {"action": SmartCheckAction.EXECUTE, "reason": "unexpected_situation"}

    except Exception as e:
        logger.error(f"❌ Ошибка в умной проверке для пользователя {user_id}: {e}")
        return {"action": SmartCheckAction.EXECUTE, "reason": f"error_in_check: {str(e)}"}
