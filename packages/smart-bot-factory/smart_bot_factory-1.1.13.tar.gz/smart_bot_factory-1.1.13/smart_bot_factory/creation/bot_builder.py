"""
Строитель ботов для Smart Bot Factory
"""

import inspect
import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sulguk import AiogramSulgukMiddleware

from ..admin.admin_manager import AdminManager
from ..analytics.analytics_manager import AnalyticsManager
from ..config import Config
from ..event.decorators.registry import get_handlers_for_prompt
from ..event.router_manager import RouterManager
from ..integrations.openai.langchain_openai import LangChainOpenAIClient
from ..integrations.openai.prompt_loader import PromptLoader
from ..integrations.supabase_client import SupabaseClient
from ..memory.memory_manager import MemoryManager
from ..utils.context import ctx
from ..utils.conversation_manager import ConversationManager

if TYPE_CHECKING:
    from ..rag.router import RagRouter
    from ..utils.tool_router import ToolRouter

logger = logging.getLogger(__name__)


class BotBuilder:
    """
    Строитель ботов, который использует существующие файлы проекта
    и добавляет новые возможности через декораторы
    """

    def __init__(self, bot_id: Optional[str] = None, config_dir: Optional[Path] = None):
        """
        Инициализация строителя бота

        Args:
            bot_id: Идентификатор бота (опционально, если не указан - определяется из имени файла или переменной окружения)
            config_dir: Путь к директории конфигурации (по умолчанию bots/bot_id)
        """
        # Если bot_id не указан, пытаемся определить
        if bot_id is None:
            # Сначала проверяем переменную окружения (устанавливается в cli.py)
            bot_id = os.environ.get("BOT_ID")
            if bot_id:
                logger.info(f"🔍 bot_id получен из переменной окружения: {bot_id}")
            else:
                bot_env_vars = [k for k in os.environ.keys() if "BOT" in k.upper()]
                logger.debug(f"🔍 BOT_ID не найден в переменных окружения. " f"Доступные переменные с 'BOT': {bot_env_vars}")
                # Пытаемся определить из имени файла
                bot_id = self._detect_bot_id_from_filename()
                if bot_id:
                    logger.info(f"🔍 bot_id автоматически определен из имени файла: {bot_id}")
                else:
                    raise ValueError("bot_id не указан и не может быть определен автоматически. " "Укажите bot_id явно: BotBuilder(bot_id='my-bot')")

        self.bot_id = bot_id
        self.config_dir = config_dir or Path("bots") / bot_id

        # Компоненты бота
        self.config: Optional[Config] = None
        self.openai_client: Optional[LangChainOpenAIClient] = None
        self.supabase_client: Optional[SupabaseClient] = None
        self.conversation_manager: Optional[ConversationManager] = None
        self.admin_manager: Optional[AdminManager] = None
        self.analytics_manager: Optional[AnalyticsManager] = None
        self.prompt_loader: Optional[PromptLoader] = None
        self.router_manager: Optional[RouterManager] = None
        self.memory_manager: Optional[MemoryManager] = None
        self._telegram_routers: List = []  # Список Telegram роутеров
        self._start_handlers: List = []  # Список обработчиков on_start
        self._utm_triggers: List = []  # Список UTM-триггеров
        self._tools: List = []  # Список инструментов для ChatOpenAI
        self._tool_routers: List = []  # Зарегистрированные роутеры инструментов
        self._rag_routers: List = []  # Зарегистрированные RAG-роутеры

        # Хуки для кастомизации process_user_message
        self._message_validators: List = []  # Валидация ДО обработки
        self._prompt_enrichers: List = []  # Обогащение системного промпта
        self._context_enrichers: List = []  # Обогащение контекста для AI
        self._response_processors: List = []  # Обработка ответа AI
        self._send_filters: List = []  # Фильтры перед отправкой пользователю

        # Кастомный PromptLoader
        self._custom_prompt_loader = None

        # Кастомный процессор событий
        self._custom_event_processor = None

        # Флаги инициализации
        self._initialized = False

        logger.info(f"🏗️ Создан BotBuilder для бота: {bot_id}")

    @staticmethod
    def _detect_bot_id_from_filename() -> Optional[str]:
        """
        Автоматически определяет bot_id из имени файла, который создает BotBuilder

        Returns:
            bot_id если удалось определить, None в противном случае
        """
        try:
            # Получаем стек вызовов
            # stack[0] - текущий кадр (_detect_bot_id_from_filename)
            # stack[1] - кадр __init__
            # stack[2] - кадр, который вызывает BotBuilder()
            stack = inspect.stack()

            logger.debug(f"🔍 Анализ стека вызовов для определения bot_id (всего кадров: {len(stack)})")

            # Ищем в стеке вызовов файл, который создает BotBuilder
            # Пропускаем текущий файл (bot_builder.py) и ищем вызывающий
            for i, frame_info in enumerate(stack[2:], start=2):  # Пропускаем _detect_bot_id_from_filename и __init__
                filename = frame_info.filename
                logger.debug(f"🔍 Кадр {i}: {filename}")

                # Пропускаем системные файлы и файлы библиотек
                if "site-packages" in filename or "__pycache__" in filename:
                    logger.debug("   Пропущен (системный файл)")
                    continue

                # Пропускаем файлы из smart_bot_factory (кроме файлов ботов в корне)
                if "smart_bot_factory" in filename and "bots" not in filename:
                    logger.debug("   Пропущен (файл библиотеки)")
                    continue

                # Получаем имя файла без расширения
                file_path = Path(filename)
                if file_path.suffix == ".py":
                    bot_id = file_path.stem
                    # Проверяем, что это не служебный файл
                    if bot_id and not bot_id.startswith("_"):
                        logger.debug(f"🔍 Найден файл для определения bot_id: {filename} -> {bot_id}")
                        return bot_id
                    else:
                        logger.debug(f"   Пропущен (служебный файл: {bot_id})")
                else:
                    logger.debug("   Пропущен (не .py файл)")

            logger.debug("🔍 Не удалось найти подходящий файл в стеке вызовов")
            return None
        except Exception as e:
            logger.debug(f"Ошибка при определении bot_id из имени файла: {e}")
            return None

    async def build(self, force: bool = False) -> "BotBuilder":
        """
        Строит и инициализирует все компоненты бота

        Идемпотентный метод: можно вызывать многократно без побочных эффектов.
        При повторном вызове без force=True просто возвращает self.

        Args:
            force: Если True, принудительно пересобирает бота даже если уже инициализирован

        Returns:
            BotBuilder: Возвращает self для цепочки вызовов
        """
        if self._initialized and not force:
            # Идемпотентность: тихо возвращаем без warning
            return self

        if force and self._initialized:
            logger.info(f"🔄 Принудительная пересборка бота {self.bot_id}")
            self._initialized = False
            # Сбрасываем состояние компонентов для пересборки
            self.config = None
            self.openai_client = None
            self.supabase_client = None
            self.conversation_manager = None
            self.admin_manager = None
            self.analytics_manager = None
            self.prompt_loader = None
            self.memory_manager = None

        try:
            logger.info(f"🚀 Начинаем сборку бота {self.bot_id}")

            # 1. Инициализируем конфигурацию
            await self._init_config()

            # 2. Инициализируем клиенты
            await self._init_clients()

            # 3. Инициализируем менеджеры
            await self._init_managers()

            # 4. Регистрируем инструменты в OpenAI клиенте
            await self._register_tools_in_client()

            # 5. Обновляем промпты с информацией о доступных инструментах
            await self._update_prompts_with_tools()

            # 6. Обновляем описание инструментов в промпт-лоадере
            await self._update_tools_description_in_prompt_loader()

            self._initialized = True
            logger.info(f"✅ Бот {self.bot_id} успешно собран и готов к работе")

            return self

        except Exception as e:
            logger.error(f"❌ Ошибка при сборке бота {self.bot_id}: {e}")
            raise

    async def _init_config(self):
        """Инициализация конфигурации"""
        logger.info(f"⚙️ Инициализация конфигурации для {self.bot_id}")

        # Устанавливаем BOT_ID в переменные окружения
        os.environ["BOT_ID"] = self.bot_id

        # Загружаем .env файл если существует
        env_file = self.config_dir / ".env"
        if env_file.exists():
            from dotenv import load_dotenv

            load_dotenv(env_file)
            logger.info(f"📄 Загружен .env файл: {env_file}")

        # Устанавливаем путь к промптам относительно папки бота
        prompts_subdir = os.environ.get("PROMT_FILES_DIR", "prompts")
        logger.info(f"🔍 PROMT_FILES_DIR из .env: {prompts_subdir}")

        prompts_dir = self.config_dir / prompts_subdir
        logger.info(f"🔍 Путь к промптам: {prompts_dir}")
        logger.info(f"🔍 Существует ли папка: {prompts_dir.exists()}")

        # ВАЖНО: Устанавливаем правильный путь ДО создания Config
        os.environ["PROMT_FILES_DIR"] = str(prompts_dir)
        logger.info(f"📁 Установлен путь к промптам: {prompts_dir}")

        # Создаем конфигурацию
        logger.info(f"🔍 PROMT_FILES_DIR перед созданием Config: {os.environ.get('PROMT_FILES_DIR')}")
        self.config = Config()
        logger.info("✅ Конфигурация инициализирована")

    async def _init_clients(self):
        """Инициализация клиентов"""
        logger.info(f"🔌 Инициализация клиентов для {self.bot_id}")

        if not self.config:
            raise RuntimeError("Config не инициализирован. Вызовите _init_config() перед _init_clients()")

        # OpenAI клиент
        self.openai_client = LangChainOpenAIClient(
            api_key=self.config.OPENAI_API_KEY,
            model=self.config.OPENAI_MODEL,
            max_tokens=self.config.OPENAI_MAX_TOKENS,
            temperature=self.config.OPENAI_TEMPERATURE,
        )
        logger.info("✅ OpenAI клиент инициализирован")

        # Supabase клиент
        self.supabase_client = SupabaseClient(
            url=self.config.SUPABASE_URL,
            key=self.config.SUPABASE_KEY,
            bot_id=self.bot_id,
        )
        await self.supabase_client.initialize()
        logger.info("✅ Supabase клиент инициализирован")

    async def _register_tools_in_client(self):
        """Регистрирует зарегистрированные инструменты в OpenAI клиенте"""
        if self._tools and self.openai_client:
            logger.info(f"🔧 Регистрация {len(self._tools)} инструментов в ChatOpenAI")
            self.openai_client.add_tools(self._tools)
            logger.info("✅ Инструменты зарегистрированы в ChatOpenAI")

    async def _update_tools_description_in_prompt_loader(self):
        """Обновляет описание инструментов в PromptLoader"""
        if self.openai_client and self.prompt_loader:
            tools_description = self.openai_client.get_tools_description_for_prompt()
            if tools_description:
                self.prompt_loader.set_tools_description(tools_description)
                logger.info("✅ Описание инструментов обновлено в PromptLoader")
            else:
                logger.debug("Нет инструментов для добавления в промпт")

    async def _init_managers(self):
        """Инициализация менеджеров"""
        logger.info(f"👥 Инициализация менеджеров для {self.bot_id}")

        # Admin Manager
        self.admin_manager = AdminManager(self.config, self.supabase_client)
        await self.admin_manager.sync_admins_from_config()
        logger.info("✅ Admin Manager инициализирован")

        # Analytics Manager
        self.analytics_manager = AnalyticsManager(self.supabase_client)
        logger.info("✅ Analytics Manager инициализирован")

        # Conversation Manager
        parse_mode = os.environ.get("MESSAGE_PARSE_MODE", "Markdown")
        admin_session_timeout_minutes = int(os.environ.get("ADMIN_SESSION_TIMEOUT_MINUTES", "30"))

        self.conversation_manager = ConversationManager(
            self.supabase_client,
            self.admin_manager,
            parse_mode,
            admin_session_timeout_minutes,
        )

        logger.info("✅ Conversation Manager инициализирован")

        # Router Manager (создаем только если еще не создан)
        if not self.router_manager:
            self.router_manager = RouterManager()
            logger.info("✅ Router Manager инициализирован")
        else:
            logger.info("✅ Router Manager уже был создан ранее")

        # Prompt Loader (используем кастомный если установлен)
        if not self.config:
            raise RuntimeError("Config не инициализирован. Вызовите _init_config() перед _init_managers()")
        
        if self._custom_prompt_loader:
            self.prompt_loader = self._custom_prompt_loader
            logger.info(f"✅ Используется кастомный Prompt Loader: {type(self.prompt_loader).__name__}")
        else:
            self.prompt_loader = PromptLoader(prompts_dir=self.config.PROMT_FILES_DIR)
            logger.info("✅ Используется стандартный Prompt Loader")

        await self.prompt_loader.validate_prompts()
        logger.info("✅ Prompt Loader инициализирован")

        # Memory Manager
        self.memory_manager = MemoryManager(supabase_client=self.supabase_client, config=self.config)
        logger.info("✅ Memory Manager инициализирован")

    async def _update_prompts_with_tools(self):
        """
        Обновляет промпты информацией о доступных обработчиках событий
        """
        logger.info("🔧 Обновление промптов с информацией об обработчиках")

        # Получаем информацию о доступных обработчиках
        # Сначала пробуем получить из роутеров, если нет - из старых декораторов
        if self.router_manager:
            event_handlers_info = self.router_manager.get_handlers_for_prompt()
        else:
            event_handlers_info = get_handlers_for_prompt()

        # Если есть обработчики, добавляем их в системный промпт
        if event_handlers_info:
            # Сохраняем информацию о обработчиках для использования в handlers.py
            self._tools_prompt = event_handlers_info

            logger.info("✅ Промпты обновлены с информацией об обработчиках")
        else:
            self._tools_prompt = ""
            logger.info("ℹ️ Нет зарегистрированных обработчиков")

    def get_tools_prompt(self) -> str:
        """Возвращает промпт с информацией об инструментах"""
        return getattr(self, "_tools_prompt", "")

    def get_status(self) -> Dict[str, Any]:
        """Возвращает статус бота"""
        return {
            "bot_id": self.bot_id,
            "initialized": self._initialized,
            "config_dir": str(self.config_dir),
            "components": {
                "config": self.config is not None,
                "openai_client": self.openai_client is not None,
                "supabase_client": self.supabase_client is not None,
                "conversation_manager": self.conversation_manager is not None,
                "admin_manager": self.admin_manager is not None,
                "analytics_manager": self.analytics_manager is not None,
                "prompt_loader": self.prompt_loader is not None,
            },
            "tools": {
                "event_handlers": (len(get_handlers_for_prompt().split("\n")) if get_handlers_for_prompt() else 0),
                "chatopenai_tools": len(self._tools),
            },
        }

    def register_router(self, router):
        """
        Регистрирует роутер событий в менеджере роутеров

        Args:
            router: EventRouter для регистрации
        """
        # Автоматически устанавливаем bot_id, если роутер поддерживает это
        if hasattr(router, "set_bot_id"):
            router.set_bot_id(self.bot_id)

        # Если RouterManager еще не инициализирован, создаем его
        if not self.router_manager:
            from ..event.router_manager import RouterManager

            self.router_manager = RouterManager()
            logger.info(f"✅ Router Manager создан для регистрации роутера '{router.name}'")

        self.router_manager.register_router(router)
        logger.info(f"✅ Роутер событий '{router.name}' зарегистрирован в боте {self.bot_id}")

    def register_routers(self, *routers):
        """
        Универсальный метод для регистрации роутеров любого типа.
        Автоматически определяет тип роутера и регистрирует его в нужном месте.

        Поддерживаемые типы роутеров:
        - EventRouter (включая FileRouter) -> регистрируется как роутер событий
        - RagRouter -> регистрируется как RAG-роутер
        - ToolRouter (но не RagRouter) -> регистрируется как набор инструментов
        - aiogram.Router -> регистрируется как Telegram роутер

        Args:
            *routers: Произвольное количество роутеров любого поддерживаемого типа

        Example:
            # EventRouter
            bot_builder.register_routers(event_router)

            # FileRouter (наследуется от EventRouter)
            bot_builder.register_routers(file_router)

            # RAG роутер
            bot_builder.register_routers(rag_router)

            # Telegram роутер
            from aiogram import Router
            telegram_router = Router(name="commands")
            bot_builder.register_routers(telegram_router)

            # Можно регистрировать несколько роутеров разных типов одновременно
            bot_builder.register_routers(event_router, file_router, rag_router, telegram_router)
        """
        if not routers:
            logger.warning("⚠️ register_routers вызван без аргументов")
            return

        # Импортируем классы для проверки типов
        from ..event.router import EventRouter
        from ..rag.router import RagRouter
        from ..utils.tool_router import ToolRouter

        # Пытаемся импортировать aiogram.Router (может быть не установлен)
        AiogramRouter: Optional[type] = None
        try:
            from aiogram import Router as AiogramRouterType
            AiogramRouter = AiogramRouterType
        except ImportError:
            pass

        event_count = 0
        rag_count = 0
        tool_count = 0
        telegram_count = 0

        for router in routers:
            # Определяем тип роутера и регистрируем соответствующим образом
            if isinstance(router, EventRouter):
                # EventRouter или его наследники (включая FileRouter)
                self.register_router(router)
                event_count += 1
            elif isinstance(router, RagRouter):
                # RAG роутер
                self.register_rag(router)
                rag_count += 1
            elif isinstance(router, ToolRouter):
                # Обычный ToolRouter (но не RagRouter, так как RagRouter уже обработан выше)
                self.register_tool_set(router)
                tool_count += 1
            elif AiogramRouter and isinstance(router, AiogramRouter):
                # Telegram роутер (aiogram.Router)
                self.register_telegram_router(router)
                telegram_count += 1
            else:
                # Неизвестный тип роутера
                router_type = type(router).__name__
                router_name = getattr(router, "name", getattr(router, "__name__", "unknown"))
                logger.warning(
                    f"⚠️ Неизвестный тип роутера '{router_type}' (name: {router_name}). "
                    f"Поддерживаются: EventRouter, RagRouter, ToolRouter, aiogram.Router"
                )

        # Логируем результаты
        total_registered = event_count + rag_count + tool_count + telegram_count
        if total_registered > 0:
            parts = []
            if event_count > 0:
                parts.append(f"{event_count} событий")
            if rag_count > 0:
                parts.append(f"{rag_count} RAG")
            if tool_count > 0:
                parts.append(f"{tool_count} инструментов")
            if telegram_count > 0:
                parts.append(f"{telegram_count} Telegram")
            logger.info(f"✅ Зарегистрировано роутеров: {', '.join(parts)}")

    def register_telegram_router(self, telegram_router):
        """
        Регистрирует Telegram роутер для обработки команд и сообщений

        Args:
            telegram_router: aiogram.Router для регистрации

        Example:
            from aiogram import Router
            from aiogram.filters import Command

            # Создаем обычный aiogram Router
            my_router = Router(name="my_commands")

            @my_router.message(Command("price"))
            async def price_handler(message: Message):
                await message.answer("Наши цены...")

            # Регистрируем в боте
            bot_builder.register_telegram_router(my_router)
        """
        from aiogram import Router as AiogramRouter

        if not isinstance(telegram_router, AiogramRouter):
            raise TypeError(f"Ожидается aiogram.Router, получен {type(telegram_router)}")

        self._telegram_routers.append(telegram_router)
        router_name = getattr(telegram_router, "name", "unnamed")
        logger.info(f"✅ Telegram роутер '{router_name}' зарегистрирован в боте {self.bot_id}")

    def register_telegram_routers(self, *telegram_routers):
        """
        Регистрирует несколько Telegram роутеров одновременно

        Args:
            *telegram_routers: Произвольное количество aiogram.Router

        Example:
            from aiogram import Router

            router1 = Router(name="commands")
            router2 = Router(name="callbacks")

            bot_builder.register_telegram_routers(router1, router2)
        """
        if not telegram_routers:
            logger.warning("⚠️ register_telegram_routers вызван без аргументов")
            return

        for router in telegram_routers:
            self.register_telegram_router(router)

        logger.info(f"✅ Зарегистрировано {len(telegram_routers)} Telegram роутеров")

    def register_tool(self, tool):
        """
        Регистрирует инструмент для ChatOpenAI

        Args:
            tool: Инструмент LangChain (например, StructuredTool, FunctionTool и т.д.)

        Example:
            from langchain_core.tools import StructuredTool
            from pydantic import BaseModel, Field

            class CalculatorInput(BaseModel):
                a: float = Field(description="Первое число")
                b: float = Field(description="Второе число")

            def add(a: float, b: float) -> float:
                return a + b

            calculator_tool = StructuredTool.from_function(
                func=add,
                name="calculator",
                description="Складывает два числа",
                args_schema=CalculatorInput
            )

            bot_builder.register_tool(calculator_tool)
        """
        if tool not in self._tools:
            self._tools.append(tool)
            # Если клиент уже инициализирован, сразу добавляем инструмент
            if self.openai_client:
                self.openai_client.add_tool(tool)
            tool_name = getattr(tool, "name", str(tool))
            logger.info(f"✅ Инструмент '{tool_name}' зарегистрирован в боте {self.bot_id}")

            # Обновляем описание инструментов в промпт-лоадере (если доступен)
            if self.prompt_loader and self.openai_client:
                tools_description = self.openai_client.get_tools_description_for_prompt()
                if tools_description:
                    self.prompt_loader.set_tools_description(tools_description)
        else:
            tool_name = getattr(tool, "name", str(tool))
            logger.warning(f"⚠️ Инструмент '{tool_name}' уже зарегистрирован")

    def register_tools(self, *tools):
        """
        Регистрирует несколько инструментов для ChatOpenAI одновременно

        Args:
            *tools: Произвольное количество инструментов LangChain или список(ы) инструментов

        Example:
            from langchain_core.tools import StructuredTool

            tool1 = StructuredTool.from_function(...)
            tool2 = StructuredTool.from_function(...)
            tool3 = StructuredTool.from_function(...)

            # Отдельные инструменты
            bot_builder.register_tools(tool1, tool2, tool3)

            # Список инструментов
            bot_builder.register_tools([tool1, tool2, tool3])
        """
        if not tools:
            logger.warning("⚠️ register_tools вызван без аргументов")
            return

        # Распаковываем списки инструментов
        unpacked_tools = []
        for tool in tools:
            if isinstance(tool, (list, tuple)):
                unpacked_tools.extend(tool)
            else:
                unpacked_tools.append(tool)

        for tool in unpacked_tools:
            self.register_tool(tool)

        # Обновляем описание инструментов в промпт-лоадере после добавления всех
        if self.openai_client and self.prompt_loader:
            tools_description = self.openai_client.get_tools_description_for_prompt()
            if tools_description:
                self.prompt_loader.set_tools_description(tools_description)

        logger.info(f"✅ Зарегистрировано {len(unpacked_tools)} инструментов для ChatOpenAI")

    def register_tool_set(self, tool_router: "ToolRouter"):
        """
        Регистрирует роутер обычных инструментов LangChain.
        """
        # Автоматически устанавливаем bot_id, если роутер поддерживает это
        if hasattr(tool_router, "set_bot_id"):
            tool_router.set_bot_id(self.bot_id)

        if tool_router in self._tool_routers:
            logger.warning(
                "⚠️ ToolRouter %s уже зарегистрирован",
                getattr(tool_router, "name", tool_router),
            )
            return

        tools = getattr(tool_router, "get_tools", lambda: [])()
        if not tools:
            logger.warning(
                "⚠️ ToolRouter %s не содержит инструментов для регистрации",
                getattr(tool_router, "name", tool_router),
            )
        else:
            self.register_tools(tools)

        self._tool_routers.append(tool_router)
        logger.info(
            "✅ Зарегистрирован ToolRouter: %s",
            getattr(tool_router, "name", tool_router),
        )
        return tool_router

    def register_tool_sets(self, *tool_routers: "ToolRouter"):
        """
        Регистрирует несколько роутеров обычных инструментов.
        """
        if not tool_routers:
            logger.warning("⚠️ register_tool_sets вызван без аргументов")
            return
        for router in tool_routers:
            self.register_tool_set(router)

    def register_rag(self, rag_router: "RagRouter"):
        """
        Регистрирует RAG-роутер и все его инструменты.

        Args:
            rag_router: Экземпляр RagRouter с описанными инструментами.
        """
        # Автоматически устанавливаем bot_id, если роутер поддерживает это
        if hasattr(rag_router, "set_bot_id"):
            rag_router.set_bot_id(self.bot_id)

        if rag_router in self._rag_routers:
            logger.warning("⚠️ RAG-роутер %s уже зарегистрирован", getattr(rag_router, "name", rag_router))
            return

        tools = getattr(rag_router, "get_tools", lambda: [])()
        if not tools:
            logger.warning("⚠️ RAG-роутер %s не содержит инструментов для регистрации", getattr(rag_router, "name", rag_router))
        else:
            self.register_tools(tools)
        self._rag_routers.append(rag_router)
        logger.info("✅ Зарегистрирован RAG-роутер: %s", getattr(rag_router, "name", rag_router))
        return rag_router

    def register_rag_routers(self, *rag_routers: "RagRouter"):
        """
        Регистрирует несколько RAG-роутеров.
        """
        if not rag_routers:
            logger.warning("⚠️ register_rag_routers вызван без аргументов")
            return
        for router in rag_routers:
            self.register_rag(router)

    def on_start(self, handler):
        """
        Регистрирует обработчик, который вызывается после стандартной логики /start

        Обработчик получает доступ к:
        - user_id: int - ID пользователя Telegram
        - session_id: str - ID созданной сессии
        - message: Message - Объект сообщения от aiogram
        - state: FSMContext - Контекст состояния

        Args:
            handler: Async функция с сигнатурой:
                     async def handler(user_id: int, session_id: str, message: Message, state: FSMContext)

        Example:
            @bot_builder.on_start
            async def my_start_handler(user_id, session_id, message, state):
                keyboard = InlineKeyboardMarkup(...)
                await message.answer("Выберите действие:", reply_markup=keyboard)
        """
        if not callable(handler):
            raise TypeError(f"Обработчик должен быть callable, получен {type(handler)}")

        self._start_handlers.append(handler)
        logger.info(f"✅ Зарегистрирован обработчик on_start: {handler.__name__}")
        return handler  # Возвращаем handler для использования как декоратор

    def get_start_handlers(self) -> List:
        """Получает список обработчиков on_start"""
        return self._start_handlers.copy()

    def register_utm_trigger(
        self,
        message: str,
        source: Optional[str] = None,
        medium: Optional[str] = None,
        campaign: Optional[str] = None,
        content: Optional[str] = None,
        term: Optional[str] = None,
        segment: Optional[str] = None,
    ):
        """
        Регистрирует UTM-триггер для обработки /start с определенными UTM параметрами

        Если UTM данные совпадают с указанными значениями, отправляется сообщение из файла
        и вся стандартная логика /start пропускается.

        Args:
            message: Имя файла с сообщением, которое будет отправлено при совпадении.
                    Файл должен находиться в директории bots/bot_id/utm_message/.
                    Содержимое файла будет прочитано и использовано как сообщение.
            source: Целевое значение utm_source (или None для игнорирования)
            medium: Целевое значение utm_medium (или None для игнорирования)
            campaign: Целевое значение utm_campaign (или None для игнорирования)
            content: Целевое значение utm_content (или None для игнорирования)
            term: Целевое значение utm_term (или None для игнорирования)
            segment: Целевое значение segment (или None для игнорирования)

        Example:
            # Триггер для конкретной кампании
            # Файл должен находиться в bots/mdclinica/utm_message/summer_campaign.txt
            bot_builder.register_utm_trigger(
                message='summer_campaign.txt',
                source='vk',
                campaign='summer2025'
            )

            # Триггер для сегмента
            # Файл должен находиться в bots/mdclinica/utm_message/premium_welcome.txt
            bot_builder.register_utm_trigger(
                message='premium_welcome.txt',
                segment='premium'
            )

            # Триггер с несколькими параметрами
            # Файл должен находиться в bots/mdclinica/utm_message/new_year.txt
            bot_builder.register_utm_trigger(
                message='new_year.txt',
                source='instagram',
                medium='story',
                campaign='new_year'
            )
        """
        # Собираем словарь из аргументов, исключая None значения
        utm_targets = {}
        if source is not None:
            utm_targets["source"] = source
        if medium is not None:
            utm_targets["medium"] = medium
        if campaign is not None:
            utm_targets["campaign"] = campaign
        if content is not None:
            utm_targets["content"] = content
        if term is not None:
            utm_targets["term"] = term
        if segment is not None:
            utm_targets["segment"] = segment

        trigger = {
            "utm_targets": utm_targets,
            "message": message,
        }
        self._utm_triggers.append(trigger)
        logger.info(f"✅ Зарегистрирован UTM-триггер: {utm_targets} -> '{message[:50]}...'")

    def get_utm_triggers(self) -> List:
        """Получает список UTM-триггеров"""
        return self._utm_triggers.copy()

    def set_prompt_loader(self, prompt_loader):
        """
        Устанавливает кастомный PromptLoader

        Должен быть вызван ДО build()

        Args:
            prompt_loader: Экземпляр PromptLoader или его наследника (например UserPromptLoader)

        Example:
            from smart_bot_factory.utils import UserPromptLoader

            # Использовать UserPromptLoader с автопоиском prompts_dir
            custom_loader = UserPromptLoader("my-bot")
            bot_builder.set_prompt_loader(custom_loader)

            # Или кастомный наследник
            class MyPromptLoader(UserPromptLoader):
                def __init__(self, bot_id):
                    super().__init__(bot_id)
                    self.extra_file = self.prompts_dir / 'extra.txt'

            my_loader = MyPromptLoader("my-bot")
            bot_builder.set_prompt_loader(my_loader)
        """
        self._custom_prompt_loader = prompt_loader
        logger.info(f"✅ Установлен кастомный PromptLoader: {type(prompt_loader).__name__}")

    def set_event_processor(self, custom_processor):
        """
        Устанавливает кастомную функцию для обработки событий

        Полностью заменяет стандартную process_events из bot_utils

        Args:
            custom_processor: async def(session_id: str, events: list, user_id: int)

        Example:
            from smart_bot_factory.message import get_bot
            from smart_bot_factory.core.decorators import execute_event_handler

            async def my_process_events(session_id, events, user_id):
                '''Моя кастомная обработка событий'''
                bot = get_bot()

                for event in events:
                    event_type = event.get('тип')
                    event_info = event.get('инфо')

                    if event_type == 'запись':
                        # Кастомная логика для бронирования
                        telegram_user = await bot.get_chat(user_id)
                        name = telegram_user.first_name or 'Клиент'
                        # ... ваша обработка
                    else:
                        # Для остальных - стандартная обработка
                        await execute_event_handler(event_type, user_id, event_info)

            bot_builder.set_event_processor(my_process_events)
        """
        if not callable(custom_processor):
            raise TypeError(f"Процессор должен быть callable, получен {type(custom_processor)}")

        self._custom_event_processor = custom_processor
        logger.info(f"✅ Установлена кастомная функция обработки событий: {custom_processor.__name__}")

    # ========== ХУКИ ДЛЯ КАСТОМИЗАЦИИ ОБРАБОТКИ СООБЩЕНИЙ ==========

    def validate_message(self, handler):
        """
        Регистрирует валидатор сообщений (вызывается ДО обработки AI)

        Если валидатор возвращает False, обработка прерывается

        Args:
            handler: async def(message: Message, supabase_client) -> bool

        Example:
            @bot_builder.validate_message
            async def check_service_names(message, supabase_client):
                if "неправильное название" in message.text:
                    await message.answer("Пожалуйста, уточните название услуги")
                    return False  # Прерываем обработку
                return True  # Продолжаем
        """
        if not callable(handler):
            raise TypeError(f"Обработчик должен быть callable, получен {type(handler)}")

        self._message_validators.append(handler)
        logger.info(f"✅ Зарегистрирован валидатор сообщений: {handler.__name__}")
        return handler

    def enrich_prompt(self, handler):
        """
        Регистрирует обогатитель системного промпта

        Args:
            handler: async def(system_prompt: str, user_id: int, session_id: str, supabase_client) -> str

        Example:
            @bot_builder.enrich_prompt
            async def add_client_info(system_prompt, user_id, session_id, supabase_client):
                session = await supabase_client.get_active_session(user_id)
                phone = session.get('metadata', {}).get('phone')
                if phone:
                    return f"{system_prompt}\\n\\nТелефон клиента: {phone}"
                return system_prompt
        """
        if not callable(handler):
            raise TypeError(f"Обработчик должен быть callable, получен {type(handler)}")

        self._prompt_enrichers.append(handler)
        logger.info(f"✅ Зарегистрирован обогатитель промпта: {handler.__name__}")
        return handler

    def enrich_context(self, handler):
        """
        Регистрирует обогатитель контекста для AI (messages array)

        Args:
            handler: async def(messages: List[dict], user_id: int, session_id: str) -> List[dict]

        Example:
            @bot_builder.enrich_context
            async def add_external_data(messages, user_id, session_id):
                # Добавляем данные из внешнего API
                messages.append({
                    "role": "system",
                    "content": "Дополнительная информация..."
                })
                return messages
        """
        if not callable(handler):
            raise TypeError(f"Обработчик должен быть callable, получен {type(handler)}")

        self._context_enrichers.append(handler)
        logger.info(f"✅ Зарегистрирован обогатитель контекста: {handler.__name__}")
        return handler

    def process_response(self, handler):
        """
        Регистрирует обработчик ответа AI (ПОСЛЕ получения ответа)

        Args:
            handler: async def(response_text: str, ai_metadata: dict, user_id: int) -> tuple[str, dict]

        Example:
            @bot_builder.process_response
            async def modify_response(response_text, ai_metadata, user_id):
                # Модифицируем ответ
                if "цена" in response_text.lower():
                    response_text += "\\n\\n💰 Актуальные цены на сайте"
                return response_text, ai_metadata
        """
        if not callable(handler):
            raise TypeError(f"Обработчик должен быть callable, получен {type(handler)}")

        self._response_processors.append(handler)
        logger.info(f"✅ Зарегистрирован обработчик ответа: {handler.__name__}")
        return handler

    def filter_send(self, handler):
        """
        Регистрирует фильтр отправки (может блокировать отправку пользователю)

        Если фильтр возвращает True, сообщение НЕ отправляется

        Args:
            handler: async def(user_id: int) -> bool

        Example:
            @bot_builder.filter_send
            async def block_during_process(user_id):
                if is_processing(user_id):
                    return True  # Блокируем отправку
                return False  # Разрешаем отправку

            # Или совместимый с should_block_ai_response
            @bot_builder.filter_send
            async def should_block_ai_response(user_id):
                # Ваша логика проверки
                return user_is_blocked(user_id)  # True = блокировать
        """
        if not callable(handler):
            raise TypeError(f"Обработчик должен быть callable, получен {type(handler)}")

        self._send_filters.append(handler)
        logger.info(f"✅ Зарегистрирован фильтр отправки: {handler.__name__}")
        return handler

    def get_message_hooks(self) -> Dict[str, List]:
        """Получает все хуки для обработки сообщений"""
        return {
            "validators": self._message_validators.copy(),
            "prompt_enrichers": self._prompt_enrichers.copy(),
            "context_enrichers": self._context_enrichers.copy(),
            "response_processors": self._response_processors.copy(),
            "send_filters": self._send_filters.copy(),
        }

    def get_router_manager(self) -> RouterManager:
        """Получает менеджер роутеров событий"""
        if not self.router_manager:
            from ..event.router_manager import RouterManager
            self.router_manager = RouterManager()
        return self.router_manager

    async def _setup_bot_commands(self, bot):
        """Устанавливает меню команд для бота (разные для админов и пользователей)"""
        from aiogram.types import BotCommand, BotCommandScopeChat, BotCommandScopeDefault

        if not self.config:
            raise RuntimeError("Config не инициализирован")

        try:
            # Команды для обычных пользователей
            user_commands = [
                BotCommand(command="start", description="🚀 Начать/перезапустить бота"),
                BotCommand(command="help", description="❓ Помощь"),
            ]

            # Устанавливаем для всех пользователей по умолчанию
            await bot.set_my_commands(user_commands, scope=BotCommandScopeDefault())
            logger.info("✅ Установлены команды для обычных пользователей")

            # Команды для админов (включая команды пользователей + админские)
            admin_commands = [
                BotCommand(command="start", description="🚀 Начать/перезапустить бота"),
                BotCommand(command="help", description="❓ Помощь"),
                BotCommand(command="cancel", description="❌ Отменить текущее действие"),
                BotCommand(command="admin", description="👑 Админ панель"),
                BotCommand(command="stats", description="📊 Статистика"),
                BotCommand(command="dashboard", description="📊 Дашборд аналитики"),
                BotCommand(command="chat", description="💬 Начать чат с пользователем"),
                BotCommand(command="chats", description="👥 Активные чаты"),
                BotCommand(command="stop", description="⛔ Остановить текущий чат"),
                BotCommand(command="history", description="📜 История сообщений"),
                BotCommand(command="create_event", description="📝 Создать событие"),
                BotCommand(command="list_events", description="📋 Список событий"),
                BotCommand(command="delete_event", description="🗑️ Удалить событие"),
                BotCommand(command="edit_event", description="✏️ Редактировать событие"),
            ]

            # Устанавливаем для каждого админа персональные команды
            for admin_id in self.config.ADMIN_TELEGRAM_IDS:
                try:
                    await bot.set_my_commands(admin_commands, scope=BotCommandScopeChat(chat_id=admin_id))
                    logger.info(f"✅ Установлены админские команды для {admin_id}")
                except Exception as e:
                    logger.warning(f"⚠️ Не удалось установить команды для админа {admin_id}: {e}")

            if self.config:
                logger.info(f"✅ Меню команд настроено ({len(self.config.ADMIN_TELEGRAM_IDS)} админов)")
            else:
                logger.warning("⚠️ Config не инициализирован, не удалось установить команды для админов")

        except Exception as e:
            logger.error(f"❌ Ошибка установки команд бота: {e}")

    async def test(self, scenario_file: Optional[str] = None, max_concurrent: int = 5, verbose: bool = False):
        """
        Запускает тестирование бота с использованием настроенных компонентов

        Args:
            scenario_file: Конкретный файл сценариев (без расширения или с .yaml)
            max_concurrent: Максимальное количество параллельных тестов
            verbose: Подробный вывод

        Returns:
            int: Код возврата (0 - успех, 1 - ошибки)
        """
        # Автоматически инициализируем компоненты, если они еще не инициализированы
        if not self._initialized:
            logger.info(f"🔧 Компоненты бота {self.bot_id} не инициализированы, вызываем build()")
            await self.build()

        logger.info(f"🧪 Запускаем тестирование бота {self.bot_id}")

        try:
            # Логируем информацию об инструментах и настройках
            logger.info("=" * 70)
            logger.info("📋 ИНФОРМАЦИЯ О НАСТРОЙКАХ БОТА:")
            logger.info("=" * 70)

            # Инструменты в OpenAI клиенте
            if self.openai_client:
                tools = self.openai_client.get_tools()
                logger.info(f"🔧 Инструментов зарегистрировано в OpenAI клиенте: {len(tools)}")
                if tools:
                    logger.info("   Список инструментов:")
                    for i, tool in enumerate(tools, 1):
                        tool_name = getattr(tool, "name", str(tool))
                        logger.info(f"   {i}. {tool_name}")

            # Описание инструментов в промпт-лоадере
            if self.prompt_loader:
                tools_description = getattr(self.prompt_loader, "_tools_description", "")
                if tools_description:
                    logger.info(f"📝 Описание инструментов в промпт-лоадере: {len(tools_description)} символов")
                    if verbose:
                        logger.info(f"   Превью: {tools_description[:200]}...")
                else:
                    logger.info("⚠️ Описание инструментов не найдено в промпт-лоадере")

            # RAG-роутеры
            if self._rag_routers:
                logger.info(f"🔍 RAG-роутеров зарегистрировано: {len(self._rag_routers)}")
                for i, rag_router in enumerate(self._rag_routers, 1):
                    router_name = getattr(rag_router, "name", f"rag_router_{i}")
                    tools = getattr(rag_router, "get_tools", lambda: [])()
                    tool_count = len(tools) if tools else 0
                    logger.info(f"   {i}. {router_name} ({tool_count} инструментов)")
            else:
                logger.info("🔍 RAG-роутеров: 0")

            # Tool роутеры
            if self._tool_routers:
                logger.info(f"🔧 Tool роутеров зарегистрировано: {len(self._tool_routers)}")
                for i, tool_router in enumerate(self._tool_routers, 1):
                    router_name = getattr(tool_router, "name", f"tool_router_{i}")
                    tools = getattr(tool_router, "get_tools", lambda: [])()
                    tool_count = len(tools) if tools else 0
                    logger.info(f"   {i}. {router_name} ({tool_count} инструментов)")
            else:
                logger.info("🔧 Tool роутеров: 0")

            # Event роутеры (через RouterManager)
            if self.router_manager:
                routers = getattr(self.router_manager, "_routers", [])
                if routers:
                    logger.info(f"📡 Event роутеров зарегистрировано: {len(routers)}")
                    for i, router in enumerate(routers, 1):
                        router_name = getattr(router, "name", f"event_router_{i}")
                        handlers = getattr(router, "_handlers", {})
                        handler_count = sum(len(h) for h in handlers.values()) if handlers else 0
                        logger.info(f"   {i}. {router_name} ({handler_count} обработчиков)")
                else:
                    logger.info("📡 Event роутеров: 0")
            else:
                logger.info("📡 Event роутеров: 0")

            # Telegram роутеры
            if self._telegram_routers:
                logger.info(f"💬 Telegram роутеров зарегистрировано: {len(self._telegram_routers)}")
                for i, telegram_router in enumerate(self._telegram_routers, 1):
                    router_name = getattr(telegram_router, "name", f"telegram_router_{i}")
                    logger.info(f"   {i}. {router_name}")
            else:
                logger.info("💬 Telegram роутеров: 0")

            # Хуки для обработки сообщений
            message_hooks = self.get_message_hooks()
            total_hooks = sum(len(hooks) for hooks in message_hooks.values())
            logger.info(f"🎣 Хуков зарегистрировано: {total_hooks}")
            for hook_type, hooks in message_hooks.items():
                if hooks:
                    logger.info(f"   - {hook_type}: {len(hooks)}")

            logger.info("=" * 70)

            # Импортируем классы тестирования
            from .bot_testing import ReportGenerator, ScenarioLoader, TestRunner

            # Загружаем сценарии
            if scenario_file:
                # Обрабатываем название файла
                if not scenario_file.endswith(".yaml"):
                    scenario_file += ".yaml"

                scenario_path = self.config_dir / "tests" / scenario_file
                scenarios = ScenarioLoader.load_scenarios_from_file(str(scenario_path))

                if not scenarios:
                    logger.error(f"Файл сценариев '{scenario_file}' не найден или пуст")
                    return 1
            else:
                scenarios = ScenarioLoader.load_all_scenarios_for_bot(self.bot_id, self.config_dir.parent.parent)

                if not scenarios:
                    logger.error(f"Сценарии для бота '{self.bot_id}' не найдены")
                    return 1

            logger.info(f"📋 Найдено сценариев: {len(scenarios)}")
            if scenario_file:
                logger.info(f"📋 Тестируется файл: {scenario_file}")
            else:
                logger.info("📋 Тестируются все файлы сценариев")

            # Создаем интегрированный тестер с готовыми компонентами
            from .bot_testing import BotTesterIntegrated

            bot_tester = BotTesterIntegrated(
                bot_id=self.bot_id,
                openai_client=self.openai_client,
                prompt_loader=self.prompt_loader,
                supabase_client=self.supabase_client,
                config_dir=self.config_dir,
                message_hooks=message_hooks,
            )
            logger.info("✅ Тестер создан с использованием всех настроек из BotBuilder")
            logger.info(f"   - OpenAI клиент: {type(self.openai_client).__name__}")
            logger.info(f"   - PromptLoader: {type(self.prompt_loader).__name__}")
            logger.info(f"   - Supabase клиент: {type(self.supabase_client).__name__}")
            logger.info(f"   - Хуков передано: {total_hooks}")

            # Запускаем тесты
            test_runner = TestRunner(self.bot_id, max_concurrent, self.config_dir.parent.parent)
            test_runner.bot_tester = bot_tester  # Заменяем тестер

            results = await test_runner.run_tests(scenarios)

            # Генерируем отчеты
            ReportGenerator.generate_console_report(self.bot_id, results)
            report_file = ReportGenerator.save_report(self.bot_id, results, self.config_dir.parent.parent)

            logger.info(f"📄 Подробный отчет сохранен: {report_file}")

            # Возвращаем код выхода
            failed_count = sum(1 for r in results if not r.passed)
            return 0 if failed_count == 0 else 1

        except Exception as e:
            logger.error(f"❌ Ошибка при тестировании бота {self.bot_id}: {e}")
            import traceback

            logger.error(f"Стек ошибки: {traceback.format_exc()}")
            return 1

    def _setup_context(self, bot=None, dp=None):
        """
        Устанавливает все компоненты в глобальный контекст ctx

        Args:
            bot: Экземпляр Bot (опционально, если None - не устанавливается)
            dp: Экземпляр Dispatcher (опционально, если None - не устанавливается)
        """
        logger.info("🔧 Установка компонентов в глобальный контекст ctx")

        # Основные компоненты
        ctx.config = self.config
        ctx.supabase_client = self.supabase_client
        ctx.openai_client = self.openai_client
        ctx.prompt_loader = self.prompt_loader

        # Менеджеры
        ctx.admin_manager = self.admin_manager
        ctx.analytics_manager = self.analytics_manager
        ctx.conversation_manager = self.conversation_manager
        ctx.memory_manager = self.memory_manager
        ctx.router_manager = self.router_manager

        # Хуки и настройки
        ctx.message_hooks = self.get_message_hooks()
        ctx.tools_prompt = self.get_tools_prompt()
        ctx.start_handlers = self._start_handlers
        ctx.utm_triggers = self._utm_triggers
        ctx.custom_event_processor = self._custom_event_processor
        ctx.custom_event_proceses = self._custom_event_processor  # DEPRECATED: для обратной совместимости

        # Bot и Dispatcher (если переданы)
        if bot is not None:
            ctx.bot = bot
        if dp is not None:
            ctx.dp = dp

    async def _cleanup_resources(self, bot=None, dp=None):
        """Централизованная очистка всех ресурсов бота"""
        try:
            # Закрываем сессию бота
            if bot and hasattr(bot, 'session'):
                await bot.session.close()
            
            # Закрываем Supabase клиент
            if self.supabase_client:
                close_method = getattr(self.supabase_client, 'close', None)
                if close_method and callable(close_method):
                    await close_method()
            
            # Очищаем временные файлы промптов
            if self.prompt_loader and hasattr(self.prompt_loader, 'cleanup_temp_files'):
                self.prompt_loader.cleanup_temp_files()
            
            # Очищаем контекст
            from ..utils.context import ctx
            ctx.bot = None
            ctx.dp = None
        except Exception:
            pass  # Тихая очистка без логирования

    async def start(self):
        """
        Запускает бота (аналог main.py)

        Автоматически вызывает build() если бот еще не инициализирован.
        Можно вызвать build() явно для проверки без запуска.
        """
        # Автоматически вызываем build() если еще не вызван
        if not self._initialized:
            logger.info(f"🔧 Бот {self.bot_id} не инициализирован, вызываем build() автоматически")
            await self.build()

        logger.info(f"🚀 Запускаем бота {self.bot_id}")

        try:
            # Импортируем необходимые компоненты
            from aiogram import Bot, Dispatcher
            from aiogram.fsm.storage.memory import MemoryStorage

            # Создаем бота и диспетчер
            if not self.config:
                raise RuntimeError("Config не инициализирован. Вызовите build() перед start()")
            bot = Bot(token=self.config.TELEGRAM_BOT_TOKEN)
            
            # Добавляем sulguk middleware для обработки HTML, если parse_mode = HTML
            if self.config.MESSAGE_PARSE_MODE.upper() == "HTML":
                bot.session.middleware(AiogramSulgukMiddleware())
                logger.info("✅ Sulguk middleware добавлен для обработки HTML")
            
            storage = MemoryStorage()
            dp = Dispatcher(storage=storage)

            # Устанавливаем меню команд для бота
            await self._setup_bot_commands(bot)

            # Инициализируем базу данных
            await self.supabase_client.initialize()

            # Синхронизируем админов из конфигурации
            await self.admin_manager.sync_admins_from_config()

            # Проверяем доступность промптов
            prompts_status = await self.prompt_loader.validate_prompts()
            logger.info(f"Статус промптов: {prompts_status}")

            # Импортируем роутеры
            from ..admin.admin_events import admin_events_router
            from ..admin.admin_events_edit import admin_events_edit_router
            from ..admin.admin_logic import admin_router
            from ..handlers.handlers import router as handlers_router
            from ..utils.bot_utils import utils_router

            # Подключаем пользовательские Telegram роутеры ПЕРВЫМИ (высший приоритет)
            if self._telegram_routers:
                logger.info(f"🔗 Подключаем {len(self._telegram_routers)} пользовательских Telegram роутеров")
                for telegram_router in self._telegram_routers:
                    dp.include_router(telegram_router)
                    router_name = getattr(telegram_router, "name", "unnamed")
                    logger.info(f"✅ Подключен Telegram роутер: {router_name}")

            # Подключаем стандартные роутеры (меньший приоритет)
            # ВАЖНО: Специфичные роутеры ПЕРЕД общим handlers_router с catch-all handler
            # Порядок важен: роутеры обрабатываются последовательно
            dp.include_routers(
                admin_events_router,  # Админские события (/создать_событие) - ПЕРВЫМ!
                admin_events_edit_router,  # Редактирование админских событий (/edit_event)
                admin_router,  # Админские команды (/админ, /стат, /чат)
                utils_router,  # Утилитарные команды (/status, /help)
                handlers_router,  # Основные пользовательские обработчики (catch-all в конце)
            )
            
            logger.info("✅ Все стандартные роутеры подключены")

            # Устанавливаем роутер-менеджер в декораторы ПЕРЕД настройкой обработчиков
            if self.router_manager:
                from ..event.decorators.registry import set_router_manager

                set_router_manager(self.router_manager)
                logger.info("✅ RouterManager установлен в decorators")

                # Обновляем обработчики после установки RouterManager
                # (на случай если декораторы выполнялись после добавления роутера)
                self.router_manager._update_combined_handlers()
                logger.info("✅ RouterManager обработчики обновлены")

            # Фоновые задачи выполняются через asyncio.create_task в decorators.py

            # Логируем информацию о запуске
            logger.info(f"✅ Бот {self.bot_id} запущен и готов к работе!")
            if self.config:
                logger.info(f"   📊 Изоляция данных: bot_id = {self.config.BOT_ID}")
                logger.info(f"   👑 Админов настроено: {len(self.config.ADMIN_TELEGRAM_IDS)}")
                logger.info(f"   📝 Загружено промптов: {len(self.config.PROMPT_FILES)}")

            # Запускаем единый фоновый процессор для всех событий
            import asyncio

            from ..event.decorators.processor import background_event_processor

            asyncio.create_task(background_event_processor())
            logger.info("✅ Фоновый процессор событий запущен (user_event, scheduled_task, global_handler, admin_event)")

            # Четкое сообщение о запуске
            print(f"\n🤖 БОТ {self.bot_id.upper()} УСПЕШНО ЗАПУЩЕН!")
            if self.config:
                print(f"📱 Telegram Bot ID: {self.config.BOT_ID}")
                print(f"👑 Админов: {len(self.config.ADMIN_TELEGRAM_IDS)}")
                print(f"📝 Промптов: {len(self.config.PROMPT_FILES)}")
            print("⏳ Ожидание сообщений...")
            print("⏹️ Для остановки нажмите Ctrl+C\n")

            # Устанавливаем все компоненты в ctx
            self._setup_context(bot=bot, dp=dp)

            # Запуск polling (бесконечная обработка сообщений)
            await dp.start_polling(bot)

        except Exception as e:
            logger.error(f"❌ Ошибка при запуске бота {self.bot_id}: {e}")
            import traceback

            logger.error(f"Стек ошибки: {traceback.format_exc()}")
            raise
        finally:
            # Централизованная очистка ресурсов
            await self._cleanup_resources(
                bot=locals().get("bot"),
                dp=locals().get("dp")
            )
