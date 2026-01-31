from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from aiogram import Bot, Dispatcher

    from ..admin.admin_manager import AdminManager
    from ..analytics.analytics_manager import AnalyticsManager
    from ..config import Config
    from ..event.router_manager import RouterManager
    from ..integrations.openai.langchain_openai import LangChainOpenAIClient
    from ..integrations.openai.prompt_loader import PromptLoader
    from ..integrations.supabase_client import SupabaseClient
    from ..memory.memory_manager import MemoryManager
    from ..utils.conversation_manager import ConversationManager


class AppContext:
    def __init__(self):
        self.config: Optional[Config] = None
        self.supabase_client: Optional[SupabaseClient] = None
        self.openai_client: Optional[LangChainOpenAIClient] = None
        self.prompt_loader: Optional[PromptLoader] = None
        self.conversation_manager: Optional[ConversationManager] = None
        self.admin_manager: Optional[AdminManager] = None
        self.analytics_manager: Optional[AnalyticsManager] = None
        self.memory_manager: Optional[MemoryManager] = None
        self.router_manager: Optional[RouterManager] = None
        self.message_hooks: Dict[str, Any] = {}
        self.tools_prompt: str = ""
        self.start_handlers: List[Any] = []
        self.utm_triggers: List[Any] = []
        self.custom_event_processor = None  # Кастомный процессор событий
        self.custom_event_proceses = None  # DEPRECATED: используйте custom_event_processor
        self.bot: Optional[Bot] = None
        self.dp: Optional[Dispatcher] = None


# глобальный, но единственный объект-контейнер
ctx = AppContext()
