"""
Функции для обработки и отправки файлов в сообщениях.
"""

import logging
from pathlib import Path

from aiogram.types import Message

from ..utils.context import ctx

logger = logging.getLogger(__name__)


async def send_chat_action_for_files(
    message: Message,
    file_senders: list,
):
    """
    Определяет и отправляет правильный chat action для файлов, которые будут отправлены.

    Args:
        message: Message объект для получения chat_id
        file_senders: Список FileSender объектов
    """
    # Проверяем, есть ли файлы для отправки
    has_any_files = any(fs.has_files() for fs in file_senders)
    if not has_any_files:
        return

    # Определяем путь к папке files относительно рабочей директории
    files_dir = Path("files").resolve()
    if not files_dir.exists():
        # Пробуем найти files относительно директории промптов
        try:
            if ctx.config and ctx.config.PROMT_FILES_DIR:
                prompts_dir = Path(ctx.config.PROMT_FILES_DIR)
                files_dir = prompts_dir.parent / "files"
        except Exception:
            pass

    # Функция для определения типа медиа по расширению файла
    def _get_media_type(file_path: Path) -> str:
        """Определяет тип медиа по расширению файла"""
        ext = file_path.suffix.lower()
        photo_extensions = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff", ".tif", ".svg", ".ico", ".heic", ".heif"}
        video_extensions = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v", ".3gp", ".flv", ".wmv", ".mpg", ".mpeg"}

        if ext in photo_extensions:
            return "photo"
        elif ext in video_extensions:
            return "video"
        else:
            return "document"

    # Собираем все файлы для определения типа из FileSender
    all_files = []

    # Обрабатываем файлы из FileSender
    for file_sender in file_senders:
        try:
            before_files, before_dirs = file_sender.get_before()
            with_files, with_dirs = file_sender.get_with_message()
            after_files, after_dirs = file_sender.get_after()

            # Обрабатываем файлы
            for file_name in before_files + with_files + after_files:
                try:
                    file_path = files_dir / file_name if not Path(file_name).is_absolute() else Path(file_name)
                    if file_path.is_file():
                        all_files.append(file_path)
                except Exception as e:
                    logger.debug(f"⚠️ Ошибка обработки файла из FileSender {file_name}: {e}")

            # Обрабатываем директории из FileSender
            for dir_name in before_dirs + with_dirs + after_dirs:
                dir_path = Path(dir_name)
                try:
                    if dir_path.is_dir():
                        for file_path in dir_path.iterdir():
                            if file_path.is_file():
                                all_files.append(file_path)
                    else:
                        logger.debug(f"⚠️ Каталог из FileSender не найден: {dir_path}")
                except Exception as e:
                    logger.debug(f"⚠️ Ошибка обработки каталога из FileSender {dir_path}: {e}")
        except Exception as e:
            logger.debug(f"⚠️ Ошибка получения файлов из FileSender: {e}")

    if not all_files:
        return

    # Определяем типы файлов
    has_photo = any(_get_media_type(f) == "photo" for f in all_files)
    has_video = any(_get_media_type(f) == "video" for f in all_files)

    # Приоритет: видео > фото > документы (видео загружается дольше)
    if has_video:
        chat_action = "upload_video"
    elif has_photo:
        chat_action = "upload_photo"
    else:
        chat_action = "upload_document"

    # Отправляем правильный chat action сразу после обработки метаданных, чтобы перекрыть typing
    try:
        await ctx.bot.send_chat_action(chat_id=message.chat.id, action=chat_action)
        logger.debug(f"📤 Chat action отправлен сразу после обработки метаданных: {chat_action}")
    except Exception as e:
        logger.warning(f"⚠️ Не удалось отправить chat action '{chat_action}': {e}")


async def send_files_before_message(file_senders: list):
    """
    Отправляет файлы ДО сообщения через FileSender.

    Args:
        file_senders: Список FileSender объектов
    """
    for file_sender in file_senders:
        try:
            before_files, before_dirs = file_sender.get_before()
            if before_files or before_dirs:
                logger.debug(f"📁 Отправка файлов ДО сообщения: {len(before_files)} файлов, {len(before_dirs)} директорий")
                # FileSender сам отправит правильный chat action перед отправкой файлов
                await file_sender.execute_before()
        except Exception as e:
            logger.error(f"❌ Ошибка отправки файлов ДО сообщения: {e}", exc_info=True)


async def send_message_with_files(
    message: Message,
    final_response: str,
    file_senders: list,
    file_sender_with_message_files: list,
    file_sender_with_message_dirs: list,
    parse_mode: str,
) -> int | None:
    """
    Отправляет сообщение с файлами (ВМЕСТЕ с сообщением или отдельно).

    Args:
        message: Message объект
        final_response: Текст сообщения для отправки
        file_senders: Список FileSender объектов
        file_sender_with_message_files: Список файлов из FileSender для отправки с сообщением
        file_sender_with_message_dirs: Список директорий из FileSender для отправки с сообщением
        parse_mode: Режим парсинга текста

    Returns:
        int | None: message_id первого отправленного сообщения или None если не удалось отправить
    """
    from .utils import send_message_in_parts

    try:
        # Если есть файлы из FileSender (with_message), отправляем их с текстом как подписью
        if file_sender_with_message_files or file_sender_with_message_dirs:
            logger.debug(
                f"📁 Отправка файлов ВМЕСТЕ с сообщением через FileSender: "
                f"{len(file_sender_with_message_files)} файлов, {len(file_sender_with_message_dirs)} директорий"
            )
            first_message_id = None
            for file_sender in file_senders:
                try:
                    files, dirs = file_sender.get_with_message()
                    if files or dirs:
                        result = await file_sender.execute_with_message(final_response, parse_mode=parse_mode)
                        # Получаем message_id из результата (может быть Message или список Messages)
                        if result:
                            if hasattr(result, 'message_id'):
                                first_message_id = result.message_id
                            elif isinstance(result, list) and len(result) > 0 and hasattr(result[0], 'message_id'):
                                first_message_id = result[0].message_id
                        logger.debug("✅ Файлы отправлены ВМЕСТЕ с сообщением через FileSender")
                except Exception as e:
                    logger.error(f"❌ Ошибка отправки файлов ВМЕСТЕ с сообщением через FileSender: {e}", exc_info=True)
            return first_message_id
        else:
            # Если нет файлов из FileSender, отправляем просто текст
            logger.debug(f"Отправка текстового сообщения длиной {len(final_response)} символов")
            first_message_id = await send_message_in_parts(
                message,
                final_response,
                parse_mode=parse_mode,
            )
            if first_message_id is None:
                logger.warning("⚠️ send_message_in_parts вернула None, сообщение не было отправлено")
            return first_message_id
    except Exception as e:
        logger.error(f"❌ ОШИБКА ОТПРАВКИ СООБЩЕНИЯ: {e}", exc_info=True)
        # Пытаемся отправить простое сообщение об ошибке
        try:
            await message.answer("Произошла ошибка при отправке ответа. Попробуйте еще раз.")
        except Exception as e2:
            logger.error(f"❌ Не удалось отправить даже сообщение об ошибке: {e2}")
        return None


async def send_files_after_message(file_senders: list):
    """
    Отправляет файлы ПОСЛЕ сообщения через FileSender.

    Args:
        file_senders: Список FileSender объектов
    """
    for file_sender in file_senders:
        try:
            after_files, after_dirs = file_sender.get_after()
            if after_files or after_dirs:
                logger.debug(f"📁 Отправка файлов ПОСЛЕ сообщения: {len(after_files)} файлов, {len(after_dirs)} директорий")
                await file_sender.execute_after()
        except Exception as e:
            logger.error(f"❌ Ошибка отправки файлов ПОСЛЕ сообщения: {e}", exc_info=True)


def collect_files_for_message(
    file_senders: list,
) -> tuple[list, list]:
    """
    Собирает файлы для отправки ВМЕСТЕ с сообщением из FileSender.

    Args:
        file_senders: Список FileSender объектов

    Returns:
        tuple: (file_sender_with_message_files, file_sender_with_message_dirs)
    """
    file_sender_with_message_files = []
    file_sender_with_message_dirs = []

    for file_sender in file_senders:
        try:
            files, dirs = file_sender.get_with_message()
            if files or dirs:
                file_sender_with_message_files.extend(files)
                file_sender_with_message_dirs.extend(dirs)
        except Exception as e:
            logger.error(f"❌ Ошибка получения файлов для отправки ВМЕСТЕ с сообщением: {e}")

    return file_sender_with_message_files, file_sender_with_message_dirs
