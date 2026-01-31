"""
FileSender - объект для управления отправкой файлов в разные моменты времени
"""

import logging
import re
from pathlib import Path
from typing import List, Literal, Optional, Tuple, Union

from aiogram.types import FSInputFile, InputMediaDocument, InputMediaPhoto, InputMediaVideo
from telegramify_markdown import standardize

logger = logging.getLogger(__name__)


class FileSenderAction:
    """
    Внутренний класс для удобного API отправки файлов
    Используется как атрибут FileSender: file_sender.send_before("file.pdf")
    """

    def __init__(self, file_sender: "FileSender", timing: str):
        """
        Args:
            file_sender: Родительский FileSender
            timing: 'before', 'with_message' или 'after'
        """
        self._file_sender = file_sender
        self._timing = timing

    def __call__(
        self, *files_args, files: Union[str, List[str], None] = None, directory: Optional[str] = None, directories: Optional[List[str]] = None
    ):
        """
        Вызов как функции: file_sender.send_before("file.pdf") или file_sender.send_before("file1.pdf", "file2.jpg")

        Args:
            *files_args: Файлы, переданные через запятую (например, "file1.pdf", "file2.jpg")
            files: Один файл (строка) или список файлов
            directory: Одна директория (строка)
            directories: Список директорий
        """
        # Если файлы переданы через запятую как аргументы, объединяем их с files
        if files_args:
            files_list = list(files_args)
            if files:
                # Если также передан параметр files, добавляем его к списку
                if isinstance(files, str):
                    files_list.append(files)
                elif isinstance(files, list):
                    files_list.extend(files)
            files = files_list

        # Вызываем методы напрямую через класс, чтобы избежать рекурсии через атрибуты
        if self._timing == "before":
            FileSender.send_now(self._file_sender, files=files, directory=directory, directories=directories)
        elif self._timing == "with_message":
            FileSender.send_with_message(self._file_sender, files=files, directory=directory, directories=directories)
        elif self._timing == "after":
            FileSender.send_after(self._file_sender, files=files, directory=directory, directories=directories)


class FileSender:
    """
    Объект для управления отправкой файлов в разные моменты времени.
    Автоматически получает bot из контекста, если не передан явно.

    Пример использования:
        @file_router.file_handler("send_files")
        async def send_files(file_sender: FileSender):
            # Через атрибуты (новый способ)
            file_sender.send_before("file.pdf")
            file_sender.send_with_message(["file1.pdf", "file2.jpg"])
            file_sender.send_after(directory="catalog_folder")

            # Через методы (старый способ, тоже работает)
            file_sender.send_now("file.pdf")
            file_sender.send_with_message("file.pdf")
            file_sender.send_after("file.pdf")
    """

    def __init__(self, user_id: int, chat_id: Optional[int] = None, bot=None):
        """
        Инициализация FileSender

        Args:
            user_id: ID пользователя (обязательно)
            chat_id: ID чата для отправки (опционально, по умолчанию = user_id)
            bot: Экземпляр бота aiogram (опционально, получается из ctx.bot если не передан)
        """
        self.user_id = user_id
        self.chat_id = chat_id or user_id

        # Получаем bot из контекста, если не передан
        if bot is None:
            try:
                from ..utils.context import ctx

                if ctx.bot:
                    self.bot = ctx.bot
                    logger.debug("📁 FileSender: bot получен из контекста")
                else:
                    raise ValueError("Bot не инициализирован в контексте. Убедитесь что bot_builder.start() вызван.")
            except ImportError:
                raise ValueError("Не удалось импортировать контекст")
        else:
            self.bot = bot

        if not self.bot:
            raise ValueError("Bot должен быть передан или доступен в контексте")

        # Хранилища файлов для разных моментов отправки
        self._before_files: List[str] = []
        self._before_directories: List[str] = []

        self._with_message_files: List[str] = []
        self._with_message_directories: List[str] = []

        self._after_files: List[str] = []
        self._after_directories: List[str] = []

        # Атрибуты для удобного доступа
        # Примечание: эти атрибуты намеренно перекрывают методы с теми же именами
        # FileSenderAction вызывает методы напрямую через класс, поэтому конфликта нет
        self.send_before = FileSenderAction(self, "before")
        self.send_after = FileSenderAction(self, "after")  # type: ignore[assignment]
        self.send_with_message = FileSenderAction(self, "with_message")  # type: ignore[assignment]

    def _get_bot_id(self) -> Optional[str]:
        """
        Получает bot_id из контекста

        Returns:
            str: bot_id или None
        """
        try:
            from ..utils.context import ctx

            # Пробуем получить из supabase_client
            if ctx.supabase_client and hasattr(ctx.supabase_client, "bot_id") and ctx.supabase_client.bot_id:
                return ctx.supabase_client.bot_id

            # Пробуем получить из config
            if ctx.config and hasattr(ctx.config, "BOT_ID") and ctx.config.BOT_ID:
                return ctx.config.BOT_ID

            return None
        except Exception:
            return None

    def _normalize_path(self, path: str) -> str:
        """
        Нормализует путь к файлу/директории, добавляя bots/{bot_id}/files/ если нужно

        Args:
            path: Путь к файлу или директории

        Returns:
            str: Полный путь к файлу/директории
        """
        from pathlib import Path

        from project_root_finder import root

        path_str = str(path)

        # Если путь уже абсолютный или содержит слеши (уже полный путь), возвращаем как есть
        if Path(path_str).is_absolute() or "/" in path_str or "\\" in path_str:
            return path_str

        # Получаем bot_id
        bot_id = self._get_bot_id()
        if not bot_id:
            logger.warning(f"⚠️ bot_id не найден, используем путь как есть: {path_str}")
            return path_str

        # Формируем полный путь: bots/{bot_id}/files/{path}
        full_path = root / "bots" / bot_id / "files" / path_str

        return str(full_path)

    def _normalize_files(self, files: Union[str, List[str], None]) -> List[str]:
        """
        Нормализует файлы: преобразует строку в список, валидирует пути, добавляет bots/{bot_id}/files/

        Args:
            files: Файл (строка) или список файлов

        Returns:
            List[str]: Список валидных путей к файлам
        """
        if files is None:
            return []

        if isinstance(files, str):
            return [self._normalize_path(files)]

        if isinstance(files, list):
            return [self._normalize_path(str(f)) for f in files if f]

        return []

    def send_now(
        self, *files_args, files: Union[str, List[str], None] = None, directory: Optional[str] = None, directories: Optional[List[str]] = None
    ):
        """
        Отправить файлы ПРЯМО СЕЙЧАС (до сообщения от ИИ)

        Можно использовать:
            send_now("file.pdf")
            send_now("file1.pdf", "file2.jpg")
            send_now(files=["file1.pdf", "file2.jpg"])
            send_now(["file1.pdf", "file2.jpg"])

        Args:
            *files_args: Файлы, переданные через запятую (например, "file1.pdf", "file2.jpg")
            files: Один файл (строка) или список файлов. Можно не передавать, если нужна только директория.
            directory: Одна директория (строка). Можно передать отдельно без файлов.
            directories: Список директорий. Можно передать отдельно без файлов.
        """
        # Если файлы переданы через запятую как аргументы, объединяем их с files
        if files_args:
            files_list = list(files_args)
            if files:
                # Если также передан параметр files, добавляем его к списку
                if isinstance(files, str):
                    files_list.append(files)
                elif isinstance(files, list):
                    files_list.extend(files)
            files = files_list

        normalized_files = self._normalize_files(files)
        self._before_files.extend(normalized_files)

        if directory:
            self._before_directories.append(self._normalize_path(directory))

        if directories:
            if isinstance(directories, str):
                self._before_directories.append(self._normalize_path(directories))
            else:
                self._before_directories.extend([self._normalize_path(str(d)) for d in directories])

        if normalized_files:
            logger.debug(f"📁 Файлы добавлены для отправки ДО сообщения: {normalized_files}")
        if directory or directories:
            dirs = [self._normalize_path(directory)] if directory else []
            if directories:
                dirs.extend([self._normalize_path(str(d)) for d in (directories if isinstance(directories, list) else [directories])])
            logger.debug(f"📂 Директории добавлены для отправки ДО сообщения: {dirs}")

    def send_with_message(
        self, *files_args, files: Union[str, List[str], None] = None, directory: Optional[str] = None, directories: Optional[List[str]] = None
    ):
        """
        Отправить файлы ВМЕСТЕ с сообщением от ИИ

        Можно использовать:
            send_with_message("file.pdf")
            send_with_message("file1.pdf", "file2.jpg")
            send_with_message(files=["file1.pdf", "file2.jpg"])
            send_with_message(["file1.pdf", "file2.jpg"])

        Args:
            *files_args: Файлы, переданные через запятую (например, "file1.pdf", "file2.jpg")
            files: Один файл (строка) или список файлов. Можно не передавать, если нужна только директория.
            directory: Одна директория (строка). Можно передать отдельно без файлов.
            directories: Список директорий. Можно передать отдельно без файлов.
        """
        # Если файлы переданы через запятую как аргументы, объединяем их с files
        if files_args:
            files_list = list(files_args)
            if files:
                # Если также передан параметр files, добавляем его к списку
                if isinstance(files, str):
                    files_list.append(files)
                elif isinstance(files, list):
                    files_list.extend(files)
            files = files_list

        normalized_files = self._normalize_files(files)
        self._with_message_files.extend(normalized_files)

        if directory:
            self._with_message_directories.append(self._normalize_path(directory))

        if directories:
            if isinstance(directories, str):
                self._with_message_directories.append(self._normalize_path(directories))
            else:
                self._with_message_directories.extend([self._normalize_path(str(d)) for d in directories])

        if normalized_files:
            logger.debug(f"📁 Файлы добавлены для отправки ВМЕСТЕ с сообщением: {normalized_files}")
        if directory or directories:
            dirs = [self._normalize_path(directory)] if directory else []
            if directories:
                dirs.extend([self._normalize_path(str(d)) for d in (directories if isinstance(directories, list) else [directories])])
            logger.debug(f"📂 Директории добавлены для отправки ВМЕСТЕ с сообщением: {dirs}")

    def send_after(
        self, *files_args, files: Union[str, List[str], None] = None, directory: Optional[str] = None, directories: Optional[List[str]] = None
    ):
        """
        Отправить файлы ПОСЛЕ сообщения от ИИ

        Можно использовать:
            send_after("file.pdf")
            send_after("file1.pdf", "file2.jpg")
            send_after(files=["file1.pdf", "file2.jpg"])
            send_after(["file1.pdf", "file2.jpg"])

        Args:
            *files_args: Файлы, переданные через запятую (например, "file1.pdf", "file2.jpg")
            files: Один файл (строка) или список файлов. Можно не передавать, если нужна только директория.
            directory: Одна директория (строка). Можно передать отдельно без файлов.
            directories: Список директорий. Можно передать отдельно без файлов.
        """
        # Если файлы переданы через запятую как аргументы, объединяем их с files
        if files_args:
            files_list = list(files_args)
            if files:
                # Если также передан параметр files, добавляем его к списку
                if isinstance(files, str):
                    files_list.append(files)
                elif isinstance(files, list):
                    files_list.extend(files)
            files = files_list

        normalized_files = self._normalize_files(files)
        self._after_files.extend(normalized_files)

        if directory:
            self._after_directories.append(self._normalize_path(directory))

        if directories:
            if isinstance(directories, str):
                self._after_directories.append(self._normalize_path(directories))
            else:
                self._after_directories.extend([self._normalize_path(str(d)) for d in directories])

        if normalized_files:
            logger.debug(f"📁 Файлы добавлены для отправки ПОСЛЕ сообщения: {normalized_files}")
        if directory or directories:
            dirs = [self._normalize_path(directory)] if directory else []
            if directories:
                dirs.extend([self._normalize_path(str(d)) for d in (directories if isinstance(directories, list) else [directories])])
            logger.debug(f"📂 Директории добавлены для отправки ПОСЛЕ сообщения: {dirs}")

    def get_before(self) -> tuple[List[str], List[str]]:
        """
        Получить файлы и директории для отправки ДО сообщения

        Returns:
            tuple: (список файлов, список директорий)
        """
        return self._before_files.copy(), self._before_directories.copy()

    def get_with_message(self) -> tuple[List[str], List[str]]:
        """
        Получить файлы и директории для отправки ВМЕСТЕ с сообщением

        Returns:
            tuple: (список файлов, список директорий)
        """
        return self._with_message_files.copy(), self._with_message_directories.copy()

    def get_after(self) -> tuple[List[str], List[str]]:
        """
        Получить файлы и директории для отправки ПОСЛЕ сообщения

        Returns:
            tuple: (список файлов, список директорий)
        """
        return self._after_files.copy(), self._after_directories.copy()

    async def execute_before(self):
        """Выполнить отправку файлов и директорий ДО сообщения"""
        await self._send_files(self._before_files, self._before_directories)

    async def execute_after(self):
        """Выполнить отправку файлов и директорий ПОСЛЕ сообщения"""
        await self._send_files(self._after_files, self._after_directories)

    async def execute_with_message(self, text: str, parse_mode: Optional[str] = None) -> Optional[int]:
        """
        Выполнить отправку файлов и директорий ВМЕСТЕ с сообщением (текст как подпись)

        Args:
            text: Текст сообщения, который будет использован как подпись к файлам
            parse_mode: Режим парсинга текста (Markdown, HTML или None)

        Returns:
            Optional[int]: message_id первого отправленного сообщения или None
        """
        return await self._send_files_with_text(self._with_message_files, self._with_message_directories, text, parse_mode)

    def _extract_number_from_filename(self, file_path: str) -> Tuple[Optional[int], str]:
        """
        Извлекает число из начала названия файла

        Args:
            file_path: Путь к файлу

        Returns:
            Tuple: (число из начала названия или None, имя файла без расширения)
        """
        path = Path(file_path)
        filename = path.stem  # Имя файла без расширения

        # Ищем число в начале названия файла
        match = re.match(r"^(\d+)", filename)
        if match:
            number = int(match.group(1))
            return number, filename
        else:
            return None, filename

    def _sort_files_by_number(self, files: List[str]) -> List[str]:
        """
        Сортирует файлы по числу в начале названия

        Если в начале названия есть число, сортирует по нему.
        Если числа нет, оставляет файл в конце (или сортирует по имени).

        Args:
            files: Список путей к файлам

        Returns:
            Отсортированный список файлов
        """

        def sort_key(file_path: str) -> Tuple[int, int, str]:
            number, filename = self._extract_number_from_filename(file_path)
            if number is not None:
                # Файлы с числами сортируем по числу, затем по имени
                return (0, number, filename)
            else:
                # Файлы без чисел идут после файлов с числами, сортируются по имени
                return (1, 0, filename)

        return sorted(files, key=sort_key)

    def _get_file_type(self, file_path: str) -> Literal["photo", "video", "document"]:
        """
        Определяет тип файла по расширению

        Args:
            file_path: Путь к файлу

        Returns:
            Тип файла: 'photo', 'video' или 'document'
        """
        path = Path(file_path)
        extension = path.suffix.lower()

        # Расширения изображений
        photo_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff", ".tif", ".ico", ".svg"}
        # Расширения видео
        video_extensions = {".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm", ".m4v", ".3gp", ".ogv"}

        if extension in photo_extensions:
            return "photo"
        elif extension in video_extensions:
            return "video"
        else:
            return "document"

    def _get_chat_action_for_files(self, files: List[str]) -> str:
        """
        Определяет chat action для списка файлов на основе их типов

        Args:
            files: Список путей к файлам

        Returns:
            Chat action: 'upload_photo', 'upload_video', 'upload_document' или 'typing'
        """
        if not files:
            return "typing"

        # Определяем типы всех файлов
        file_types = [self._get_file_type(file_path) for file_path in files if Path(file_path).exists()]

        if not file_types:
            return "typing"

        # Приоритет: видео > фото > документы (видео загружается дольше)
        # Если есть хотя бы одно видео - показываем upload_video
        if "video" in file_types:
            return "upload_video"
        # Если есть хотя бы одно фото - показываем upload_photo
        elif "photo" in file_types:
            return "upload_photo"
        # Иначе показываем upload_document
        else:
            return "upload_document"

    async def _send_chat_action(self, action: str):
        """
        Отправляет chat action пользователю (кроме typing, который управляется извне)

        Args:
            action: Тип действия ('upload_photo', 'upload_video', 'upload_document', и т.д.)
        """
        # Не отправляем typing, он управляется извне
        if action == "typing":
            return

        try:
            await self.bot.send_chat_action(chat_id=self.chat_id, action=action)
            logger.debug(f"📤 Chat action отправлен: {action}")
        except Exception as e:
            logger.warning(f"⚠️ Не удалось отправить chat action '{action}': {e}")

    async def _send_single_file(self, file_path: str, caption: Optional[str] = None, parse_mode: Optional[str] = None) -> Optional[int]:
        """
        Отправляет один файл соответствующим методом в зависимости от типа

        Args:
            file_path: Путь к файлу
            caption: Подпись к файлу (опционально)
            parse_mode: Режим парсинга подписи (опционально)

        Returns:
            Optional[int]: message_id отправленного сообщения или None
        """
        file_path_str = str(file_path)
        file_type = self._get_file_type(file_path_str)

        try:
            sent_message = None
            if file_type == "photo":
                sent_message = await self.bot.send_photo(chat_id=self.chat_id, photo=FSInputFile(file_path_str), caption=caption, parse_mode=parse_mode)
            elif file_type == "video":
                sent_message = await self.bot.send_video(chat_id=self.chat_id, video=FSInputFile(file_path_str), caption=caption, parse_mode=parse_mode)
            else:
                sent_message = await self.bot.send_document(chat_id=self.chat_id, document=FSInputFile(file_path_str), caption=caption, parse_mode=parse_mode)
            logger.debug(f"✅ Файл отправлен ({file_type}): {file_path_str}")
            return sent_message.message_id if sent_message and hasattr(sent_message, 'message_id') else None
        except Exception as e:
            logger.error(f"❌ Ошибка отправки файла {file_path}: {e}", exc_info=True)
            return None

    async def _send_files_group(self, files: List[str], caption: Optional[str] = None, parse_mode: Optional[str] = None) -> Optional[int]:
        """
        Отправляет группу файлов через media group
        Фото и видео отправляются вместе в одной media group с сохранением порядка, документы отдельно

        Args:
            files: Список путей к файлам
            caption: Подпись к файлам (будет добавлена только к первому файлу в группе)
            parse_mode: Режим парсинга подписи (опционально)

        Returns:
            Optional[int]: message_id первого отправленного сообщения или None
        """
        # Разделяем файлы на группы: фото/видео (можно вместе) и документы (отдельно)
        media_group_photo_video = []  # Сохраняем порядок для фото и видео
        documents = []

        for file_path in files:
            file_path_str = str(file_path)
            if not Path(file_path_str).exists():
                logger.warning(f"⚠️ Файл не найден: {file_path_str}")
                continue

            file_type = self._get_file_type(file_path_str)

            if file_type == "photo":
                media_group_photo_video.append(("photo", file_path_str))
            elif file_type == "video":
                media_group_photo_video.append(("video", file_path_str))
            else:
                documents.append(file_path_str)

        first_message_id = None
        # Отправляем фото и видео вместе в одной media group с сохранением порядка
        if media_group_photo_video:
            # Определяем chat action для фото/видео: приоритет видео (загружается дольше)
            has_video = any(t == "video" for t, _ in media_group_photo_video)
            chat_action = "upload_video" if has_video else "upload_photo"
            await self._send_chat_action(chat_action)

            try:
                media_group = []
                for idx, (file_type, file_path) in enumerate(media_group_photo_video):
                    if file_type == "photo":
                        # Подпись добавляем только к первому файлу
                        media_group.append(
                            InputMediaPhoto(
                                media=FSInputFile(file_path), caption=caption if idx == 0 else None, parse_mode=parse_mode if idx == 0 else None
                            )
                        )
                    elif file_type == "video":
                        # Подпись добавляем только к первому файлу
                        media_group.append(
                            InputMediaVideo(
                                media=FSInputFile(file_path), caption=caption if idx == 0 else None, parse_mode=parse_mode if idx == 0 else None
                            )
                        )

                if media_group:
                    messages = await self.bot.send_media_group(chat_id=self.chat_id, media=media_group)
                    # Сохраняем message_id первого сообщения из media_group
                    if messages and len(messages) > 0 and hasattr(messages[0], 'message_id'):
                        first_message_id = messages[0].message_id
                    photo_count = sum(1 for t, _ in media_group_photo_video if t == "photo")
                    video_count = sum(1 for t, _ in media_group_photo_video if t == "video")
                    logger.debug(f"✅ Отправлено {photo_count} фото и {video_count} видео через media group (с сохранением порядка)")
            except Exception as e:
                logger.error(f"❌ Ошибка отправки фото/видео через media group: {e}", exc_info=True)

        # Отправляем документы через media group отдельно
        if documents:
            # Отправляем chat action для документов (если фото/видео не было, иначе уже отправлен)
            if not media_group_photo_video:
                await self._send_chat_action("upload_document")

            try:
                media_group = []
                for idx, doc in enumerate(documents):
                    # Подпись добавляем только к первому документу
                    media_group.append(
                        InputMediaDocument(
                            media=FSInputFile(doc),
                            caption=caption if idx == 0 and not media_group_photo_video else None,
                            parse_mode=parse_mode if idx == 0 and not media_group_photo_video else None,
                        )
                    )
                if media_group:
                    messages = await self.bot.send_media_group(chat_id=self.chat_id, media=media_group)
                    # Если еще нет message_id, сохраняем из документов (если фото/видео не было)
                    if not first_message_id and messages and len(messages) > 0 and hasattr(messages[0], 'message_id'):
                        first_message_id = messages[0].message_id
                    logger.debug(f"✅ Отправлено {len(documents)} документов через media group")
            except Exception as e:
                logger.error(f"❌ Ошибка отправки документов через media group: {e}", exc_info=True)

        return first_message_id

    async def _send_files_with_text(self, files: List[str], directories: List[str], text: str, parse_mode: Optional[str] = None) -> Optional[int]:
        """
        Внутренний метод для отправки файлов и директорий ВМЕСТЕ с текстом (текст как подпись)

        Args:
            files: Список путей к файлам
            directories: Список путей к директориям
            text: Текст сообщения, который будет использован как подпись
            parse_mode: Режим парсинга текста (опционально)

        Returns:
            Optional[int]: message_id первого отправленного сообщения или None
        """
        # Фильтруем существующие файлы
        existing_files = []
        for file_path in files:
            file_path_str = str(file_path)
            if not Path(file_path_str).exists():
                logger.warning(f"⚠️ Файл не найден: {file_path_str}")
                continue
            existing_files.append(file_path_str)

        # Собираем файлы из директорий
        for directory in directories:
            try:
                directory_str = str(directory)
                directory_path = Path(directory_str)

                if not directory_path.exists() or not directory_path.is_dir():
                    logger.warning(f"⚠️ Директория не найдена: {directory_str}")
                    continue

                # Отправляем все файлы из директории
                files_in_dir = list(directory_path.glob("*"))
                files_in_dir = [str(f) for f in files_in_dir if f.is_file()]

                if files_in_dir:
                    # Сортируем файлы по числу в начале названия
                    files_in_dir = self._sort_files_by_number(files_in_dir)
                    existing_files.extend(files_in_dir)
            except Exception as e:
                logger.error(f"❌ Ошибка обработки директории {directory}: {e}", exc_info=True)

        # Стандартизируем текст для Markdown/MarkdownV2 и преобразуем в MarkdownV2
        if parse_mode in ("Markdown", "MarkdownV2") and text:
            text_to_send = standardize(text)
            parse_mode = "MarkdownV2"
        else:
            text_to_send = text

        # Если нет файлов, отправляем только текст
        if not existing_files:
            sent_message = await self.bot.send_message(chat_id=self.chat_id, text=text_to_send, parse_mode=parse_mode)
            return sent_message.message_id if sent_message and hasattr(sent_message, 'message_id') else None

        # Определяем и отправляем chat action для файлов
        chat_action = self._get_chat_action_for_files(existing_files)
        await self._send_chat_action(chat_action)

        # Отправляем файлы с текстом как подписью: если один - отдельно, если несколько - через media group
        if len(existing_files) == 1:
            return await self._send_single_file(existing_files[0], caption=text_to_send, parse_mode=parse_mode)
        elif len(existing_files) > 1:
            return await self._send_files_group(existing_files, caption=text_to_send, parse_mode=parse_mode)
        return None

    async def _send_files(self, files: List[str], directories: List[str]):
        """
        Внутренний метод для отправки файлов и директорий

        Args:
            files: Список путей к файлам
            directories: Список путей к директориям
        """
        # Фильтруем существующие файлы
        existing_files = []
        for file_path in files:
            file_path_str = str(file_path)
            if not Path(file_path_str).exists():
                logger.warning(f"⚠️ Файл не найден: {file_path_str}")
                continue
            existing_files.append(file_path_str)

        # Собираем все файлы из директорий для определения chat action
        all_files_for_action = existing_files.copy()

        # Отправляем файлы: если один - отдельно, если несколько - через media group
        if existing_files:
            # Определяем и отправляем chat action для файлов
            chat_action = self._get_chat_action_for_files(existing_files)
            await self._send_chat_action(chat_action)

            if len(existing_files) == 1:
                await self._send_single_file(existing_files[0])
            elif len(existing_files) > 1:
                await self._send_files_group(existing_files)

        # Отправляем директории
        for directory in directories:
            try:
                directory_str = str(directory)
                directory_path = Path(directory_str)

                if not directory_path.exists() or not directory_path.is_dir():
                    logger.warning(f"⚠️ Директория не найдена: {directory_str}")
                    continue

                # Отправляем все файлы из директории
                files_in_dir = list(directory_path.glob("*"))
                files_in_dir = [str(f) for f in files_in_dir if f.is_file()]

                if not files_in_dir:
                    logger.warning(f"⚠️ Директория пуста: {directory_str}")
                    continue

                # Сортируем файлы по числу в начале названия
                files_in_dir = self._sort_files_by_number(files_in_dir)

                # Добавляем файлы из директории к списку для определения chat action
                all_files_for_action.extend(files_in_dir)

                logger.debug(f"📂 Отправка {len(files_in_dir)} файлов из директории: {directory_str} (отсортировано по номеру в названии)")

                # Определяем и отправляем chat action для файлов из директории
                chat_action = self._get_chat_action_for_files(files_in_dir)
                await self._send_chat_action(chat_action)

                # Отправляем файлы из директории: если один - отдельно, если несколько - через media group
                if len(files_in_dir) == 1:
                    await self._send_single_file(files_in_dir[0])
                elif len(files_in_dir) > 1:
                    await self._send_files_group(files_in_dir)

                logger.debug(f"✅ Директория отправлена: {directory_str} ({len(files_in_dir)} файлов)")

            except Exception as e:
                logger.error(f"❌ Ошибка отправки директории {directory}: {e}", exc_info=True)

    def has_files(self) -> bool:
        """
        Проверяет, есть ли файлы или директории для отправки

        Returns:
            bool: True если есть файлы или директории для отправки
        """
        return bool(
            self._before_files
            or self._before_directories
            or self._with_message_files
            or self._with_message_directories
            or self._after_files
            or self._after_directories
        )

    def __repr__(self):
        return (
            f"FileSender(user_id={self.user_id}, chat_id={self.chat_id}, "
            f"before={len(self._before_files)} files + {len(self._before_directories)} dirs, "
            f"with_message={len(self._with_message_files)} files + {len(self._with_message_directories)} dirs, "
            f"after={len(self._after_files)} files + {len(self._after_directories)} dirs)"
        )
