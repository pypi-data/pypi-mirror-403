"""
Mdclinica Bot - Умный Telegram бот на Smart Bot Factory
"""

from smart_bot_factory.router import EventRouter
from smart_bot_factory.message import send_message_by_human
from smart_bot_factory.creation import BotBuilder
from rag_tools import rag_router

# Инициализация
event_router = EventRouter()
bot_builder = BotBuilder()

# =============================================================================
# ОБРАБОТЧИКИ СОБЫТИЙ
# =============================================================================

@event_router.event_handler(notify=True, once_only=True)
async def collect_contact(user_id: int, contact_data: str):
    """
    Обрабатывает получение контактных данных
    
    ИИ создает: {"тип": "collect_contact", "инфо": "+79001234567"}
    """
    await send_message_by_human(
        user_id=user_id,
        message_text=f"✅ Спасибо! Ваши данные сохранены: {contact_data}"
    )
    
    return {"status": "success", "contact": contact_data}


# Регистрация роутеров
bot_builder.register_routers(event_router, rag_router)
