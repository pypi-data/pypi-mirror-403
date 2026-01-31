# Вспомогательные функции для работы с админскими событиями

import json
import logging
import os
import re
import shutil
import uuid
from datetime import datetime, timedelta, timezone

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from aiogram.fsm.context import FSMContext

from ..handlers.constants import MOSCOW_TZ
from ..utils.context import ctx

# Константы
TEMP_DIR = "temp_event_files"
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 МБ - максимум на один файл (ограничение Telegram)
MAX_TOTAL_SIZE = 200 * 1024 * 1024  # 200 МБ - общий размер всех файлов (документы + видео)
MAX_FILES_COUNT = 10
MAX_TEXT_MESSAGE_LENGTH = 4096  # Лимит для текстовых сообщений
MAX_CAPTION_LENGTH = 1024  # Лимит для подписей к медиа
EDIT_TIME_LIMIT_HOURS = 48  # Время редактирования событий
RECENT_EVENTS_COUNT = 5  # Количество последних событий для отображения
TEST_USERNAME = "test_user"  # Имя тестового пользователя

logger = logging.getLogger(__name__)


# ========== Утилиты для текста и ошибок ==========

def find_error_position(error_message: str, text: str) -> tuple[int, str] | None:
    """
    Находит позицию ошибки в тексте на основе byte offset из сообщения об ошибке Telegram.
    
    Returns:
        tuple[int, str] | None: (позиция_символа, контекст_вокруг) или None если не удалось определить
    """
    # Ищем byte offset в сообщении об ошибке
    # Пример: "Can't find end of the entity starting at byte offset 461"
    match = re.search(r"byte offset (\d+)", error_message, re.IGNORECASE)
    if not match:
        return None
    
    try:
        byte_offset = int(match.group(1))
        
        # Конвертируем byte offset в позицию символа
        text_bytes = text.encode("utf-8")
        if byte_offset >= len(text_bytes):
            byte_offset = len(text_bytes) - 1
        
        # Находим позицию символа, соответствующую этому byte offset
        problem_prefix_bytes = text_bytes[:byte_offset]
        char_position = len(problem_prefix_bytes.decode("utf-8", errors="ignore"))
        
        # Формируем контекст вокруг проблемного места (по 15 символов до и после)
        start = max(0, char_position - 15)
        end = min(len(text), char_position + 15)

        def is_word_char(ch: str) -> bool:
            # Считаем частью "слова" буквы/цифры/подчёркивание (чтобы числа тоже не резать)
            return ch.isalnum() or ch == "_"

        # Если попали в середину слова — расширяем до границ слова,
        # чтобы "последнее слово/число" в контексте не обрезалось.
        while start > 0 and start < len(text) and is_word_char(text[start]) and is_word_char(text[start - 1]):
            start -= 1
        while end < len(text) and end > 0 and is_word_char(text[end - 1]) and is_word_char(text[end]):
            end += 1

        context = text[start:end]
        
        # Показываем место проблемы стрелкой
        relative_pos = char_position - start
        marker = " " * relative_pos + "↑"
        
        return char_position, f"{context}\n{marker}"
    except Exception as e:
        logger.error(f"Ошибка при определении позиции: {e}")
        return None


async def validate_event_text(message: Message, event_message: str) -> bool:
    """
    Проверяет текст события на корректность Markdown-разметки.
    
    Возвращает:
        True – если текст прошёл проверку,
        False – если есть ошибка (и пользователю отправлено объяснение).
    """
    if not event_message:
        return True

    try:
        # Пробуем отправить тот же текст в том же чате,
        # чтобы проверить корректность Markdown-разметки
        test_message = await message.answer(
            event_message,
            parse_mode="Markdown",
        )
        # Сразу удаляем тестовое сообщение, чтобы не дублировать текст для пользователя
        await test_message.delete()
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка парсинга текста сообщения: {e}")

        # Пытаемся определить место ошибки
        error_msg = str(e)
        error_info = find_error_position(error_msg, event_message)

        error_text = "❌ **Ошибка форматирования текста**\n\n"
        error_text += "Текст сообщения содержит некорректные символы для Markdown.\n\n"

        if error_info:
            _, context = error_info
            error_text += "📍 **Возможно, ошибка находится в этом месте:**\n\n"
            error_text += f"```\n{context}\n```\n\n"

        error_text += (
            "💡 **Попробуйте:**\n"
            "• Убрать специальные символы: `_`, `*`, `[`, `]`, `(`, `)`, `~`, `` ` ``, `>`, `#`, `+`, `-`, `=`, `|`, `{`, `}`, `.`, `!`\n"
            "• Или экранировать их обратным слэшем: `\\`\n\n"
            "Пожалуйста, перепишите сообщение:"
        )

        await message.answer(error_text, parse_mode="Markdown")
        return False


# ========== Утилиты для работы с файлами ==========

def generate_file_id() -> str:
    """Генерирует уникальный ID для файла"""
    return f"file_{uuid.uuid4().hex}"


def ensure_temp_dir():
    """Создает временную папку если её нет"""
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)
        logger.info(f"📁 Создана временная папка {TEMP_DIR}")


def get_file_size_from_message(message: Message) -> tuple[int, str | None]:
    """
    Получает размер файла из сообщения
    
    Returns:
        tuple: (размер в байтах, тип файла) или (0, None) если файла нет
    """
    if message.document:
        return (message.document.file_size or 0, "document")
    elif message.video:
        return (message.video.file_size or 0, "video")
    elif message.audio:
        return (message.audio.file_size or 0, "audio")
    elif message.photo:
        # Для фото возвращаем 0, так как не учитываем в общей сумме
        return (0, "photo")
    return (0, None)


def calculate_total_files_size(files: list) -> int:
    """
    Подсчитывает общий размер файлов (только документы и видео)
    
    Args:
        files: Список файлов из state
        
    Returns:
        Общий размер в байтах
    """
    return sum(
        file_info.get("size", 0)
        for file_info in files
        if file_info.get("type") in ["document", "video"]
    )


# ========== Валидация файлов ==========

async def validate_file_count(files: list, message: Message) -> bool:
    """
    Проверяет количество файлов
    
    Returns:
        True если проверка пройдена, False если превышен лимит
    """
    if len(files) >= MAX_FILES_COUNT:
        await message.answer(
            f"❌ **Превышен лимит файлов**\n\n"
            f"Максимальное количество файлов: {MAX_FILES_COUNT}\n"
            f"Текущее количество: {len(files)}\n\n"
            f"💡 Завершите добавление файлов или удалите некоторые файлы.",
            parse_mode="Markdown",
        )
        return False
    return True


async def _send_file_too_large_error(message: Message, file_size: int, file_name: str, file_type: str):
    """Отправляет сообщение об ошибке - файл слишком большой"""
    size_mb = file_size / (1024 * 1024)
    max_mb = MAX_FILE_SIZE / (1024 * 1024)
    type_name = "документ" if file_type == "document" else "видео"
    
    await message.answer(
        f"❌ **Файл слишком большой**\n\n"
        f"Файл: {file_name}\n"
        f"Тип: {type_name}\n"
        f"Размер: {size_mb:.1f} МБ\n"
        f"Максимальный размер одного файла: {max_mb:.0f} МБ\n\n"
        f"💡 Пожалуйста, отправьте файл меньшего размера.",
        parse_mode="Markdown",
    )


async def _send_total_size_exceeded_error(message: Message, total_size: int, new_size: int, file_type: str):
    """Отправляет сообщение об ошибке - превышен общий лимит"""
    total_mb = (total_size + new_size) / (1024 * 1024)
    max_mb = MAX_TOTAL_SIZE / (1024 * 1024)
    current_mb = total_size / (1024 * 1024)
    new_mb = new_size / (1024 * 1024)
    type_name = "документ" if file_type == "document" else "видео"
    
    await message.answer(
        f"❌ **Превышен общий лимит размера файлов**\n\n"
        f"Текущий размер файлов: {current_mb:.1f} МБ\n"
        f"Размер нового {type_name}: {new_mb:.1f} МБ\n"
        f"Общий размер: {total_mb:.1f} МБ\n"
        f"Максимальный общий размер: {max_mb:.0f} МБ\n\n"
        f"💡 Удалите некоторые файлы или отправьте файл меньшего размера.",
        parse_mode="Markdown",
    )


async def validate_total_size(files: list, new_file_size: int, file_type: str, message: Message) -> bool:
    """
    Проверяет размер отдельного файла и общий размер файлов
    
    Args:
        files: Список уже добавленных файлов
        new_file_size: Размер нового файла
        file_type: Тип файла ("document" или "video")
        message: Сообщение для ответа
        
    Returns:
        True если проверка пройдена, False если превышен лимит
    """
    if file_type not in ["document", "video"] or new_file_size == 0:
        return True  # Фото не проверяем или размер неизвестен
    
    # Проверка размера отдельного файла
    if new_file_size > MAX_FILE_SIZE:
        file_name = (message.document.file_name if message.document else message.video.file_name) or file_type
        await _send_file_too_large_error(message, new_file_size, file_name, file_type)
        return False
    
    # Проверка общего размера всех файлов
    total_size = calculate_total_files_size(files)
    if total_size + new_file_size > MAX_TOTAL_SIZE:
        await _send_total_size_exceeded_error(message, total_size, new_file_size, file_type)
        return False
    
    return True


# ========== Загрузка и обработка файлов ==========

async def download_and_save_file(message: Message, file_type: str) -> dict | None:
    """
    Скачивает и сохраняет файл из сообщения
    
    Args:
        message: Сообщение с файлом
        file_type: Тип файла ("document", "photo", "video")
        
    Returns:
        Словарь с информацией о файле или None при ошибке
    """
    if not ctx.bot:
        return None
    
    ensure_temp_dir()
    
    try:
        if file_type == "document":
            if not message.document:
                return None
            file = await ctx.bot.get_file(message.document.file_id)
            if not file or not file.file_path:
                return None
            file_name = message.document.file_name or f"{message.document.file_id}.bin"
            file_size = message.document.file_size or 0
        elif file_type == "photo":
            if not message.photo:
                return None
            photo = message.photo[-1]
            file = await ctx.bot.get_file(photo.file_id)
            if not file or not file.file_path:
                return None
            file_name = f"photo_{datetime.now().strftime('%H%M%S')}.jpg"
            file_size = 0  # Фото не учитываем в общей сумме
        elif file_type == "video":
            if not message.video:
                return None
            file = await ctx.bot.get_file(message.video.file_id)
            if not file or not file.file_path:
                return None
            file_name = message.video.file_name or f"{message.video.file_id}.mp4"
            file_size = message.video.file_size or 0
        elif file_type == "audio":
            # Обрабатываем аудио (включая .ogg файлы)
            if not message.audio:
                return None
            file = await ctx.bot.get_file(message.audio.file_id)
            if not file or not file.file_path:
                return None
            # Используем file_name из audio или генерируем по file_id
            file_name = message.audio.file_name or f"{message.audio.file_id}.ogg"
            file_size = message.audio.file_size or 0
        else:
            return None
        
        file_path = os.path.join(TEMP_DIR, file_name)
        await ctx.bot.download_file(file.file_path, file_path)
        
        logger.info(f"{file_type.capitalize()} сохранен: {file_path}")
        
        return {
            "type": file_type,
            "file_path": file_path,
            "name": file_name,
            "size": file_size,
        }
    except Exception as e:
        logger.error(f"Ошибка при сохранении файла: {e}")
        return None


async def validate_and_process_video(message: Message, files: list, error_target: Message) -> dict | None:
    """
    Проверяет и обрабатывает видео из сообщения
    
    Args:
        message: Сообщение с видео
        files: Список уже добавленных файлов
        error_target: Сообщение для отправки ошибок (может быть другим сообщением)
        
    Returns:
        Информация о файле или None если ошибка
    """
    if not message.video:
        return None
    
    video_size = message.video.file_size or 0
    
    # Проверяем размер отдельного файла
    if video_size > MAX_FILE_SIZE:
        size_mb = video_size / (1024 * 1024)
        max_mb = MAX_FILE_SIZE / (1024 * 1024)
        await error_target.answer(
            f"❌ **Видео слишком большое**\n\n"
            f"Размер: {size_mb:.1f} МБ\n"
            f"Максимальный размер одного файла: {max_mb:.0f} МБ\n\n"
            f"💡 Пожалуйста, отправьте видео меньшего размера.",
            parse_mode="Markdown",
        )
        return None
    
    # Проверяем общий размер всех файлов
    total_size = calculate_total_files_size(files)
    if total_size + video_size > MAX_TOTAL_SIZE:
        total_mb = (total_size + video_size) / (1024 * 1024)
        max_mb = MAX_TOTAL_SIZE / (1024 * 1024)
        current_mb = total_size / (1024 * 1024)
        video_mb = video_size / (1024 * 1024)
        await error_target.answer(
            f"❌ **Превышен общий лимит размера файлов**\n\n"
            f"Текущий размер: {current_mb:.1f} МБ\n"
            f"Размер видео: {video_mb:.1f} МБ\n"
            f"Общий размер: {total_mb:.1f} МБ\n"
            f"Максимальный общий размер: {max_mb:.0f} МБ\n\n"
            f"💡 Удалите некоторые файлы или отправьте видео меньшего размера.",
            parse_mode="Markdown",
        )
        return None
    
    # Скачиваем видео
    if not ctx.bot:
        return None
    
    file = await ctx.bot.get_file(message.video.file_id)
    if not file or not file.file_path:
        return None
    
    file_name = message.video.file_name or f"{message.video.file_id}.mp4"
    file_path = os.path.join(TEMP_DIR, file_name)
    await ctx.bot.download_file(file.file_path, file_path)
    
    return {
        "type": "video",
        "file_path": file_path,
        "name": file_name,
        "size": video_size,
    }


async def download_photo_from_message(message: Message, order: int = 0) -> dict | None:
    """
    Скачивает фото из сообщения
    
    Args:
        message: Сообщение с фото
        order: Порядковый номер (для альбомов)
        
    Returns:
        Информация о файле или None если ошибка
    """
    if not message.photo or not ctx.bot:
        return None
    
    photo = message.photo[-1]
    file = await ctx.bot.get_file(photo.file_id)
    if not file or not file.file_path:
        return None
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    file_name = f"photo_{timestamp}_{order}.jpg" if order else f"photo_{timestamp}.jpg"
    file_path = os.path.join(TEMP_DIR, file_name)
    await ctx.bot.download_file(file.file_path, file_path)
    
    return {
        "type": "photo",
        "file_path": file_path,
        "name": file_name,
        "size": 0,  # Фото не учитываем в общей сумме
    }


async def cleanup_temp_files(state: FSMContext):
    """Очистка временных файлов события"""
    # Удаляем все файлы из временной папки
    if os.path.exists(TEMP_DIR):
        try:
            shutil.rmtree(TEMP_DIR)
        except Exception:
            pass  # Тихая очистка без логирования

    # Очищаем информацию о файлах в состоянии
    if state:
        try:
            data = await state.get_data()
            if "files" in data:
                data["files"] = []
                await state.set_data(data)
        except Exception:
            pass  # Тихая очистка без логирования


# ========== Форматирование и UI ==========

def format_event_time_display(data: dict) -> str:
    """Форматирует отображение времени события"""
    if data.get("is_immediate"):
        return "Прямо сейчас 🔥"
    
    event_date = data.get("event_date")
    event_time = data.get("event_time")
    if event_date and event_time:
        naive_datetime = datetime.strptime(f"{event_date} {event_time}", "%Y-%m-%d %H:%M")
        moscow_datetime = MOSCOW_TZ.localize(naive_datetime)
        return f"{moscow_datetime.strftime('%d.%m.%Y %H:%M')} (МСК)"
    
    return "Не указано"


def create_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру для подтверждения события"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Создать", callback_data="confirm:yes"),
                InlineKeyboardButton(text="❌ Отменить", callback_data="confirm:no"),
            ],
            [InlineKeyboardButton(text="👁 Предпросмотр", callback_data="preview:show")],
        ]
    )


def format_files_info_message(files: list) -> str:
    """
    Форматирует сообщение с информацией о файлах
    
    Args:
        files: Список файлов
        
    Returns:
        Отформатированное сообщение
    """
    remaining_count = MAX_FILES_COUNT - len(files)
    
    return (
        f"✅ Файл добавлен\n\n"
        f"📊 Всего файлов: {len(files)}/{MAX_FILES_COUNT}\n"
        f"📦 Можно добавить еще: {remaining_count}\n\n"
        f"💡 Отправьте еще файлы или нажмите кнопку для завершения:"
    )


# ========== Работа с медиа-группами ==========

def create_media_group_from_files(files: list, event_message: str) -> list:
    """
    Создает медиа-группу из файлов
    
    Args:
        files: Список файлов с информацией
        event_message: Текст сообщения для первого файла
        
    Returns:
        Список InputMedia объектов
    """
    from aiogram.types import FSInputFile, InputMediaPhoto, InputMediaVideo
    
    media_group = []
    sorted_files = sorted(files, key=lambda x: x.get("order", 0))
    
    for i, file_info in enumerate(sorted_files):
        file_path = file_info.get("file_path")
        if not file_path or not os.path.exists(file_path):
            logger.warning(f"⚠️ Файл не найден, пропускаем: {file_info.get('name')} ({file_path})")
            continue
        
        try:
            if file_info["type"] == "photo":
                media = InputMediaPhoto(
                    media=FSInputFile(file_path),
                    caption=event_message if i == 0 else None,
                    parse_mode="MarkdownV2" if i == 0 else None,
                )
                media_group.append(media)
            elif file_info["type"] == "video":
                media = InputMediaVideo(
                    media=FSInputFile(file_path),
                    caption=event_message if i == 0 else None,
                    parse_mode="MarkdownV2" if i == 0 else None,
                )
                media_group.append(media)
        except Exception as e:
            logger.error(f"❌ Ошибка создания медиа для файла {file_info.get('name')}: {e}")
    
    return media_group


async def send_media_group_with_fallback(bot, chat_id: int, media_group: list, event_message: str, fallback_message: Message | None = None):
    """
    Отправляет медиа-группу с fallback на отправку по одному
    
    Args:
        bot: Экземпляр бота
        chat_id: ID чата
        media_group: Список медиа-объектов
        event_message: Текст сообщения
        fallback_message: Сообщение для fallback отправки
    """
    from aiogram.types import InputMediaPhoto, InputMediaVideo
    
    try:
        await bot.send_media_group(chat_id=chat_id, media=media_group)
        logger.info(f"✅ Отправлена медиа-группа из {len(media_group)} файлов")
    except Exception as e:
        logger.error(f"❌ Ошибка отправки медиа-группы: {e}")
        if not fallback_message:
            return
        
        # Отправляем по одному
        first_file = True
        for media in media_group:
            try:
                if isinstance(media, InputMediaPhoto):
                    await fallback_message.answer_photo(
                        photo=media.media,
                        caption=event_message if first_file else None,
                        parse_mode="MarkdownV2" if first_file else None,
                    )
                elif isinstance(media, InputMediaVideo):
                    await fallback_message.answer_video(
                        video=media.media,
                        caption=event_message if first_file else None,
                        parse_mode="MarkdownV2" if first_file else None,
                    )
                first_file = False
            except Exception as e2:
                logger.error(f"❌ Ошибка отправки отдельного файла: {e2}")


# ========== Утилиты для работы с медиа-группами ==========

def get_max_order_for_stage(files: list, stage: str) -> int:
    """Получает максимальный order для указанной стадии"""
    existing_files = [f for f in files if f.get("stage") == stage]
    return max([f.get("order", 0) for f in existing_files], default=0)


def generate_group_id() -> str:
    """Генерирует уникальный ID для медиа-группы"""
    return f"group_{uuid.uuid4().hex[:8]}"


async def save_media_group_files(
    bot, messages: list, files: list, stage: str, max_order: int, group_id: str
) -> list:
    """
    Сохраняет файлы из медиа-группы.
    
    Args:
        bot: Экземпляр бота
        messages: Список сообщений из медиа-группы
        files: Текущий список файлов
        stage: Стадия сохранения (with_message, after_message)
        max_order: Максимальный порядок для этой стадии
        group_id: ID группы для этих файлов
    
    Returns:
        list: Обновленный список файлов
    """
    for i, message in enumerate(messages, 1):
        try:
            order = max_order + i
            file_info = None
            
            if message.photo:
                file_info = await download_photo_from_message(message, order=order)
            elif message.video:
                file_info = await validate_and_process_video(message, files, messages[0])
            
            if file_info:
                file_info.update({
                    "stage": stage,
                    "order": order,
                    "group_id": group_id,
                })
                files.append(file_info)
                logger.info(f"Файл сохранен: {file_info['file_path']} (stage={stage}, order={order}, group_id={group_id})")
        
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки файла {i} из медиа-группы: {e}")
            continue
    
    return files


def group_files_by_group_id(files: list) -> tuple[dict, list]:
    """
    Группирует файлы по group_id.
    
    Args:
        files: Список файлов
    
    Returns:
        tuple: (словарь групп {group_id: [files]}, список одиночных файлов)
    """
    groups = {}
    standalone_files = []
    
    for file_info in files:
        group_id = file_info.get("group_id")
        if group_id and file_info["type"] in ("photo", "video"):
            if group_id not in groups:
                groups[group_id] = []
            groups[group_id].append(file_info)
        else:
            standalone_files.append(file_info)
    
    return groups, standalone_files


def create_media_group_from_files_for_sending(group_files: list):
    """
    Создает список InputMedia из файлов для отправки как media_group.
    
    Args:
        group_files: Список файлов одной группы
    
    Returns:
        list: Список InputMedia объектов
    """
    from aiogram.types import FSInputFile, InputMediaPhoto, InputMediaVideo
    
    media_group = []
    
    for file_info in group_files:
        try:
            file_path = file_info.get("file_path")
            if not file_path or not os.path.exists(file_path):
                logger.warning(f"⚠️ Файл не найден, пропускаем: {file_info.get('name')} ({file_path})")
                continue
            
            if file_info["type"] == "photo":
                media = InputMediaPhoto(media=FSInputFile(file_path))
                media_group.append(media)
            elif file_info["type"] == "video":
                media = InputMediaVideo(media=FSInputFile(file_path))
                media_group.append(media)
        except Exception as e:
            logger.error(f"❌ Ошибка создания медиа для файла {file_info.get('name')}: {e}")
            continue
    
    return media_group


async def send_media_group_with_fallback_for_additional(
    bot, chat_id: int, media_group: list, group_files: list
) -> list:
    """
    Отправляет медиа-группу с fallback на отправку по одному при ошибке.
    
    Args:
        bot: Экземпляр бота
        chat_id: ID чата
        media_group: Список InputMedia объектов
        group_files: Исходные файлы для fallback
    
    Returns:
        list: Список message_id отправленных сообщений
    """
    from aiogram.types import FSInputFile
    
    message_ids = []
    
    if not media_group:
        return message_ids
    
    try:
        messages = await bot.send_media_group(chat_id=chat_id, media=media_group)
        if messages:
            for msg in messages:
                if hasattr(msg, 'message_id'):
                    message_ids.append(msg.message_id)
    except Exception as e:
        logger.error(f"❌ Ошибка отправки медиа-группы: {e}")
        # Fallback: отправляем по одному
        for file_info in group_files:
            try:
                file_path = file_info.get("file_path")
                if not file_path or not os.path.exists(file_path):
                    continue
                
                if file_info["type"] == "photo":
                    sent_message = await bot.send_photo(chat_id=chat_id, photo=FSInputFile(file_path))
                elif file_info["type"] == "video":
                    sent_message = await bot.send_video(chat_id=chat_id, video=FSInputFile(file_path))
                
                if sent_message and hasattr(sent_message, 'message_id'):
                    message_ids.append(sent_message.message_id)
            except Exception as e2:
                logger.error(f"❌ Ошибка отправки отдельного файла из группы: {e2}")
    
    return message_ids


async def send_single_file_for_additional(
    bot, chat_id: int, file_info: dict
) -> int | None:
    """
    Отправляет одиночный файл.
    
    Args:
        bot: Экземпляр бота
        chat_id: ID чата
        file_info: Информация о файле
    
    Returns:
        int | None: message_id или None при ошибке
    """
    from aiogram.types import FSInputFile
    
    try:
        file_path = file_info.get("file_path")
        if not file_path or not os.path.exists(file_path):
            logger.warning(f"⚠️ Файл не найден: {file_info.get('name')} ({file_path})")
            return None
        
        sent_message = None
        if file_info["type"] == "document":
            sent_message = await bot.send_document(chat_id=chat_id, document=FSInputFile(file_path))
        elif file_info["type"] == "photo":
            sent_message = await bot.send_photo(chat_id=chat_id, photo=FSInputFile(file_path))
        elif file_info["type"] == "video":
            sent_message = await bot.send_video(chat_id=chat_id, video=FSInputFile(file_path))
        
        if sent_message and hasattr(sent_message, 'message_id'):
            return sent_message.message_id
        return None
    except Exception as e:
        logger.error(f"❌ Ошибка отправки файла {file_info.get('name')}: {e}")
        return None


async def send_additional_files_grouped(bot, files_after: list, chat_id: int) -> list:
    """
    Отправляет дополнительные файлы с группировкой медиа-групп.
    
    Args:
        bot: Экземпляр бота
        files_after: Список файлов с stage="after_message"
        chat_id: ID чата для отправки
    
    Returns:
        list: Список message_id всех отправленных сообщений
    """
    message_ids = []
    sorted_files = sorted(files_after, key=lambda x: x.get("order", 0))
    
    # Группируем файлы по group_id
    groups, standalone_files = group_files_by_group_id(sorted_files)
    
    # Отправляем медиа-группы
    for group_id, group_files in groups.items():
        # Сортируем файлы в группе по order
        group_files = sorted(group_files, key=lambda x: x.get("order", 0))
        
        if len(group_files) == 1:
            # Если в группе один файл, отправляем как обычный
            standalone_files.append(group_files[0])
        else:
            # Создаем media_group и отправляем
            media_group = create_media_group_from_files_for_sending(group_files)
            group_message_ids = await send_media_group_with_fallback_for_additional(
                bot, chat_id, media_group, group_files
            )
            message_ids.extend(group_message_ids)
    
    # Отправляем одиночные файлы
    for file_info in standalone_files:
        msg_id = await send_single_file_for_additional(bot, chat_id, file_info)
        if msg_id:
            message_ids.append(msg_id)
    
    return message_ids


# ========== Утилиты для редактирования событий ==========

def parse_json_data(data):
    """Парсит JSON данные (строку или словарь)"""
    if not data:
        return {}
    if isinstance(data, str):
        try:
            return json.loads(data)
        except Exception:
            return {}
    return data or {}


def format_executed_time(executed_at: str) -> str:
    """Форматирует время выполнения события для отображения"""
    if not executed_at:
        return "Дата неизвестна"
    try:
        utc_time = datetime.fromisoformat(executed_at.replace("Z", "+00:00"))
        moscow_time = utc_time.astimezone(MOSCOW_TZ)
        return moscow_time.strftime('%d.%m.%Y в %H:%M') + " МСК"
    except Exception:
        return "Дата неизвестна"


def check_edit_availability(executed_at: str) -> tuple[bool, timedelta | None]:
    """Проверяет возможность редактирования события (48 часов)"""
    if not executed_at:
        return False, None
    
    try:
        event_time = datetime.fromisoformat(executed_at.replace("Z", "+00:00"))
        if event_time.tzinfo is None:
            event_time = event_time.replace(tzinfo=timezone.utc)
        
        now = datetime.now(timezone.utc)
        time_diff = now - event_time
        can_edit = time_diff < timedelta(hours=48)
        
        if can_edit:
            time_remaining = timedelta(hours=48) - time_diff
            return True, time_remaining
        return False, None
    except Exception:
        return False, None


def format_time_remaining(time_remaining: timedelta) -> str:
    """Форматирует оставшееся время в человекочитаемом формате"""
    total_seconds = int(time_remaining.total_seconds())
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    time_parts = []
    if days > 0:
        time_parts.append(f"{days} дн.")
    if hours > 0:
        time_parts.append(f"{hours} ч.")
    if minutes > 0:
        time_parts.append(f"{minutes} мин.")
    if seconds > 0 and len(time_parts) == 0:
        time_parts.append(f"{seconds} сек.")
    
    return " ".join(time_parts) if time_parts else "0 сек."


def get_message_from_data(result_data, event_data) -> str:
    """Получает сообщение из result_data (приоритет) или event_data"""
    parsed_result = parse_json_data(result_data)
    message = parsed_result.get("message", "")
    
    if not message:
        parsed_event = parse_json_data(event_data)
        message = parsed_event.get("message", "")
    
    return message


def get_message_type_limits(message_type: str) -> tuple[int, str, str]:
    """Возвращает лимиты и описания для типа сообщения"""
    if message_type == "text":
        return MAX_TEXT_MESSAGE_LENGTH, "текстового сообщения", "текстовое сообщение"
    elif message_type == "photo":
        return MAX_CAPTION_LENGTH, "подписи к фото", "подпись к фото"
    elif message_type == "video":
        return MAX_CAPTION_LENGTH, "подписи к видео", "подпись к видео"
    elif message_type == "document":
        return MAX_CAPTION_LENGTH, "подписи к документу", "подпись к документу"
    elif message_type == "media_group":
        return MAX_CAPTION_LENGTH, "подписи к группе медиа", "подпись к группе медиа (фото/видео)"
    else:
        return MAX_TEXT_MESSAGE_LENGTH, "сообщения", "сообщение"


def truncate_text(text: str, max_length: int = 2000, suffix: str = "...") -> str:
    """Обрезает текст до указанной длины с добавлением суффикса"""
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    truncated = text[:max_length - len(suffix)]
    return truncated + suffix + f"\n\n_⚠️ Текст обрезан (показано {max_length} из {len(text)} символов)_"


def create_action_keyboard(can_edit: bool):
    """Создает клавиатуру с действиями для редактирования события"""
    from aiogram.types import InlineKeyboardButton
    
    keyboard_buttons = []
    if can_edit:
        keyboard_buttons.append([
            InlineKeyboardButton(text="✏️ Отредактировать сообщение", callback_data="edit_action:message")
        ])
    keyboard_buttons.append([
        InlineKeyboardButton(text="🗑️ Удалить событие", callback_data="edit_action:delete")
    ])
    keyboard_buttons.append([
        InlineKeyboardButton(text="❌ Отмена", callback_data="edit_action:cancel")
    ])
    return keyboard_buttons


def create_action_message_text(event_name: str, can_edit: bool, time_remaining=None) -> str:
    """Создает текст сообщения с действиями для редактирования"""
    message_text = f"✅ **Событие найдено:** `{event_name}`\n\n"
    
    if can_edit and time_remaining:
        time_str = format_time_remaining(time_remaining)
        message_text += (
            "💡 **Редактирование доступно**\n"
            f"⏰ Осталось времени: **{time_str}**\n"
            "_Сообщение можно изменить только в течение 48 часов с момента отправки_\n\n"
        )
    elif not can_edit:
        message_text += "⚠️ _Редактирование недоступно (событие старше 48 часов)_\n\n"
    
    message_text += "Выберите действие:"
    return message_text


async def delete_user_messages(message_ids: dict) -> tuple[int, int]:
    """Удаляет сообщения у пользователей. Возвращает (успешно, ошибок)"""
    deleted_count = 0
    failed_count = 0
    
    for chat_id_str, message_id_list in message_ids.items():
        for msg_id in message_id_list:
            try:
                chat_id = int(chat_id_str)
                await ctx.bot.delete_message(chat_id=chat_id, message_id=msg_id)
                deleted_count += 1
            except Exception as e:
                logger.error(f"Ошибка удаления сообщения {msg_id} для пользователя {chat_id_str}: {e}")
                failed_count += 1
    
    return deleted_count, failed_count


async def edit_user_messages(message_ids: dict, new_message: str, message_type: str) -> tuple[int, int]:
    """Редактирует сообщения у пользователей. Возвращает (успешно, ошибок)"""
    from telegramify_markdown import standardize
    
    standardized_message = standardize(new_message)
    edited_count = 0
    failed_count = 0
    
    for chat_id_str, message_id_list in message_ids.items():
        if not message_id_list:
            continue
        
        try:
            chat_id = int(chat_id_str)
            first_message_id = message_id_list[0]
            
            if message_type != "text":
                await ctx.bot.edit_message_caption(
                    chat_id=chat_id,
                    message_id=first_message_id,
                    caption=standardized_message,
                    parse_mode="MarkdownV2",
                )
            else:
                await ctx.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=first_message_id,
                    text=standardized_message,
                    parse_mode="MarkdownV2",
                )
            edited_count += 1
        except Exception as e:
            logger.error(f"Ошибка редактирования сообщения для пользователя {chat_id_str}: {e}")
            failed_count += 1
    
    return edited_count, failed_count


def update_event_message_data(event_id: str, new_message: str) -> str:
    """Обновляет сообщение в event_data и result_data"""
    response = (
        ctx.supabase_client.client.table("scheduled_events")
        .select("event_data, result_data")
        .eq("id", event_id)
        .eq("bot_id", ctx.supabase_client.bot_id)
    )
    
    result = response.execute()
    if not result.data:
        return ""
    
    event_data = parse_json_data(result.data[0].get("event_data"))
    result_data = parse_json_data(result.data[0].get("result_data"))
    
    old_message = result_data.get("message", "") or event_data.get("message", "")
    
    event_data["message"] = new_message
    result_data["message"] = new_message
    
    query = (
        ctx.supabase_client.client.table("scheduled_events")
        .update({
            "event_data": json.dumps(event_data, ensure_ascii=False),
            "result_data": json.dumps(result_data, ensure_ascii=False)
        })
        .eq("id", event_id)
        .eq("bot_id", ctx.supabase_client.bot_id)
    )
    query.execute()
    
    return old_message

