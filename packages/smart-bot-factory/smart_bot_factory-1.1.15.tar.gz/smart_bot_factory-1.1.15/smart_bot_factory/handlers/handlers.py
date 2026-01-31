# Исправленный handlers.py с отладкой маршрутизации

import logging
from typing import Optional

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.chat_action import ChatActionMiddleware

from ..utils.bot_utils import send_message
from ..utils.context import ctx
from .admin_middleware import AdminMiddleware
from .commands import timeup_handler, user_start_handler

# Импорты из созданных модулей
from .constants import MessageRole
from .file_handlers import (
    collect_files_for_message,
    send_chat_action_for_files,
    send_files_after_message,
    send_files_before_message,
    send_message_with_files,
)
from .message_processing import (
    _build_context,
    _enrich_prompt,
    _process_ai_response,
    _process_metadata,
    _validate_message,
)
from .states import UserStates
from .utils import (
    apply_send_filters,
    get_parse_mode_and_fix_html,
    prepare_final_response,
    send_critical_error_message,
)
from .voice_handler import (
    voice_edit_handler,
    voice_edit_text_handler,
    voice_handler,
    voice_retry_handler,
    voice_send_handler,
)

logger = logging.getLogger(__name__)

# ============ РОУТЕР И MIDDLEWARE ============

# Создаем роутер для обработчиков
router = Router()

# Middleware для обновления информации об админах
router.message.middleware(AdminMiddleware())

# Middleware для отправки chat action
router.message.middleware(ChatActionMiddleware())


# ============ ОБРАБОТЧИКИ КОМАНД ============


@router.message(Command(commands=["start", "старт", "ст"]))
async def start_handler(message: Message, state: FSMContext):
    """Обработчик команды /start - сброс сессии и начало заново"""
    from ..admin.admin_logic import admin_start_handler
    from ..utils.debug_routing import debug_user_state

    try:
        await debug_user_state(message, state, "START_COMMAND")

        # Проверяем, админ ли это и в каком режиме
        if ctx.admin_manager.is_admin(message.from_user.id):
            if ctx.admin_manager.is_in_admin_mode(message.from_user.id):
                # Админ в режиме администратора - работаем как админ
                await admin_start_handler(message, state)
                return
            # Админ в режиме пользователя - работаем как обычный пользователь

        await user_start_handler(message, state)

    except Exception as e:
        logger.error(f"Ошибка при обработке /start: {e}")
        await send_message(message, "Произошла ошибка при инициализации. Попробуйте позже.")


@router.message(Command(commands=["timeup", "вперед"]))
async def timeup_command_handler(message: Message, state: FSMContext):
    """Обработчик команды /timeup - делегирует в timeup_handler из commands.py"""
    await timeup_handler(message, state)


# ============ ОБРАБОТЧИКИ ГОЛОСОВЫХ СООБЩЕНИЙ ============


@router.message(F.voice | F.audio)
async def voice_message_handler(message: Message, state: FSMContext):
    """Обработчик голосовых и аудио сообщений - делегирует в voice_handler"""
    await voice_handler(message, state)


@router.callback_query(F.data == "voice_send")
async def voice_send_callback_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки 'Отправить' для голосового сообщения"""
    await voice_send_handler(callback, state)


@router.callback_query(F.data == "voice_edit")
async def voice_edit_callback_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки 'Изменить текст' для голосового сообщения"""
    await voice_edit_handler(callback, state)


@router.callback_query(F.data == "voice_retry")
async def voice_retry_callback_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки 'Надиктовать заново' для голосового сообщения"""
    await voice_retry_handler(callback, state)


@router.message(StateFilter(UserStates.voice_editing))
async def voice_edit_text_message_handler(message: Message, state: FSMContext):
    """Обработчик получения отредактированного текста"""
    await voice_edit_text_handler(message, state)


# ============ ОБРАБОТЧИКИ СООБЩЕНИЙ БЕЗ СОСТОЯНИЯ ============


@router.message(StateFilter(None))
async def message_without_state_handler(message: Message, state: FSMContext):
    """Обработчик сообщений без состояния (после перезапуска бота)"""
    from ..admin.admin_logic import AdminStates as AdminLogicStates
    from ..utils.debug_routing import debug_user_state

    try:
        await debug_user_state(message, state, "NO_STATE")

        # СНАЧАЛА проверяем диалог с админом
        conversation = await ctx.conversation_manager.is_user_in_admin_chat(message.from_user.id)

        if conversation:
            logger.info(f"✅ Найден диалог с админом {conversation['admin_id']}, устанавливаем состояние admin_chat")

            # Устанавливаем состояние admin_chat
            await state.set_state(UserStates.admin_chat)
            await state.update_data(admin_conversation=conversation)

            # Сразу пересылаем сообщение админу
            await ctx.conversation_manager.forward_message_to_admin(message, conversation)

            # Сохраняем сообщение в БД
            session_info = await ctx.supabase_client.get_active_session(message.from_user.id)
            if session_info and message.text:
                await ctx.supabase_client.add_message(
                    session_id=session_info["id"],
                    role="user",
                    content=message.text,
                    message_type="text",
                    metadata={
                        "in_admin_chat": True,
                        "admin_id": conversation["admin_id"],
                    },
                )

            return

        # Проверяем, админ ли это
        if ctx.admin_manager.is_admin(message.from_user.id):
            logger.info("👑 Админ в режиме администратора без состояния")
            await state.set_state(AdminLogicStates.admin_mode)
            await message.answer("👑 Режим администратора\nИспользуйте /start для панели управления")
            return

        logger.info("👤 Обычный пользователь без состояния, ищем активную сессию")

        # Ищем активную сессию в БД
        session_info = await ctx.supabase_client.get_active_session(message.from_user.id)

        if session_info:
            logger.info(f"📝 Восстанавливаем сессию {session_info['id']}")
            # Восстанавливаем сессию из БД (без системного промпта)
            session_id = session_info["id"]

            # Сохраняем в состояние (без system_prompt)
            await state.update_data(session_id=session_id)
            await state.set_state(UserStates.waiting_for_message)

            logger.info("✅ Сессия восстановлена, обрабатываем сообщение")

            # Теперь обрабатываем сообщение как обычно (системный промпт загрузится из временного файла)
            await process_user_message(message, state, session_id)
        else:
            logger.info("❌ Нет активной сессии, просим написать /start")
            await send_message(message, "Привет! Напишите /start для начала диалога.")

    except Exception as e:
        logger.error(f"❌ Ошибка при обработке сообщения без состояния: {e}")
        await send_message(message, "Произошла ошибка. Попробуйте написать /start для начала диалога.")


# ✅ ИСПРАВЛЕНИЕ: Обработчик admin_chat должен быть ПЕРВЫМ и более приоритетным
@router.message(StateFilter(UserStates.admin_chat))
async def user_in_admin_chat_handler(message: Message, state: FSMContext):
    """ПРИОРИТЕТНЫЙ обработчик сообщений пользователей в диалоге с админом"""
    from ..utils.debug_routing import debug_user_state

    await debug_user_state(message, state, "ADMIN_CHAT_HANDLER")

    user_id = message.from_user.id
    logger.info(f"🎯 ADMIN_CHAT HANDLER: сообщение от {user_id}: '{message.text}'")

    # Проверяем, есть ли еще активный диалог
    if ctx.conversation_manager is None:
        logger.warning("⚠️ conversation_manager не инициализирован, возвращаем к обычному режиму")
        await state.set_state(UserStates.waiting_for_message)
        return

    conversation = await ctx.conversation_manager.is_user_in_admin_chat(user_id)

    if conversation:
        logger.info(f"✅ Диалог активен, пересылаем админу {conversation['admin_id']}")

        try:
            # Сохраняем сообщение в БД
            session_info = await ctx.supabase_client.get_active_session(user_id)
            if session_info and message.text:
                await ctx.supabase_client.add_message(
                    session_id=session_info["id"],
                    role="user",
                    content=message.text,
                    message_type="text",
                    metadata={
                        "in_admin_chat": True,
                        "admin_id": conversation["admin_id"],
                    },
                )
                logger.info("💾 Сообщение сохранено в БД")

            # Пересылаем админу
            await ctx.conversation_manager.forward_message_to_admin(message, conversation)
            logger.info("📤 Сообщение переслано админу")

        except Exception as e:
            logger.error(f"❌ Ошибка обработки admin_chat: {e}")
            await message.answer("Произошла ошибка. Попробуйте позже.")
    else:
        logger.info("💬 Диалог завершен, возвращаем к обычному режиму")
        # Диалог завершен, возвращаем к обычному режиму
        await state.set_state(UserStates.waiting_for_message)

        # Обрабатываем как обычное сообщение
        data = await state.get_data()
        session_id = data.get("session_id")

        if session_id:
            await process_user_message(message, state, session_id)
        else:
            await send_message(message, "Сессия не найдена. Пожалуйста, напишите /start")


# Обработчик для обычных сообщений (НЕ в admin_chat)
@router.message(StateFilter(UserStates.waiting_for_message), ~F.text.startswith("/"))
async def user_message_handler(message: Message, state: FSMContext):
    """Обработчик сообщений пользователей (исключая admin_chat)"""
    from ..utils.debug_routing import debug_user_state

    try:
        await debug_user_state(message, state, "USER_MESSAGE_HANDLER")

        # ✅ ВАЖНО: Сначала проверяем диалог с админом
        conversation = await ctx.conversation_manager.is_user_in_admin_chat(message.from_user.id)

        if conversation:
            logger.info("⚠️ НЕОЖИДАННО: пользователь в waiting_for_message, но есть диалог с админом!")
            logger.info("🔄 Принудительно переключаем в admin_chat состояние")

            # Принудительно переключаем состояние
            await state.set_state(UserStates.admin_chat)
            await state.update_data(admin_conversation=conversation)

            # Обрабатываем сообщение как admin_chat
            await user_in_admin_chat_handler(message, state)
            return

        logger.info("🤖 Обычный диалог с ботом")
        data = await state.get_data()
        session_id = data.get("session_id")

        if not session_id:
            logger.warning("❌ Нет session_id в состоянии")
            await send_message(message, "Сессия не найдена. Пожалуйста, напишите /start")
            return

        logger.info(f"📝 Обрабатываем сообщение с session_id: {session_id}")
        await process_user_message(message, state, session_id)

    except Exception as e:
        logger.error(f"❌ Ошибка при обработке сообщения пользователя: {e}")
        await send_message(
            message,
            "Произошла ошибка. Попробуйте еще раз или напишите /start для перезапуска.",
        )


@router.message()
async def catch_all_handler(message: Message, state: FSMContext):
    """Перехватчик всех необработанных сообщений"""
    from ..utils.debug_routing import debug_user_state

    await debug_user_state(message, state, "CATCH_ALL")

    current_state = await state.get_state()
    logger.warning(f"⚠️ НЕОБРАБОТАННОЕ СООБЩЕНИЕ от {message.from_user.id}: '{message.text}', состояние: {current_state}")

    # Проверяем, админ ли это
    if ctx.admin_manager.is_admin(message.from_user.id):
        logger.info("👑 Необработанное сообщение админа")
        await message.answer("Команда не распознана. Используйте /help для справки.")
    else:
        logger.info("👤 Необработанное сообщение пользователя")
        await message.answer("Не понимаю. Напишите /start для начала диалога.")


# ============ PROCESS_USER_MESSAGE ============


async def process_user_message(message: Message, state: FSMContext, session_id: str, recognized_text: Optional[str] = None):
    """Общая функция для обработки сообщений пользователя (текстовых и голосовых)"""

    try:
        # ============ ПОДГОТОВКА И ВАЛИДАЦИЯ СООБЩЕНИЯ ============
        user_message_text = recognized_text if recognized_text else message.text

        if not user_message_text or not await _validate_message(user_message_text, message, ctx.message_hooks or {}):
            return

        # ============ СОХРАНЕНИЕ СООБЩЕНИЯ ПОЛЬЗОВАТЕЛЯ ============
        # Пропускаем обновление аналитики, будем обновлять в конце батчем
        if recognized_text:
            await ctx.supabase_client.add_message(
                session_id=session_id,
                role=MessageRole.USER,
                content=recognized_text,
                message_type="text",
                metadata={
                    "original_type": "voice",
                    "duration": message.voice.duration if message.voice else 0,
                },
                skip_analytics_update=True,
            )
            logger.debug("Распознанное голосовое сообщение сохранено в БД")
        elif message.text:
            await ctx.supabase_client.add_message(
                session_id=session_id,
                role=MessageRole.USER,
                content=message.text,
                message_type="text",
                skip_analytics_update=True,
            )
            logger.debug("Сообщение пользователя сохранено в БД")

        # ============ ПОДГОТОВКА ПРОМПТА И КОНТЕКСТА ============
        system_prompt = await ctx.prompt_loader.load_system_prompt()
        logger.debug(f"Системный промпт загружен ({len(system_prompt)} символов)")

        system_prompt_with_time, time_info = await _enrich_prompt(system_prompt, message.from_user.id, ctx.message_hooks or {})

        messages = await _build_context(
            system_prompt_with_time,
            session_id,
            ctx.prompt_loader,
            ctx.memory_manager,
            ctx.message_hooks or {},
            time_info,
        )

        # ============ ПОЛУЧЕНИЕ ОТВЕТА ОТ AI ============
        response_text, ai_metadata, processing_time, ai_response = await _process_ai_response(
            messages, ctx.openai_client, ctx.message_hooks or {}, message.from_user.id
        )

        # ============ ОБРАБОТКА МЕТАДАННЫХ И ФАЙЛОВ ============
        should_send_response, file_senders = await _process_metadata(
            ai_metadata, session_id, message.from_user.id, ctx.supabase_client, response_text, message.chat.id
        )

        await send_chat_action_for_files(message, file_senders)

        # ============ СОХРАНЕНИЕ ОТВЕТА АССИСТЕНТА ============
        # Вычисляем токены заранее для батч-обновления
        tokens_used = ctx.openai_client.estimate_tokens(response_text) if response_text else 0

        # Сохраняем ID сообщения в БД для обновления после отправки
        db_message_id = None
        try:
            # Пропускаем обновление аналитики, будем обновлять в конце батчем
            db_message_id = await ctx.supabase_client.add_message(
                session_id=session_id,
                role=MessageRole.ASSISTANT,
                content=response_text,
                message_type="text",
                tokens_used=tokens_used,
                processing_time_ms=processing_time,
                ai_metadata=ai_metadata,
                skip_analytics_update=True,
            )
            logger.debug(f"Ответ ассистента сохранен в БД с ID: {db_message_id}")
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения ответа в БД: {e}")

        # ============ БАТЧ-ОБНОВЛЕНИЕ АНАЛИТИКИ ============
        # Обновляем аналитику один раз для обоих сообщений (user + assistant)
        try:
            await ctx.supabase_client.update_session_analytics_batch(
                session_id=session_id,
                messages_count=2,  # user + assistant
                tokens_used=tokens_used,
                processing_time_ms=processing_time,
            )
            logger.debug("Аналитика сессии обновлена (батч)")
        except Exception as e:
            logger.error(f"❌ Ошибка обновления аналитики: {e}")
            # Не критично, продолжаем выполнение

        # ============ ПОДГОТОВКА ФИНАЛЬНОГО ОТВЕТА ============
        # Преобразуем ai_response (dict) в строку для prepare_final_response
        import json
        ai_response_str = json.dumps(ai_response, ensure_ascii=False, indent=2) if isinstance(ai_response, dict) else str(ai_response)
        debug_mode = ctx.config.DEBUG_MODE if ctx.config else False
        final_response = prepare_final_response(response_text, ai_response_str, debug_mode)
        logger.debug(f"Отправляем пользователю: {len(final_response)} символов")

        # ============ ПРОВЕРКА РАЗРЕШЕНИЯ НА ОТПРАВКУ ============
        if not should_send_response:
            logger.info("События запретили отправку сообщения от ИИ, пропускаем отправку")
            return

        await send_files_before_message(file_senders)

        # ============ ПРИМЕНЕНИЕ ФИЛЬТРОВ ОТПРАВКИ ============
        if await apply_send_filters(message.from_user.id):
            return

        # ============ ФОРМАТИРОВАНИЕ И ОТПРАВКА ============
        parse_mode, final_response = get_parse_mode_and_fix_html(final_response)

        file_sender_with_message_files, file_sender_with_message_dirs = collect_files_for_message(
            file_senders
        )

        # Отправляем сообщение и получаем telegram_message_id
        telegram_message_id = await send_message_with_files(
            message,
            final_response,
            file_senders,
            file_sender_with_message_files,
            file_sender_with_message_dirs,
            parse_mode,
        )

        # Обновляем запись в БД с telegram_message_id
        if telegram_message_id and db_message_id:
            try:
                await ctx.supabase_client.update_message_telegram_id(db_message_id, telegram_message_id)
                logger.debug(f"✅ Обновлен telegram_message_id={telegram_message_id} для сообщения {db_message_id}")
            except Exception as e:
                logger.error(f"❌ Ошибка обновления telegram_message_id: {e}")

        await send_files_after_message(file_senders)

    except Exception as e:
        logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА в process_user_message: {e}")
        logger.exception("Полный стек ошибки:")
        await send_critical_error_message(message)
