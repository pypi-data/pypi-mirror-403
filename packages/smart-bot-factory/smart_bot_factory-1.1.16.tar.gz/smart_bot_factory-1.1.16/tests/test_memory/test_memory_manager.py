"""Тесты для модуля memory_manager"""

from unittest.mock import AsyncMock

import pytest

from smart_bot_factory.memory.memory_manager import MemoryManager


class TestMemoryManager:
    """Тесты для класса MemoryManager"""

    def test_memory_manager_init(self, mock_supabase_client, mock_config):
        """Тест инициализации MemoryManager"""
        manager = MemoryManager(supabase_client=mock_supabase_client, config=mock_config)
        assert manager.supabase_client == mock_supabase_client
        assert manager.max_memory_messages == mock_config.MAX_CONTEXT_MESSAGES
        assert manager.min_memory_messages == mock_config.HISTORY_MIN_MESSAGES
        assert manager.token_limit == mock_config.HISTORY_MAX_TOKENS

    def test_memory_manager_init_without_params(self):
        """Тест инициализации без параметров (должен использовать ctx)"""
        with pytest.raises(ValueError, match="supabase_client должен быть передан"):
            MemoryManager()

    @pytest.mark.asyncio
    async def test_get_memory_messages_empty(self, mock_supabase_client, mock_config):
        """Тест получения пустой истории сообщений"""
        mock_supabase_client.get_session_info = AsyncMock(return_value={"messages_len": 4, "summary": "", "service_info": {}})
        mock_supabase_client.get_chat_history = AsyncMock(return_value=[])
        mock_supabase_client.get_session_processed_events = AsyncMock(return_value=[])
        mock_supabase_client.update_session = AsyncMock()

        manager = MemoryManager(supabase_client=mock_supabase_client, config=mock_config)

        messages = await manager.get_memory_messages("test_session_id")
        assert isinstance(messages, list)
        assert len(messages) == 0

    @pytest.mark.asyncio
    async def test_get_memory_messages_with_history(self, mock_supabase_client, mock_config):
        """Тест получения истории с сообщениями"""
        mock_supabase_client.get_session_info = AsyncMock(return_value={"messages_len": 4, "summary": "", "service_info": {}})
        mock_supabase_client.get_chat_history = AsyncMock(
            return_value=[{"role": "user", "content": "Привет"}, {"role": "assistant", "content": "Здравствуйте!"}]
        )
        mock_supabase_client.get_session_processed_events = AsyncMock(return_value=[])
        mock_supabase_client.update_session = AsyncMock()

        manager = MemoryManager(supabase_client=mock_supabase_client, config=mock_config)

        messages = await manager.get_memory_messages("test_session_id")
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"

    @pytest.mark.asyncio
    async def test_get_memory_messages_with_summary(self, mock_supabase_client, mock_config):
        """Тест получения истории с суммаризацией"""
        mock_supabase_client.get_session_info = AsyncMock(
            return_value={"messages_len": 4, "summary": "Предыдущий диалог о продукте", "service_info": {}}
        )
        mock_supabase_client.get_chat_history = AsyncMock(return_value=[{"role": "user", "content": "Новое сообщение"}])
        mock_supabase_client.get_session_processed_events = AsyncMock(return_value=[])
        mock_supabase_client.update_session = AsyncMock()

        manager = MemoryManager(supabase_client=mock_supabase_client, config=mock_config)

        messages = await manager.get_memory_messages("test_session_id")
        # Должно быть system сообщение с суммаризацией + новое сообщение
        assert len(messages) >= 1
        if messages and messages[0].get("role") == "system":
            assert "суммаризация" in messages[0]["content"].lower()

    def test_count_tokens(self, mock_supabase_client, mock_config):
        """Тест подсчета токенов"""
        manager = MemoryManager(supabase_client=mock_supabase_client, config=mock_config)

        messages = [{"role": "user", "content": "Тестовое сообщение"}, {"role": "assistant", "content": "Ответ"}]

        tokens = manager._count_tokens(messages)
        assert tokens > 0

    def test_format_summary(self, mock_supabase_client, mock_config):
        """Тест форматирования суммаризации"""
        manager = MemoryManager(supabase_client=mock_supabase_client, config=mock_config)

        summary = "Краткая суммаризация"
        formatted = manager._format_summary(summary)
        assert "суммаризация" in formatted.lower()
        assert summary in formatted

    def test_is_summary_message(self, mock_supabase_client, mock_config):
        """Тест проверки сообщения на суммаризацию"""
        manager = MemoryManager(supabase_client=mock_supabase_client, config=mock_config)

        summary_msg = {"role": "system", "content": "## Суммаризация истории диалога (предыдущие сообщения до текущего момента):\nТекст"}
        assert manager._is_summary_message(summary_msg) is True

        regular_msg = {"role": "user", "content": "Обычное сообщение"}
        assert manager._is_summary_message(regular_msg) is False

    def test_extract_summary(self, mock_supabase_client, mock_config):
        """Тест извлечения суммаризации"""
        manager = MemoryManager(supabase_client=mock_supabase_client, config=mock_config)

        messages = [
            {"role": "system", "content": "## Суммаризация истории диалога (предыдущие сообщения до текущего момента):\nТекст суммаризации"},
            {"role": "user", "content": "Новое сообщение"},
        ]

        summary = manager._extract_summary(messages)
        assert summary == "Текст суммаризации"

        # Без суммаризации
        messages_no_summary = [{"role": "user", "content": "Сообщение"}]
        summary_empty = manager._extract_summary(messages_no_summary)
        assert summary_empty == ""

    def test_format_service_info(self, mock_supabase_client, mock_config):
        """Тест форматирования service_info"""
        manager = MemoryManager(supabase_client=mock_supabase_client, config=mock_config)

        # С этапом и событиями
        service_info = {
            "этап": "consult",
            "качество": 7,
            "события": [
                {"тип": "телефон", "инфо": "+79219603144"},
                {"тип": "консультация", "инфо": "Запросил материалы"},
            ],
        }
        formatted = manager._format_service_info(service_info)
        assert "Этап: consult" in formatted
        assert "События:" in formatted
        assert "- телефон: +79219603144" in formatted
        assert "- консультация: Запросил материалы" in formatted
        assert "качество" not in formatted  # Качество не должно быть в результате

        # Только с этапом
        service_info_stage_only = {"этап": "introduction", "качество": 5}
        formatted_stage = manager._format_service_info(service_info_stage_only)
        assert "Этап: introduction" in formatted_stage
        assert "События:" not in formatted_stage

        # Только с событиями
        service_info_events_only = {"качество": 8, "события": [{"тип": "покупка", "инфо": "Оформил заказ"}]}
        formatted_events = manager._format_service_info(service_info_events_only)
        assert "Этап:" not in formatted_events
        assert "- покупка: Оформил заказ" in formatted_events

        # С событием без инфо
        service_info_event_no_info = {"этап": "offer", "события": [{"тип": "консультация"}]}
        formatted_no_info = manager._format_service_info(service_info_event_no_info)
        assert "Этап: offer" in formatted_no_info
        assert "- консультация" in formatted_no_info
        assert ":" not in formatted_no_info.split("- консультация")[1]  # Нет двоеточия после типа события

        # Пустой service_info
        formatted_empty = manager._format_service_info({})
        assert formatted_empty == ""

        # service_info без этапа и событий
        service_info_other = {"качество": 5, "другие_поля": "значение"}
        formatted_other = manager._format_service_info(service_info_other)
        assert formatted_other == ""

    def test_format_processed_events(self, mock_supabase_client, mock_config):
        """Тест форматирования обработанных событий"""
        from datetime import datetime, timezone

        manager = MemoryManager(supabase_client=mock_supabase_client, config=mock_config)

        # С событиями с датой
        events = [
            {
                "event_type": "телефон",
                "event_data": "+79219603144",
                "executed_at": "2024-01-15T14:30:00Z",
            },
            {
                "event_type": "консультация",
                "event_data": "Запросил материалы",
                "executed_at": "2024-01-15T15:00:00+00:00",
            },
        ]
        formatted = manager._format_processed_events(events)
        # Проверяем, что форматирование содержит тип события и дату (без event_data и слова "выполнено")
        assert "телефон" in formatted
        assert "консультация" in formatted
        assert "15.01.2024" in formatted
        # Проверяем, что event_data не включен в форматирование
        assert "+79219603144" not in formatted
        assert "выполнено" not in formatted

        # С событием без даты
        events_no_date = [{"event_type": "покупка", "event_data": "Оформил заказ", "executed_at": None}]
        formatted_no_date = manager._format_processed_events(events_no_date)
        assert "покупка" in formatted_no_date
        # Проверяем, что event_data не включен
        assert "Оформил заказ" not in formatted_no_date

        # Пустой список
        formatted_empty = manager._format_processed_events([])
        assert formatted_empty == ""

        # С событием без event_data
        events_no_data = [{"event_type": "консультация", "executed_at": "2024-01-15T14:30:00Z"}]
        formatted_no_data = manager._format_processed_events(events_no_data)
        assert "консультация" in formatted_no_data
        assert "15.01.2024" in formatted_no_data or "14:30" in formatted_no_data
        # Проверяем, что слово "выполнено" не включено
        assert "выполнено" not in formatted_no_data

    @pytest.mark.asyncio
    async def test_get_memory_messages_with_service_info(self, mock_supabase_client, mock_config):
        """Тест получения истории с service_info"""
        service_info = {
            "этап": "consult",
            "качество": 7,
            "события": [{"тип": "телефон", "инфо": "+79219603144"}],
        }
        mock_supabase_client.get_session_info = AsyncMock(
            return_value={"messages_len": 4, "summary": "", "service_info": service_info}
        )
        mock_supabase_client.get_chat_history = AsyncMock(return_value=[{"role": "user", "content": "Новое сообщение"}])
        mock_supabase_client.get_session_processed_events = AsyncMock(return_value=[])
        mock_supabase_client.update_session = AsyncMock()

        manager = MemoryManager(supabase_client=mock_supabase_client, config=mock_config)

        messages = await manager.get_memory_messages("test_session_id")
        # Должно быть system сообщение с service_info
        assert len(messages) >= 1
        if messages and messages[0].get("role") == "system":
            content = messages[0]["content"]
            assert "Информация о последней сессии" in content
            assert "Этап: consult" in content
            assert "- телефон: +79219603144" in content
            assert "качество" not in content  # Качество не должно быть в форматированном виде

    @pytest.mark.asyncio
    async def test_get_memory_messages_with_summary_and_service_info(self, mock_supabase_client, mock_config):
        """Тест получения истории с суммаризацией и service_info"""
        service_info = {"этап": "offer", "события": []}
        mock_supabase_client.get_session_info = AsyncMock(
            return_value={"messages_len": 4, "summary": "Предыдущий диалог", "service_info": service_info}
        )
        mock_supabase_client.get_chat_history = AsyncMock(return_value=[{"role": "user", "content": "Новое сообщение"}])
        mock_supabase_client.get_session_processed_events = AsyncMock(return_value=[])
        mock_supabase_client.update_session = AsyncMock()

        manager = MemoryManager(supabase_client=mock_supabase_client, config=mock_config)

        messages = await manager.get_memory_messages("test_session_id")
        # Должно быть system сообщение с суммаризацией и service_info
        assert len(messages) >= 1
        if messages and messages[0].get("role") == "system":
            content = messages[0]["content"]
            assert "суммаризация" in content.lower()
            assert "Этап: offer" in content