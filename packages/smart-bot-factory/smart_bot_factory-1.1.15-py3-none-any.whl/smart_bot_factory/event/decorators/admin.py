"""
Обработка админских событий и подготовка данных для дашборда.
"""

import json
import logging
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from aiogram.types import FSInputFile, InputMediaPhoto, InputMediaVideo
from telegramify_markdown import standardize

from ...utils.context import ctx

logger = logging.getLogger(__name__)


async def process_admin_event(event: Dict, single_user_id: Optional[int] = None):
    """
    Обрабатывает одно админское событие - скачивает файлы из Storage и отправляет пользователям

    Args:
        event: Событие из БД с данными для отправки
        single_user_id: ID пользователя для тестовой отправки. Если указан, сообщение будет отправлено только ему
    """
    event_id = event["id"]
    event_name = event["event_type"]
    event_data_str = event["event_data"]

    try:
        event_data = json.loads(event_data_str)
    except Exception as e:
        logger.error(f"❌ Не удалось распарсить event_data для события {event_id}: {e}")
        return {
            "success_count": 0,
            "failed_count": 0,
            "total_users": 0,
            "error": f"Ошибка парсинга event_data: {str(e)}",
        }

    segment = event_data.get("segment")
    message_text_raw = event_data.get("message", "")
    # Стандартизируем текст сообщения для MarkdownV2
    message_text = standardize(message_text_raw) if message_text_raw else ""
    files_metadata = event_data.get("files", [])

    logger.info(f"📨 Обработка события '{event_name}': сегмент='{segment}', файлов={len(files_metadata)}")

    if not ctx.supabase_client:
        logger.error("❌ Supabase клиент не найден")
        return {
            "success_count": 0,
            "failed_count": 0,
            "total_users": 0,
            "error": "Нет Supabase клиента",
        }

    if not ctx.bot:
        logger.error("❌ Бот не найден")
        return {
            "success_count": 0,
            "failed_count": 0,
            "total_users": 0,
            "error": "Нет бота",
        }

    temp_with_msg = Path("temp_with_msg")
    temp_after_msg = Path("temp_after_msg")
    temp_with_msg.mkdir(exist_ok=True)
    temp_after_msg.mkdir(exist_ok=True)

    try:
        # Распараллеливаем скачивание файлов для ускорения
        import asyncio

        async def download_file(file_info: dict) -> tuple[dict, Optional[Path]]:
            """Скачивает один файл, возвращает (file_info, file_path)"""
            try:
                file_bytes = await ctx.supabase_client.download_event_file(event_id=event_id, storage_path=file_info["storage_path"])

                if file_info["stage"] == "with_message":
                    file_path = temp_with_msg / file_info["original_name"]
                else:
                    file_path = temp_after_msg / file_info["original_name"]

                with open(file_path, "wb") as f:
                    f.write(file_bytes)

                logger.info(f"📥 Скачан файл: {file_path}")
                return (file_info, file_path)
            except Exception as e:
                logger.error(f"❌ Ошибка скачивания файла {file_info['name']}: {e}")
                raise

        # Скачиваем все файлы параллельно
        download_tasks = [download_file(file_info) for file_info in files_metadata]
        download_results = await asyncio.gather(*download_tasks, return_exceptions=True)

        # Проверяем результаты
        for result in download_results:
            if isinstance(result, Exception):
                raise result

        if single_user_id:
            users = [{"telegram_id": single_user_id}]
            logger.info(f"🔍 Тестовая отправка для пользователя {single_user_id}")
        else:
            users = await ctx.supabase_client.get_users_by_segment(segment)
            if not users:
                logger.warning(f"⚠️ Нет пользователей для сегмента '{segment}'")
                return {
                    "success_count": 0,
                    "failed_count": 0,
                    "total_users": 0,
                    "segment": segment or "Все",
                    "warning": "Нет пользователей",
                }

        success_count = 0
        failed_count = 0
        message_ids = {}  # Словарь: {user_id: message_id}

        for user in users:
            telegram_id = user["telegram_id"]

            try:
                message = None  # Будет хранить результат отправки основного сообщения
                files_with_msg = [f for f in files_metadata if f["stage"] == "with_message"]

                if files_with_msg:
                    media_group = []
                    first_file = True

                    sorted_files = sorted(files_with_msg, key=lambda x: x.get("order", 0))

                    for file_info in sorted_files:
                        file_path = temp_with_msg / file_info["original_name"]

                        if file_info["type"] == "photo":
                            media = InputMediaPhoto(
                                media=FSInputFile(file_path),
                                caption=message_text if first_file else None,
                                parse_mode="MarkdownV2" if first_file else None,
                            )
                            media_group.append(media)
                        elif file_info["type"] == "video":
                            media = InputMediaVideo(
                                media=FSInputFile(file_path),
                                caption=message_text if first_file else None,
                                parse_mode="MarkdownV2" if first_file else None,
                            )
                            media_group.append(media)

                        first_file = False

                    if media_group:
                        messages = await ctx.bot.send_media_group(chat_id=telegram_id, media=media_group)
                        if messages and len(messages) > 0:
                            message = messages[0]  # Берем первое сообщение из media_group
                else:
                    message = await ctx.bot.send_message(chat_id=telegram_id, text=message_text, parse_mode="MarkdownV2")

                # Сохраняем message_id если сообщение было успешно отправлено
                if message and hasattr(message, 'message_id'):
                    message_ids[telegram_id] = message.message_id

                files_after = [f for f in files_metadata if f["stage"] == "after_message"]

                for file_info in files_after:
                    file_path = temp_after_msg / file_info["original_name"]

                    if file_info["type"] == "document":
                        await ctx.bot.send_document(chat_id=telegram_id, document=FSInputFile(file_path))
                    elif file_info["type"] == "photo":
                        await ctx.bot.send_photo(chat_id=telegram_id, photo=FSInputFile(file_path))
                    elif file_info["type"] == "video":
                        await ctx.bot.send_video(chat_id=telegram_id, video=FSInputFile(file_path))

                success_count += 1
                logger.info(f"✅ Отправлено пользователю {telegram_id}")

            except Exception as e:
                logger.error(f"❌ Ошибка отправки пользователю {telegram_id}: {e}")
                failed_count += 1

        logger.info(f"📊 Результат '{event_name}': успешно={success_count}, ошибок={failed_count}")
        logger.info(f"📝 Сохранено message_ids: {len(message_ids)} записей")

        shutil.rmtree(temp_with_msg, ignore_errors=True)
        shutil.rmtree(temp_after_msg, ignore_errors=True)

        try:
            await ctx.supabase_client.delete_event_files(event_id)
        except Exception:
            pass  # Тихая очистка без логирования

        result = {
            "success_count": success_count,
            "failed_count": failed_count,
            "total_users": len(users),
            "segment": segment or "Все пользователи",
            "files_count": len(files_metadata),
            "message_ids": message_ids,
        }
        logger.info(f"📦 Возвращаемый результат: {result}")
        return result

    except Exception as e:
        shutil.rmtree(temp_with_msg, ignore_errors=True)
        shutil.rmtree(temp_after_msg, ignore_errors=True)
        logger.error(f"❌ Критическая ошибка обработки события: {e}")
        raise


async def prepare_dashboard_info(description_template: str, title: str, user_id: int) -> Dict[str, Any]:
    """
    Подготавливает данные для дашборда (БЕЗ записи в БД)

    Возвращаемый dict нужно поместить в поле 'info' результата обработчика.
    bot_utils.py автоматически запишет его в столбец info_dashboard таблицы.

    Args:
        description_template: Строка с {username}, например "{username} купил подписку"
        title: Заголовок для дашборда
        user_id: Telegram ID

    Returns:
        Dict с данными для дашборда

    Example:
        @event_router.event_handler("collect_phone", notify=True)
        async def handle_phone_collection(user_id: int, phone_number: str):
            # ... бизнес-логика ...

            return {
                "status": "success",
                "phone": phone_number,
                "info": await prepare_dashboard_info(
                    description_template="{username} оставил телефон",
                    title="Новый контакт",
                    user_id=user_id
                )
            }
    """
    username = f"user_{user_id}"
    if ctx.supabase_client:
        try:
            query = ctx.supabase_client.client.table("sales_users").select("username").eq("telegram_id", user_id)
            if ctx.supabase_client.bot_id:
                query = query.eq("bot_id", ctx.supabase_client.bot_id)
            response = query.execute()
            if response.data:
                username = response.data[0].get("username") or username
        except Exception as e:
            logger.warning(f"⚠️ Не удалось получить username для дашборда: {e}")

    description = description_template.format(username=username)

    moscow_tz = timezone(timedelta(hours=3))
    moscow_time = datetime.now(moscow_tz)

    return {
        "title": title,
        "description": description,
        "created_at": moscow_time.isoformat(),
    }
