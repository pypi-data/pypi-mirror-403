# Обработчики для редактирования админских событий

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

from ..utils.context import ctx
from .admin_events_utils import (
    MAX_CAPTION_LENGTH,
    MAX_TEXT_MESSAGE_LENGTH,
    RECENT_EVENTS_COUNT,
    check_edit_availability,
    create_action_keyboard,
    create_action_message_text,
    delete_user_messages,
    edit_user_messages,
    format_executed_time,
    format_time_remaining,
    get_message_from_data,
    get_message_type_limits,
    parse_json_data,
    truncate_text,
    update_event_message_data,
    validate_event_text,
)
from .states import AdminStates

logger = logging.getLogger(__name__)

admin_events_edit_router = Router()


@admin_events_edit_router.message(Command(commands=["cancel", "отмена"]))
async def cancel_handler(message: Message, state: FSMContext):
    """Отмена текущей операции"""
    await state.clear()
    await message.answer(
        "❌ Операция отменена",
        reply_markup=ReplyKeyboardRemove(),
    )


@admin_events_edit_router.message(Command(commands=["редактировать_событие", "edit_event"]))
async def edit_event_start(message: Message, state: FSMContext):
    """Начало редактирования события"""
    events = await ctx.supabase_client.get_admin_events(status="completed")
    
    events_sorted = sorted(
        events,
        key=lambda x: x.get("executed_at") or "",
        reverse=True
    )[:RECENT_EVENTS_COUNT]

    if not events_sorted:
        await message.answer(
            "📋 **Нет завершенных событий**\n\n"
            "Нет завершенных событий для редактирования.",
            parse_mode="Markdown",
        )
        return

    text_parts = [f"📋 **Последние {RECENT_EVENTS_COUNT} завершенных событий**\n\n"]
    
    keyboard_buttons = []
    for idx, event in enumerate(events_sorted, 1):
        event_name = event.get("event_type", "Без названия")
        time_str = format_executed_time(event.get("executed_at", ""))
        text_parts.append(f"**{idx}.** `{event_name}`\n    🕐 {time_str}\n")
        
        # Распределяем кнопки: 2, 2, 1
        if idx <= 2:
            # Первые две кнопки в одной строке
            if idx == 1:
                keyboard_buttons.append([KeyboardButton(text=event_name)])
            else:
                keyboard_buttons[-1].append(KeyboardButton(text=event_name))
        elif idx <= 4:
            # Следующие две кнопки в одной строке
            if idx == 3:
                keyboard_buttons.append([KeyboardButton(text=event_name)])
            else:
                keyboard_buttons[-1].append(KeyboardButton(text=event_name))
        else:
            # Последняя кнопка отдельно
            keyboard_buttons.append([KeyboardButton(text=event_name)])

    text_parts.append(
        "━━━━━━━━━━━━━━━━━━━━\n"
        "💡 **Выберите событие из списка ниже или введите название любого другого события**\n"
        "_(Можно нажать на кнопку или написать название вручную)_"
    )

    keyboard = ReplyKeyboardMarkup(keyboard=keyboard_buttons, resize_keyboard=True, one_time_keyboard=True)

    await state.set_state(AdminStates.edit_event_select)
    await message.answer("\n".join(text_parts), parse_mode="Markdown", reply_markup=keyboard)




@admin_events_edit_router.message(AdminStates.edit_event_select, ~F.text.startswith("/"))
async def process_edit_event_name(message: Message, state: FSMContext):
    """Обработка выбора события для редактирования"""
    event_name = message.text.strip() if message.text else ""

    if not event_name:
        await message.answer("❌ Название не может быть пустым. Попробуйте еще раз:")
        return

    # Проверяем, не нажата ли кнопка "Отмена"
    if event_name.lower() in ["❌ отмена", "отмена", "cancel"]:
        await message.answer(
            "❌ Редактирование события отменено",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()
        return

    await _process_event_selection(message, state, event_name)


async def _process_event_selection(message: Message, state: FSMContext, event_name: str):
    """Обработка выбранного события"""
    response = (
        ctx.supabase_client.client.table("scheduled_events")
        .select("*")
        .eq("event_type", event_name)
        .eq("event_category", "admin_event")
        .eq("status", "completed")
        .eq("bot_id", ctx.supabase_client.bot_id)
    )
    
    result = response.execute()

    if not result.data:
        await message.answer(
            f"❌ **Завершенное событие с названием `{event_name}` не найдено**\n\n"
            "Проверьте правильность названия и убедитесь, что событие завершено.",
            parse_mode="Markdown",
        )
        return

    event = result.data[0]
    executed_at = event.get("executed_at", "")
    
    can_edit, time_remaining = check_edit_availability(executed_at)

    await state.update_data(
        event_id=event["id"],
        event_name=event_name,
        event_data=event.get("event_data"),
        result_data=event.get("result_data"),
        executed_at=executed_at
    )
    await state.set_state(AdminStates.edit_event_action)

    keyboard_buttons = create_action_keyboard(can_edit)
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    message_text = create_action_message_text(event_name, can_edit, time_remaining)

    await message.answer(
        message_text,
        reply_markup=keyboard,
        parse_mode="Markdown",
    )


@admin_events_edit_router.callback_query(F.data.startswith("edit_action:"), AdminStates.edit_event_action)
async def process_edit_action(callback_query: CallbackQuery, state: FSMContext):
    """Обработка выбора действия (редактировать/удалить)"""
    action = callback_query.data.split(":", 1)[1]
    data = await state.get_data()
    event_name = data.get("event_name") or ""

    if action == "delete":
        await _handle_delete_action(callback_query, state, data, event_name)
    elif action == "message":
        await _handle_edit_message_action(callback_query, state, data, event_name)
    elif action == "cancel":
        # Отмена - удаляем сообщение и очищаем state
        await callback_query.message.delete()
        await state.clear()
        logger.info(f"Отмена редактирования события '{event_name}'")


async def _handle_delete_action(callback_query: CallbackQuery, state: FSMContext, data: dict, event_name: str):
    """Обработка удаления события - показываем подтверждение"""
    event_id = data.get("event_id")
    result_data = parse_json_data(data.get("result_data"))
    message_ids = result_data.get("message_ids")

    if not message_ids:
        await callback_query.message.delete()
        await callback_query.message.answer(
            f"❌ **Невозможно удалить событие**\n\n"
            f"Событие `{event_name}` не содержит данных о сообщениях.\n\n"
            "ℹ️ _К сожалению, сообщения, связанные с этим событием, не могут быть удалены "
            "(отсутствуют данные о сообщениях). Событие не было удалено._",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove()
        )
        logger.warning(f"Попытка удаления события '{event_name}' (ID: {event_id}) без данных о сообщениях - событие не удалено")
        await state.clear()
        return

    # Подсчитываем количество сообщений для удаления
    total_messages = sum(len(msg_ids) for msg_ids in message_ids.values()) if message_ids else 0
    total_users = len(message_ids) if message_ids else 0

    # Показываем подтверждение удаления
    await state.set_state(AdminStates.edit_event_delete_confirm)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить удаление", callback_data="confirm_delete:yes"),
            InlineKeyboardButton(text="❌ Отменить", callback_data="confirm_delete:no"),
        ]
    ])

    await callback_query.message.edit_text(
        f"⚠️ **Подтверждение удаления события**\n\n"
        f"📝 **Событие:** `{event_name}`\n\n"
        f"📊 **Событие будет удалено у {total_users} пользователей**\n\n"
        f"⚠️ **ВНИМАНИЕ!**\n"
        f"После удаления сообщения **нельзя вернуть**.\n"
        f"Чтобы отправить сообщения снова, нужно создать новое событие.\n\n"
        f"Вы уверены, что хотите удалить это событие?",
        parse_mode="Markdown",
        reply_markup=keyboard
    )


@admin_events_edit_router.callback_query(F.data.startswith("confirm_delete:"), AdminStates.edit_event_delete_confirm)
async def process_delete_confirmation(callback_query: CallbackQuery, state: FSMContext):
    """Обработка подтверждения удаления события"""
    action = callback_query.data.split(":", 1)[1]
    data = await state.get_data()
    event_name = data.get("event_name", "")
    
    if action == "no":
        # Отмена удаления - возвращаемся к выбору действия
        await state.set_state(AdminStates.edit_event_action)
        
        can_edit, time_remaining = check_edit_availability(data.get("executed_at", ""))
        keyboard_buttons = create_action_keyboard(can_edit)
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        message_text = create_action_message_text(event_name, can_edit, time_remaining)
        
        await callback_query.message.edit_text(
            message_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        return
    
    # Подтверждение удаления - выполняем удаление
    event_id = data.get("event_id")
    result_data = parse_json_data(data.get("result_data"))
    message_ids = result_data.get("message_ids")

    deleted_count, failed_count = await delete_user_messages(message_ids)

    try:
        await ctx.supabase_client.delete_event_files(str(event_id))
    except Exception:
        pass

    query = ctx.supabase_client.client.table("scheduled_events").update({"status": "removed"}).eq("id", event_id).eq("bot_id", ctx.supabase_client.bot_id)
    query.execute()

    await callback_query.message.delete()
    await callback_query.message.answer(
        f"✅ **Событие успешно удалено**\n\n"
        f"📝 Событие: `{event_name}`\n"
        f"🗑️ Все сообщения, связанные с этим событием у пользователей, удалены\n\n"
        f"ℹ️ _Удаленные сообщения нельзя вернуть. Для отправки сообщений снова создайте новое событие._",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    logger.info(f"Удалено завершенное событие '{event_name}' (ID: {event_id}): статус изменен на 'removed', {deleted_count} сообщений удалено, {failed_count} ошибок")
    
    await state.clear()


async def _handle_edit_message_action(callback_query: CallbackQuery, state: FSMContext, data: dict, event_name: str):
    """Обработка редактирования сообщения"""
    executed_at = data.get("executed_at", "")
    can_edit, _ = check_edit_availability(executed_at)

    if not can_edit:
        await callback_query.message.edit_text(
            f"❌ **Редактирование недоступно**\n\n"
            f"Событие `{event_name}` старше 48 часов и не может быть отредактировано.\n\n"
            "💡 _Вы можете только удалить событие._",
            parse_mode="Markdown",
        )
        await state.clear()
        return

    result_data = parse_json_data(data.get("result_data"))
    message_ids = result_data.get("message_ids")

    if not message_ids:
        await callback_query.message.edit_text(
            f"❌ **Невозможно отредактировать событие**\n\n"
            f"Событие `{event_name}` не содержит данных о сообщениях.\n\n"
            "💡 _Это может быть старое событие, созданное до добавления функции редактирования._",
            parse_mode="Markdown",
        )
        await state.clear()
        return

    await state.set_state(AdminStates.edit_event_message)

    current_message = get_message_from_data(data.get("result_data"), data.get("event_data"))
    
    # Обрезаем длинный текст для отображения
    display_message = truncate_text(current_message, max_length=2000) if current_message else ""

    # Создаем клавиатуру с кнопкой "Назад"
    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="edit_message:back")]
    ])

    if current_message:
        await callback_query.message.edit_text(
            f"✏️ **Редактирование события:** `{event_name}`\n\n"
            f"📝 **Текущий текст:**\n{display_message}\n\n"
            "💬 **На какой текст хотите заменить?**\n"
            "Пришлите текст, на который нужно заменить:",
            parse_mode="Markdown",
            reply_markup=back_keyboard
        )
    else:
        await callback_query.message.edit_text(
            f"✏️ **Редактирование события:** `{event_name}`\n\n"
            "💬 **Пришлите текст, на который нужно заменить:**",
            parse_mode="Markdown",
            reply_markup=back_keyboard
        )


@admin_events_edit_router.callback_query(F.data == "edit_message:back", AdminStates.edit_event_message)
async def back_to_action_selection(callback_query: CallbackQuery, state: FSMContext):
    """Возврат к выбору действия"""
    data = await state.get_data()
    event_name = data.get("event_name", "")
    
    await state.set_state(AdminStates.edit_event_action)
    
    can_edit, time_remaining = check_edit_availability(data.get("executed_at", ""))
    keyboard_buttons = create_action_keyboard(can_edit)
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    message_text = create_action_message_text(event_name, can_edit, time_remaining)
    
    await callback_query.message.edit_text(
        message_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@admin_events_edit_router.message(AdminStates.edit_event_message, ~F.text.startswith("/"))
async def process_edit_message(message: Message, state: FSMContext):
    """Обработка нового сообщения для события - показываем предпросмотр"""
    new_message = message.text.strip() if message.text else ""

    if not new_message:
        await message.answer("❌ Сообщение не может быть пустым. Попробуйте еще раз:", reply_markup=ReplyKeyboardRemove())
        return

    data = await state.get_data()
    event_id = data.get("event_id", "")
    event_name = data.get("event_name", "")
    result_data = parse_json_data(data.get("result_data"))
    
    message_ids = result_data.get("message_ids")
    
    if not message_ids:
        await message.answer(
            "❌ **Невозможно отредактировать событие**\n\n"
            "Событие не содержит данных о сообщениях.",
            parse_mode="Markdown",
        )
        await state.clear()
        return

    message_type = result_data.get("message_type", "text")
    
    # Проверяем размер текста
    max_length, limit_name, message_type_name = get_message_type_limits(message_type)
    if len(new_message) > max_length:
        await message.answer(
            f"❌ **Текст слишком длинный**\n\n"
            f"Максимальная длина {limit_name}: **{max_length}** символов\n"
            f"Ваш текст: **{len(new_message)}** символов\n\n"
            f"Пожалуйста, сократите текст до {max_length} символов:",
            parse_mode="Markdown",
        )
        return
    
    # Проверяем корректность Markdown
    if not await validate_event_text(message, new_message):
        return
    
    # Сохраняем новый текст в state для предпросмотра
    await state.update_data(new_message=new_message)
    
    # Показываем предпросмотр
    old_message = get_message_from_data(data.get("result_data"), data.get("event_data"))
    old_message_display = truncate_text(old_message, max_length=500, suffix="...") if old_message else "(текст отсутствовал)"
    new_message_display = truncate_text(new_message, max_length=500, suffix="...")
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_edit:yes"),
            InlineKeyboardButton(text="❌ Отменить", callback_data="confirm_edit:no"),
        ]
    ])
    
    await message.answer(
        f"👁️ **Предпросмотр изменения**\n\n"
        f"📝 Событие: `{event_name}`\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📝 **Было:**\n`{old_message_display}`\n\n"
        f"📝 **Стало:**\n`{new_message_display}`\n\n"
        f"Подтвердите изменение:",
        parse_mode="Markdown",
        reply_markup=keyboard
    )


@admin_events_edit_router.callback_query(F.data.startswith("confirm_edit:"), AdminStates.edit_event_message)
async def process_edit_confirmation(callback_query: CallbackQuery, state: FSMContext):
    """Обработка подтверждения редактирования"""
    action = callback_query.data.split(":", 1)[1]
    data = await state.get_data()
    event_id = data.get("event_id", "")
    event_name = data.get("event_name", "")
    new_message = data.get("new_message", "")
    
    if action == "no":
        # Отмена - возвращаемся к редактированию
        current_message = get_message_from_data(data.get("result_data"), data.get("event_data"))
        display_message = truncate_text(current_message, max_length=2000) if current_message else ""
        
        back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="edit_message:back")]
        ])
        
        if current_message:
            await callback_query.message.edit_text(
                f"✏️ **Редактирование события:** `{event_name}`\n\n"
                f"📝 **Текущий текст:**\n{display_message}\n\n"
                "💬 **На какой текст хотите заменить?**\n"
                "Пришлите текст, на который нужно заменить:",
                parse_mode="Markdown",
                reply_markup=back_keyboard
            )
        else:
            await callback_query.message.edit_text(
                f"✏️ **Редактирование события:** `{event_name}`\n\n"
                "💬 **Пришлите текст, на который нужно заменить:**",
                parse_mode="Markdown",
                reply_markup=back_keyboard
            )
        return
    
    # Подтверждение - выполняем редактирование
    result_data = parse_json_data(data.get("result_data"))
    message_ids = result_data.get("message_ids")
    message_type = result_data.get("message_type", "text")
    
    edited_count, failed_count = await edit_user_messages(message_ids, new_message, message_type)
    old_message = update_event_message_data(str(event_id), new_message)
    
    old_message_display = truncate_text(old_message, max_length=500, suffix="...") if old_message else "(текст отсутствовал)"
    new_message_display = truncate_text(new_message, max_length=500, suffix="...")
    
    if failed_count == 0:
        message_text = (
            f"✅ **Сообщение события `{event_name}` успешно изменено**"
        )
        await callback_query.message.edit_text(message_text, parse_mode="Markdown")
    else:
        await callback_query.message.edit_text(
            f"⚠️ **Сообщение изменено с ошибками**\n\n"
            f"📝 Событие: `{event_name}`\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📝 **Было:**\n`{old_message_display}`\n\n"
            f"📝 **Стало:**\n`{new_message_display}`\n\n"
            f"❌ Ошибок: **{failed_count}**",
            parse_mode="Markdown"
        )
    logger.info(f"Обновлено сообщение события '{event_name}' (ID: {event_id}): {edited_count} успешно, {failed_count} ошибок")
    
    await state.clear()