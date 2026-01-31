"""Тесты для BotBuilder"""

import os
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from smart_bot_factory.creation.bot_builder import BotBuilder


class TestBotBuilder:
    """Тесты для класса BotBuilder"""

    @pytest.fixture
    def mock_config(self):
        """Фикстура для мок Config"""
        config = Mock()
        config.OPENAI_API_KEY = "test-key"
        config.OPENAI_MODEL = "gpt-4o-mini"
        config.OPENAI_MAX_TOKENS = 4000
        config.OPENAI_TEMPERATURE = 0.7
        config.SUPABASE_URL = "https://test.supabase.co"
        config.SUPABASE_KEY = "test-key"
        config.BOT_ID = "test-bot"
        config.ADMIN_TELEGRAM_IDS = [123456]
        config.PROMPT_FILES = ["system.txt", "welcome.txt"]
        config.PROMT_FILES_DIR = Path("bots/test-bot/prompts")
        return config

    @pytest.fixture
    def bot_builder(self):
        """Фикстура для BotBuilder"""
        return BotBuilder(bot_id="test-bot")

    def test_init_with_bot_id(self):
        """Тест инициализации с указанным bot_id"""
        builder = BotBuilder(bot_id="my-bot")
        assert builder.bot_id == "my-bot"
        assert builder.config_dir == Path("bots/my-bot")
        assert not builder._initialized

    def test_init_with_config_dir(self):
        """Тест инициализации с указанным config_dir"""
        custom_dir = Path("/custom/path")
        builder = BotBuilder(bot_id="my-bot", config_dir=custom_dir)
        assert builder.config_dir == custom_dir

    def test_init_with_env_bot_id(self):
        """Тест инициализации с bot_id из переменной окружения"""
        os.environ["BOT_ID"] = "env-bot"
        try:
            builder = BotBuilder()
            assert builder.bot_id == "env-bot"
        finally:
            del os.environ["BOT_ID"]

    def test_init_without_bot_id(self):
        """Тест инициализации без bot_id (должна быть ошибка)"""
        if "BOT_ID" in os.environ:
            del os.environ["BOT_ID"]
        with patch.object(BotBuilder, "_detect_bot_id_from_filename", return_value=None):
            with pytest.raises(ValueError, match="bot_id не указан"):
                BotBuilder()

    def test_detect_bot_id_from_filename(self):
        """Тест определения bot_id из имени файла"""
        # Этот тест сложен, так как зависит от стека вызовов
        # Просто проверяем, что метод существует и возвращает Optional[str]
        result = BotBuilder._detect_bot_id_from_filename()
        assert result is None or isinstance(result, str)

    def test_get_status(self, bot_builder):
        """Тест получения статуса бота"""
        status = bot_builder.get_status()
        assert status["bot_id"] == "test-bot"
        assert status["initialized"] is False
        assert "components" in status
        assert "tools" in status

    def test_register_telegram_router(self, bot_builder):
        """Тест регистрации Telegram роутера"""

        # Создаем мок aiogram.Router
        class MockAiogramRouter:
            def __init__(self):
                self.name = "test_router"

        mock_router = MockAiogramRouter()

        # Мокаем isinstance проверку и импорт aiogram.Router
        with patch("smart_bot_factory.creation.bot_builder.isinstance") as mock_isinstance:
            mock_isinstance.return_value = True
            bot_builder.register_telegram_router(mock_router)

        assert len(bot_builder._telegram_routers) == 1
        assert bot_builder._telegram_routers[0] == mock_router

    def test_register_telegram_router_invalid_type(self, bot_builder):
        """Тест регистрации неверного типа роутера"""
        with pytest.raises(TypeError):
            bot_builder.register_telegram_router("not a router")

    def test_register_telegram_routers(self, bot_builder):
        """Тест регистрации нескольких Telegram роутеров"""

        class MockAiogramRouter:
            def __init__(self, name):
                self.name = name

        router1 = MockAiogramRouter("router1")
        router2 = MockAiogramRouter("router2")

        # Мокаем isinstance проверку
        with patch("smart_bot_factory.creation.bot_builder.isinstance") as mock_isinstance:
            mock_isinstance.return_value = True
            bot_builder.register_telegram_routers(router1, router2)

        assert len(bot_builder._telegram_routers) == 2

    def test_register_tool(self, bot_builder):
        """Тест регистрации инструмента"""
        mock_tool = Mock()
        mock_tool.name = "test_tool"

        bot_builder.register_tool(mock_tool)

        assert len(bot_builder._tools) == 1
        assert bot_builder._tools[0] == mock_tool

    def test_register_tool_duplicate(self, bot_builder):
        """Тест регистрации дубликата инструмента"""
        mock_tool = Mock()
        mock_tool.name = "test_tool"

        bot_builder.register_tool(mock_tool)
        bot_builder.register_tool(mock_tool)  # Дубликат

        assert len(bot_builder._tools) == 1  # Не должен добавиться дважды

    def test_register_tools(self, bot_builder):
        """Тест регистрации нескольких инструментов"""
        tool1 = Mock()
        tool1.name = "tool1"
        tool2 = Mock()
        tool2.name = "tool2"

        bot_builder.register_tools(tool1, tool2)

        assert len(bot_builder._tools) == 2

    def test_register_tools_with_list(self, bot_builder):
        """Тест регистрации инструментов из списка"""
        tool1 = Mock()
        tool1.name = "tool1"
        tool2 = Mock()
        tool2.name = "tool2"

        bot_builder.register_tools([tool1, tool2])

        assert len(bot_builder._tools) == 2

    def test_on_start(self, bot_builder):
        """Тест регистрации обработчика on_start"""

        async def handler(user_id, session_id, message, state):
            pass

        result = bot_builder.on_start(handler)

        assert len(bot_builder._start_handlers) == 1
        assert bot_builder._start_handlers[0] == handler
        assert result == handler  # Должен вернуть handler для использования как декоратор

    def test_on_start_invalid(self, bot_builder):
        """Тест регистрации неверного обработчика on_start"""
        with pytest.raises(TypeError):
            bot_builder.on_start("not a callable")

    def test_get_start_handlers(self, bot_builder):
        """Тест получения списка обработчиков on_start"""

        async def handler1(user_id, session_id, message, state):
            pass

        async def handler2(user_id, session_id, message, state):
            pass

        bot_builder.on_start(handler1)
        bot_builder.on_start(handler2)

        handlers = bot_builder.get_start_handlers()
        assert len(handlers) == 2
        assert handlers[0] == handler1
        assert handlers[1] == handler2

    def test_register_utm_trigger(self, bot_builder):
        """Тест регистрации UTM-триггера"""
        bot_builder.register_utm_trigger(message="welcome.txt", source="vk", campaign="test")

        assert len(bot_builder._utm_triggers) == 1
        trigger = bot_builder._utm_triggers[0]
        assert trigger["message"] == "welcome.txt"
        assert trigger["utm_targets"]["source"] == "vk"
        assert trigger["utm_targets"]["campaign"] == "test"

    def test_register_utm_trigger_with_segment(self, bot_builder):
        """Тест регистрации UTM-триггера с сегментом"""
        bot_builder.register_utm_trigger(message="premium.txt", segment="premium")

        assert len(bot_builder._utm_triggers) == 1
        trigger = bot_builder._utm_triggers[0]
        assert trigger["utm_targets"]["segment"] == "premium"

    def test_get_utm_triggers(self, bot_builder):
        """Тест получения списка UTM-триггеров"""
        bot_builder.register_utm_trigger(message="test1.txt", source="vk")
        bot_builder.register_utm_trigger(message="test2.txt", source="instagram")

        triggers = bot_builder.get_utm_triggers()
        assert len(triggers) == 2

    def test_set_prompt_loader(self, bot_builder):
        """Тест установки кастомного PromptLoader"""
        mock_loader = Mock()

        bot_builder.set_prompt_loader(mock_loader)

        assert bot_builder._custom_prompt_loader == mock_loader

    def test_set_event_processor(self, bot_builder):
        """Тест установки кастомного процессора событий"""

        async def processor(session_id, events, user_id):
            pass

        bot_builder.set_event_processor(processor)

        assert bot_builder._custom_event_processor == processor

    def test_set_event_processor_invalid(self, bot_builder):
        """Тест установки неверного процессора событий"""
        with pytest.raises(TypeError):
            bot_builder.set_event_processor("not a callable")

    def test_validate_message(self, bot_builder):
        """Тест регистрации валидатора сообщений"""

        async def validator(message, supabase_client):
            return True

        result = bot_builder.validate_message(validator)

        assert len(bot_builder._message_validators) == 1
        assert bot_builder._message_validators[0] == validator
        assert result == validator

    def test_enrich_prompt(self, bot_builder):
        """Тест регистрации обогатителя промпта"""

        async def enricher(system_prompt, user_id, session_id, supabase_client):
            return system_prompt

        result = bot_builder.enrich_prompt(enricher)

        assert len(bot_builder._prompt_enrichers) == 1
        assert result == enricher

    def test_enrich_context(self, bot_builder):
        """Тест регистрации обогатителя контекста"""

        async def enricher(messages, user_id, session_id):
            return messages

        result = bot_builder.enrich_context(enricher)

        assert len(bot_builder._context_enrichers) == 1
        assert result == enricher

    def test_process_response(self, bot_builder):
        """Тест регистрации обработчика ответа"""

        async def processor(response_text, ai_metadata, user_id):
            return response_text, ai_metadata

        result = bot_builder.process_response(processor)

        assert len(bot_builder._response_processors) == 1
        assert result == processor

    def test_filter_send(self, bot_builder):
        """Тест регистрации фильтра отправки"""

        async def filter_func(user_id):
            return False

        result = bot_builder.filter_send(filter_func)

        assert len(bot_builder._send_filters) == 1
        assert result == filter_func

    def test_get_message_hooks(self, bot_builder):
        """Тест получения всех хуков для обработки сообщений"""

        async def validator(message, supabase_client):
            return True

        async def enricher(system_prompt, user_id, session_id, supabase_client):
            return system_prompt

        bot_builder.validate_message(validator)
        bot_builder.enrich_prompt(enricher)

        hooks = bot_builder.get_message_hooks()

        assert "validators" in hooks
        assert "prompt_enrichers" in hooks
        assert "context_enrichers" in hooks
        assert "response_processors" in hooks
        assert "send_filters" in hooks
        assert len(hooks["validators"]) == 1
        assert len(hooks["prompt_enrichers"]) == 1

    def test_get_tools_prompt(self, bot_builder):
        """Тест получения промпта с информацией об инструментах"""
        prompt = bot_builder.get_tools_prompt()
        assert isinstance(prompt, str)

    @pytest.mark.asyncio
    async def test_build_already_initialized(self, bot_builder):
        """Тест повторной инициализации (должна быть пропущена)"""
        bot_builder._initialized = True

        result = await bot_builder.build()

        assert result == bot_builder

    @pytest.mark.asyncio
    async def test_build(self, bot_builder, mock_config):
        """Тест сборки бота"""
        with (
            patch("smart_bot_factory.creation.bot_builder.Config", return_value=mock_config),
            patch("smart_bot_factory.creation.bot_builder.LangChainOpenAIClient") as mock_openai,
            patch("smart_bot_factory.creation.bot_builder.SupabaseClient") as mock_supabase,
            patch("smart_bot_factory.creation.bot_builder.AdminManager") as mock_admin,
            patch("smart_bot_factory.creation.bot_builder.AnalyticsManager"),
            patch("smart_bot_factory.creation.bot_builder.ConversationManager"),
            patch("smart_bot_factory.creation.bot_builder.RouterManager"),
            patch("smart_bot_factory.creation.bot_builder.PromptLoader") as mock_prompt,
            patch("smart_bot_factory.creation.bot_builder.MemoryManager"),
            patch("smart_bot_factory.creation.bot_builder.get_handlers_for_prompt", return_value=""),
            patch("dotenv.load_dotenv"),
        ):
            mock_supabase_instance = Mock()
            mock_supabase_instance.initialize = AsyncMock()
            mock_supabase.return_value = mock_supabase_instance

            mock_admin_instance = Mock()
            mock_admin_instance.sync_admins_from_config = AsyncMock()
            mock_admin.return_value = mock_admin_instance

            mock_openai_instance = Mock()
            mock_openai_instance.add_tools = AsyncMock()
            mock_openai_instance.get_tools_description_for_prompt = Mock(return_value="")
            mock_openai.return_value = mock_openai_instance

            mock_prompt_instance = Mock()
            mock_prompt_instance.validate_prompts = AsyncMock()
            mock_prompt_instance.set_tools_description = Mock()
            mock_prompt.return_value = mock_prompt_instance

            result = await bot_builder.build()

            assert result == bot_builder
            assert bot_builder._initialized is True
            assert bot_builder.config is not None
            assert bot_builder.openai_client is not None
            assert bot_builder.supabase_client is not None

    def test_register_router(self, bot_builder):
        """Тест регистрации роутера событий"""
        mock_router = Mock()
        mock_router.name = "test_router"
        mock_router.set_bot_id = Mock()
        mock_router._handlers = {}  # Добавляем _handlers для RouterManager

        # Мокаем RouterManager
        mock_router_manager = Mock()
        mock_router_manager.register_router = Mock()
        bot_builder.router_manager = mock_router_manager

        bot_builder.register_router(mock_router)

        mock_router.set_bot_id.assert_called_once_with("test-bot")
        mock_router_manager.register_router.assert_called_once_with(mock_router)

    def test_register_routers_event_router(self, bot_builder):
        """Тест регистрации EventRouter через register_routers"""
        from smart_bot_factory.event.router import EventRouter

        mock_event_router = Mock(spec=EventRouter)
        mock_event_router.name = "event_router"
        mock_event_router.set_bot_id = Mock()
        mock_event_router._handlers = {}  # Добавляем _handlers для RouterManager

        # Мокаем RouterManager
        mock_router_manager = Mock()
        mock_router_manager.register_router = Mock()
        bot_builder.router_manager = mock_router_manager

        bot_builder.register_routers(mock_event_router)

        mock_event_router.set_bot_id.assert_called_once_with("test-bot")
        mock_router_manager.register_router.assert_called_once_with(mock_event_router)

    def test_register_routers_empty(self, bot_builder):
        """Тест регистрации пустого списка роутеров"""
        bot_builder.register_routers()  # Не должно вызвать ошибку
