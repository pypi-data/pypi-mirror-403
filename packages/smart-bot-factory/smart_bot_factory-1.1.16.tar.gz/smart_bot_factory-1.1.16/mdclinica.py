"""mdclinica.py"""
import asyncio
from smart_bot_factory.router import EventRouter
from smart_bot_factory.message import send_message_by_human
from smart_bot_factory.creation import BotBuilder
from rag_tools import rag_router

# Инициализация
event_router = EventRouter("mdclinica")
bot_builder = BotBuilder("mdclinica")

# =============================================================================
# UTM-ТРИГГЕРЫ
# =============================================================================

bot_builder.register_utm_trigger(
    message='vk_campaign.txt',  # Файл из bots/mdclinica/utm_message/
    source='vk',                 # utm_source должен быть 'vk'
    campaign='summer2025'       # utm_campaign должен быть 'summer2025'
)

# =============================================================================
# ОБРАБОТЧИКИ СОБЫТИЙ
# =============================================================================

@event_router.event_handler("collect_contact", once_only=True)
async def collect_contact(user_id: int, contact_data: str):
    """ИИ создает: {"тип": "collect_contact", "инфо": "+79001234567"}"""
    await send_message_by_human(
        user_id=user_id,
        message_text=f"✅ Спасибо! Ваши данные сохранены: {contact_data}"
    )
    return {"status": "success", "contact": contact_data}


async def main():
    bot_builder.register_routers(event_router, rag_router)
    await bot_builder.build()
    await bot_builder.start()


if __name__ == "__main__":
    asyncio.run(main())
