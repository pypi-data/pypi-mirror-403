"""Тесты для модуля integrations.supabase_client"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from smart_bot_factory.integrations.supabase_client import SupabaseClient


class TestSupabaseClient:
    """Тесты для класса SupabaseClient"""

    def test_supabase_client_init(self):
        """Тест инициализации клиента"""
        client = SupabaseClient(url="https://test.supabase.co", key="test_key", bot_id="test-bot")
        assert client.url == "https://test.supabase.co"
        assert client.key == "test_key"
        assert client.bot_id == "test-bot"
        assert client.client is None

    def test_supabase_client_init_without_bot_id(self):
        """Тест инициализации без bot_id"""
        client = SupabaseClient(url="https://test.supabase.co", key="test_key")
        assert client.bot_id is None

    @pytest.mark.asyncio
    async def test_initialize(self):
        """Тест инициализации соединения"""
        with patch("smart_bot_factory.integrations.supabase_client.create_client") as mock_create:
            mock_client = Mock()
            mock_create.return_value = mock_client

            client = SupabaseClient(url="https://test.supabase.co", key="test_key")
            await client.initialize()

            assert client.client == mock_client
            mock_create.assert_called_once_with("https://test.supabase.co", "test_key")

    @pytest.mark.asyncio
    async def test_create_or_get_user_new(self):
        """Тест создания нового пользователя"""
        client = SupabaseClient(url="https://test.supabase.co", key="test_key", bot_id="test-bot")

        # Создаем правильную структуру моков для цепочки вызовов
        mock_table = Mock()

        # Первый запрос - проверка существования пользователя (пустой результат)
        mock_query1 = Mock()
        mock_response1 = Mock()
        mock_response1.data = []  # Пользователь не найден
        mock_query1.execute.return_value = mock_response1

        # Настраиваем цепочку: table().select().eq().eq().execute() (с bot_id)
        select_mock = Mock()
        eq_mock1 = Mock()
        eq_mock2 = Mock()
        eq_mock2.execute.return_value = mock_response1
        eq_mock1.eq.return_value = eq_mock2
        select_mock.eq.return_value = eq_mock1
        mock_table.select.return_value = select_mock

        # Второй запрос - вставка нового пользователя
        mock_insert_query = Mock()
        mock_insert_response = Mock()
        mock_insert_response.data = [{"telegram_id": 123456}]
        mock_insert_query.execute.return_value = mock_insert_response
        mock_table.insert.return_value = mock_insert_query

        client.client = Mock()
        client.client.table.return_value = mock_table

        user_data = {"telegram_id": 123456, "username": "test_user", "first_name": "Test", "last_name": "User"}

        user_id = await client.create_or_get_user(user_data)
        assert user_id == 123456

    @pytest.mark.asyncio
    async def test_create_or_get_user_existing(self):
        """Тест получения существующего пользователя"""
        client = SupabaseClient(url="https://test.supabase.co", key="test_key", bot_id="test-bot")

        mock_table = Mock()

        # Первый запрос - проверка существования пользователя (найден)
        mock_query1 = Mock()
        mock_response1 = Mock()
        mock_response1.data = [{"telegram_id": 123456}]
        mock_query1.execute.return_value = mock_response1
        mock_table.select.return_value.eq.return_value = mock_query1

        # Второй запрос - получение существующих UTM данных
        mock_query2 = Mock()
        mock_response2 = Mock()
        mock_response2.data = [{"source": None, "medium": None, "campaign": None, "content": None, "term": None, "segments": None}]
        mock_query2.execute.return_value = mock_response2

        # Настраиваем вторую цепочку вызовов
        mock_table2 = Mock()
        mock_table2.select.return_value.eq.return_value.eq.return_value = mock_query2

        # Третий запрос - обновление пользователя
        mock_update_query = Mock()
        mock_update_response = Mock()
        mock_update_response.data = None
        mock_update_query.eq.return_value.eq.return_value.execute.return_value = mock_update_response
        mock_table.update.return_value = mock_update_query

        # Настраиваем table() чтобы возвращал разные моки для разных вызовов
        call_count = [0]

        def table_side_effect(table_name):
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_table  # Первый вызов для проверки существования
            elif call_count[0] == 2:
                return mock_table2  # Второй вызов для получения UTM
            else:
                return mock_table  # Третий вызов для обновления

        client.client = Mock()
        client.client.table.side_effect = table_side_effect

        user_data = {"telegram_id": 123456, "username": "test_user", "first_name": "Test", "last_name": "User"}

        user_id = await client.create_or_get_user(user_data)
        assert user_id == 123456

    @pytest.mark.asyncio
    async def test_create_chat_session(self):
        """Тест создания сессии чата"""
        client = SupabaseClient(url="https://test.supabase.co", key="test_key", bot_id="test-bot")

        mock_table = Mock()
        mock_insert = Mock()
        mock_insert.execute.return_value = Mock(data=[{"id": "session_123"}])
        mock_table.insert.return_value = mock_insert
        mock_table.update.return_value.eq.return_value.execute.return_value = Mock()

        client.client = Mock()
        client.client.table.return_value = mock_table

        # Мокаем create_or_get_user и close_active_sessions
        client.create_or_get_user = AsyncMock(return_value=123456)
        client.close_active_sessions = AsyncMock()
        client.create_session_analytics = AsyncMock()

        user_data = {"telegram_id": 123456, "username": "test_user"}

        session_id = await client.create_chat_session(user_data)
        assert session_id == "session_123"

    @pytest.mark.asyncio
    async def test_get_chat_history(self):
        """Тест получения истории чата"""
        client = SupabaseClient(url="https://test.supabase.co", key="test_key")

        mock_table = Mock()
        mock_query = Mock()
        # История возвращается в обратном порядке, потом переворачивается
        mock_response = Mock()
        mock_response.data = [{"role": "assistant", "content": "Здравствуйте!"}, {"role": "user", "content": "Привет"}]
        mock_query.execute.return_value = mock_response
        # 🆕 Обновлена цепочка моков: добавлен .neq() для фильтрации system сообщений на уровне БД
        mock_table.select.return_value.eq.return_value.neq.return_value.order.return_value.limit.return_value = mock_query

        client.client = Mock()
        client.client.table.return_value = mock_table

        history = await client.get_chat_history("session_123", limit=10)
        assert len(history) == 2
        # После reverse порядок меняется
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"

    @pytest.mark.asyncio
    async def test_add_message(self):
        """Тест добавления сообщения"""
        client = SupabaseClient(url="https://test.supabase.co", key="test_key")

        mock_table = Mock()
        mock_insert = Mock()
        mock_insert.execute.return_value = Mock(data=[{"id": 1}])
        mock_table.insert.return_value = mock_insert

        client.client = Mock()
        client.client.table.return_value = mock_table
        client.update_session_analytics = AsyncMock()

        message_id = await client.add_message(session_id="session_123", role="user", content="Тестовое сообщение")
        assert message_id == 1

    @pytest.mark.asyncio
    async def test_get_active_session(self):
        """Тест получения активной сессии"""
        client = SupabaseClient(url="https://test.supabase.co", key="test_key", bot_id="test-bot")

        # Создаем правильную структуру моков с реальным списком данных
        session_data = [{"id": "session_123", "current_stage": "introduction"}]

        # Используем MagicMock для правильной работы с атрибутами
        from unittest.mock import MagicMock

        mock_response = MagicMock()
        mock_response.data = session_data  # Используем реальный список

        # Настраиваем цепочку: table().select().eq().eq().eq().execute() (с bot_id)
        # Порядок: table -> select -> eq(user_id) -> eq(status) -> eq(bot_id) -> execute
        mock_table = MagicMock()
        select_mock = MagicMock()
        eq_mock1 = MagicMock()  # для user_id
        eq_mock2 = MagicMock()  # для status
        eq_mock3 = MagicMock()  # для bot_id
        eq_mock3.execute.return_value = mock_response
        eq_mock2.eq.return_value = eq_mock3
        eq_mock1.eq.return_value = eq_mock2
        select_mock.eq.return_value = eq_mock1
        mock_table.select.return_value = select_mock

        client.client = MagicMock()
        client.client.table.return_value = mock_table

        session = await client.get_active_session(123456)
        assert session is not None
        assert session["id"] == "session_123"

    @pytest.mark.asyncio
    async def test_get_active_session_not_found(self):
        """Тест получения несуществующей активной сессии"""
        client = SupabaseClient(url="https://test.supabase.co", key="test_key")

        mock_table = Mock()
        mock_query = Mock()
        mock_response = Mock()
        mock_response.data = []
        mock_query.execute.return_value = mock_response
        mock_table.select.return_value.eq.return_value.eq.return_value = mock_query

        client.client = Mock()
        client.client.table.return_value = mock_table

        session = await client.get_active_session(123456)
        assert session is None
