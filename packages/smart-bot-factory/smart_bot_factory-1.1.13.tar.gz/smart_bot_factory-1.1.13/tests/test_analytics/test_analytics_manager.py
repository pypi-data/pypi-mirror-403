"""Тесты для AnalyticsManager"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest

from smart_bot_factory.analytics.analytics_manager import AnalyticsManager


class TestAnalyticsManager:
    """Тесты для класса AnalyticsManager"""

    @pytest.fixture
    def mock_supabase_client(self):
        """Фикстура для мок Supabase клиента"""
        client = Mock()
        client.bot_id = "test-bot"
        client.client = Mock()

        # Настраиваем мок для запроса новых пользователей
        mock_users_query = Mock()
        mock_users_query.eq.return_value = mock_users_query
        mock_users_query.neq.return_value = mock_users_query
        mock_users_query.gte.return_value = mock_users_query
        mock_users_query.execute.return_value = Mock(data=[{"id": 1}])

        mock_table = Mock()
        mock_table.select.return_value = mock_users_query
        client.client.table.return_value = mock_table

        client.get_funnel_stats = AsyncMock(
            return_value={
                "total_sessions": 100,
                "total_unique_users": 80,
                "stages": {
                    "introduction": 50,
                    "consult": 30,
                    "offer": 15,
                    "contacts": 5,
                },
                "avg_quality": 6.5,
            }
        )
        client.get_events_stats = AsyncMock(
            return_value={
                "телефон": 10,
                "консультация": 20,
                "покупка": 5,
            }
        )
        client.get_active_session = AsyncMock(
            return_value={
                "id": "session-123",
                "current_stage": "consult",
                "lead_quality_score": 7,
                "created_at": "2024-01-01T12:00:00Z",
            }
        )
        return client

    @pytest.fixture
    def analytics_manager(self, mock_supabase_client):
        """Фикстура для AnalyticsManager"""
        return AnalyticsManager(mock_supabase_client)

    @pytest.mark.asyncio
    async def test_get_funnel_stats(self, analytics_manager, mock_supabase_client):
        """Тест получения статистики воронки"""
        stats = await analytics_manager.get_funnel_stats(days=7)

        assert stats["total_sessions"] == 100
        assert stats["total_unique_users"] == 80
        assert "new_users" in stats
        assert stats["period_days"] == 7
        assert "stages" in stats
        assert stats["avg_quality"] == 6.5

    @pytest.mark.asyncio
    async def test_get_funnel_stats_with_new_users(self, analytics_manager, mock_supabase_client):
        """Тест получения статистики с новыми пользователями"""
        # Переопределяем мок для запроса новых пользователей
        mock_users_query = Mock()
        mock_users_query.eq.return_value = mock_users_query
        mock_users_query.neq.return_value = mock_users_query
        mock_users_query.gte.return_value = mock_users_query
        mock_users_query.execute.return_value = Mock(data=[{"id": 1}, {"id": 2}, {"id": 3}])

        mock_table = Mock()
        mock_table.select.return_value = mock_users_query
        mock_supabase_client.client.table.return_value = mock_table

        stats = await analytics_manager.get_funnel_stats(days=7)

        assert stats["new_users"] == 3

    @pytest.mark.asyncio
    async def test_get_funnel_stats_error(self, analytics_manager, mock_supabase_client):
        """Тест обработки ошибки при получении статистики"""
        mock_supabase_client.get_funnel_stats = AsyncMock(side_effect=Exception("Error"))

        stats = await analytics_manager.get_funnel_stats(days=7)

        assert stats["total_sessions"] == 0
        assert stats["new_users"] == 0
        assert stats["period_days"] == 7

    @pytest.mark.asyncio
    async def test_get_events_stats(self, analytics_manager, mock_supabase_client):
        """Тест получения статистики событий"""
        events = await analytics_manager.get_events_stats(days=7)

        assert events["телефон"] == 10
        assert events["консультация"] == 20
        assert events["покупка"] == 5

    @pytest.mark.asyncio
    async def test_get_events_stats_error(self, analytics_manager, mock_supabase_client):
        """Тест обработки ошибки при получении статистики событий"""
        mock_supabase_client.get_events_stats = AsyncMock(side_effect=Exception("Error"))

        events = await analytics_manager.get_events_stats(days=7)

        assert events == {}

    @pytest.mark.asyncio
    async def test_get_user_journey(self, analytics_manager, mock_supabase_client):
        """Тест получения истории пользователя"""
        # Мокаем запросы сообщений и событий
        mock_messages_query = Mock()
        mock_messages_query.eq.return_value = mock_messages_query
        mock_messages_query.neq.return_value = mock_messages_query
        mock_messages_query.order.return_value = mock_messages_query
        mock_messages_query.execute.return_value = Mock(
            data=[
                {"role": "user", "content": "Привет", "created_at": "2024-01-01T12:00:00Z", "message_type": "text"},
                {"role": "assistant", "content": "Здравствуйте", "created_at": "2024-01-01T12:01:00Z", "message_type": "text"},
            ]
        )

        mock_events_query = Mock()
        mock_events_query.eq.return_value = mock_events_query
        mock_events_query.order.return_value = mock_events_query
        mock_events_query.execute.return_value = Mock(
            data=[
                {"event_type": "телефон", "event_info": "+1234567890", "created_at": "2024-01-01T12:02:00Z"},
            ]
        )

        mock_table = Mock()
        mock_table.select.return_value = mock_messages_query
        mock_supabase_client.client.table.return_value = mock_table

        # Первый вызов для сообщений, второй для событий
        def table_side_effect(table_name):
            if table_name == "sales_messages":
                return mock_table
            elif table_name == "session_events":
                mock_table.select.return_value = mock_events_query
                return mock_table
            return mock_table

        mock_supabase_client.client.table.side_effect = table_side_effect

        journey = await analytics_manager.get_user_journey(user_id=123456)

        assert len(journey) == 1
        assert journey[0]["id"] == "session-123"
        assert len(journey[0]["messages"]) == 2
        assert len(journey[0]["events"]) == 1

    @pytest.mark.asyncio
    async def test_get_user_journey_no_session(self, analytics_manager, mock_supabase_client):
        """Тест получения истории когда нет активной сессии"""
        mock_supabase_client.get_active_session = AsyncMock(return_value=None)

        journey = await analytics_manager.get_user_journey(user_id=123456)

        assert journey == []

    @pytest.mark.asyncio
    async def test_get_user_journey_error(self, analytics_manager, mock_supabase_client):
        """Тест обработки ошибки при получении истории"""
        mock_supabase_client.get_active_session = AsyncMock(side_effect=Exception("Error"))

        journey = await analytics_manager.get_user_journey(user_id=123456)

        assert journey == []

    def test_truncate_message_for_history_short(self, analytics_manager):
        """Тест сокращения короткого сообщения"""
        text = "Короткое сообщение"
        result = analytics_manager._truncate_message_for_history(text)

        assert result == text

    def test_truncate_message_for_history_long(self, analytics_manager):
        """Тест сокращения длинного сообщения"""
        text = "a" * 200
        result = analytics_manager._truncate_message_for_history(text, max_length=150)

        assert len(result) == 150
        assert result.endswith("...")

    def test_truncate_message_for_history_empty(self, analytics_manager):
        """Тест сокращения пустого сообщения"""
        result = analytics_manager._truncate_message_for_history("")

        assert result == ""

    def test_truncate_message_for_history_with_newlines(self, analytics_manager):
        """Тест сокращения сообщения с переносами строк"""
        text = "Строка 1\nСтрока 2\nСтрока 3"
        result = analytics_manager._truncate_message_for_history(text)

        assert "\n" not in result
        assert "Строка 1" in result

    def test_format_funnel_stats(self, analytics_manager):
        """Тест форматирования статистики воронки"""
        stats = {
            "total_sessions": 100,
            "total_unique_users": 80,
            "new_users": 20,
            "period_days": 7,
            "stages": {
                "introduction": 50,
                "consult": 30,
                "offer": 15,
                "contacts": 5,
            },
            "avg_quality": 6.5,
        }

        result = analytics_manager.format_funnel_stats(stats)

        assert "ВОРОНКА ЗА 7 ДНЕЙ" in result
        assert "80" in result
        assert "20" in result
        assert "Знакомство" in result
        assert "6.5" in result

    def test_format_funnel_stats_empty(self, analytics_manager):
        """Тест форматирования пустой статистики"""
        stats = {"total_sessions": 0}

        result = analytics_manager.format_funnel_stats(stats)

        assert "Нет данных" in result

    def test_format_events_stats(self, analytics_manager):
        """Тест форматирования статистики событий"""
        events = {
            "телефон": 10,
            "консультация": 20,
            "покупка": 5,
        }

        result = analytics_manager.format_events_stats(events)

        assert "СОБЫТИЯ" in result
        assert "10" in result
        assert "20" in result
        assert "5" in result

    def test_format_events_stats_empty(self, analytics_manager):
        """Тест форматирования пустой статистики событий"""
        result = analytics_manager.format_events_stats({})

        assert "нет данных" in result

    def test_format_user_journey(self, analytics_manager):
        """Тест форматирования истории пользователя"""
        journey = [
            {
                "id": "session-123",
                "current_stage": "consult",
                "lead_quality_score": 7,
                "created_at": "2024-01-01T12:00:00Z",
                "messages": [
                    {"role": "user", "content": "Привет", "created_at": "2024-01-01T12:00:00Z"},
                    {"role": "assistant", "content": "Здравствуйте", "created_at": "2024-01-01T12:01:00Z"},
                ],
                "events": [
                    {"event_type": "телефон", "event_info": "+1234567890", "created_at": "2024-01-01T12:02:00Z"},
                ],
            }
        ]

        result = analytics_manager.format_user_journey(user_id=123456, journey=journey)

        assert "Пользователь 123456" in result
        assert "consult" in result
        assert "7" in result
        assert "2 сообщений" in result
        assert "1 событий" in result
        assert "Привет" in result
        assert "Здравствуйте" in result

    def test_format_user_journey_empty(self, analytics_manager):
        """Тест форматирования пустой истории"""
        result = analytics_manager.format_user_journey(user_id=123456, journey=[])

        assert "История не найдена" in result

    def test_format_user_journey_long_message(self, analytics_manager):
        """Тест форматирования истории с длинным сообщением"""
        long_content = "a" * 300
        journey = [
            {
                "id": "session-123",
                "current_stage": "consult",
                "lead_quality_score": 7,
                "created_at": "2024-01-01T12:00:00Z",
                "messages": [
                    {"role": "user", "content": long_content, "created_at": "2024-01-01T12:00:00Z"},
                ],
                "events": [],
            }
        ]

        result = analytics_manager.format_user_journey(user_id=123456, journey=journey)

        assert "..." in result
        assert len([line for line in result.split("\n") if long_content[:197] in line]) > 0

    @pytest.mark.asyncio
    async def test_get_daily_summary(self, analytics_manager, mock_supabase_client):
        """Тест получения сводки за сегодня"""
        summary = await analytics_manager.get_daily_summary()

        assert "СВОДКА ЗА СЕГОДНЯ" in summary
        assert "События" in summary

    @pytest.mark.asyncio
    async def test_get_daily_summary_error(self, analytics_manager, mock_supabase_client):
        """Тест обработки ошибки при получении сводки"""
        # Мокаем ошибку в get_funnel_stats
        mock_supabase_client.get_funnel_stats = AsyncMock(side_effect=Exception("Error"))
        # get_events_stats тоже должен вернуть ошибку или пустой словарь
        mock_supabase_client.get_events_stats = AsyncMock(return_value={})

        summary = await analytics_manager.get_daily_summary()

        # При ошибке в get_funnel_stats возвращается дефолтное значение, но может быть ошибка в get_events_stats
        # Проверяем что сводка содержит либо ошибку, либо дефолтные значения
        assert "СВОДКА" in summary or "Ошибка" in summary or "❌" in summary

    @pytest.mark.asyncio
    async def test_get_performance_metrics(self, analytics_manager, mock_supabase_client):
        """Тест получения метрик производительности"""
        metrics = await analytics_manager.get_performance_metrics()

        assert "total_sessions_7d" in metrics
        assert "conversion_rates" in metrics
        assert "avg_quality" in metrics
        assert metrics["total_sessions_7d"] == 100

    @pytest.mark.asyncio
    async def test_get_performance_metrics_with_conversions(self, analytics_manager, mock_supabase_client):
        """Тест получения метрик с конверсиями"""
        mock_supabase_client.get_funnel_stats = AsyncMock(
            return_value={
                "total_sessions": 100,
                "stages": {
                    "introduction": 50,
                    "consult": 30,
                    "offer": 15,
                    "contacts": 5,
                },
                "avg_quality": 6.5,
            }
        )

        metrics = await analytics_manager.get_performance_metrics()

        assert "conversion_rates" in metrics
        conversions = metrics["conversion_rates"]
        assert "intro_to_consult" in conversions
        assert "consult_to_offer" in conversions
        assert "offer_to_contacts" in conversions
        assert "intro_to_contacts" in conversions

    @pytest.mark.asyncio
    async def test_get_performance_metrics_error(self, analytics_manager, mock_supabase_client):
        """Тест обработки ошибки при получении метрик"""
        mock_supabase_client.get_funnel_stats = AsyncMock(side_effect=Exception("Error"))

        metrics = await analytics_manager.get_performance_metrics()

        # При ошибке возвращается пустой словарь или словарь с дефолтными значениями
        assert isinstance(metrics, dict)
        # Проверяем что метрики не содержат реальных данных
        assert metrics.get("total_sessions_7d", 0) == 0 or metrics == {}

    def test_format_performance_metrics(self, analytics_manager):
        """Тест форматирования метрик производительности"""
        metrics = {
            "total_sessions_7d": 100,
            "avg_quality": 6.5,
            "conversion_rates": {
                "intro_to_consult": 60.0,
                "consult_to_offer": 50.0,
                "offer_to_contacts": 33.3,
                "intro_to_contacts": 10.0,
            },
        }

        result = analytics_manager.format_performance_metrics(metrics)

        assert "МЕТРИКИ ЭФФЕКТИВНОСТИ" in result
        assert "100" in result
        assert "6.5" in result
        assert "КОНВЕРСИИ" in result
        assert "60.0" in result

    def test_format_performance_metrics_empty(self, analytics_manager):
        """Тест форматирования пустых метрик"""
        result = analytics_manager.format_performance_metrics({})

        assert "недоступны" in result

    @pytest.mark.asyncio
    async def test_get_top_performing_hours(self, analytics_manager, mock_supabase_client):
        """Тест получения топ часов активности"""
        # Мокаем запрос сообщений
        # Используем фиксированную дату для предсказуемости
        base_date = datetime(2024, 1, 1, 12, 0, 0)  # Фиксированная дата
        mock_messages = [
            {"created_at": (base_date.replace(hour=10)).isoformat() + "Z"},
            {"created_at": (base_date.replace(hour=10)).isoformat() + "Z"},
            {"created_at": (base_date.replace(hour=14)).isoformat() + "Z"},
            {"created_at": (base_date.replace(hour=14)).isoformat() + "Z"},
            {"created_at": (base_date.replace(hour=14)).isoformat() + "Z"},
            {"created_at": (base_date.replace(hour=18)).isoformat() + "Z"},
        ]

        mock_query = Mock()
        mock_query.gte.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.execute.return_value = Mock(data=mock_messages)

        mock_table = Mock()
        mock_table.select.return_value = mock_query
        mock_supabase_client.client.table.return_value = mock_table

        hours = await analytics_manager.get_top_performing_hours()

        assert isinstance(hours, list)
        assert len(hours) <= 5
        # Проверяем что час 14 (самый активный - 3 сообщения) присутствует в результате
        assert len(hours) > 0
        assert 14 in hours  # Самый активный час должен быть в топе
        # Проверяем что часы отсортированы по убыванию активности
        assert hours[0] == 14  # Первый должен быть самый активный

    @pytest.mark.asyncio
    async def test_get_top_performing_hours_empty(self, analytics_manager, mock_supabase_client):
        """Тест получения топ часов когда нет данных"""
        mock_query = Mock()
        mock_query.gte.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.execute.return_value = Mock(data=[])

        mock_table = Mock()
        mock_table.select.return_value = mock_query
        mock_supabase_client.client.table.return_value = mock_table

        hours = await analytics_manager.get_top_performing_hours()

        assert hours == []

    @pytest.mark.asyncio
    async def test_get_top_performing_hours_error(self, analytics_manager, mock_supabase_client):
        """Тест обработки ошибки при получении топ часов"""
        mock_supabase_client.client.table.side_effect = Exception("Error")

        hours = await analytics_manager.get_top_performing_hours()

        assert hours == []
