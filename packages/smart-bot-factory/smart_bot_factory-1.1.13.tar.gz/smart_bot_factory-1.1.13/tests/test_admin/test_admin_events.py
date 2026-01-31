"""Тесты для admin_events"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, User

from smart_bot_factory.admin.admin_events import (
    TEMP_DIR,
    cleanup_temp_files,
    ensure_temp_dir,
    generate_file_id,
)
from smart_bot_factory.admin.states import AdminStates


class TestAdminEventsHelpers:
    """Тесты для вспомогательных функций admin_events"""

    def test_generate_file_id(self):
        """Тест генерации ID файла"""
        file_id1 = generate_file_id()
        file_id2 = generate_file_id()

        assert file_id1.startswith("file_")
        assert file_id2.startswith("file_")
        assert file_id1 != file_id2
        assert len(file_id1) > 10

    def test_ensure_temp_dir(self):
        """Тест создания временной папки"""
        with patch("smart_bot_factory.admin.admin_events.os") as mock_os:
            mock_os.path.exists.return_value = False
            mock_os.makedirs = Mock()

            ensure_temp_dir()

            mock_os.makedirs.assert_called_once_with(TEMP_DIR)

    def test_ensure_temp_dir_exists(self):
        """Тест что папка не создается если уже существует"""
        with patch("smart_bot_factory.admin.admin_events.os") as mock_os:
            mock_os.path.exists.return_value = True
            mock_os.makedirs = Mock()

            ensure_temp_dir()

            mock_os.makedirs.assert_not_called()

    @pytest.mark.asyncio
    async def test_cleanup_temp_files_with_state(self):
        """Тест очистки временных файлов с состоянием"""
        mock_state = AsyncMock()
        mock_state.get_data = AsyncMock(return_value={"files": [{"name": "test.jpg"}]})

        with patch("smart_bot_factory.admin.admin_events.shutil") as mock_shutil:
            with patch("smart_bot_factory.admin.admin_events.os") as mock_os:
                mock_os.path.exists.return_value = True
                mock_shutil.rmtree = Mock()

                await cleanup_temp_files(mock_state)

                mock_shutil.rmtree.assert_called_once_with(TEMP_DIR)
                assert mock_state.set_data.called

    @pytest.mark.asyncio
    async def test_cleanup_temp_files_no_state(self):
        """Тест очистки временных файлов без состояния"""
        with patch("smart_bot_factory.admin.admin_events.shutil") as mock_shutil:
            with patch("smart_bot_factory.admin.admin_events.os") as mock_os:
                mock_os.path.exists.return_value = True
                mock_shutil.rmtree = Mock()

                await cleanup_temp_files(None)

                mock_shutil.rmtree.assert_called_once_with(TEMP_DIR)

    @pytest.mark.asyncio
    async def test_cleanup_temp_files_no_dir(self):
        """Тест очистки когда папки нет"""
        with patch("smart_bot_factory.admin.admin_events.shutil") as mock_shutil:
            with patch("smart_bot_factory.admin.admin_events.os") as mock_os:
                mock_os.path.exists.return_value = False
                mock_shutil.rmtree = Mock()

                await cleanup_temp_files(None)

                mock_shutil.rmtree.assert_not_called()


class TestAdminEventsHandlers:
    """Тесты для обработчиков событий"""

    @pytest.fixture
    def mock_admin_manager(self):
        """Фикстура для мок AdminManager"""
        manager = Mock()
        manager.is_admin = Mock(return_value=True)
        return manager

    @pytest.fixture
    def mock_supabase_client(self):
        """Фикстура для мок Supabase клиента"""
        client = Mock()
        client.check_event_name_exists = AsyncMock(return_value=False)
        client.get_all_segments = AsyncMock(return_value=["segment1", "segment2"])
        client.save_admin_event = AsyncMock(return_value={"id": "event-123"})
        client.get_admin_events = AsyncMock(return_value=[])
        client.get_users_by_segment = AsyncMock(return_value=[])
        client.upload_event_file = AsyncMock(return_value={"storage_path": "path/to/file"})
        client.delete_event_files = AsyncMock()
        return client

    @pytest.fixture
    def mock_bot(self):
        """Фикстура для мок бота"""
        bot = Mock()
        bot.get_file = AsyncMock(return_value=Mock(file_path="test.jpg"))
        bot.download_file = AsyncMock()
        bot.send_message = AsyncMock()
        bot.send_photo = AsyncMock()
        bot.send_video = AsyncMock()
        bot.send_document = AsyncMock()
        bot.send_media_group = AsyncMock()
        return bot

    @pytest.fixture
    def mock_message(self):
        """Фикстура для мок сообщения"""
        message = Mock(spec=Message)
        message.from_user = Mock(spec=User)
        message.from_user.id = 123456789
        message.text = "/create_event"
        message.answer = AsyncMock()
        return message

    @pytest.fixture
    def mock_state(self):
        """Фикстура для мок состояния FSM"""
        state = AsyncMock(spec=FSMContext)
        state.set_state = AsyncMock()
        state.update_data = AsyncMock()
        state.get_data = AsyncMock(return_value={})
        state.clear = AsyncMock()
        return state

    @pytest.fixture
    def setup_context(self, mock_admin_manager, mock_supabase_client, mock_bot):
        """Фикстура для настройки контекста"""
        with patch("smart_bot_factory.admin.admin_events.ctx") as mock_ctx:
            mock_ctx.admin_manager = mock_admin_manager
            mock_ctx.supabase_client = mock_supabase_client
            mock_ctx.bot = mock_bot
            yield mock_ctx

    @pytest.mark.asyncio
    async def test_create_event_start(self, mock_message, mock_state, setup_context):
        """Тест начала создания события"""
        from smart_bot_factory.admin.admin_events import create_event_start

        await create_event_start(mock_message, mock_state)

        mock_state.set_state.assert_called_once_with(AdminStates.create_event_name)
        mock_message.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_event_start_not_admin(self, mock_message, mock_state, setup_context):
        """Тест что не-админ не может создать событие"""
        setup_context.admin_manager.is_admin.return_value = False

        from smart_bot_factory.admin.admin_events import create_event_start

        await create_event_start(mock_message, mock_state)

        mock_state.set_state.assert_not_called()
        mock_message.answer.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_event_name(self, mock_message, mock_state, setup_context):
        """Тест обработки названия события"""
        mock_message.text = "Test Event"

        from smart_bot_factory.admin.admin_events import process_event_name

        await process_event_name(mock_message, mock_state)

        mock_state.update_data.assert_called()
        mock_state.set_state.assert_called_with(AdminStates.create_event_date)
        mock_message.answer.assert_called()

    @pytest.mark.asyncio
    async def test_process_event_name_empty(self, mock_message, mock_state, setup_context):
        """Тест обработки пустого названия"""
        mock_message.text = "   "

        from smart_bot_factory.admin.admin_events import process_event_name

        await process_event_name(mock_message, mock_state)

        # Должно быть сообщение об ошибке
        assert mock_message.answer.called
        call_args = mock_message.answer.call_args[0][0]
        assert "пустым" in call_args.lower()

    @pytest.mark.asyncio
    async def test_process_event_name_exists(self, mock_message, mock_state, setup_context):
        """Тест обработки существующего названия"""
        mock_message.text = "Existing Event"
        setup_context.supabase_client.check_event_name_exists = AsyncMock(return_value=True)

        from smart_bot_factory.admin.admin_events import process_event_name

        await process_event_name(mock_message, mock_state)

        # Должно быть сообщение о существовании
        assert mock_message.answer.called
        call_args = mock_message.answer.call_args[0][0]
        assert "уже существует" in call_args.lower()

    @pytest.mark.asyncio
    async def test_process_event_time_valid(self, mock_message, mock_state, setup_context):
        """Тест обработки валидного времени"""
        mock_message.text = "14:30"

        from smart_bot_factory.admin.admin_events import process_event_time

        await process_event_time(mock_message, mock_state)

        mock_state.update_data.assert_called()
        mock_state.set_state.assert_called_with(AdminStates.create_event_segment)
        mock_message.answer.assert_called()

    @pytest.mark.asyncio
    async def test_process_event_time_invalid(self, mock_message, mock_state, setup_context):
        """Тест обработки невалидного времени"""
        mock_message.text = "25:99"

        from smart_bot_factory.admin.admin_events import process_event_time

        await process_event_time(mock_message, mock_state)

        # Должно быть сообщение об ошибке
        assert mock_message.answer.called
        call_args = mock_message.answer.call_args[0][0]
        assert "формат" in call_args.lower() or "неверный" in call_args.lower()

    @pytest.mark.asyncio
    async def test_list_events_command(self, mock_message, mock_state, setup_context):
        """Тест команды списка событий"""
        from smart_bot_factory.admin.admin_events import list_events_command

        await list_events_command(mock_message, mock_state)

        setup_context.supabase_client.get_admin_events.assert_called_once_with(status="pending")
        mock_message.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_events_empty(self, mock_message, mock_state, setup_context):
        """Тест списка событий когда их нет"""
        setup_context.supabase_client.get_admin_events = AsyncMock(return_value=[])

        from smart_bot_factory.admin.admin_events import list_events_command

        await list_events_command(mock_message, mock_state)

        assert mock_message.answer.called
        call_args = mock_message.answer.call_args[0][0]
        assert "нет активных" in call_args.lower() or "нет доступных" in call_args.lower()

    @pytest.mark.asyncio
    async def test_delete_event_command(self, mock_message, mock_state, setup_context):
        """Тест команды удаления события"""
        mock_message.text = "/delete_event Test Event"
        mock_table = setup_context.supabase_client.client.table.return_value
        mock_table.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
            {"id": "event-123"}
        ]

        from smart_bot_factory.admin.admin_events import delete_event_command

        await delete_event_command(mock_message, mock_state)

        mock_message.answer.assert_called()
        call_args = mock_message.answer.call_args[0][0]
        assert "отменено" in call_args.lower() or "удалено" in call_args.lower()

    @pytest.mark.asyncio
    async def test_delete_event_not_found(self, mock_message, mock_state, setup_context):
        """Тест удаления несуществующего события"""
        mock_message.text = "/delete_event Non Existent"
        mock_table = setup_context.supabase_client.client.table.return_value
        mock_table.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value.data = []

        from smart_bot_factory.admin.admin_events import delete_event_command

        await delete_event_command(mock_message, mock_state)

        assert mock_message.answer.called
        call_args = mock_message.answer.call_args[0][0]
        assert "не найдено" in call_args.lower()

    @pytest.mark.asyncio
    async def test_delete_event_no_name(self, mock_message, mock_state, setup_context):
        """Тест удаления события без указания названия"""
        mock_message.text = "/delete_event"

        from smart_bot_factory.admin.admin_events import delete_event_command

        await delete_event_command(mock_message, mock_state)

        assert mock_message.answer.called
        call_args = mock_message.answer.call_args[0][0]
        assert "название" in call_args.lower()
