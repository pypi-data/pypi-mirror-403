# Исправленный admin_logic.py с правильной обработкой диалогов

import logging

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from ..utils.context import ctx

# Импортируем состояния
from .states import AdminStates

logger = logging.getLogger(__name__)

# Создаем роутер для админских обработчиков
admin_router = Router()


@admin_router.message(Command(commands=["отмена", "cancel"]))
async def cancel_handler(message: Message, state: FSMContext):
    """Отмена текущего действия и очистка state"""
    # Получаем текущий state
    current_state = await state.get_state()

    # Очищаем временные файлы если это создание события
    if current_state and current_state.startswith("AdminStates:create_event"):
        from .admin_events import cleanup_temp_files

        await cleanup_temp_files(state)

    # Очищаем state
    await state.clear()

    if current_state:
        logger.info(f"State очищен для пользователя {message.from_user.id}: {current_state}")

        # Если это админ, возвращаем в админ режим
        if ctx.admin_manager.is_admin(message.from_user.id):
            await state.set_state(AdminStates.admin_mode)
            await message.answer(
                "✅ Текущее действие отменено\n" "Вы вернулись в админ режим\n\n" "Используйте /admin для просмотра доступных команд",
                parse_mode="Markdown",
            )
        else:
            await message.answer(
                "✅ Текущее действие отменено\n\n" "Используйте /start для начала работы",
                parse_mode="Markdown",
            )
    else:
        await message.answer("ℹ️ Нет активных действий для отмены", parse_mode="Markdown")


async def admin_start_handler(message: Message, state: FSMContext):
    """Обработчик /start для админов в режиме администратора"""
    await state.set_state(AdminStates.admin_mode)

    # Основное меню админа
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
            [InlineKeyboardButton(text="💬 Активные чаты", callback_data="admin_active_chats")],
            [InlineKeyboardButton(text="🔄 Режим польз.", callback_data="admin_toggle_mode")],
        ]
    )

    welcome_text = f"""
{ctx.admin_manager.get_admin_mode_text(message.from_user.id)}

🎛️ **Панель администратора**

Доступные команды:
• `/stats` - статистика воронки
• `/dashboard` - ссылка на дашборд аналитики
• `/history user_id` - история пользователя
• `/chat user_id` - начать диалог
• `/chats` - активные диалоги
• `/stop` - завершить диалог
• `/admin` - переключить режим
• `/cancel` - отменить текущее действие

📅 **Управление событиями:**
• `/create_event` - создать новое событие
• `/list_events` - список активных событий
• `/cancel_event название` - отменить событие
• `/edit_event` - редактировать событие
"""

    await message.answer(welcome_text, reply_markup=keyboard, parse_mode="Markdown")


@admin_router.message(Command(commands=["стат", "stats"]))
async def admin_stats_handler(message: Message, state: FSMContext):
    """Статистика воронки"""
    logger.debug(f"admin_stats_handler вызван для пользователя {message.from_user.id}")
    logger.debug(f"admin_manager = {ctx.admin_manager is not None}, analytics_manager = {ctx.analytics_manager is not None}")

    if ctx.admin_manager is None:
        logger.error("❌ admin_manager is None в admin_stats_handler")
        await message.answer("❌ Ошибка: admin_manager не инициализирован")
        return

    if ctx.analytics_manager is None:
        logger.error("❌ analytics_manager is None в admin_stats_handler")
        await message.answer("❌ Ошибка: analytics_manager не инициализирован")
        return

    if not ctx.admin_manager.is_admin(message.from_user.id):
        return

    try:
        # Получаем статистику
        funnel_stats = await ctx.analytics_manager.get_funnel_stats(7)
        events_stats = await ctx.analytics_manager.get_events_stats(7)

        # Форматируем ответ
        full_text = f"{ctx.analytics_manager.format_funnel_stats(funnel_stats)}\n\n{ctx.analytics_manager.format_events_stats(events_stats)}"

        await message.answer(full_text)

    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        await message.answer("❌ Ошибка получения статистики")


@admin_router.message(Command(commands=["история", "history"]))
async def admin_history_handler(message: Message, state: FSMContext):
    """История пользователя"""
    if not ctx.admin_manager.is_admin(message.from_user.id):
        return

    try:
        parts = message.text.split()
        if len(parts) < 2:
            await message.answer("Укажите ID пользователя: /история 123456789")
            return

        user_id = int(parts[1])

        # Получаем историю (та же функция что использует кнопка)
        journey = await ctx.analytics_manager.get_user_journey(user_id)

        if not journey:
            await message.answer(f"❌ У пользователя {user_id} нет активной сессии")
            return

        # Используем ту же функцию форматирования что и кнопка
        await message.answer(ctx.analytics_manager.format_user_journey(user_id, journey))

    except ValueError:
        await message.answer("❌ Неверный формат ID пользователя")
    except Exception as e:
        logger.error(f"Ошибка получения истории: {e}")
        await message.answer("❌ Ошибка получения истории")


@admin_router.message(Command(commands=["чат", "chat"]))
async def admin_chat_handler(message: Message, state: FSMContext):
    """Начать диалог с пользователем"""
    if not ctx.admin_manager.is_admin(message.from_user.id):
        return

    try:
        # Парсим user_id из команды
        parts = message.text.split()
        if len(parts) < 2:
            await message.answer("Укажите ID пользователя: /чат 123456789")
            return

        user_id = int(parts[1])
        admin_id = message.from_user.id

        logger.info(f"👑 Админ {admin_id} хочет начать диалог с пользователем {user_id}")

        # Проверяем, есть ли активная сессия у пользователя
        session_info = await ctx.supabase_client.get_active_session(user_id)
        if not session_info:
            await message.answer(f"❌ У пользователя {user_id} нет активной сессии")
            logger.warning(f"❌ У пользователя {user_id} нет активной сессии")
            return

        logger.info(f"✅ У пользователя {user_id} есть активная сессия: {session_info['id']}")

        # Начинаем диалог
        logger.info("🚀 Запускаем создание диалога...")
        success = await ctx.conversation_manager.start_admin_conversation(admin_id, user_id)

        if success:
            # ✅ ИСПРАВЛЕНИЕ: Правильно переключаем состояние админа
            await state.set_state(AdminStates.in_conversation)
            await state.update_data(conversation_user_id=user_id)

            await message.answer(
                f"✅ Диалог с пользователем {user_id} начат\n💬 Ваши сообщения будут переданы пользователю\n⏹️ Используйте /стоп для завершения"
            )
            logger.info("✅ Диалог успешно создан, админ переключен в состояние in_conversation")
        else:
            await message.answer(f"❌ Не удалось начать диалог с пользователем {user_id}")
            logger.error("❌ Не удалось создать диалог")

    except ValueError:
        await message.answer("❌ Неверный формат ID пользователя")
        logger.error(f"❌ Неверный формат ID пользователя: {message.text}")
    except Exception as e:
        logger.error(f"❌ Ошибка начала диалога: {e}")
        await message.answer("❌ Ошибка начала диалога")


@admin_router.message(Command(commands=["чаты", "chats"]))
async def admin_active_chats_command(message: Message, state: FSMContext):
    """Показать активные диалоги админов"""
    if not ctx.admin_manager.is_admin(message.from_user.id):
        return

    try:
        conversations = await ctx.conversation_manager.get_active_conversations()

        # ✅ ИСПРАВЛЕНИЕ: Убираем parse_mode='Markdown' чтобы избежать ошибок парсинга
        await message.answer(ctx.conversation_manager.format_active_conversations(conversations))

    except Exception as e:
        logger.error(f"Ошибка получения активных чатов: {e}")
        await message.answer("❌ Ошибка получения активных диалогов")


@admin_router.message(Command(commands=["стоп", "stop"]))
async def admin_stop_handler(message: Message, state: FSMContext):
    """Завершить диалог"""
    if not ctx.admin_manager.is_admin(message.from_user.id):
        return

    try:
        admin_id = message.from_user.id

        # Проверяем есть ли активный диалог
        conversation = await ctx.conversation_manager.get_admin_active_conversation(admin_id)

        if conversation:
            user_id = conversation["user_id"]
            logger.info(f"🛑 Завершаем диалог админа {admin_id} с пользователем {user_id}")

            success = await ctx.conversation_manager.end_admin_conversation(admin_id)

            if success:
                # ✅ ИСПРАВЛЕНИЕ: Правильно переключаем состояние обратно
                await state.set_state(AdminStates.admin_mode)
                await state.update_data(conversation_user_id=None)

                await message.answer(f"✅ Диалог с пользователем {user_id} завершен")
                logger.info("✅ Диалог завершен, админ переключен в admin_mode")
            else:
                await message.answer("❌ Ошибка завершения диалога")
        else:
            await message.answer("❌ Нет активного диалога")
            logger.info(f"❌ У админа {admin_id} нет активного диалога")

    except Exception as e:
        logger.error(f"Ошибка завершения диалога: {e}")
        await message.answer("❌ Ошибка завершения диалога")


@admin_router.message(Command(commands=["админ", "admin"]))
async def admin_toggle_handler(message: Message, state: FSMContext):
    """Переключение режима админа"""
    if not ctx.admin_manager.is_admin(message.from_user.id):
        return

    if ctx.admin_manager.toggle_admin_mode(message.from_user.id):
        # Переключились в режим админа
        await admin_start_handler(message, state)
    else:
        # Переключились в режим пользователя
        await state.clear()
        await message.answer("🔄 Переключен в режим пользователя\nНапишите /start для начала диалога")


@admin_router.message(Command(commands=["дашборд", "dashboard"]))
async def admin_dashboard_handler(message: Message, state: FSMContext):
    """Отправка ссылки на дашборд"""
    if not ctx.admin_manager.is_admin(message.from_user.id):
        return

    dashboard_url = "https://dshb.lemifar.ru"
    dashboard_text = f"""
📊 **Дашборд аналитики**

Перейдите по ссылке для просмотра детальной статистики и аналитики:

🔗 [Открыть дашборд]({dashboard_url})

На дашборде доступна информация о:
• Статистике воронки продаж
• Активности пользователей
• Конверсиях по этапам
• Событиях и метриках
"""

    await message.answer(dashboard_text, parse_mode="Markdown")


@admin_router.message(Command("debug_chat"))
async def debug_chat_handler(message: Message, state: FSMContext):
    """Отладка диалогов админов"""
    if not ctx.admin_manager.is_admin(message.from_user.id):
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Использование: /debug_chat USER_ID")
        return

    try:
        user_id = int(parts[1])

        # 1. Проверяем запись в БД
        conversation = await ctx.conversation_manager.is_user_in_admin_chat(user_id)

        debug_info = [
            f"🔍 ОТЛАДКА ДИАЛОГА С {user_id}",
            "",
            f"📊 Диалог в БД: {'✅' if conversation else '❌'}",
        ]

        if conversation:
            debug_info.extend(
                [
                    f"👑 Админ: {conversation['admin_id']}",
                    f"🕐 Начат: {conversation['started_at']}",
                ]
            )

        # 2. Проверяем активную сессию пользователя
        session_info = await ctx.supabase_client.get_active_session(user_id)
        debug_info.append(f"🎯 Активная сессия: {'✅' if session_info else '❌'}")

        if session_info:
            debug_info.append(f"📝 ID сессии: {session_info['id']}")

        # 3. Проверяем состояние пользователя (если он онлайн)
        debug_info.append("")
        debug_info.append("ℹ️ Для проверки состояния пользователь должен написать что-то")

        await message.answer("\n".join(debug_info))

    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
        logger.error(f"Ошибка отладки: {e}")


@admin_router.callback_query(F.data.startswith("admin_"))
async def admin_callback_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик callback кнопок админов"""
    if not ctx.admin_manager.is_admin(callback.from_user.id):
        await callback.answer("Нет доступа")
        return

    data = callback.data

    try:
        if data == "admin_stats":
            # Показываем статистику
            funnel_stats = await ctx.analytics_manager.get_funnel_stats(7)
            events_stats = await ctx.analytics_manager.get_events_stats(7)

            await callback.message.answer(
                f"{ctx.analytics_manager.format_funnel_stats(funnel_stats)}\n\n{ctx.analytics_manager.format_events_stats(events_stats)}"
            )

        elif data == "admin_toggle_mode":
            # Переключаем режим
            new_mode = ctx.admin_manager.toggle_admin_mode(callback.from_user.id)
            await callback.answer(f"Режим переключен: {'администратор' if new_mode else 'пользователь'}")

            if not new_mode:
                await state.clear()
                await callback.message.answer("🔄 Теперь вы в режиме пользователя")

        elif data == "admin_active_chats":
            # Показываем активные диалоги
            conversations = await ctx.conversation_manager.get_active_conversations()

            # ✅ ИСПРАВЛЕНИЕ: Убираем parse_mode='Markdown'
            await callback.message.answer(ctx.conversation_manager.format_active_conversations(conversations))

        elif data.startswith("admin_history_"):
            user_id = int(data.split("_")[2])
            journey = await ctx.analytics_manager.get_user_journey(user_id)
            await callback.message.answer(ctx.analytics_manager.format_user_journey(user_id, journey))

        elif data.startswith("admin_end_"):
            user_id = int(data.split("_")[2])

            # Проверяем есть ли активный диалог
            conversation = await ctx.conversation_manager.get_admin_active_conversation(callback.from_user.id)

            if conversation and conversation["user_id"] == user_id:
                await ctx.conversation_manager.end_admin_conversation(callback.from_user.id)

                # ✅ ИСПРАВЛЕНИЕ: Правильно переключаем состояние
                await state.set_state(AdminStates.admin_mode)
                await state.update_data(conversation_user_id=None)

                await callback.answer("Диалог завершен")
                await callback.message.answer(f"✅ Диалог с пользователем {user_id} завершен")
                logger.info("✅ Диалог завершен через кнопку, админ переключен в admin_mode")
            else:
                await callback.answer("Диалог не найден")

        elif data.startswith("admin_chat_"):
            user_id = int(data.split("_")[2])
            admin_id = callback.from_user.id

            success = await ctx.conversation_manager.start_admin_conversation(admin_id, user_id)
            if success:
                # ✅ ИСПРАВЛЕНИЕ: Правильно переключаем состояние
                await state.set_state(AdminStates.in_conversation)
                await state.update_data(conversation_user_id=user_id)

                await callback.answer("Диалог начат")
                await callback.message.answer(f"✅ Диалог с пользователем {user_id} начат")
                logger.info("✅ Диалог начат через кнопку, админ переключен в in_conversation")
            else:
                await callback.answer("Не удалось начать диалог")

        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка обработки callback {data}: {e}")
        await callback.answer("Ошибка")


@admin_router.message(
    StateFilter(AdminStates.admin_mode, AdminStates.in_conversation),
    F.text,
    lambda message: not message.text.startswith("/"),
)
async def admin_message_handler(message: Message, state: FSMContext):
    """Обработчик сообщений админов"""
    if not ctx.admin_manager.is_admin(message.from_user.id):
        return

    try:
        logger.info(f"👑 Получено сообщение от админа {message.from_user.id}: '{message.text}'")

        # Пытаемся обработать как админское сообщение
        handled = await ctx.conversation_manager.route_admin_message(message, state)

        if handled:
            logger.info("✅ Сообщение админа обработано и переслано пользователю")
        else:
            # Не админское сообщение - показываем справку
            logger.info("❌ Сообщение админа не обработано, показываем справку")
            await message.answer(
                """
👑 **Режим администратора**

Доступные команды:
• `/stats` - статистика воронки
• `/dashboard` - ссылка на дашборд аналитики
• `/history user_id` - история пользователя
• `/chat user_id` - начать диалог
• `/chats` - активные диалоги
• `/stop` - завершить диалог
• `/admin` - переключить режим
• `/cancel` - отменить текущее действие

📅 **Управление событиями:**
• `/create_event` - создать новое событие
• `/list_events` - список активных событий
• `/cancel_event название` - отменить событие
• `/edit_event` - редактировать событие

💡 Если вы в диалоге с пользователем, просто напишите сообщение - оно будет переслано пользователю.
""",
                parse_mode="Markdown",
            )

    except Exception as e:
        logger.error(f"Ошибка обработки сообщения админа: {e}")
        await message.answer("❌ Ошибка обработки команды")
