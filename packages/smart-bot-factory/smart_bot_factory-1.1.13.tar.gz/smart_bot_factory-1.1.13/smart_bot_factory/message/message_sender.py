"""
Функции для отправки сообщений через ИИ и от человека
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from aiogram.types import FSInputFile, InlineKeyboardMarkup
from project_root_finder import root
from sulguk import SULGUK_PARSE_MODE

logger = logging.getLogger(__name__)


async def send_message_by_ai(user_id: int, message_text: str, session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Отправляет сообщение пользователю через ИИ (использует ту же логику, что и process_user_message)

    Args:
        user_id: ID пользователя в Telegram
        message_text: Текст сообщения для обработки ИИ
        session_id: ID сессии чата (если не указан, будет использована активная сессия)

    Returns:
        Результат отправки
    """
    try:
        # Импортируем необходимые компоненты
        from ..handlers.constants import MessageRole
        from ..handlers.message_processing import (
            _build_context,
            _enrich_prompt,
            _process_ai_response,
            _process_metadata,
        )
        from ..utils.context import ctx

        # Если session_id не указан, получаем активную сессию пользователя
        if not session_id:
            session_info = await ctx.supabase_client.get_active_session(user_id)
            if not session_info:
                return {
                    "status": "error",
                    "error": "Активная сессия не найдена",
                    "user_id": user_id,
                }
            session_id = session_info["id"]

        # Загружаем системный промпт
        try:
            system_prompt = await ctx.prompt_loader.load_system_prompt()
            logger.debug(f"Системный промпт загружен ({len(system_prompt)} символов)")
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки системного промпта: {e}")
            return {
                "status": "error",
                "error": "Не удалось загрузить системный промпт",
                "user_id": user_id,
            }

        # Сохраняем сообщение пользователя в БД
        await ctx.supabase_client.add_message(
            session_id=session_id,
            role=MessageRole.USER,
            content=message_text,
            message_type="text",
        )
        logger.debug("Сообщение пользователя сохранено в БД")

        # ============ ОБОГАЩЕНИЕ ПРОМПТА ============
        system_prompt_with_time, time_info = await _enrich_prompt(system_prompt, user_id, ctx.message_hooks or {})

        # ============ ПОСТРОЕНИЕ КОНТЕКСТА ============
        messages = await _build_context(
            system_prompt_with_time,
            session_id,
            ctx.prompt_loader,
            ctx.memory_manager,
            ctx.message_hooks or {},
            time_info,
        )

        # ============ ОБРАБОТКА ОТВЕТА AI ============
        response_text, ai_metadata, processing_time, original_ai_response = await _process_ai_response(
            messages, ctx.openai_client, ctx.message_hooks or {}, user_id
        )

        # ============ ОБРАБОТКА МЕТАДАННЫХ ============
        should_send_response, files_list, directories_list, file_senders = await _process_metadata(
            ai_metadata, session_id, user_id, ctx.supabase_client, response_text
        )

        # Сохраняем ответ ассистента
        try:
            await ctx.supabase_client.add_message(
                session_id=session_id,
                role=MessageRole.ASSISTANT,
                content=response_text,
                message_type="text",
                tokens_used=ctx.openai_client.estimate_tokens(response_text) if response_text else 0,
                processing_time_ms=processing_time,
                ai_metadata=ai_metadata,
            )
            logger.debug("Ответ ассистента сохранен в БД")
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения ответа в БД: {e}")

        # Определяем финальный ответ для пользователя
        if ctx.config.DEBUG_MODE:
            # В режиме отладки показываем полный ответ с JSON
            final_response = original_ai_response
            logger.debug("Режим отладки: отправляем полный ответ с JSON")
        else:
            # В обычном режиме показываем только текст без JSON
            final_response = response_text
            logger.debug("Обычный режим: отправляем очищенный текст")

        # Проверяем, нужно ли отправлять сообщение от ИИ
        if not should_send_response:
            logger.info("🔇 События запретили отправку сообщения от ИИ (message_sender), пропускаем отправку")
            return {
                "status": "skipped",
                "reason": "send_ai_response=False",
                "user_id": user_id,
            }

        # Отправляем ответ пользователю напрямую через бота
        await ctx.bot.send_message(chat_id=user_id, text=final_response)

        # Подсчитываем количество обработанных событий
        events = ai_metadata.get("события", []) if ai_metadata else []

        return {
            "status": "success",
            "user_id": user_id,
            "response_text": response_text,
            "tokens_used": ctx.openai_client.estimate_tokens(response_text) if response_text else 0,
            "processing_time_ms": processing_time,
            "events_processed": len(events),
        }

    except Exception as e:
        logger.error(f"❌ Ошибка в send_message_by_ai: {e}")
        logger.exception("Полный стек ошибки:")
        return {"status": "error", "error": str(e), "user_id": user_id}


async def send_message_by_human(
    user_id: int,
    message_text: str,
    session_id: Optional[str] = None,
    parse_mode: str = "Markdown",
    reply_markup: Optional[InlineKeyboardMarkup] = None,
    photo: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Отправляет сообщение пользователю от имени человека (готовый текст или фото с подписью).

    Args:
        user_id: ID пользователя в Telegram
        message_text: Готовый текст сообщения или подпись к фото
        session_id: ID сессии (опционально, для сохранения в БД)
        parse_mode: Тип форматирования текста
        reply_markup: Клавиатура/markup (опционально)
        photo: (str) путь к локальному файлу относительно корня проекта
    Returns:
        Результат отправки
    """
    try:
        # Импортируем необходимые компоненты
        from ..utils.context import ctx
        
        # Если parse_mode="HTML" и в конфиге HTML, используем SULGUK_PARSE_MODE
        if parse_mode == "HTML" and ctx.config and ctx.config.MESSAGE_PARSE_MODE.upper() == "HTML":
            parse_mode = SULGUK_PARSE_MODE

        msg_type = "text"
        message = None

        if photo:
            photo_path = root / photo
            if not photo_path.exists():
                raise FileNotFoundError(f"Файл с фото не найден: {photo}")
            message = await ctx.bot.send_photo(
                chat_id=user_id, photo=FSInputFile(str(photo_path)), caption=message_text, parse_mode=parse_mode, reply_markup=reply_markup
            )
            msg_type = "photo"
        else:
            message = await ctx.bot.send_message(
                chat_id=user_id,
                text=message_text,
                parse_mode=parse_mode,
                reply_markup=reply_markup,
            )

        # Если указана сессия, сохраняем сообщение в БД
        if session_id:
            await ctx.supabase_client.add_message(
                session_id=session_id,
                role="assistant",
                content=message_text,
                message_type=msg_type,
                metadata={"sent_by_human": True, "has_photo": bool(photo)},
            )
            logger.debug(f"Сообщение от человека сохранено в БД (photo={bool(photo)})")

        return {
            "status": "success",
            "user_id": user_id,
            "message_id": message.message_id,
            "message_text": message_text,
            "saved_to_db": bool(session_id),
            "has_photo": bool(photo),
        }

    except Exception as e:
        logger.error(f"❌ Ошибка в send_message_by_human: {e}")
        return {"status": "error", "error": str(e), "user_id": user_id}


async def send_message_to_users_by_stage(stage: str, message_text: str, bot_id: str, photo: Optional[str] = None) -> Dict[str, Any]:
    """
    Отправляет сообщение (или фото с подписью) всем пользователям, находящимся на определенной стадии

    Args:
        stage: Стадия диалога (например, 'introduction', 'qualification', 'closing')
        message_text: Текст сообщения для отправки / подпись к фото
        bot_id: ID бота (если не указан, используется текущий бот)
        photo: путь к файлу с фото (относительно корня проекта, опционально)
    Returns:
        Результат отправки с количеством отправленных сообщений
    """
    try:
        import asyncio

        from ..utils.context import ctx

        # Кэшируем bot_id для избежания повторных проверок
        resolved_bot_id = ctx.config.BOT_ID if ctx.config else bot_id
        if not resolved_bot_id:
            return {"status": "error", "error": "Не удалось определить bot_id"}
        logger.debug(f"Ищем пользователей на стадии '{stage}' для бота '{resolved_bot_id}'")
        sessions_query = (
            ctx.supabase_client.client.table("sales_chat_sessions")
            .select("user_id, id, current_stage, created_at")
            .eq("status", "active")
            .eq("current_stage", stage)
            .eq("bot_id", resolved_bot_id)
        )
        sessions_query = sessions_query.order("created_at", desc=True)
        sessions_data = sessions_query.execute()
        if not sessions_data.data:
            logger.info(f"📭 Пользователи на стадии '{stage}' не найдены")
            return {
                "status": "success",
                "stage": stage,
                "users_found": 0,
                "messages_sent": 0,
                "errors": [],
            }
        unique_users = {}
        for session in sessions_data.data:
            user_id = session["user_id"]
            if user_id not in unique_users:
                unique_users[user_id] = {
                    "session_id": session["id"],
                    "current_stage": session["current_stage"],
                }
        logger.info(f"👥 Найдено {len(unique_users)} уникальных пользователей на стадии '{stage}'")
        photo_path = None
        if photo:
            photo_path = root / photo
            if not photo_path.exists():
                raise FileNotFoundError(f"Файл с фото не найден: {photo}")

        # Распараллеливаем отправку сообщений
        async def send_to_user(user_id: int, user_data: dict) -> tuple[int, Optional[str]]:
            """Отправляет сообщение одному пользователю, возвращает (user_id, error)"""
            session_id = user_data["session_id"]
            try:
                if photo_path:
                    await ctx.bot.send_photo(chat_id=user_id, photo=FSInputFile(str(photo_path)), caption=message_text)
                    msg_type = "photo"
                else:
                    await ctx.bot.send_message(chat_id=user_id, text=message_text)
                    msg_type = "text"
                await ctx.supabase_client.add_message(
                    session_id=session_id,
                    role="assistant",
                    content=message_text,
                    message_type=msg_type,
                    metadata={
                        "sent_by_stage_broadcast": True,
                        "target_stage": stage,
                        "broadcast_timestamp": datetime.now().isoformat(),
                        "has_photo": bool(photo),
                    },
                )
                logger.debug(f"Сообщение отправлено пользователю {user_id} (стадия: {stage})")
                return (user_id, None)
            except Exception as e:
                error_msg = f"Ошибка отправки пользователю {user_id}: {str(e)}"
                logger.error(f"❌ {error_msg}")
                return (user_id, error_msg)

        # Выполняем отправку параллельно с ограничением на количество одновременных задач
        tasks = [send_to_user(user_id, user_data) for user_id, user_data in unique_users.items()]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Подсчитываем результаты
        messages_sent = 0
        errors = []
        for result in results:
            if isinstance(result, Exception):
                errors.append(f"Неожиданная ошибка: {str(result)}")
            elif result[1] is None:
                messages_sent += 1
            else:
                errors.append(result[1])
        result = {
            "status": "success",
            "stage": stage,
            "users_found": len(unique_users),
            "messages_sent": messages_sent,
            "errors": errors,
        }
        logger.info(f"📊 Результат рассылки по стадии '{stage}': {messages_sent}/{len(unique_users)} сообщений отправлено")
        return result
    except Exception as e:
        logger.error(f"❌ Ошибка в send_message_to_users_by_stage: {e}")
        return {"status": "error", "error": str(e), "stage": stage}


async def get_users_by_stage_stats(bot_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Получает статистику пользователей по стадиям

    Args:
        bot_id: ID бота (если не указан, используется текущий бот)

    Returns:
        Статистика по стадиям с количеством пользователей
    """
    try:
        # Импортируем необходимые компоненты
        from ..utils.context import ctx

        if not (ctx.config.BOT_ID if ctx.config else bot_id):
            return {"status": "error", "error": "Не удалось определить bot_id"}

        logger.debug(f"Получаем статистику по стадиям для бота '{ctx.config.BOT_ID if ctx.config else bot_id}'")

        # Получаем статистику по стадиям с user_id для подсчета уникальных пользователей
        stats_query = ctx.supabase_client.client.table("sales_chat_sessions").select("user_id, current_stage, created_at").eq("status", "active")

        # Фильтруем по bot_id если указан
        if ctx.config.BOT_ID if ctx.config else bot_id:
            stats_query = stats_query.eq("bot_id", ctx.config.BOT_ID if ctx.config else bot_id)

        # Сортируем по дате создания (последние сначала)
        stats_query = stats_query.order("created_at", desc=True)

        sessions_data = stats_query.execute()

        # Подсчитываем уникальных пользователей по стадиям (берем последнюю сессию каждого пользователя)
        user_stages = {}  # {user_id: stage}

        for session in sessions_data.data:
            user_id = session["user_id"]
            stage = session["current_stage"] or "unknown"

            # Если пользователь еще не добавлен, добавляем его стадию (первая встреченная - самая последняя)
            if user_id not in user_stages:
                user_stages[user_id] = stage

        # Подсчитываем количество пользователей по стадиям
        stage_stats = {}
        for stage in user_stages.values():
            stage_stats[stage] = stage_stats.get(stage, 0) + 1

        total_users = len(user_stages)

        # Сортируем по количеству пользователей (по убыванию)
        sorted_stages = sorted(stage_stats.items(), key=lambda x: x[1], reverse=True)

        result = {
            "status": "success",
            "bot_id": ctx.config.BOT_ID if ctx.config else bot_id,
            "total_active_users": total_users,
            "stages": dict(sorted_stages),
            "stages_list": sorted_stages,
        }

        logger.debug(f"Статистика по стадиям: {total_users} активных пользователей")
        if logger.isEnabledFor(logging.DEBUG):
            for stage, count in sorted_stages:
                logger.debug(f"   {stage}: {count} пользователей")

        return result

    except Exception as e:
        logger.error(f"❌ Ошибка в get_users_by_stage_stats: {e}")
        return {"status": "error", "error": str(e), "bot_id": bot_id}


async def send_message(
    message,
    text: str,
    supabase_client,
    files_list: list = [],
    directories_list: list = [],
    parse_mode: str = "Markdown",
    **kwargs,
):
    """
    Пользовательская функция для отправки сообщений с файлами и кнопками

    Args:
        message: Message объект от aiogram
        text: Текст сообщения
        supabase_client: SupabaseClient для работы с БД
        files_list: Список файлов для отправки
        directories_list: Список каталогов (отправятся все файлы)
        parse_mode: Режим парсинга ('Markdown', 'HTML' или None)
        **kwargs: Дополнительные параметры (reply_markup и т.д.)

    Returns:
        Message объект отправленного сообщения или None

    Example:
        from smart_bot_factory.message import send_message
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Кнопка", callback_data="action")]
        ])

        await send_message(
            message=message,
            text="Привет!",
            supabase_client=supabase_client,
            files_list=["file.pdf"],
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    """
    from pathlib import Path

    from aiogram.types import FSInputFile
    from aiogram.utils.media_group import MediaGroupBuilder

    from ..utils.context import ctx

    logger.debug(f"send_message вызвана: user={message.from_user.id}, text_len={len(text)}, parse_mode={parse_mode}")

    try:
        user_id = message.from_user.id

        # Устанавливаем parse_mode (None если передана строка 'None')
        actual_parse_mode = None if parse_mode == "None" else parse_mode

        # Текст уже готов, используем как есть
        final_text = text

        # Работаем с переданными файлами и каталогами
        logger.debug(f"Передано файлов: {files_list}, каталогов: {directories_list}")

        # Используем файлы и каталоги напрямую без фильтрации
        actual_files_list = files_list
        actual_directories_list = directories_list

        if actual_files_list or actual_directories_list:
            logger.debug(f"Файлов для отправки: {len(actual_files_list)}, каталогов: {len(actual_directories_list)}")

        # Проверяем, что есть что отправлять
        if not final_text or not final_text.strip():
            logger.error("❌ КРИТИЧЕСКАЯ ОШИБКА: final_text пуст после обработки!")
            logger.error(f"   Исходный text: '{text[:200]}...'")
            final_text = "Ошибка формирования ответа. Попробуйте еще раз."

        logger.debug(f"Подготовка сообщения: {len(final_text)} символов")

        # Проверяем наличие файлов для отправки
        if actual_files_list or actual_directories_list:
            # Функция определения типа медиа по расширению
            def get_media_type(file_path: str) -> str:
                ext = Path(file_path).suffix.lower()
                if ext in {".jpg", ".jpeg", ".png"}:
                    return "photo"
                elif ext in {".mp4", ".mov"}:
                    return "video"
                else:
                    return "document"

            # Создаем списки для разных типов файлов
            video_files = []
            photo_files = []
            document_files = []

            # Функция обработки файла
            def process_file(file_path: Path, source: str = ""):
                if file_path.is_file():
                    media_type = get_media_type(str(file_path))
                    if media_type == "video":
                        video_files.append(file_path)
                        logger.debug(f"Добавлено видео{f' из {source}' if source else ''}: {file_path.name}")
                    elif media_type == "photo":
                        photo_files.append(file_path)
                        logger.debug(f"Добавлено фото{f' из {source}' if source else ''}: {file_path.name}")
                    else:
                        document_files.append(file_path)
                        logger.debug(f"Добавлен документ{f' из {source}' if source else ''}: {file_path.name}")
                else:
                    logger.warning(f"   ⚠️ Файл не найден: {file_path}")

            # Обрабатываем прямые файлы
            # Определяем путь к папке files относительно рабочей директории
            files_dir = Path("files").resolve()
            if not files_dir.exists():
                # Пробуем найти files относительно директории промптов
                try:
                    if ctx.config and hasattr(ctx.config, "PROMT_FILES_DIR") and ctx.config.PROMT_FILES_DIR:
                        prompts_dir = Path(ctx.config.PROMT_FILES_DIR)
                        files_dir = prompts_dir.parent / "files"
                except Exception:
                    pass

            for file_name in actual_files_list:
                try:
                    file_path = files_dir / file_name
                    process_file(file_path)
                except Exception as e:
                    logger.error(f"   ❌ Ошибка обработки файла {file_name}: {e}")

            # Обрабатываем файлы из каталогов
            for dir_name in actual_directories_list:
                dir_name = Path(dir_name)
                try:
                    if dir_name.is_dir():
                        for file_path in dir_name.iterdir():
                            try:
                                process_file(file_path, dir_name)
                            except Exception as e:
                                logger.error(f"   ❌ Ошибка обработки файла {file_path}: {e}")
                    else:
                        logger.warning(f"   ⚠️ Каталог не найден: {dir_name}")
                except Exception as e:
                    logger.error(f"   ❌ Ошибка обработки каталога {dir_name}: {e}")

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
            result = await message.answer(final_text, parse_mode=actual_parse_mode, **kwargs)
            logger.debug("Отправлен текст сообщения")

            # 4. Отправляем документы (если есть)
            if document_files:
                doc_group = MediaGroupBuilder()
                for file_path in document_files:
                    doc_group.add_document(media=FSInputFile(str(file_path)))

                docs = doc_group.build()
                if docs:
                    await message.answer_media_group(media=docs)
                    logger.debug(f"Отправлено {len(docs)} документов")

            # 🆕 Сохранение названий файлов и каталогов в БД убрано

            return result
        else:
            # Если нет файлов, отправляем просто текст
            logger.debug("Нет файлов для отправки, отправляем как текст")
            result = await message.answer(final_text, parse_mode=actual_parse_mode, **kwargs)
            return result

    except Exception as e:
        # Проверяем, является ли ошибка блокировкой бота
        if "Forbidden: bot was blocked by the user" in str(e):
            logger.warning(f"🚫 Бот заблокирован пользователем {user_id}")
            return None
        elif "TelegramForbiddenError" in str(type(e).__name__):
            logger.warning(f"🚫 Бот заблокирован пользователем {user_id}")
            return None

        logger.error(f"❌ ОШИБКА в send_message: {e}")
        logger.exception("Полный стек ошибки send_message:")

        # Пытаемся отправить простое сообщение без форматирования
        try:
            fallback_text = "Произошла ошибка при отправке ответа. Попробуйте еще раз."
            result = await message.answer(fallback_text)
            logger.info("✅ Запасное сообщение отправлено")
            return result
        except Exception as e2:
            if "Forbidden: bot was blocked by the user" in str(e2):
                logger.warning(f"🚫 Бот заблокирован пользователем {user_id} (fallback)")
                return None
            elif "TelegramForbiddenError" in str(type(e2).__name__):
                logger.warning(f"🚫 Бот заблокирован пользователем {user_id} (fallback)")
                return None

            logger.error(f"❌ Даже запасное сообщение не отправилось: {e2}")
            raise
