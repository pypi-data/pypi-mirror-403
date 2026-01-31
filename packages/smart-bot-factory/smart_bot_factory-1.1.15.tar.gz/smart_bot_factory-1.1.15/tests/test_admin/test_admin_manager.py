"""Тесты для AdminManager"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from smart_bot_factory.admin.admin_manager import AdminManager


class TestAdminManager:
    """Тесты для класса AdminManager"""

    @pytest.fixture
    def mock_config(self):
        """Фикстура для мок-конфигурации"""
        config = Mock()
        config.ADMIN_TELEGRAM_IDS = [123456789, 987654321]
        return config

    @pytest.fixture
    def mock_supabase_client(self):
        """Фикстура для мок Supabase клиента"""
        client = Mock()
        client.sync_admin = AsyncMock()
        return client

    @pytest.fixture
    def admin_manager(self, mock_config, mock_supabase_client):
        """Фикстура для AdminManager"""
        return AdminManager(mock_config, mock_supabase_client)

    def test_init(self, admin_manager, mock_config):
        """Тест инициализации AdminManager"""
        assert len(admin_manager.admin_ids) == 2
        assert 123456789 in admin_manager.admin_ids
        assert 987654321 in admin_manager.admin_ids
        assert admin_manager.config == mock_config

    def test_is_admin_true(self, admin_manager):
        """Тест проверки админа - админ"""
        assert admin_manager.is_admin(123456789) is True
        assert admin_manager.is_admin(987654321) is True

    def test_is_admin_false(self, admin_manager):
        """Тест проверки админа - не админ"""
        assert admin_manager.is_admin(111111111) is False
        assert admin_manager.is_admin(999999999) is False

    def test_is_in_admin_mode_default(self, admin_manager):
        """Тест режима админа по умолчанию"""
        # По умолчанию админы в режиме администратора
        assert admin_manager.is_in_admin_mode(123456789) is True
        assert admin_manager.is_in_admin_mode(111111111) is False  # Не админ

    def test_toggle_admin_mode(self, admin_manager):
        """Тест переключения режима админа"""
        admin_id = 123456789

        # Начальное состояние - True (по умолчанию)
        assert admin_manager.is_in_admin_mode(admin_id) is True

        # Переключаем в режим пользователя
        new_mode = admin_manager.toggle_admin_mode(admin_id)
        assert new_mode is False
        assert admin_manager.is_in_admin_mode(admin_id) is False

        # Переключаем обратно в режим админа
        new_mode = admin_manager.toggle_admin_mode(admin_id)
        assert new_mode is True
        assert admin_manager.is_in_admin_mode(admin_id) is True

    def test_toggle_admin_mode_not_admin(self, admin_manager):
        """Тест переключения режима для не-админа"""
        non_admin_id = 111111111
        result = admin_manager.toggle_admin_mode(non_admin_id)
        assert result is False

    def test_set_admin_mode(self, admin_manager):
        """Тест установки режима админа"""
        admin_id = 123456789

        # Устанавливаем режим пользователя
        admin_manager.set_admin_mode(admin_id, False)
        assert admin_manager.is_in_admin_mode(admin_id) is False

        # Устанавливаем режим админа
        admin_manager.set_admin_mode(admin_id, True)
        assert admin_manager.is_in_admin_mode(admin_id) is True

    def test_set_admin_mode_not_admin(self, admin_manager):
        """Тест установки режима для не-админа"""
        non_admin_id = 111111111
        # Не должно изменить ничего
        admin_manager.set_admin_mode(non_admin_id, False)
        assert admin_manager.is_in_admin_mode(non_admin_id) is False

    @pytest.mark.asyncio
    async def test_get_active_admins(self, admin_manager):
        """Тест получения активных админов"""
        admin_id1 = 123456789
        admin_id2 = 987654321

        # Оба админа в режиме админа по умолчанию
        active = await admin_manager.get_active_admins()
        assert len(active) == 2
        assert admin_id1 in active
        assert admin_id2 in active

        # Переключаем одного в режим пользователя
        admin_manager.set_admin_mode(admin_id1, False)
        active = await admin_manager.get_active_admins()
        assert len(active) == 1
        assert admin_id2 in active
        assert admin_id1 not in active

    def test_get_admin_mode_text_admin_mode(self, admin_manager):
        """Тест получения текста режима - режим админа"""
        admin_id = 123456789
        text = admin_manager.get_admin_mode_text(admin_id)
        assert "администратора" in text.lower()

    def test_get_admin_mode_text_user_mode(self, admin_manager):
        """Тест получения текста режима - режим пользователя"""
        admin_id = 123456789
        admin_manager.set_admin_mode(admin_id, False)
        text = admin_manager.get_admin_mode_text(admin_id)
        assert "пользователя" in text.lower()

    def test_get_admin_mode_text_not_admin(self, admin_manager):
        """Тест получения текста режима - не админ"""
        non_admin_id = 111111111
        text = admin_manager.get_admin_mode_text(non_admin_id)
        assert "Не администратор" in text

    def test_format_admin_status_admin_mode(self, admin_manager):
        """Тест форматирования статуса - режим админа"""
        admin_id = 123456789
        status = admin_manager.format_admin_status(admin_id)
        assert "АДМИН" in status

    def test_format_admin_status_user_mode(self, admin_manager):
        """Тест форматирования статуса - режим пользователя"""
        admin_id = 123456789
        admin_manager.set_admin_mode(admin_id, False)
        status = admin_manager.format_admin_status(admin_id)
        assert "ПОЛЬЗ" in status

    def test_format_admin_status_not_admin(self, admin_manager):
        """Тест форматирования статуса - не админ"""
        non_admin_id = 111111111
        status = admin_manager.format_admin_status(non_admin_id)
        assert status == ""

    def test_get_stats(self, admin_manager):
        """Тест получения статистики"""
        stats = admin_manager.get_stats()

        assert stats["total_admins"] == 2
        assert stats["active_admins"] == 2
        assert len(stats["admin_ids"]) == 2
        assert isinstance(stats["modes"], dict)

        # Переключаем одного админа
        admin_manager.set_admin_mode(123456789, False)
        stats = admin_manager.get_stats()
        assert stats["active_admins"] == 1

    @pytest.mark.asyncio
    async def test_sync_admins_from_config(self, admin_manager, mock_supabase_client):
        """Тест синхронизации админов из конфига"""
        await admin_manager.sync_admins_from_config()

        # Проверяем что sync_admin был вызван для каждого админа
        assert mock_supabase_client.sync_admin.call_count == 2

        # Проверяем что режимы установлены
        assert admin_manager.is_in_admin_mode(123456789) is True
        assert admin_manager.is_in_admin_mode(987654321) is True

    @pytest.mark.asyncio
    async def test_sync_admins_from_config_empty(self, mock_config, mock_supabase_client):
        """Тест синхронизации при пустом списке админов"""
        mock_config.ADMIN_TELEGRAM_IDS = []
        admin_manager = AdminManager(mock_config, mock_supabase_client)

        await admin_manager.sync_admins_from_config()

        # Не должно быть вызовов
        mock_supabase_client.sync_admin.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_admin_info(self, admin_manager, mock_supabase_client):
        """Тест обновления информации об админе"""
        from aiogram.types import User

        user = User(id=123456789, is_bot=False, first_name="Test", last_name="Admin", username="testadmin")

        await admin_manager.update_admin_info(user)

        mock_supabase_client.sync_admin.assert_called_once()
        call_args = mock_supabase_client.sync_admin.call_args[0][0]
        assert call_args["telegram_id"] == 123456789
        assert call_args["username"] == "testadmin"
        assert call_args["first_name"] == "Test"
        assert call_args["last_name"] == "Admin"

    @pytest.mark.asyncio
    async def test_update_admin_info_not_admin(self, admin_manager, mock_supabase_client):
        """Тест обновления информации для не-админа"""
        from aiogram.types import User

        user = User(id=111111111, is_bot=False, first_name="Regular", last_name="User")

        await admin_manager.update_admin_info(user)

        # Не должно быть вызовов для не-админа
        mock_supabase_client.sync_admin.assert_not_called()

    @pytest.mark.asyncio
    async def test_notify_admins(self, admin_manager):
        """Тест уведомления админов"""
        from smart_bot_factory.utils.context import ctx

        with patch.object(ctx, "bot") as mock_bot:
            mock_bot.send_message = AsyncMock()

            sent_count = await admin_manager.notify_admins("Test message")

            # Оба админа должны получить уведомление
            assert sent_count == 2
            assert mock_bot.send_message.call_count == 2

    @pytest.mark.asyncio
    async def test_notify_admins_exclude(self, admin_manager):
        """Тест уведомления админов с исключением"""
        from smart_bot_factory.utils.context import ctx

        with patch.object(ctx, "bot") as mock_bot:
            mock_bot.send_message = AsyncMock()

            sent_count = await admin_manager.notify_admins("Test message", exclude_admin=123456789)

            # Только один админ должен получить уведомление
            assert sent_count == 1
            assert mock_bot.send_message.call_count == 1

    @pytest.mark.asyncio
    async def test_notify_admins_no_active(self, admin_manager):
        """Тест уведомления когда нет активных админов"""
        # Переключаем всех в режим пользователя
        admin_manager.set_admin_mode(123456789, False)
        admin_manager.set_admin_mode(987654321, False)

        from smart_bot_factory.utils.context import ctx

        with patch.object(ctx, "bot") as mock_bot:
            mock_bot.send_message = AsyncMock()

            sent_count = await admin_manager.notify_admins("Test message")

            # Никто не должен получить уведомление
            assert sent_count == 0
            mock_bot.send_message.assert_not_called()
