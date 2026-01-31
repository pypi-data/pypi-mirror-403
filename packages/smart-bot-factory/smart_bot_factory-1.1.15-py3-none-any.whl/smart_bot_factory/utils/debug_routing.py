# debug_routing.py - Утилиты для отладки маршрутизации сообщений

import logging

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from .context import ctx

logger = logging.getLogger(__name__)

# Создаем роутер для отладочных обработчиков
debug_router = Router()


def setup_debug_handlers(dp):
    """Настройка отладочных обработчиков"""
    dp.include_router(debug_router)


async def debug_user_state(message: Message, state: FSMContext, context: str):
    """Отладочная функция для логирования состояния пользователя"""
    user_id = message.from_user.id
    current_state = await state.get_state()
    state_data = await state.get_data()

    logger.debug(f"DEBUG [{context}] User {user_id}:")
    logger.debug(f"   FSM State: {current_state}")
    logger.debug(f"   State Data: {list(state_data.keys())}")
    logger.debug(f"   Message: '{message.text[:50]}...'")

    # Проверяем диалог с админом в БД
    conversation = await ctx.conversation_manager.is_user_in_admin_chat(user_id)
    logger.debug(f"   Admin Chat in DB: {'✅' if conversation else '❌'}")

    if conversation:
        logger.debug(f"   Admin ID: {conversation['admin_id']}")
        logger.debug(f"   Conversation ID: {conversation['id']}")

    # Проверяем активную сессию
    session_info = await ctx.supabase_client.get_active_session(user_id)
    logger.debug(f"   Active Session: {'✅' if session_info else '❌'}")

    if session_info:
        logger.debug(f"   Session ID: {session_info['id']}")

    logger.debug(f"   {'='*50}")


async def debug_admin_conversation_creation(admin_id: int, user_id: int):
    """Отладка создания диалога админа с пользователем"""
    logger.debug("DEBUG CONVERSATION CREATION:")
    logger.debug(f"   Admin: {admin_id}")
    logger.debug(f"   User: {user_id}")

    # Проверяем активную сессию пользователя ДО создания диалога
    session_info = await ctx.supabase_client.get_active_session(user_id)
    logger.debug(f"   User has active session: {'✅' if session_info else '❌'}")

    if session_info:
        logger.debug(f"   Session ID: {session_info['id']}")
        logger.debug(f"   Session created: {session_info['created_at']}")

    # Проверяем существующие диалоги пользователя
    try:
        existing = ctx.supabase_client.client.table("admin_user_conversations").select("*").eq("user_id", user_id).eq("status", "active").execute()

        logger.debug(f"   Existing active conversations: {len(existing.data)}")
        for conv in existing.data:
            logger.debug(f"      - ID: {conv['id']}, Admin: {conv['admin_id']}")
    except Exception as e:
        logger.error(f"   ❌ Error checking existing conversations: {e}")


async def test_message_routing(user_id: int, test_message: str):
    """Тестирует маршрутизацию сообщения без отправки через Telegram"""
    logger.info("🧪 TESTING MESSAGE ROUTING:")
    logger.info(f"   👤 User: {user_id}")
    logger.info(f"   💬 Message: '{test_message}'")

    # Проверяем есть ли диалог с админом
    conversation = await ctx.conversation_manager.is_user_in_admin_chat(user_id)
    logger.info(f"   🗃️ Admin conversation exists: {'✅' if conversation else '❌'}")

    if conversation:
        logger.info(f"   👑 Admin: {conversation['admin_id']}")
        logger.info(f"   🆔 Conv ID: {conversation['id']}")
        logger.info(f"   📅 Started: {conversation['started_at']}")

        # Тестируем должен ли этот пользователь быть в admin_chat
        return "admin_chat"
    else:
        return "bot_chat"
