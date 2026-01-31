"""Тесты для file_handlers"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from aiogram.types import Chat, Message

from smart_bot_factory.handlers.file_handlers import (
    collect_files_for_message,
    send_chat_action_for_files,
    send_files_after_message,
    send_files_before_message,
)


class TestSendChatActionForFiles:
    """Тесты для функции send_chat_action_for_files"""

    @pytest.fixture
    def mock_message(self):
        """Фикстура для мок сообщения"""
        message = Mock(spec=Message)
        message.chat = Mock(spec=Chat)
        message.chat.id = 123456789
        return message

    @pytest.fixture
    def mock_bot(self):
        """Фикстура для мок бота"""
        bot = Mock()
        bot.send_chat_action = AsyncMock()
        return bot

    @pytest.fixture
    def setup_context(self, mock_bot):
        """Фикстура для настройки контекста"""
        with patch("smart_bot_factory.handlers.file_handlers.ctx") as mock_ctx:
            mock_ctx.bot = mock_bot
            mock_ctx.config = Mock()
            mock_ctx.config.PROMT_FILES_DIR = "prompts"
            yield mock_ctx

    @pytest.mark.asyncio
    async def test_send_chat_action_no_files(self, mock_message, setup_context):
        """Тест что chat action не отправляется если нет файлов"""
        await send_chat_action_for_files(mock_message, [], [], [])

        setup_context.bot.send_chat_action.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_chat_action_photo(self, mock_message, setup_context, tmp_path):
        """Тест отправки chat action для фото"""
        # Создаем временный файл изображения
        photo_file = tmp_path / "test.jpg"
        photo_file.write_bytes(b"fake image data")

        files_list = ["test.jpg"]

        with patch("smart_bot_factory.handlers.file_handlers.Path") as mock_path:
            mock_path.return_value.resolve.return_value = tmp_path

            await send_chat_action_for_files(mock_message, files_list, [], [])

            setup_context.bot.send_chat_action.assert_called_once()
            call_args = setup_context.bot.send_chat_action.call_args
            assert call_args[1]["action"] == "upload_photo"

    @pytest.mark.asyncio
    async def test_send_chat_action_video(self, mock_message, setup_context, tmp_path):
        """Тест отправки chat action для видео"""
        video_file = tmp_path / "test.mp4"
        video_file.write_bytes(b"fake video data")

        files_list = ["test.mp4"]

        with patch("smart_bot_factory.handlers.file_handlers.Path") as mock_path:
            mock_path.return_value.resolve.return_value = tmp_path

            await send_chat_action_for_files(mock_message, files_list, [], [])

            setup_context.bot.send_chat_action.assert_called_once()
            call_args = setup_context.bot.send_chat_action.call_args
            assert call_args[1]["action"] == "upload_video"


class TestCollectFilesForMessage:
    """Тесты для функции collect_files_for_message"""

    def test_collect_files_empty(self):
        """Тест сбора файлов когда их нет"""
        file_sender_with_msg, file_sender_with_msg_dirs, metadata_files, metadata_dirs = collect_files_for_message([], [], [])

        assert file_sender_with_msg == []
        assert file_sender_with_msg_dirs == []
        assert metadata_files == []
        assert metadata_dirs == []

    def test_collect_files_from_metadata(self):
        """Тест сбора файлов из метаданных"""
        files_list = ["file1.pdf", "file2.jpg"]
        dirs_list = ["dir1"]

        _, _, metadata_files, metadata_dirs = collect_files_for_message([], files_list, dirs_list)

        assert metadata_files == files_list
        assert metadata_dirs == dirs_list

    def test_collect_files_from_file_sender(self):
        """Тест сбора файлов из FileSender"""
        mock_file_sender = Mock()
        mock_file_sender.get_with_message = Mock(return_value=(["sender_file.pdf"], ["sender_dir"]))

        file_sender_files, file_sender_dirs, _, _ = collect_files_for_message([mock_file_sender], [], [])

        assert "sender_file.pdf" in file_sender_files
        assert "sender_dir" in file_sender_dirs


class TestSendFilesBeforeMessage:
    """Тесты для функции send_files_before_message"""

    @pytest.fixture
    def mock_file_sender(self):
        """Фикстура для мок FileSender"""
        sender = Mock()
        sender.get_before = Mock(return_value=([], []))
        sender.execute_before = AsyncMock()
        return sender

    @pytest.mark.asyncio
    async def test_send_files_before_empty(self, mock_file_sender):
        """Тест отправки файлов когда их нет"""
        mock_file_sender.get_before.return_value = ([], [])

        await send_files_before_message([mock_file_sender])

        mock_file_sender.execute_before.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_files_before_with_files(self, mock_file_sender):
        """Тест отправки файлов до сообщения"""
        mock_file_sender.get_before.return_value = (["file1.pdf"], [])

        await send_files_before_message([mock_file_sender])

        mock_file_sender.execute_before.assert_called_once()


class TestSendFilesAfterMessage:
    """Тесты для функции send_files_after_message"""

    @pytest.fixture
    def mock_file_sender(self):
        """Фикстура для мок FileSender"""
        sender = Mock()
        sender.get_after = Mock(return_value=([], []))
        sender.execute_after = AsyncMock()
        return sender

    @pytest.mark.asyncio
    async def test_send_files_after_empty(self, mock_file_sender):
        """Тест отправки файлов когда их нет"""
        mock_file_sender.get_after.return_value = ([], [])

        await send_files_after_message([mock_file_sender])

        mock_file_sender.execute_after.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_files_after_with_files(self, mock_file_sender):
        """Тест отправки файлов после сообщения"""
        mock_file_sender.get_after.return_value = (["file1.pdf"], [])

        await send_files_after_message([mock_file_sender])

        mock_file_sender.execute_after.assert_called_once()
