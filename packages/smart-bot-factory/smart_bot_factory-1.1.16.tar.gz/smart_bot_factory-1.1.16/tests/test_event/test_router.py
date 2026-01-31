"""Тесты для модуля event.router"""

import pytest

from smart_bot_factory.event.router import EventRouter


class TestEventRouter:
    """Тесты для класса EventRouter"""

    def test_event_router_init(self):
        """Тест инициализации роутера"""
        router = EventRouter()
        assert router.name is not None
        assert router._event_handlers == {}
        assert router._scheduled_tasks == {}
        assert router._global_handlers == {}

    def test_event_router_init_with_name(self):
        """Тест инициализации роутера с именем"""
        router = EventRouter(name="test_router", bot_id="test-bot")
        assert router.name == "test_router"
        assert router.bot_id == "test-bot"

    def test_set_bot_id(self):
        """Тест установки bot_id"""
        router = EventRouter()
        router.set_bot_id("new-bot-id")
        assert router.bot_id == "new-bot-id"

    def test_event_handler_decorator(self):
        """Тест декоратора event_handler"""
        router = EventRouter()

        @router.event_handler("test_event", notify=True, once_only=False)
        async def test_handler(user_id, event_info):
            return {"status": "ok"}

        handlers = router.get_event_handlers()
        assert "test_event" in handlers
        assert handlers["test_event"]["notify"] is True
        assert handlers["test_event"]["once_only"] is False
        assert handlers["test_event"]["name"] == "test_handler"

    def test_schedule_task_decorator(self):
        """Тест декоратора schedule_task"""
        router = EventRouter()

        @router.schedule_task("test_task", delay="1h", notify=True)
        async def test_task(user_id, event_info, session_id):
            return {"status": "scheduled"}

        tasks = router.get_scheduled_tasks()
        assert "test_task" in tasks
        assert tasks["test_task"]["notify"] is True
        assert tasks["test_task"]["default_delay"] == 3600  # 1 час в секундах

    def test_schedule_task_without_delay(self):
        """Тест schedule_task без delay (должна быть ошибка)"""
        router = EventRouter()

        with pytest.raises(ValueError, match="ОБЯЗАТЕЛЬНО нужно указать параметр delay"):

            @router.schedule_task("test_task")
            async def test_task(user_id, event_info, session_id):
                return {"status": "scheduled"}

    def test_global_handler_decorator(self):
        """Тест декоратора global_handler"""
        router = EventRouter()

        @router.global_handler("test_global", delay="30m")
        async def test_global(event_info):
            return {"status": "global"}

        handlers = router.get_global_handlers()
        assert "test_global" in handlers
        assert handlers["test_global"]["default_delay"] == 1800  # 30 минут в секундах

    def test_get_all_handlers(self):
        """Тест получения всех обработчиков"""
        router = EventRouter()

        @router.event_handler("event1")
        async def handler1():
            pass

        @router.schedule_task("task1", delay="1h")
        async def task1():
            pass

        @router.global_handler("global1", delay="1h")
        async def global1():
            pass

        all_handlers = router.get_all_handlers()
        assert "event1" in all_handlers
        assert "task1" in all_handlers
        assert "global1" in all_handlers

    def test_include_router(self):
        """Тест включения другого роутера"""
        router1 = EventRouter(name="router1")
        router2 = EventRouter(name="router2")

        @router2.event_handler("event2")
        async def handler2():
            pass

        router1.include_router(router2)

        handlers = router1.get_event_handlers()
        assert "event2" in handlers

    def test_include_router_conflict(self):
        """Тест включения роутера с конфликтом имен"""
        router1 = EventRouter(name="router1")
        router2 = EventRouter(name="router2")

        @router1.event_handler("conflict_event")
        async def handler1():
            pass

        @router2.event_handler("conflict_event")
        async def handler2():
            pass

        # Должно предупредить, но включить
        router1.include_router(router2)
        handlers = router1.get_event_handlers()
        assert "conflict_event" in handlers

    def test_event_handler_without_name(self):
        """Тест event_handler без указания name (автоматическое имя из функции)"""
        router = EventRouter()

        @router.event_handler()
        async def my_custom_handler(user_id, event_info):
            return {"status": "ok"}

        handlers = router.get_event_handlers()
        assert "my_custom_handler" in handlers
        assert handlers["my_custom_handler"]["name"] == "my_custom_handler"

    def test_event_handler_with_explicit_name(self):
        """Тест event_handler с явным указанием name"""
        router = EventRouter()

        @router.event_handler(name="custom_event_name")
        async def handler_function(user_id, event_info):
            return {"status": "ok"}

        handlers = router.get_event_handlers()
        assert "custom_event_name" in handlers
        assert handlers["custom_event_name"]["name"] == "handler_function"

    def test_schedule_task_without_name(self):
        """Тест schedule_task без указания name (автоматическое имя из функции)"""
        router = EventRouter()

        @router.schedule_task(delay="1h")
        async def my_scheduled_task(user_id, event_info, session_id):
            return {"status": "scheduled"}

        tasks = router.get_scheduled_tasks()
        assert "my_scheduled_task" in tasks
        assert tasks["my_scheduled_task"]["name"] == "my_scheduled_task"

    def test_schedule_task_with_explicit_name(self):
        """Тест schedule_task с явным указанием task_name"""
        router = EventRouter()

        @router.schedule_task(task_name="custom_task_name", delay="30m")
        async def task_function(user_id, event_info, session_id):
            return {"status": "scheduled"}

        tasks = router.get_scheduled_tasks()
        assert "custom_task_name" in tasks
        assert tasks["custom_task_name"]["name"] == "task_function"

    def test_global_handler_without_name(self):
        """Тест global_handler без указания name (автоматическое имя из функции)"""
        router = EventRouter()

        @router.global_handler(delay="1h")
        async def my_global_handler(event_info):
            return {"status": "global"}

        handlers = router.get_global_handlers()
        assert "my_global_handler" in handlers
        assert handlers["my_global_handler"]["name"] == "my_global_handler"

    def test_global_handler_with_explicit_name(self):
        """Тест global_handler с явным указанием name"""
        router = EventRouter()

        @router.global_handler(name="custom_global_name", delay="2h")
        async def global_function(event_info):
            return {"status": "global"}

        handlers = router.get_global_handlers()
        assert "custom_global_name" in handlers
        assert handlers["custom_global_name"]["name"] == "global_function"
