"""Тесты для file_router.sender"""

import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from smart_bot_factory.file_router.sender import FileSender, FileSenderAction


class TestFileSenderAction:
    """Тесты для класса FileSenderAction"""

    def test_file_sender_action_init(self):
        """Тест инициализации FileSenderAction"""
        mock_file_sender = Mock()
        action = FileSenderAction(mock_file_sender, "before")

        assert action._file_sender == mock_file_sender
        assert action._timing == "before"

    def test_file_sender_action_call_with_files_args(self):
        """Тест вызова FileSenderAction с файлами через аргументы (строки 30-51)"""
        mock_file_sender = Mock()
        action = FileSenderAction(mock_file_sender, "before")

        # Мокируем send_now
        with patch.object(FileSender, "send_now") as mock_send_now:
            action("file1.pdf", "file2.jpg")

            mock_send_now.assert_called_once()
            call_args = mock_send_now.call_args
            assert call_args[1]["files"] == ["file1.pdf", "file2.jpg"]

    def test_file_sender_action_call_with_files_param(self):
        """Тест вызова FileSenderAction с параметром files"""
        mock_file_sender = Mock()
        action = FileSenderAction(mock_file_sender, "with_message")

        with patch.object(FileSender, "send_with_message") as mock_send:
            action(files=["file1.pdf", "file2.jpg"])

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[1]["files"] == ["file1.pdf", "file2.jpg"]

    def test_file_sender_action_call_with_directory(self):
        """Тест вызова FileSenderAction с директорией"""
        mock_file_sender = Mock()
        action = FileSenderAction(mock_file_sender, "after")

        with patch.object(FileSender, "send_after") as mock_send:
            action(directory="test_dir")

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[1]["directory"] == "test_dir"


class TestFileSender:
    """Тесты для класса FileSender"""

    @pytest.fixture
    def mock_bot(self):
        """Фикстура для мок бота"""
        bot = AsyncMock()
        bot.send_photo = AsyncMock()
        bot.send_video = AsyncMock()
        bot.send_document = AsyncMock()
        bot.send_media_group = AsyncMock()
        bot.send_chat_action = AsyncMock()
        return bot

    @pytest.fixture
    def file_sender(self, mock_bot):
        """Фикстура для FileSender"""
        return FileSender(user_id=123456, chat_id=123456, bot=mock_bot)

    def test_file_sender_init_with_bot(self, mock_bot):
        """Тест инициализации FileSender с переданным bot (строки 81-109)"""
        sender = FileSender(user_id=123456, chat_id=789012, bot=mock_bot)

        assert sender.user_id == 123456
        assert sender.chat_id == 789012
        assert sender.bot == mock_bot
        assert sender._before_files == []
        assert sender._before_directories == []
        assert sender._with_message_files == []
        assert sender._with_message_directories == []
        assert sender._after_files == []
        assert sender._after_directories == []

    def test_file_sender_init_without_chat_id(self, mock_bot):
        """Тест инициализации FileSender без chat_id (используется user_id)"""
        sender = FileSender(user_id=123456, bot=mock_bot)

        assert sender.user_id == 123456
        assert sender.chat_id == 123456  # Должен быть равен user_id

    def test_file_sender_init_without_bot_from_ctx(self, mock_bot):
        """Тест инициализации FileSender без bot, получение из ctx (строки 94-104)"""
        with patch("smart_bot_factory.utils.context.ctx") as mock_ctx:
            mock_ctx.bot = mock_bot

            sender = FileSender(user_id=123456)

            assert sender.bot == mock_bot

    def test_file_sender_init_without_bot_error(self):
        """Тест ошибки инициализации FileSender без bot (строки 102-109)"""
        with patch("smart_bot_factory.utils.context.ctx") as mock_ctx:
            mock_ctx.bot = None

            with pytest.raises(ValueError) as exc_info:
                FileSender(user_id=123456)

            assert "Bot" in str(exc_info.value)

    def test_file_sender_action_attributes(self, file_sender):
        """Тест атрибутов для удобного доступа (строки 122-124)"""
        assert isinstance(file_sender.send_before, FileSenderAction)
        assert isinstance(file_sender.send_after, FileSenderAction)
        assert isinstance(file_sender.send_with_message, FileSenderAction)
        assert file_sender.send_before._timing == "before"
        assert file_sender.send_after._timing == "after"
        assert file_sender.send_with_message._timing == "with_message"

    def test_get_bot_id_from_supabase_client(self, file_sender):
        """Тест получения bot_id из supabase_client (строки 126-146)"""
        with patch("smart_bot_factory.utils.context.ctx") as mock_ctx:
            mock_ctx.supabase_client = Mock()
            mock_ctx.supabase_client.bot_id = "test-bot"
            mock_ctx.config = None

            bot_id = file_sender._get_bot_id()

            assert bot_id == "test-bot"

    def test_get_bot_id_from_config(self, file_sender):
        """Тест получения bot_id из config"""
        with patch("smart_bot_factory.utils.context.ctx") as mock_ctx:
            mock_ctx.supabase_client = None
            mock_ctx.config = Mock()
            mock_ctx.config.BOT_ID = "config-bot"

            bot_id = file_sender._get_bot_id()

            assert bot_id == "config-bot"

    def test_get_bot_id_not_found(self, file_sender):
        """Тест когда bot_id не найден"""
        with patch("smart_bot_factory.utils.context.ctx") as mock_ctx:
            mock_ctx.supabase_client = None
            mock_ctx.config = None

            bot_id = file_sender._get_bot_id()

            assert bot_id is None

    def test_normalize_path_absolute(self, file_sender):
        """Тест нормализации абсолютного пути (строки 148-177)"""
        abs_path = "/absolute/path/to/file.pdf"
        result = file_sender._normalize_path(abs_path)

        assert result == abs_path

    def test_normalize_path_relative_with_bot_id(self, file_sender):
        """Тест нормализации относительного пути с bot_id"""
        with patch("smart_bot_factory.utils.context.ctx") as mock_ctx, patch("project_root_finder.root", Path("/project")):
            mock_ctx.supabase_client = Mock()
            mock_ctx.supabase_client.bot_id = "test-bot"

            result = file_sender._normalize_path("file.pdf")

            assert "test-bot" in result
            assert "file.pdf" in result

    def test_normalize_path_relative_without_bot_id(self, file_sender):
        """Тест нормализации относительного пути без bot_id (строки 170-172)"""
        with patch("smart_bot_factory.utils.context.ctx") as mock_ctx:
            mock_ctx.supabase_client = None
            mock_ctx.config = None

            result = file_sender._normalize_path("file.pdf")

            assert result == "file.pdf"

    def test_normalize_files_none(self, file_sender):
        """Тест нормализации None (строки 179-198)"""
        result = file_sender._normalize_files(None)

        assert result == []

    def test_normalize_files_string(self, file_sender):
        """Тест нормализации строки"""
        with patch.object(file_sender, "_normalize_path", return_value="/normalized/file.pdf"):
            result = file_sender._normalize_files("file.pdf")

            assert result == ["/normalized/file.pdf"]

    def test_normalize_files_list(self, file_sender):
        """Тест нормализации списка"""
        with patch.object(file_sender, "_normalize_path", side_effect=lambda x: f"/normalized/{x}"):
            result = file_sender._normalize_files(["file1.pdf", "file2.jpg"])

            assert len(result) == 2
            assert "/normalized/file1.pdf" in result
            assert "/normalized/file2.jpg" in result

    def test_send_now_with_files_args(self, file_sender):
        """Тест send_now с файлами через аргументы (строки 200-248)"""
        with patch.object(file_sender, "_normalize_path", side_effect=lambda x: f"/normalized/{x}"):
            file_sender.send_now("file1.pdf", "file2.jpg")

            assert len(file_sender._before_files) == 2
            assert "/normalized/file1.pdf" in file_sender._before_files
            assert "/normalized/file2.jpg" in file_sender._before_files

    def test_send_now_with_files_param(self, file_sender):
        """Тест send_now с параметром files"""
        with patch.object(file_sender, "_normalize_path", side_effect=lambda x: f"/normalized/{x}"):
            file_sender.send_now(files=["file1.pdf", "file2.jpg"])

            assert len(file_sender._before_files) == 2

    def test_send_now_with_directory(self, file_sender):
        """Тест send_now с директорией"""
        with patch.object(file_sender, "_normalize_path", side_effect=lambda x: f"/normalized/{x}"):
            file_sender.send_now(directory="test_dir")

            assert len(file_sender._before_directories) == 1
            assert "/normalized/test_dir" in file_sender._before_directories

    def test_send_with_message(self, file_sender):
        """Тест send_with_message (строки 249-296)"""
        with patch.object(file_sender, "_normalize_path", side_effect=lambda x: f"/normalized/{x}"):
            file_sender.send_with_message("file.pdf")

            assert len(file_sender._with_message_files) == 1
            assert "/normalized/file.pdf" in file_sender._with_message_files

    def test_send_after(self, file_sender):
        """Тест send_after (строки 298-345)"""
        with patch.object(file_sender, "_normalize_path", side_effect=lambda x: f"/normalized/{x}"):
            file_sender.send_after("file.pdf")

            assert len(file_sender._after_files) == 1
            assert "/normalized/file.pdf" in file_sender._after_files

    def test_extract_number_from_filename_with_number(self, file_sender):
        """Тест извлечения числа из имени файла (строки 396-411)"""
        number, filename = file_sender._extract_number_from_filename("1_presentation.pdf")

        assert number == 1
        assert filename == "1_presentation"

    def test_extract_number_from_filename_without_number(self, file_sender):
        """Тест извлечения из имени файла без числа"""
        number, filename = file_sender._extract_number_from_filename("presentation.pdf")

        assert number is None
        assert filename == "presentation"

    def test_sort_files_by_number(self, file_sender):
        """Тест сортировки файлов по числу (строки 413-436)"""
        files = ["3_file.pdf", "1_file.pdf", "2_file.pdf", "file.pdf"]
        sorted_files = file_sender._sort_files_by_number(files)

        # Файлы с числами должны быть первыми, отсортированными по числу
        assert sorted_files[0] == "1_file.pdf"
        assert sorted_files[1] == "2_file.pdf"
        assert sorted_files[2] == "3_file.pdf"
        # Файл без числа должен быть последним
        assert sorted_files[3] == "file.pdf"

    def test_get_file_type_photo(self, file_sender):
        """Тест определения типа файла - фото (строки 438-461)"""
        assert file_sender._get_file_type("image.jpg") == "photo"
        assert file_sender._get_file_type("image.png") == "photo"
        assert file_sender._get_file_type("image.jpeg") == "photo"

    def test_get_file_type_video(self, file_sender):
        """Тест определения типа файла - видео"""
        assert file_sender._get_file_type("video.mp4") == "video"
        assert file_sender._get_file_type("video.avi") == "video"

    def test_get_file_type_document(self, file_sender):
        """Тест определения типа файла - документ"""
        assert file_sender._get_file_type("document.pdf") == "document"
        assert file_sender._get_file_type("document.doc") == "document"

    def test_get_chat_action_for_files_empty(self, file_sender):
        """Тест определения chat action для пустого списка (строки 463-491)"""
        assert file_sender._get_chat_action_for_files([]) == "typing"

    def test_get_chat_action_for_files_video(self, file_sender):
        """Тест определения chat action для видео"""
        with patch("pathlib.Path.exists", return_value=True):
            assert file_sender._get_chat_action_for_files(["video.mp4"]) == "upload_video"

    def test_get_chat_action_for_files_photo(self, file_sender):
        """Тест определения chat action для фото"""
        with patch("pathlib.Path.exists", return_value=True):
            assert file_sender._get_chat_action_for_files(["image.jpg"]) == "upload_photo"

    def test_get_chat_action_for_files_document(self, file_sender):
        """Тест определения chat action для документа"""
        with patch("pathlib.Path.exists", return_value=True):
            assert file_sender._get_chat_action_for_files(["document.pdf"]) == "upload_document"

    @pytest.mark.asyncio
    async def test_send_chat_action_typing(self, file_sender):
        """Тест отправки chat action - typing пропускается (строки 493-508)"""
        await file_sender._send_chat_action("typing")

        file_sender.bot.send_chat_action.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_chat_action_upload_photo(self, file_sender):
        """Тест отправки chat action - upload_photo"""
        await file_sender._send_chat_action("upload_photo")

        file_sender.bot.send_chat_action.assert_called_once_with(chat_id=123456, action="upload_photo")

    @pytest.mark.asyncio
    async def test_send_single_file_photo(self, file_sender):
        """Тест отправки одного файла - фото (строки 510-531)"""
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_file:
            tmp_path = tmp_file.name
            tmp_file.write(b"fake image data")

        try:
            await file_sender._send_single_file(tmp_path, caption="Test")

            file_sender.bot.send_photo.assert_called_once()
            call_args = file_sender.bot.send_photo.call_args
            assert call_args[1]["chat_id"] == 123456
            assert call_args[1]["caption"] == "Test"
        finally:
            os.unlink(tmp_path)

    @pytest.mark.asyncio
    async def test_send_single_file_video(self, file_sender):
        """Тест отправки одного файла - видео"""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_file:
            tmp_path = tmp_file.name
            tmp_file.write(b"fake video data")

        try:
            await file_sender._send_single_file(tmp_path)

            file_sender.bot.send_video.assert_called_once()
        finally:
            os.unlink(tmp_path)

    @pytest.mark.asyncio
    async def test_send_single_file_document(self, file_sender):
        """Тест отправки одного файла - документ"""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            tmp_path = tmp_file.name
            tmp_file.write(b"fake document data")

        try:
            await file_sender._send_single_file(tmp_path)

            file_sender.bot.send_document.assert_called_once()
        finally:
            os.unlink(tmp_path)
