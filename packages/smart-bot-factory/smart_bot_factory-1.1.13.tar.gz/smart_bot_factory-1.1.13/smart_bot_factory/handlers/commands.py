"""
Обработчики команд для бота.
"""

import logging
import traceback
from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from project_root_finder import root

from ..utils.bot_utils import parse_utm_from_start_param, send_message, send_welcome_file
from ..utils.context import ctx
from .states import UserStates

logger = logging.getLogger(__name__)


async def user_start_handler(message: Message, state: FSMContext):
    """Обработчик /start для обычных пользователей"""
    try:
        # 0. ПОЛУЧАЕМ UTM ДАННЫЕ
        start_param = message.text.split(" ", 1)[1] if len(message.text.split()) > 1 else None

        logger.info(f"📥 Получен start параметр: '{start_param}'")

        utm_data = {}
        if start_param:
            # Парсим UTM данные
            utm_data = parse_utm_from_start_param(start_param)

            # Подробное логирование UTM
            logger.info(f"📊 UTM данные для пользователя {message.from_user.id}:")
            if utm_data:
                for key, value in utm_data.items():
                    logger.info(f"   • {key}: {value}")
                logger.info("✅ UTM данные успешно распознаны")
            else:
                logger.warning(f"⚠️ UTM данные не найдены в параметре: '{start_param}'")
        else:
            logger.info("ℹ️ Start параметр отсутствует (обычный /start)")

        # 1. ЯВНО ОЧИЩАЕМ СОСТОЯНИЕ FSM
        await state.clear()
        logger.info(f"🔄 Состояние FSM очищено для пользователя {message.from_user.id}")

        # 2. ЗАГРУЖАЕМ ПРОМПТЫ
        logger.info(f"Загрузка промптов для пользователя {message.from_user.id}")

        # Загружаем приветственное сообщение
        welcome_message = await ctx.prompt_loader.load_welcome_message()

        # 3. ПОЛУЧАЕМ ДАННЫЕ ПОЛЬЗОВАТЕЛЯ
        user_data = {
            "telegram_id": message.from_user.id,
            "username": message.from_user.username,
            "first_name": message.from_user.first_name,
            "last_name": message.from_user.last_name,
            "language_code": message.from_user.language_code,
            "source": utm_data.get("utm_source"),
            "medium": utm_data.get("utm_medium"),
            "campaign": utm_data.get("utm_campaign"),
            "content": utm_data.get("utm_content"),
            "term": utm_data.get("utm_term"),
            "segment": utm_data.get("segment"),
        }

        # 4. СОЗДАЕМ НОВУЮ СЕССИЮ (автоматически закроет активные)
        # Добавляем UTM данные в метаданные пользователя
        if utm_data:
            user_data["metadata"] = {"utm_data": utm_data}
            logger.info("📈 UTM данные добавлены в метаданные пользователя")

        # Создаем сессию БЕЗ системного промпта (он теперь во временном файле)
        session_id = await ctx.supabase_client.create_chat_session(user_data, "")
        logger.info(f"✅ Создана новая сессия {session_id} для пользователя {message.from_user.id}")

        # 5. УСТАНАВЛИВАЕМ НОВОЕ СОСТОЯНИЕ (без system_prompt в state)
        await state.update_data(session_id=session_id)
        await state.set_state(UserStates.waiting_for_message)

        # 5.5. ПРОВЕРЯЕМ UTM-ТРИГГЕРЫ (после инициализации, перед отправкой сообщения)
        trigger_message = None
        if ctx.utm_triggers and utm_data:
            if ctx.config and hasattr(ctx.config, "BOT_ID"):
                utm_message_dir = root / "bots" / ctx.config.BOT_ID / "utm_message"

                for trigger in ctx.utm_triggers:
                    utm_targets = trigger.get("utm_targets", {})
                    trigger_msg = trigger.get("message", "")

                    # Проверяем совпадение всех указанных параметров
                    match = True
                    for key, target_value in utm_targets.items():
                        if target_value is None:
                            continue  # None означает игнорирование параметра

                        # Преобразуем ключ из формата без префикса в формат с префиксом для сравнения
                        if key in ["source", "medium", "campaign", "content", "term"]:
                            utm_key = "utm_" + key
                        elif key == "segment":
                            utm_key = "segment"
                        else:
                            utm_key = key  # Оставляем как есть, если не распознали

                        actual_value = utm_data.get(utm_key)
                        if actual_value != target_value:
                            match = False
                            break

                    if match:
                        logger.info(f"🎯 UTM-триггер сработал для пользователя {message.from_user.id}: {utm_targets}")
                        trigger_msg_path = utm_message_dir / trigger_msg

                        if trigger_msg_path.exists() and trigger_msg_path.is_file():
                            try:
                                trigger_message = trigger_msg_path.read_text(encoding="utf-8")
                                logger.info(f"📄 Сообщение UTM-триггера загружено из файла: {trigger_msg_path}")
                            except Exception as e:
                                logger.error(f"❌ Ошибка чтения файла UTM-триггера {trigger_msg_path}: {e}")
                                continue
                        else:
                            logger.error(f"❌ Файл UTM-триггера не найден: {trigger_msg}. " f"Файл должен находиться в директории: {utm_message_dir}")
                            continue
                        break  # Используем первое совпадение

        # 6. ОТПРАВЛЯЕМ ПРИВЕТСТВЕННОЕ СООБЩЕНИЕ (или сообщение триггера)
        final_message = trigger_message if trigger_message else welcome_message
        try:
            await send_message(message, final_message)
            logger.info(f"Приветственное сообщение отправлено пользователю {message.from_user.id}")
        except Exception as e:
            if "Forbidden: bot was blocked by the user" in str(e):
                logger.warning(f"🚫 Бот заблокирован пользователем {message.from_user.id}")
                return
            else:
                logger.error(f"❌ Ошибка отправки приветственного сообщения: {e}")
                raise

        # 7. ЕСЛИ ЕСТЬ ФАЙЛ ОТПРАВЛЯЕМ ВМЕСТЕ С ПОДПИСЬЮ (только если не сработал триггер)
        if not trigger_message:
            logger.info(f"📎 Попытка отправки приветственного файла для сессии {session_id}")
            caption = await send_welcome_file(message)

            # 8. ПОДГОТАВЛИВАЕМ СООБЩЕНИЕ ДЛЯ СОХРАНЕНИЯ В БД
            if caption:
                logger.info(f"📄 Добавление подписи к файлу в приветственное сообщение для сессии {session_id}")
                message_to_save = f"{welcome_message}\n\nПодпись к файлу:\n\n{caption}"
            else:
                logger.info(f"📄 Приветственный файл отправлен без подписи для сессии {session_id}")
                message_to_save = welcome_message
        else:
            logger.info(f"⏭️ Приветственный файл пропущен (сработал UTM-триггер) для сессии {session_id}")
            message_to_save = trigger_message

        logger.info(f"💾 Сохранение сообщения в БД для сессии {session_id}")

        await ctx.supabase_client.add_message(
            session_id=session_id,
            role="assistant",
            content=message_to_save,
            message_type="text",
        )

        logger.info(f"✅ Приветственное сообщение успешно сохранено в БД для сессии {session_id}")

        # ВЫЗЫВАЕМ ПОЛЬЗОВАТЕЛЬСКИЕ ОБРАБОТЧИКИ on_start
        if ctx.start_handlers:
            logger.info(f"🔔 Вызов {len(ctx.start_handlers)} пользовательских обработчиков on_start")
            for handler in ctx.start_handlers:
                try:
                    await handler(
                        user_id=message.from_user.id,
                        session_id=session_id,
                        message=message,
                        state=state,
                    )
                    logger.info(f"✅ Обработчик on_start '{handler.__name__}' выполнен успешно")
                except Exception as handler_error:
                    logger.error(f"❌ Ошибка в обработчике on_start '{handler.__name__}': {handler_error}")
                    # Продолжаем выполнение остальных обработчиков

    except Exception as e:
        logger.error(f"Ошибка при обработке user /start: {e}")
        await send_message(message, "Произошла ошибка при инициализации. Попробуйте позже.")


async def timeup_handler(message: Message, state: FSMContext):
    """Обработчик команды /timeup (или /вперед) - выполнение ближайшего запланированного события"""
    from ..event.decorators.admin import process_admin_event
    from ..event.decorators.db import update_event_result
    from ..event.decorators.processor import process_scheduled_event

    try:
        await message.answer("🔄 Ищу ближайшее запланированное событие...")

        # Получаем события для этого пользователя И глобальные события (user_id = null) одним запросом
        # Используем OR условие для объединения двух типов событий
        all_events_query = (
            ctx.supabase_client.client.table("scheduled_events")
            .select("*")
            .in_("status", ["pending", "immediate"])
            .eq("bot_id", ctx.supabase_client.bot_id)
            .or_(f"user_id.eq.{message.from_user.id},user_id.is.null")
        )

        all_events_response = all_events_query.execute()
        all_events = all_events_response.data or []

        if not all_events:
            await message.answer("📭 Нет запланированных событий для выполнения")
            return

        # Находим ближайшее событие по времени
        nearest_event = None
        nearest_time = None

        for event in all_events:
            scheduled_at_str = event.get("scheduled_at")

            # События immediate (scheduled_at = null) считаются ближайшими
            if scheduled_at_str is None:
                nearest_event = event
                nearest_time = None  # Немедленное выполнение
                break

            # Парсим время события
            try:
                scheduled_at = datetime.fromisoformat(scheduled_at_str.replace("Z", "+00:00"))
                if nearest_time is None or scheduled_at < nearest_time:
                    nearest_time = scheduled_at
                    nearest_event = event
            except Exception as e:
                logger.warning(f"⚠️ Не удалось распарсить scheduled_at для события {event.get('id')}: {e}")
                continue

        if not nearest_event:
            await message.answer("📭 Не удалось определить ближайшее событие")
            return

        event_id = nearest_event["id"]
        event_type = nearest_event["event_type"]
        event_category = nearest_event["event_category"]
        is_global = nearest_event.get("user_id") is None

        # Заменяем _ на пробелы для красивого отображения
        event_type_display = event_type.replace("_", " ")
        event_category_display = event_category.replace("_", " ")

        event_label = f"🌍 {event_type_display}" if is_global else f"👤 {event_type_display}"

        # Форматируем время запланированного запуска
        scheduled_time_str = "немедленно"
        if nearest_time:
            try:
                # Конвертируем в московское время для отображения
                moscow_tz = ZoneInfo("Europe/Moscow")
                moscow_time = nearest_time.astimezone(moscow_tz)
                scheduled_time_str = moscow_time.strftime("%d.%m.%Y %H:%M:%S (МСК)")
            except Exception:
                scheduled_time_str = nearest_time.strftime("%d.%m.%Y %H:%M:%S UTC")

        logger.info(
            f"⏭️ Обрабатываем ближайшее событие {event_id}: {event_category}/{event_type} "
            f"({'глобальное' if is_global else f'пользователя {message.from_user.id}'}), "
            f"запланировано на: {scheduled_time_str}"
        )

        try:
            logger.info(f"🚀 Начинаю выполнение события {event_id}...")

            # Выполняем событие
            if event_category == "admin_event":
                # Для админских событий используем тестовую отправку только текущему пользователю
                logger.info(f"📧 Обработка админского события {event_id} для пользователя {message.from_user.id}")
                result = await process_admin_event(nearest_event, single_user_id=message.from_user.id)
                logger.info(f"📧 Результат админского события: {result}")
                logger.info(f"✅ Событие {event_id} протестировано для пользователя {message.from_user.id}")
            else:
                logger.info(f"⚙️ Обработка события {event_id} категории {event_category}")
                result = await process_scheduled_event(nearest_event)
                logger.info(f"⚙️ Результат обработки события: {result}")
                # Помечаем как выполненное только не-админские события
                if event_category != "global_handler":
                    await update_event_result(
                        event_id,
                        "completed",
                        {
                            "executed": True,
                            "test_mode": True,
                            "tested_by_user": message.from_user.id,
                            "tested_at": datetime.now().isoformat(),
                        },
                    )
                logger.info(f"✅ Событие {event_id} успешно выполнено")

            # Отправляем сообщение о выполненном событии
            result_text = [
                "✅ *Событие успешно обработано*",
                "",
                "━━━━━━━━━━━━━━━━━━━━",
                "📋 **Тип события:**",
                f"   {event_label}",
                "",
                "🏷️ **Категория:**",
                f"   {event_category_display}",
                "",
                "⏰ **Запланировано на:**",
                f"   {scheduled_time_str}",
                "━━━━━━━━━━━━━━━━━━━━",
            ]

            await message.answer("\n".join(result_text), parse_mode="Markdown")

        except Exception as e:
            error_msg = str(e)
            error_traceback = traceback.format_exc()
            logger.error(f"❌ Ошибка выполнения события {event_id}: {error_msg}")
            logger.error(f"❌ Трассировка ошибки: {error_traceback}")

            # Помечаем как failed
            try:
                await update_event_result(event_id, "failed", None, error_msg)
            except Exception as update_error:
                logger.error(f"❌ Ошибка обновления статуса события: {update_error}")

            result_text = [
                "❌ *Ошибка обработки события*",
                "",
                "━━━━━━━━━━━━━━━━━━━━",
                "📋 **Тип события:**",
                f"   {event_label}",
                "",
                "🏷️ **Категория:**",
                f"   {event_category_display}",
                "",
                "⏰ **Запланировано на:**",
                f"   {scheduled_time_str}",
                "",
                "⚠️ **Ошибка:**",
                f"   `{error_msg[:100]}`",
                "━━━━━━━━━━━━━━━━━━━━",
            ]

            await message.answer("\n".join(result_text), parse_mode="Markdown")

    except Exception as e:
        logger.error(f"❌ Критическая ошибка в timeup_handler: {e}")
        logger.error(f"❌ Трассировка критической ошибки: {traceback.format_exc()}")
        await message.answer(f"❌ Ошибка выполнения: `{str(e)}`", parse_mode="Markdown")
