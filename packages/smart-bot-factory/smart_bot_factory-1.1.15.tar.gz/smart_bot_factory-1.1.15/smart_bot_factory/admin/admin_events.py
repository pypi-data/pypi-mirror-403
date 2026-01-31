# Обработчики для создания админских событий

import json
import logging
import os
from datetime import datetime, timezone

import pytz
from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from aiogram_media_group import media_group_handler
from dateutil.relativedelta import relativedelta

from telegramify_markdown import standardize

from ..handlers.constants import MOSCOW_TZ
from ..ui.aiogram_calendar import SimpleCalendar, SimpleCalendarCallback
from ..utils.context import ctx
from .states import AdminStates
from .admin_events_utils import (
    generate_file_id,
    ensure_temp_dir,
    get_file_size_from_message,
    validate_file_count,
    validate_total_size,
    download_and_save_file,
    validate_and_process_video,
    download_photo_from_message,
    format_event_time_display,
    create_confirmation_keyboard,
    create_media_group_from_files,
    send_media_group_with_fallback,
    send_additional_files_grouped,
    format_files_info_message,
    cleanup_temp_files
)

logger = logging.getLogger(__name__)

# Создаем роутер для админских событий
admin_events_router = Router()


@admin_events_router.message(Command(commands=["создать_событие", "create_event"]))
async def create_event_start(message: Message, state: FSMContext):
    """Начало создания события"""
    if not ctx.admin_manager.is_admin(message.from_user.id):
        return

    await state.set_state(AdminStates.create_event_name)

    await message.answer(
        "📝 **Введите название события**\n\n" "💡 _По этому названию вы сможете:\n" "• Найти событие в списке\n" "• Отменить его при необходимости_",
        parse_mode="Markdown",
    )


@admin_events_router.message(AdminStates.create_event_name, ~F.text.startswith("/"))
async def process_event_name(message: Message, state: FSMContext):
    """Обработка названия события"""
    event_name = message.text.strip() if message.text else ""

    if not event_name:
        await message.answer("❌ Название не может быть пустым. Попробуйте еще раз:")
        return

    # Проверяем уникальность названия (исключая отменённые и удалённые события)
    name_exists = await ctx.supabase_client.check_event_name_exists(event_name)

    if name_exists:
        await message.answer(
            f"⚠️ **Событие с названием «{event_name}» уже существует!**\n\n"
            f"Название события должно быть уникальным. Пожалуйста, выберите другое название.\n\n"
            f"💡 _Вы можете использовать это же название только для отменённых или удалённых событий._",
            parse_mode="Markdown",
        )
        return

    # Сохраняем название
    await state.update_data(event_name=event_name)

    # Устанавливаем состояние для обработки выбора времени
    await state.set_state(AdminStates.create_event_date)

    # Создаем клавиатуру с выбором времени
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🚀 Запустить сразу", callback_data="timing:immediate"),
                InlineKeyboardButton(text="📅 Выбрать время", callback_data="timing:scheduled"),
            ]
        ]
    )

    await message.answer(f"✅ Название события: **{event_name}**\n\n" "🕒 Когда запустить событие?", reply_markup=keyboard, parse_mode="Markdown")


@admin_events_router.callback_query(F.data.startswith("timing:"), StateFilter(AdminStates.create_event_date))
async def process_event_timing(callback_query: CallbackQuery, state: FSMContext):
    """Обработка выбора времени запуска события"""
    action = callback_query.data.split(":", 1)[1]

    if action == "immediate":
        # Устанавливаем текущее время
        now = datetime.now(MOSCOW_TZ)
        await state.update_data(event_date=now.strftime("%Y-%m-%d"), event_time=now.strftime("%H:%M"), is_immediate=True)
        # Переходим к выбору сегмента
        await state.set_state(AdminStates.create_event_segment)

        # Получаем все доступные сегменты
        segments = await ctx.supabase_client.get_all_segments()

        # Создаем клавиатуру с сегментами
        keyboard = []
        keyboard.append([InlineKeyboardButton(text="📢 Отправить всем", callback_data="segment:all")])
        if segments:
            for i in range(0, len(segments), 2):
                row = [InlineKeyboardButton(text=f"👥 {segments[i]}", callback_data=f"segment:{segments[i]}")]
                if i + 1 < len(segments):
                    row.append(InlineKeyboardButton(text=f"👥 {segments[i+1]}", callback_data=f"segment:{segments[i+1]}"))
                keyboard.append(row)

        markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        await callback_query.message.edit_text(
            f"✅ Время: **Сейчас**\n\n" f"👥 Выберите сегмент пользователей для отправки:\n" f"_(Найдено сегментов: {len(segments)})_",
            reply_markup=markup,
            parse_mode="Markdown",
        )

    else:  # scheduled
        await state.set_state(AdminStates.create_event_date)
        # Показываем календарь для выбора даты
        calendar = SimpleCalendar(locale="ru", today_btn="Сегодня", cancel_btn="Отмена")
        # Ограничиваем выбор датами от вчера до +12 месяцев (чтобы сегодня был доступен)
        calendar.set_dates_range(
            datetime.now() + relativedelta(days=-1),
            datetime.now() + relativedelta(months=+12),
        )
        calendar_markup = await calendar.start_calendar()

        await callback_query.message.edit_text("📅 Выберите дату отправки:", reply_markup=calendar_markup, parse_mode="Markdown")


@admin_events_router.callback_query(SimpleCalendarCallback.filter(), AdminStates.create_event_date)
async def process_event_date(callback_query: CallbackQuery, callback_data: SimpleCalendarCallback, state: FSMContext):
    """Обработка выбора даты"""
    calendar = SimpleCalendar(locale="ru", cancel_btn="Отмена", today_btn="Сегодня")

    # Ограничиваем выбор датами от вчера до +12 месяцев (чтобы сегодня был доступен)
    calendar.set_dates_range(
        datetime.now() + relativedelta(days=-1),
        datetime.now() + relativedelta(months=+12),
    )
    selected, date = await calendar.process_selection(callback_query, callback_data)

    if selected == "cancel":
        # Нажата кнопка "Отмена"
        await state.clear()
        await callback_query.message.edit_text("❌ Создание события отменено", parse_mode="Markdown")
    elif selected:
        # Дата выбрана успешно (True или обычный выбор)
        await state.update_data(event_date=date.strftime("%Y-%m-%d"))
        await state.set_state(AdminStates.create_event_time)

        await callback_query.message.edit_text(
            f"✅ Дата: **{date.strftime('%d.%m.%Y')}**\n\n" "⏰ Введите время отправки в формате ЧЧ:ММ\n" "_(Например: 14:30)_",
            parse_mode="Markdown",
        )
    # Если selected is False/None - это навигация по календарю, ничего не делаем
    # Календарь сам обновится при навигации


@admin_events_router.message(AdminStates.create_event_time, ~F.text.startswith("/"))
async def process_event_time(message: Message, state: FSMContext):
    """Обработка времени события"""
    time_str = message.text.strip() if message.text else ""

    # Валидация формата времени
    try:
        datetime.strptime(time_str, "%H:%M").time()
    except ValueError:
        await message.answer(
            "❌ Неверный формат времени. Используйте формат HH:MM\n" "_(Например: 14:30)_",
            parse_mode="Markdown",
        )
        return

    # Сохраняем время
    await state.update_data(event_time=time_str)
    await state.set_state(AdminStates.create_event_segment)

    # Получаем все доступные сегменты
    segments = await ctx.supabase_client.get_all_segments()

    # Создаем клавиатуру с сегментами
    keyboard = []

    # Большая кнопка "Отправить всем" на два столбца
    keyboard.append([InlineKeyboardButton(text="📢 Отправить всем", callback_data="segment:all")])

    # Кнопки сегментов (по 2 в ряд)
    if segments:
        for i in range(0, len(segments), 2):
            row = []
            row.append(InlineKeyboardButton(text=f"👥 {segments[i]}", callback_data=f"segment:{segments[i]}"))
            if i + 1 < len(segments):
                row.append(
                    InlineKeyboardButton(
                        text=f"👥 {segments[i+1]}",
                        callback_data=f"segment:{segments[i+1]}",
                    )
                )
            keyboard.append(row)

    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

    await message.answer(
        f"✅ Время: **{time_str}**\n\n" f"👥 Выберите сегмент пользователей для отправки:\n" f"_(Найдено сегментов: {len(segments)})_",
        reply_markup=markup,
        parse_mode="Markdown",
    )


@admin_events_router.callback_query(F.data.startswith("segment:"), AdminStates.create_event_segment)
async def process_event_segment(callback_query: CallbackQuery, state: FSMContext):
    """Обработка выбора сегмента"""
    segment_data = callback_query.data.split(":", 1)[1]

    # segment_data = "all" или название сегмента
    segment_name = None if segment_data == "all" else segment_data
    segment_display = "Все пользователи" if segment_data == "all" else segment_data

    # Сохраняем сегмент
    await state.update_data(segment=segment_name, segment_display=segment_display)
    await state.set_state(AdminStates.create_event_message)

    await callback_query.message.edit_text(
        f"✅ Сегмент: **{segment_display}**\n\n"
        "💬 **Введите сообщение для пользователей**\n\n"
        "📸 _Вы можете прикрепить к сообщению **фото или видео** — они будут отправлены пользователям в том же порядке_\n\n"
        "📄 _Если нужно добавить **PDF или другие документы**, вы сможете это сделать на следующем шаге_",
        parse_mode="Markdown",
    )


@admin_events_router.message(
    AdminStates.create_event_message,
    F.media_group_id,
    F.content_type.in_({"photo", "video"}),
)
@media_group_handler
async def handle_album(messages: list[Message], state: FSMContext):
    """Обработка альбома фотографий/видео"""
    if not messages:
        return

    # Берем текст из первого сообщения с подписью
    event_message = next((msg.caption for msg in messages if msg.caption), None)
    if not event_message:
        await messages[0].answer(
            "❌ **Добавьте подпись к альбому**\n\n" "💡 _Отправьте альбом заново с текстом сообщения в подписи к любой фотографии_",
            parse_mode="Markdown",
        )
        return

    # Сохраняем сообщение
    await state.update_data(event_message=event_message)

    # Показываем сообщение о начале загрузки
    await messages[0].answer(
        "📸 **Загружаю файлы...**\n\n" "💡 _Дождитесь загрузки всех файлов из альбома_",
        parse_mode="Markdown",
    )

    # Сохраняем все файлы
    ensure_temp_dir()

    data = await state.get_data()
    files = data.get("files", [])

    for i, message in enumerate(messages, 1):
        try:
            file_info = None
            
            if message.photo:
                file_info = await download_photo_from_message(message, order=i)
            elif message.video:
                file_info = await validate_and_process_video(message, files, messages[0])
            
            if file_info:
                file_info.update({
                    "stage": "with_message",
                    "has_caption": bool(message.caption),
                    "order": i,
                })
                files.append(file_info)
            
            # Показываем прогресс каждые 5 файлов
            if i % 5 == 0:
                await messages[0].answer(f"📸 Загружено файлов: {i}/{len(messages)}", parse_mode="Markdown")

        except Exception as e:
            logger.error(f"❌ Ошибка загрузки файла {i}: {e}")
            continue

    # Сохраняем файлы
    await state.update_data(files=files)

    # Переходим к следующему этапу
    await state.set_state(AdminStates.create_event_files)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="➡️ Продолжить без файлов", callback_data="files:skip")]])

    await messages[0].answer(
        f"✅ **Сообщение и {len(files)} файлов сохранены!**\n\n"
        "📎 **Дополнительные файлы**\n\n"
        "Теперь вы можете отправить:\n"
        "📄 PDF документы\n"
        "📁 Файлы любых форматов\n"
        "🎥 Дополнительные видео\n"
        "🖼 Дополнительные фото\n\n"
        "💡 _Можно отправить несколько файлов по очереди_\n\n"
        "Или нажмите кнопку, если дополнительных файлов нет:",
        reply_markup=keyboard,
        parse_mode="Markdown",
    )


@admin_events_router.message(AdminStates.create_event_message, F.text | F.photo | F.video | F.document | F.audio)
async def process_event_message(message: Message, state: FSMContext):
    """Обработка одиночного сообщения с текстом/фото/видео"""
    # Если это часть альбома - пропускаем, его обработает другой handler
    if message.media_group_id:
        return

    event_message = message.text or message.caption or ""

    # Проверяем текст
    if not event_message.strip():
        await message.answer("❌ Сообщение не может быть пустым. Попробуйте еще раз:")
        return
    
    # Сохраняем сообщение
    await state.update_data(event_message=event_message)

    # Если есть медиа, сохраняем его
    data = await state.get_data()
    files = data.get("files", [])

    if message.photo or message.video or message.document or message.audio:
        # Создаем временную папку
        ensure_temp_dir()

        if message.photo:
            file_info = await download_photo_from_message(message)
            if file_info:
                file_info.update({
                    "stage": "with_message",
                    "has_caption": bool(message.caption),
                })
                files.append(file_info)
                logger.info(f"Фото сохранено: {file_info['file_path']} (with_message)")

        elif message.video:
            file_info = await validate_and_process_video(message, files, message)
            if file_info:
                file_info.update({
                    "stage": "with_message",
                    "has_caption": bool(message.caption),
                })
                files.append(file_info)
                logger.info(f"Видео сохранено: {file_info['file_path']} (with_message)")
            else:
                return  # Ошибка валидации, уже отправлено сообщение
        
        elif message.document:
            # Обрабатываем документ
            file_info = await download_and_save_file(message, "document")
            if file_info:
                file_info.update({
                    "stage": "with_message",
                    "has_caption": bool(message.caption),
                })
                files.append(file_info)
                logger.info(f"Документ сохранен: {file_info['file_path']} (with_message)")
        
        elif message.audio:
            # Обрабатываем аудио (сохраняем как document для единообразия)
            file_info = await download_and_save_file(message, "audio")
            if file_info:
                file_info.update({
                    "stage": "with_message",
                    "has_caption": bool(message.caption),
                    "type": "document",  # Аудио сохраняем как document для отправки
                })
                files.append(file_info)
                logger.info(f"Аудио сохранено: {file_info['file_path']} (with_message)")

    await state.update_data(files=files)

    # Переходим к добавлению файлов
    await state.set_state(AdminStates.create_event_files)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="➡️ Продолжить без файлов", callback_data="files:skip")]])

    await message.answer(
        "✅ **Сообщение сохранено!**\n\n"
        "📎 **Дополнительные файлы**\n\n"
        "Теперь вы можете отправить:\n"
        "📄 PDF документы\n"
        "📁 Файлы любых форматов\n"
        "🎥 Дополнительные видео\n"
        "🖼 Дополнительные фото\n\n"
        "💡 _Можно отправить несколько файлов по очереди_\n\n"
        "Или нажмите кнопку, если дополнительных файлов нет:",
        reply_markup=keyboard,
        parse_mode="Markdown",
    )


@admin_events_router.message(
    AdminStates.create_event_files,
    F.media_group_id,
    F.content_type.in_({"photo", "video"}),
)
@media_group_handler
async def handle_additional_album(messages: list[Message], state: FSMContext):
    """Обработка альбома фотографий/видео для дополнительных файлов"""
    if not messages:
        return

    await messages[0].answer(
        "📸 **Загружаю файлы из альбома...**\n\n"
        "💡 _Дождитесь загрузки всех файлов из альбома_",
        parse_mode="Markdown",
    )

    from .admin_events_utils import (
        get_max_order_for_stage,
        generate_group_id,
        save_media_group_files,
    )

    ensure_temp_dir()

    data = await state.get_data()
    files = data.get("files", [])

    max_order = get_max_order_for_stage(files, "after_message")
    group_id = generate_group_id()

    files = await save_media_group_files(
        ctx.bot, messages, files, "after_message", max_order, group_id
    )

    for i in range(5, len(messages) + 1, 5):
        await messages[0].answer(
            f"📸 Загружено файлов из альбома: {i}/{len(messages)}",
            parse_mode="Markdown"
        )

    await state.update_data(files=files)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="✅ Завершить добавление файлов", callback_data="files:done")]]
    )

    await messages[0].answer(
        f"✅ **Альбом из {len(messages)} файлов добавлен (всего: {len(files)})**\n\n"
        "Отправьте еще файлы или нажмите кнопку для завершения:",
        reply_markup=keyboard,
        parse_mode="Markdown",
    )


@admin_events_router.message(AdminStates.create_event_files, F.document | F.photo | F.video | F.audio)
async def process_event_files(message: Message, state: FSMContext):
    """Обработка файлов для события"""
    # Если это часть альбома - пропускаем, его обработает другой handler
    if message.media_group_id:
        return
    
    data = await state.get_data()
    files = data.get("files", [])

    # Проверка количества файлов
    if not await validate_file_count(files, message):
        return

    # Получаем размер и тип нового файла
    new_file_size, file_type = get_file_size_from_message(message)
    
    if file_type is None:
        return  # Неизвестный тип файла

    # Проверка общего размера файлов (только для документов и видео)
    if not await validate_total_size(files, new_file_size, file_type, message):
        return

    # Определяем порядок для одиночного файла
    existing_after_files = [f for f in files if f.get("stage") == "after_message"]
    max_order = max([f.get("order", 0) for f in existing_after_files], default=0)
    order = max_order + 1

    # Скачиваем и сохраняем файл
    file_info = await download_and_save_file(message, file_type)
    if file_info is None:
        await message.answer("❌ Ошибка при загрузке файла")
        return

    # Добавляем order и stage
    file_info.update({
        "stage": "after_message",
        "order": order,
    })

    # Добавляем файл в список
    files.append(file_info)
    await state.update_data(files=files)

    # Отправляем сообщение с информацией о файлах
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="✅ Завершить добавление файлов", callback_data="files:done")]]
    )
    
    await message.answer(
        format_files_info_message(files),
        reply_markup=keyboard,
    )


@admin_events_router.callback_query(F.data.startswith("files:"), AdminStates.create_event_files)
async def process_files_action(callback_query: CallbackQuery, state: FSMContext):
    """Обработка действий с файлами"""
    action = callback_query.data.split(":", 1)[1]

    data = await state.get_data()
    files = data.get("files", [])

    if action == "skip" and not files:
        # Если файлов нет и нажали "Продолжить без файлов" - очищаем
        files = []
        await state.update_data(files=files)
    elif action == "skip":
        # Если файлы уже есть - оставляем их
        logger.info(f"Продолжаем с {len(files)} существующими файлами")

    # Переход к подтверждению
    await state.set_state(AdminStates.create_event_confirm)

    # Отправляем сообщение с подтверждением
    time_display = format_event_time_display(data)
    summary = (
        f"📋 **Подтверждение создания события**\n\n"
        f"📝 Название: **{data.get('event_name')}**\n"
        f"📅 Время запуска: **{time_display}**\n"
        f"👥 Сегмент: **{data.get('segment_display')}**\n"
        f"📎 Файлов: **{len(files)}**\n\n"
        "Подтвердите создание события:"
    )

    await callback_query.message.edit_text(summary, reply_markup=create_confirmation_keyboard(), parse_mode="Markdown")


@admin_events_router.callback_query(F.data == "preview:show", AdminStates.create_event_confirm)
async def show_event_preview(callback_query: CallbackQuery, state: FSMContext):
    """Показываем предпросмотр сообщения"""
    data = await state.get_data()
    files = data.get("files", [])
    event_message = standardize(data.get("event_message", "")) # стандартизируем текст сообщения для MarkdownV2
    
    await callback_query.message.delete()

    # Разделяем файлы
    files_with_msg = [f for f in files if f.get("stage") == "with_message"]
    files_after = [f for f in files if f.get("stage") == "after_message"]

    # Отправляем основное сообщение с медиа
    if files_with_msg:
        media_group = create_media_group_from_files(files_with_msg, event_message)
        if media_group and isinstance(callback_query.message, Message):
            await send_media_group_with_fallback(
                ctx.bot,
                callback_query.message.chat.id,
                media_group,
                event_message,
                callback_query.message
            )
    elif event_message and isinstance(callback_query.message, Message):
        await callback_query.message.answer(event_message, parse_mode="MarkdownV2")

    # Отправляем дополнительные файлы с группировкой
    if files_after and isinstance(callback_query.message, Message):
        await send_additional_files_grouped(
            ctx.bot,
            files_after,
            callback_query.message.chat.id
        )

    # Отправляем сообщение с подтверждением
    time_display = format_event_time_display(data)
    summary = (
        f"📋 **Подтверждение создания события**\n\n"
        f"📝 Название: **{data.get('event_name')}**\n"
        f"📅 Время запуска: **{time_display}**\n"
        f"👥 Сегмент: **{data.get('segment_display')}**\n"
        f"📎 Файлов: **{len(files)}**\n\n"
        "Подтвердите создание события:"
    )

    await callback_query.message.answer(summary, reply_markup=create_confirmation_keyboard(), parse_mode="Markdown")


@admin_events_router.callback_query(F.data.startswith("confirm:"), AdminStates.create_event_confirm)
async def process_event_confirmation(callback_query: CallbackQuery, state: FSMContext):
    """Обработка подтверждения создания события"""
    action = callback_query.data.split(":", 1)[1]

    if action == "no":
        # Очищаем временные файлы
        await cleanup_temp_files(state)
        # Очищаем состояние
        await state.clear()
        await callback_query.message.edit_text("❌ Создание события отменено", parse_mode="Markdown")
        return

    # Получаем данные события
    data = await state.get_data()
    is_immediate = data.get("is_immediate", False)
    files = data.get("files", [])

    from aiogram.types import FSInputFile

    if is_immediate:
        # Для немедленной отправки - сразу рассылаем сообщения
        # Инициализируем segment до try блока, чтобы он был доступен в except
        segment = data.get("segment")
        try:
            # Показываем сообщение о начале рассылки
            await callback_query.message.edit_text("📤 **Выполняется рассылка...**", parse_mode="Markdown")

            # Получаем список пользователей для рассылки
            users = await ctx.supabase_client.get_users_by_segment(segment)
            
            # Фильтруем пользователей: исключаем админов, тестовых пользователей и пользователей с другим bot_id
            current_bot_id = ctx.supabase_client.bot_id
            filtered_users = []
            for user in users:
                # Исключаем админов
                if ctx.admin_manager.is_admin(user["telegram_id"]):
                    continue
                
                # Исключаем тестовых пользователей
                if user.get("username") == "test_user":
                    continue
                
                # Исключаем пользователей с другим bot_id
                if user.get("bot_id") != current_bot_id:
                    continue
                
                filtered_users.append(user)
            
            users = filtered_users
            total_users = len(users)
            sent_count = 0
            failed_count = 0
            message_ids = {}  # Словарь: {user_id: [message_id1, message_id2, ...]}

            # Группируем файлы по стадиям
            files_with_msg = [f for f in files if f.get("stage") == "with_message"]
            files_after = [f for f in files if f.get("stage") == "after_message"]

            # Определяем message_type для result_data
            message_type = "text"  # По умолчанию
            if files_with_msg:
                sorted_files = sorted(files_with_msg, key=lambda x: x.get("order", 0))
                if len(sorted_files) == 1:
                    # Один файл - тип файла
                    file_info = sorted_files[0]
                    message_type = file_info.get("type", "document")
                else:
                    # Несколько файлов - медиагруппа
                    message_type = "media_group"

            # Отправляем сообщения каждому пользователю
            for user in users:
                user_id = user["telegram_id"]
                user_message_ids = []  # Список message_id для этого пользователя
                
                try:
                    message = None  # Будет хранить результат отправки основного сообщения
                    # 1. Отправляем основное сообщение с медиа (если есть)
                    event_message = standardize(data.get("event_message", "")) # стандартизируем текст сообщения для MarkdownV2
                    
                    if files_with_msg:
                        sorted_files = sorted(files_with_msg, key=lambda x: x.get("order", 0))
                        
                        # Если только один файл - отправляем как обычный файл с caption
                        if len(sorted_files) == 1:
                            file_info = sorted_files[0]
                            file_path = file_info.get("file_path")
                            if not file_path or not os.path.exists(file_path):
                                logger.warning(f"⚠️ Файл не найден: {file_info.get('name')} ({file_path})")
                                if event_message:
                                    message = await ctx.bot.send_message(chat_id=user_id, text=event_message, parse_mode="MarkdownV2")
                                    if message and hasattr(message, 'message_id'):
                                        user_message_ids.append(message.message_id)
                            elif file_info["type"] == "photo":
                                try:
                                    message = await ctx.bot.send_photo(
                                        chat_id=user_id,
                                        photo=FSInputFile(file_path),
                                        caption=event_message,
                                        parse_mode="MarkdownV2",
                                    )
                                    if message and hasattr(message, 'message_id'):
                                        user_message_ids.append(message.message_id)
                                except Exception as e:
                                    error_msg = str(e)
                                    if "IMAGE_PROCESS_FAILED" in error_msg:
                                        logger.error(f"❌ Файл поврежден: {file_info.get('name')}, отправляем только текст")
                                        if event_message:
                                            message = await ctx.bot.send_message(chat_id=user_id, text=event_message, parse_mode="MarkdownV2")
                                            if message and hasattr(message, 'message_id'):
                                                user_message_ids.append(message.message_id)
                                    else:
                                        raise
                            elif file_info["type"] == "video":
                                message = await ctx.bot.send_video(
                                    chat_id=user_id,
                                    video=FSInputFile(file_path),
                                    caption=event_message,
                                    parse_mode="MarkdownV2",
                                )
                                if message and hasattr(message, 'message_id'):
                                    user_message_ids.append(message.message_id)
                            elif file_info["type"] == "document":
                                message = await ctx.bot.send_document(
                                    chat_id=user_id,
                                    document=FSInputFile(file_path),
                                    caption=event_message,
                                    parse_mode="MarkdownV2",
                                )
                                if message and hasattr(message, 'message_id'):
                                    user_message_ids.append(message.message_id)
                        else:
                            # Если несколько файлов - используем media_group
                            media_group = create_media_group_from_files(sorted_files, event_message)
                            if media_group:
                                messages = await ctx.bot.send_media_group(chat_id=user_id, media=media_group)
                                if messages:
                                    # Сохраняем все message_id из медиагруппы (первое - с текстом)
                                    for msg in messages:
                                        if hasattr(msg, 'message_id'):
                                            user_message_ids.append(msg.message_id)
                    elif event_message:
                        # Только текст
                        message = await ctx.bot.send_message(chat_id=user_id, text=event_message, parse_mode="MarkdownV2")
                        if message and hasattr(message, 'message_id'):
                            user_message_ids.append(message.message_id)

                    # 2. Отправляем дополнительные файлы с группировкой медиа-групп
                    if files_after:
                        additional_message_ids = await send_additional_files_grouped(
                            ctx.bot,
                            files_after,
                            user_id
                        )
                        user_message_ids.extend(additional_message_ids)

                    # Сохраняем список message_id для этого пользователя
                    if user_message_ids:
                        message_ids[user_id] = user_message_ids

                    sent_count += 1

                except Exception as e:
                    logger.error(f"❌ Ошибка отправки пользователю {user_id}: {e}")
                    failed_count += 1

            # Сохраняем событие в БД
            event_status = "success" if failed_count == 0 else "partial_success"
            event_name = data.get("event_name")
            if event_name:
                import json
                # Стандартизируем текст сообщения для сохранения
                standardized_message = standardize(data.get("event_message", ""))
                
                event = await ctx.supabase_client.save_admin_event(
                    event_name=event_name,
                    event_data={
                        "segment": segment,
                        "message": standardized_message,
                        "total_users": total_users,
                        "sent_success": sent_count,
                        "failed_count": failed_count,
                        "message_ids": message_ids,
                        "type": "immediate_event",
                        "admin_id": callback_query.from_user.id,
                        "execution_status": event_status,
                        "completed_at": datetime.now(timezone.utc).isoformat(),
                    },
                    scheduled_datetime=datetime.now(timezone.utc),
                )
                
                # Обновляем result_data для немедленных событий
                result_data = {
                    "success_count": sent_count,
                    "failed_count": failed_count,
                    "total_users": total_users,
                    "segment": segment or "Все пользователи",
                    "message": standardized_message,
                    "message_ids": message_ids,
                    "message_type": message_type,
                    "type": "immediate_event",
                    "execution_status": event_status,
                }
                
                update_data = {
                    "status": "completed",
                    "executed_at": datetime.now(timezone.utc).isoformat(),
                    "result_data": json.dumps(result_data, ensure_ascii=False),
                }
                
                query = ctx.supabase_client.client.table("scheduled_events").update(update_data).eq("id", event["id"]).eq("bot_id", ctx.supabase_client.bot_id)
                query.execute()
                
                logger.info(f"✅ Обновлен result_data для немедленного события {event['id']}: message_ids={len(message_ids)} записей")

            # Показываем итоговое сообщение
            status = "✅" if failed_count == 0 else "⚠️"

            await callback_query.message.edit_text(
                f"{status} **Админское событие выполнено**\n\n"
                f"📝 Название: **{data.get('event_name')}**\n"
                f"👥 Сегмент: **{data.get('segment_display')}**\n\n"
                f"📊 Результат:\n"
                f"• Доставлено: **{sent_count}**\n"
                f"• Не доставлено: **{failed_count}**",
                parse_mode="Markdown",
            )

        except Exception as e:
            logger.error(f"❌ Ошибка массовой рассылки: {e}")

            # Сохраняем ошибку события в БД
            event_name = data.get("event_name")
            if event_name:
                await ctx.supabase_client.save_admin_event(
                    event_name=event_name,
                event_data={
                    "segment": segment,
                    "error": str(e),
                    "type": "immediate_event",
                    "admin_id": callback_query.from_user.id,
                    "execution_status": "error",
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                },
                scheduled_datetime=datetime.now(timezone.utc),
            )

            await callback_query.message.edit_text(
                f"❌ **Ошибка выполнения админского события**\n\n"
                f"📝 Название: **{data.get('event_name')}**\n"
                f"👥 Сегмент: **{data.get('segment_display')}**\n\n"
                f"Произошла техническая ошибка. Попробуйте позже.",
                parse_mode="Markdown",
            )

    else:
        # Для отложенного события - стандартная логика
        try:
            # Формируем datetime для планирования
            event_date = data.get("event_date")
            event_time = data.get("event_time")
            naive_datetime = datetime.strptime(f"{event_date} {event_time}", "%Y-%m-%d %H:%M")
            moscow_datetime = MOSCOW_TZ.localize(naive_datetime)
            utc_datetime = moscow_datetime.astimezone(pytz.UTC)

            # Создаем событие
            event_name = data.get("event_name")
            event_id = None
            if event_name:
                # Стандартизируем текст сообщения для сохранения
                standardized_message = standardize(data.get("event_message", ""))
                
                event = await ctx.supabase_client.save_admin_event(
                    event_name=event_name,
                    event_data={
                        "segment": data.get("segment"),
                        "message": standardized_message,
                        "files": [],
                    },
                    scheduled_datetime=utc_datetime,
                )
                event_id = event["id"]

            # Загружаем файлы в Storage
            uploaded_files = []
            if event_id:
                for file_info in files:
                    try:
                        with open(file_info["file_path"], "rb") as f:
                            file_bytes = f.read()
                        file_id = generate_file_id()
                        storage_info = await ctx.supabase_client.upload_event_file(
                            event_id=event_id,
                            file_data=file_bytes,
                            original_name=file_info["name"],
                            file_id=file_id,
                        )
                        uploaded_files.append(
                            {
                                "type": file_info["type"],
                                "storage_path": storage_info["storage_path"],
                                "original_name": file_info["name"],
                                "stage": file_info["stage"],
                                "has_caption": file_info.get("has_caption", False),
                                "order": file_info.get("order", 0),
                            }
                        )
                    except Exception as e:
                        logger.error(f"❌ Ошибка загрузки файла {file_info['name']}: {e}")
                        await ctx.supabase_client.delete_event_files(event_id)
                        raise

            # Обновляем событие с информацией о файлах
            import json
            # Стандартизируем текст сообщения для сохранения
            standardized_message = standardize(data.get("event_message", ""))
            
            event_data = {
                "segment": data.get("segment"),
                "message": standardized_message,
                "files": uploaded_files,
            }
            ctx.supabase_client.client.table("scheduled_events").update({"event_data": json.dumps(event_data, ensure_ascii=False)}).eq(
                "id", event_id
            ).execute()

        except Exception as e:
            logger.error(f"❌ Ошибка создания отложенного события: {e}")
            raise

    # Определяем time_display для обоих случаев (немедленных и отложенных)
    if is_immediate:
        time_display = "🔥 Прямо сейчас"
    else:
        event_date = data.get("event_date")
        event_time = data.get("event_time")
        naive_datetime = datetime.strptime(f"{event_date} {event_time}", "%Y-%m-%d %H:%M")
        moscow_datetime = MOSCOW_TZ.localize(naive_datetime)
        time_display = f"{moscow_datetime.strftime('%d.%m.%Y %H:%M')} (МСК)"

    await callback_query.message.edit_text(
        f"✅ **Событие успешно создано!**\n\n"
        f"📝 Название: `{data.get('event_name')}`\n"
        f"📅 Время запуска: **{time_display}**\n"
        f"👥 Сегмент: **{data.get('segment_display')}**\n\n"
        f"💡 _Нажмите на название для копирования_",
        parse_mode="Markdown",
    )

    # Очищаем временные файлы и состояние
    await cleanup_temp_files(state)
    await state.set_state(AdminStates.admin_mode)


@admin_events_router.message(Command(commands=["список_событий", "list_events"]))
async def list_events_command(message: Message, state: FSMContext):
    """Просмотр всех запланированных событий"""
    logger.debug(f"list_events_command вызван для пользователя {message.from_user.id}")
    logger.debug(f"admin_manager = {ctx.admin_manager is not None}, supabase_client = {ctx.supabase_client is not None}")

    if ctx.admin_manager is None:
        logger.error("❌ admin_manager is None в list_events_command")
        await message.answer("❌ Ошибка: admin_manager не инициализирован")
        return

    if ctx.supabase_client is None:
        logger.error("❌ supabase_client is None в list_events_command")
        await message.answer("❌ Ошибка: supabase_client не инициализирован")
        return

    if not ctx.admin_manager.is_admin(message.from_user.id):
        return

    try:
        # Получаем все pending события (незавершенные и неотмененные)
        events = await ctx.supabase_client.get_admin_events(status="pending")

        if not events:
            await message.answer(
                "📋 **Нет активных событий**\n\n" "Используйте `/create_event` для создания нового события",
                parse_mode="Markdown",
            )
            return

        # Формируем список событий в красивом формате
        text_parts = [f"📋 **Активные события** ({len(events)})\n"]

        for idx, event in enumerate(events, 1):
            event_name = event["event_type"]

            # Конвертируем UTC в московское время для отображения
            utc_time = datetime.fromisoformat(event["scheduled_at"].replace("Z", "+00:00"))
            moscow_time = utc_time.astimezone(MOSCOW_TZ)

            # Красивый формат с эмодзи и структурой
            text_parts.append(f"📌 **{idx}.** `{event_name}`\n" f"    🕐 {moscow_time.strftime('%d.%m.%Y в %H:%M')} МСК\n")

        text_parts.append("━━━━━━━━━━━━━━━━━━━━\n" "💡 _Нажмите на название для копирования_\n" "🗑️ Отменить: `/cancel_event название`")

        await message.answer("\n".join(text_parts), parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Ошибка получения событий: {e}")
        await message.answer(f"❌ Ошибка получения событий:\n`{str(e)}`", parse_mode="Markdown")


@admin_events_router.message(Command(commands=["отменить_событие", "cancel_event"]))
async def cancel_event_command(message: Message, state: FSMContext):
    """Отмена события по названию"""
    if not ctx.admin_manager.is_admin(message.from_user.id):
        return

    # Парсим название из команды
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "❌ Укажите название события:\n" "`/cancel_event название`\n\n" "Используйте /list_events для просмотра списка событий",
            parse_mode="Markdown",
        )
        return

    event_name = parts[1].strip()
    escaped_event_name = standardize(event_name)

    try:
        # Сначала получаем событие чтобы узнать его ID
        response = (
            ctx.supabase_client.client.table("scheduled_events")
            .select("id")
            .eq("event_type", event_name)
            .eq("event_category", "admin_event")
            .eq("status", "pending")
            .execute()
        )

        if response.data:
            event_id = response.data[0]["id"]

            # Удаляем файлы из Storage
            try:
                await ctx.supabase_client.delete_event_files(event_id)
            except Exception:
                pass  # Тихая очистка без логирования

            # Отмечаем событие как отмененное
            ctx.supabase_client.client.table("scheduled_events").update({"status": "cancelled"}).eq("id", event_id).execute()

            await message.answer(
                f"✅ Событие `{escaped_event_name}` отменено",
                parse_mode="Markdown",
            )
            logger.info(f"Отменено событие '{event_name}' (ID: {event_id})")
        else:
            await message.answer(
                f"❌ Активное событие с названием `{escaped_event_name}` не найдено\n\n" f"Используйте /list_events для просмотра списка активных событий",
                parse_mode="Markdown",
            )

    except Exception as e:
        logger.error(f"Ошибка удаления события: {e}")
        await message.answer(f"❌ Ошибка удаления события:\n`{str(e)}`", parse_mode="Markdown")
