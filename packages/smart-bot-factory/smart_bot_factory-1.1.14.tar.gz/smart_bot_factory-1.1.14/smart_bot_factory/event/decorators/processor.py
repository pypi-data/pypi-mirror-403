"""
Фоновый процессор событий.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

from ...utils.context import ctx
from .admin import process_admin_event
from .checks import ensure_not_processed_once, smart_execute_check
from .constants import EventCategory, EventStatus, NotifyTime, SmartCheckAction
from .db import get_pending_events_in_next_minute, update_event_result
from .execution import execute_event_handler, execute_global_handler, execute_scheduled_task
from .registry import _get_registry

logger = logging.getLogger(__name__)


async def background_event_processor():
    """Фоновый процессор для ВСЕХ типов событий включая админские (проверяет БД каждую минуту)"""

    logger.info("🔄 Запуск фонового процессора событий (user_event, scheduled_task, global_handler, admin_event)")

    async def handle_admin_event(event: Dict) -> None:
        """Обрабатывает админское событие и обновляет статус"""
        if not event.get("bot_id"):
            logger.warning(f"⚠️ Админское событие {event['id']} не имеет bot_id")

        try:
            logger.info(f"🔄 Начало обработки админского события {event['id']}")
            logger.info(f"📝 Данные события: {event}")

            result = await process_admin_event(event)
            logger.info(f"📦 Результат process_admin_event: {result}")

            import json

            if not ctx.supabase_client:
                raise RuntimeError("Не найден supabase_client")

            result_data_json = json.dumps(result, ensure_ascii=False) if result else None
            logger.info(f"📝 result_data для сохранения: {result_data_json}")

            update_data = {
                "status": EventStatus.COMPLETED,
                "executed_at": datetime.now(timezone.utc).isoformat(),
                "result_data": result_data_json,
            }

            if not event.get("bot_id") and ctx.supabase_client.bot_id:
                update_data["bot_id"] = ctx.supabase_client.bot_id
                logger.info(f"📝 Добавлен bot_id: {ctx.supabase_client.bot_id}")

            query = ctx.supabase_client.client.table("scheduled_events").update(update_data).eq("id", event["id"])

            if event.get("bot_id"):
                query = query.eq("bot_id", event["bot_id"])

            query.execute()

            logger.info(f"✅ Админское событие {event['id']} выполнено и обновлено в БД")
        except Exception as e:
            logger.error(f"❌ Ошибка обработки админского события {event['id']}: {e}")
            logger.exception("Стек ошибки:")

            try:
                if not ctx.supabase_client:
                    raise RuntimeError("Не найден supabase_client")

                update_data = {
                    "status": EventStatus.FAILED,
                    "last_error": str(e),
                    "executed_at": datetime.now(timezone.utc).isoformat(),
                }

                if not event.get("bot_id") and ctx.supabase_client.bot_id:
                    update_data["bot_id"] = ctx.supabase_client.bot_id
                    logger.info(f"📝 Добавлен bot_id: {ctx.supabase_client.bot_id}")

                query = ctx.supabase_client.client.table("scheduled_events").update(update_data).eq("id", event["id"])

                if event.get("bot_id"):
                    query = query.eq("bot_id", event["bot_id"])

                query.execute()
                logger.info(f"✅ Статус события {event['id']} обновлен на failed")
            except Exception as update_error:
                logger.error(f"❌ Ошибка обновления статуса события: {update_error}")
                logger.exception("Стек ошибки обновления:")

    async def should_skip_user_event(event: Dict, event_type: str, user_id: Optional[int], session_id: Optional[str]) -> bool:
        """Проверяет once_only для user_event"""
        event_handlers, _ = _get_registry("event")
        event_handler_info = event_handlers.get(event_type, {})
        once_only = event_handler_info.get("once_only", True)

        if not once_only:
            return False

        already_done = await ensure_not_processed_once(
            event_type,
            user_id=user_id,
            session_id=session_id,
            current_event_id=event["id"],
        )
        if already_done:
            await update_event_result(
                event["id"],
                EventStatus.CANCELLED,
                {"reason": "already_executed_once_only"},
            )
            logger.info(f"⛔ Событие {event['id']} ({event_type}) пропущено: уже выполнялось для пользователя {user_id} (once_only=True)")
            return True
        return False

    async def should_skip_scheduled_task(event: Dict, event_type: str, user_id: Optional[int], session_id: Optional[str]) -> bool:
        """Проверяет once_only и smart_check для scheduled_task"""
        scheduled_tasks, _ = _get_registry("task")
        task_info = scheduled_tasks.get(event_type, {})
        use_smart_check = task_info.get("smart_check", True)
        once_only = task_info.get("once_only", True)

        if once_only:
            already_done = await ensure_not_processed_once(
                event_type,
                user_id=user_id,
                session_id=session_id,
                current_event_id=event["id"],
            )
            if already_done:
                await update_event_result(
                    event["id"],
                    EventStatus.CANCELLED,
                    {"reason": "already_executed_once_only"},
                )
                logger.info(f"⛔ Задача {event['id']} ({event_type}) пропущена: уже выполнялась для пользователя {user_id} (once_only=True)")
                return True

        if not use_smart_check:
            return False

        check_result = await smart_execute_check(
            event["id"],
            user_id,
            session_id,
            event_type,
            event["event_data"],
        )

        if check_result["action"] == SmartCheckAction.CANCEL:
            await update_event_result(
                event["id"],
                EventStatus.CANCELLED,
                {"reason": check_result["reason"]},
            )
            logger.info(f"⛔ Задача {event['id']} отменена: {check_result['reason']}")
            return True

        if check_result["action"] == SmartCheckAction.RESCHEDULE:
            new_scheduled_at = datetime.now(timezone.utc) + timedelta(seconds=check_result["new_delay"])
            ctx.supabase_client.client.table("scheduled_events").update(
                {
                    "scheduled_at": new_scheduled_at.isoformat(),
                    "status": EventStatus.PENDING,
                }
            ).eq("id", event["id"]).execute()
            logger.info(f"🔄 Задача {event['id']} перенесена на {check_result['new_delay']}с")
            return True

        return False

    while True:
        try:
            pending_events = await get_pending_events_in_next_minute(limit=100)

            if pending_events:
                logger.info(f"📋 Найдено {len(pending_events)} событий для обработки")

                for event in pending_events:
                    try:
                        event_type = event["event_type"]
                        event_category = event["event_category"]
                        user_id = event.get("user_id")
                        session_id = event.get("session_id")

                        if event_category == EventCategory.ADMIN_EVENT:
                            await handle_admin_event(event)
                            continue

                        if event_category == EventCategory.USER_EVENT:
                            skip = await should_skip_user_event(event, event_type, user_id, session_id)
                            if skip:
                                continue

                        if event_category == EventCategory.SCHEDULED_TASK:
                            skip = await should_skip_scheduled_task(event, event_type, user_id, session_id)
                            if skip:
                                continue

                        result = await process_scheduled_event(event)

                        result_data = {"processed": True}
                        if isinstance(result, dict):
                            result_data.update(result)
                            if "info" in result:
                                logger.info(f"   📊 Дашборд данные для задачи: {result['info'].get('title', 'N/A')}")

                        await update_event_result(event["id"], "completed", result_data)
                        logger.info(f"✅ Событие {event['id']} выполнено")

                    except Exception as e:
                        logger.error(f"❌ Ошибка обработки события {event['id']}: {e}")
                        await update_event_result(event["id"], "failed", None, str(e))

            await asyncio.sleep(60)

        except Exception as e:
            logger.error(f"❌ Ошибка в фоновом процессоре: {e}")
            await asyncio.sleep(60)


async def process_scheduled_event(event: Dict):
    """Обрабатывает одно событие из БД и возвращает результат"""

    event_type = event["event_type"]
    event_category = event["event_category"]
    event_data = event["event_data"]
    user_id = event.get("user_id")

    logger.info(f"🔄 Обработка события {event['id']}: {event_category}/{event_type}")

    async def handle_scheduled_task():
        scheduled_tasks, _ = _get_registry("task")
        task_info = scheduled_tasks.get(event_type, {})
        notify = task_info.get("notify", False)
        notify_time = task_info.get("notify_time", "after")

        result = await execute_scheduled_task(event_type, user_id, event_data)

        if notify and notify_time == NotifyTime.AFTER:
            from ...utils.bot_utils import notify_admins_about_event

            event_for_notify = {"тип": event_type, "инфо": event_data}
            await notify_admins_about_event(user_id, event_for_notify)
            logger.info(f"   ✅ Админы уведомлены после выполнения задачи '{event_type}'")

        return result

    async def handle_global_handler():
        return await execute_global_handler(event_type, event_data)

    async def handle_user_event():
        return await execute_event_handler(event_type, user_id, event_data)

    handlers = {
        "scheduled_task": handle_scheduled_task,
        "global_handler": handle_global_handler,
        "user_event": handle_user_event,
    }

    handler = handlers.get(event_category)
    if not handler:
        logger.warning(f"⚠️ Неизвестная категория события: {event_category}")
        return None

    return await handler()
