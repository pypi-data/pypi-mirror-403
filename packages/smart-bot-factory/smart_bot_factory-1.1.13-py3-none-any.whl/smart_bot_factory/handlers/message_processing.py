"""
Функции для обработки сообщений пользователей.
"""

import logging
import time
from datetime import datetime
from typing import Optional

from aiogram.types import Message

from ..memory.memory_manager import MemoryManager
from ..utils.bot_utils import process_events
from .constants import (
    EVENT_EMOJI_MAP,
    FALLBACK_ERROR_MESSAGE,
    MOSCOW_TZ,
    AIMetadataKey,
    HookType,
    MessageRole,
)
from .converters import MessageConverter

logger = logging.getLogger(__name__)


async def _validate_message(user_message_text: str, message: Message, message_hooks: dict) -> bool:
    """
    Валидирует сообщение пользователя через зарегистрированные хуки.

    Args:
        user_message_text: Текст сообщения пользователя
        message: Объект сообщения от aiogram
        message_hooks: Словарь с хуками для обработки сообщений

    Returns:
        bool: True если валидация прошла, False если обработка должна быть прервана
    """
    validators = message_hooks.get(HookType.VALIDATORS, [])
    if not validators:
        return True  # Нет валидаторов - пропускаем

    for validator in validators:
        try:
            should_continue = await validator(user_message_text, message)
            if not should_continue:
                logger.info(f"⛔ Валидатор '{validator.__name__}' прервал обработку")
                return False  # Прерываем обработку
        except Exception as e:
            logger.error(f"❌ Ошибка в валидаторе '{validator.__name__}': {e}")

    return True  # Все валидаторы прошли


async def _enrich_prompt(system_prompt: str, user_id: int, message_hooks: dict) -> tuple[str, str]:
    """
    Обогащает системный промпт временем и через хуки обогащения.

    Args:
        system_prompt: Базовый системный промпт
        user_id: ID пользователя
        message_hooks: Словарь с хуками для обработки сообщений

    Returns:
        tuple[str, str]: (обогащенный промпт, информация о времени в строковом формате)
    """
    # Получаем текущее время
    current_time = datetime.now(MOSCOW_TZ)
    time_info = current_time.strftime("%H:%M, %d.%m.%Y, %A")

    # Базовый системный промпт с временем
    system_prompt_with_time = f"""
{system_prompt}

ТЕКУЩЕЕ ВРЕМЯ: {time_info} (московское время)
"""

    # Обогащаем промпт через хуки
    prompt_enrichers = message_hooks.get(HookType.PROMPT_ENRICHERS, [])
    for enricher in prompt_enrichers:
        try:
            system_prompt_with_time = await enricher(system_prompt_with_time, user_id)
            logger.debug(f"✅ Промпт обогащен '{enricher.__name__}'")
        except Exception as e:
            logger.error(f"❌ Ошибка в обогатителе промпта '{enricher.__name__}': {e}")

    return system_prompt_with_time, time_info


async def _build_context(system_prompt_with_time: str, session_id: str, prompt_loader, memory_manager, message_hooks: dict, time_info: str) -> list:
    """
    Строит контекст для OpenAI из системного промпта, истории и финальных инструкций.

    Args:
        system_prompt_with_time: Обогащенный системный промпт с временем
        session_id: ID сессии
        prompt_loader: Загрузчик промптов
        memory_manager: Менеджер памяти
        message_hooks: Словарь с хуками для обработки сообщений
        time_info: Информация о времени в строковом формате

    Returns:
        list: Список сообщений для OpenAI
    """
    # Формируем контекст для OpenAI с обновленным системным промптом
    messages = [{"role": MessageRole.SYSTEM, "content": system_prompt_with_time}]

    # Получаем историю сообщений через MemoryManager
    if not memory_manager:
        logger.warning("⚠️ MemoryManager не найден — создаю новый экземпляр")
        # MemoryManager будет использовать отложенный импорт ctx при необходимости
        try:
            memory_manager = MemoryManager()
        except (ValueError, AttributeError) as e:
            logger.error(f"❌ Не удалось создать MemoryManager: {e}")
            logger.warning("⚠️ Продолжаем без MemoryManager - история будет пустой")
            memory_messages = []
            return messages
        import smart_bot_factory.handlers.handlers as handlers_module

        setattr(handlers_module, "memory_manager", memory_manager)
        logger.info("✅ MemoryManager инициализирован динамически")

    logger.debug("Загружаем историю из MemoryManager")
    memory_messages = await memory_manager.get_memory_messages(session_id)
    logger.debug(f"История MemoryManager: {len(memory_messages)} сообщений")

    # Детальное логирование только в DEBUG режиме
    if logger.isEnabledFor(logging.DEBUG):
        for idx, msg in enumerate(memory_messages):
            role = msg.get("role", "unknown")
            content_preview = (msg.get("content", "") or "")[:120].replace("\n", " ")
            logger.debug(f"   #{idx + 1} [{role}] {content_preview}")

    messages.extend(memory_messages)

    # Добавляем финальные инструкции в конец контекста
    final_instructions = await prompt_loader.load_final_instructions()
    if final_instructions:
        messages.append({"role": MessageRole.SYSTEM, "content": final_instructions})
        logger.debug("Добавлены финальные инструкции")
    else:
        logger.debug("Нет финальных инструкций")

    # ============ ХУК 3: ОБОГАЩЕНИЕ КОНТЕКСТА ============
    context_enrichers = message_hooks.get(HookType.CONTEXT_ENRICHERS, [])
    for enricher in context_enrichers:
        try:
            # Вызываем хук с сообщениями в формате OpenAI
            messages = await enricher(messages)
            logger.debug(f"✅ Контекст обогащен '{enricher.__name__}'")
        except Exception as e:
            logger.error(f"❌ Ошибка в обогатителе контекста '{enricher.__name__}': {e}")

    logger.debug(f"Контекст сформирован: {len(messages)} сообщений")

    return messages


async def _process_ai_response(messages: list, openai_client, message_hooks: dict, user_id: int) -> tuple[str, dict, int, dict]:
    """
    Обрабатывает ответ от OpenAI: получает ответ, парсит, обрабатывает через хуки.

    Args:
        messages: Список сообщений в формате OpenAI
        openai_client: Клиент OpenAI
        message_hooks: Словарь с хуками для обработки сообщений
        user_id: ID пользователя

    Returns:
        tuple[str, dict, int, dict]: (текст ответа, метаданные, время обработки в мс, исходный ответ для DEBUG)
    """
    start_time = time.time()

    # Конвертируем сообщения в формат LangChain и получаем ответ
    langchain_messages = MessageConverter.openai_messages_to_langchain(messages)
    ai_response = await openai_client.get_completion(langchain_messages)

    processing_time = int((time.time() - start_time) * 1000)

    # Сохраняем исходный ответ для DEBUG_MODE
    original_ai_response = ai_response

    # Инициализируем переменные
    ai_metadata = ai_response.service_info
    response_text = ai_response.user_message

    # Проверяем ответ
    if not response_text or not response_text.strip():
        logger.warning("❌ OpenAI вернул пустой/пробельный ответ!")

        # Проверяем, были ли использованы токены при пустом ответе
        if hasattr(openai_client, "last_completion_tokens"):
            logger.warning(f"⚠️ Токены использованы ({openai_client.last_completion_tokens}), но ответ пустой")

        # Устанавливаем fallback ответ
        response_text = FALLBACK_ERROR_MESSAGE
        ai_metadata = {}
    else:
        logger.debug(f"Ответ OpenAI получен: {len(response_text)} символов")

    # ============ ХУК 4: ОБРАБОТКА ОТВЕТА ============
    response_processors = message_hooks.get(HookType.RESPONSE_PROCESSORS, [])
    for processor in response_processors:
        try:
            response_text, ai_metadata = await processor(response_text, ai_metadata, user_id)
            logger.debug(f"✅ Ответ обработан '{processor.__name__}'")
        except Exception as e:
            logger.error(f"❌ Ошибка в обработчике ответа '{processor.__name__}': {e}")

    # Проверяем response_text после обработки процессорами
    if not response_text or not response_text.strip():
        logger.warning("⚠️ response_text стал пустым после обработки процессорами, устанавливаем fallback")
        response_text = FALLBACK_ERROR_MESSAGE

    return response_text, ai_metadata, processing_time, original_ai_response


async def _process_metadata(
    ai_metadata: dict, session_id: str, user_id: int, supabase_client, response_text: str, chat_id: Optional[int] = None
) -> tuple[bool, list]:
    """
    Обрабатывает метаданные от AI: этап, качество, события, файловые события.

    Args:
        ai_metadata: Словарь с метаданными от AI
        session_id: ID сессии
        user_id: ID пользователя
        supabase_client: Клиент Supabase
        response_text: Текст ответа (для возможной модификации)
        chat_id: ID чата для отправки файлов (опционально, по умолчанию = user_id)

    Returns:
        tuple[bool, list]: (should_send_response, file_senders)
        file_senders - список FileSender объектов для обработки файловых событий
    """
    from ..utils.bot_utils import process_file_events

    should_send_response = True  # По умолчанию отправляем ответ
    file_senders = []

    if not ai_metadata:
        return should_send_response, file_senders

    logger.debug("Анализ метаданных от ИИ")

    # Вывод информации об этапе
    stage = ai_metadata.get(AIMetadataKey.STAGE)
    if stage:
        logger.debug(f"Этап диалога: {stage}")

    # Вывод информации о качестве лида
    quality = ai_metadata.get(AIMetadataKey.QUALITY)
    if quality is not None:
        logger.debug(f"Качество лида: {quality}/10")

    # Обрабатываем события
    events = ai_metadata.get(AIMetadataKey.EVENTS, [])
    if events:
        logger.info(f"События в диалоге: {len(events)}")
        if logger.isEnabledFor(logging.DEBUG):
            for idx, event in enumerate(events, 1):
                event_type = event.get(AIMetadataKey.EVENT_TYPE, "неизвестно")
                event_info = event.get(AIMetadataKey.EVENT_INFO, "нет информации")
                event_emoji = EVENT_EMOJI_MAP.get(event_type.lower(), "📌")
                logger.debug(f"   {idx}. {event_emoji} {event_type}: {event_info}")

        # Обрабатываем обычные события (не файловые)
        should_send_response = await process_events(session_id, events, user_id)
        logger.debug(f"События обработаны, should_send_response = {should_send_response}")

        # Обрабатываем файловые события отдельно
        if chat_id is None:
            chat_id = user_id  # По умолчанию chat_id = user_id

        file_senders = await process_file_events(
            events=events,
            user_id=user_id,
            session_id=session_id,
            chat_id=chat_id,
            supabase_client=supabase_client,
        )

        if file_senders:
            logger.info(f"📁 Обработано {len(file_senders)} файловых событий")

    # Обновляем все данные сессии одним запросом (оптимизация: объединяем stage, quality и service_info)
    service_info = ai_metadata
    has_updates = (stage or quality is not None) or service_info
    if has_updates:
        try:
            await supabase_client.update_session_all(session_id, stage, quality, service_info)
            logger.debug("Данные сессии обновлены в БД (stage, quality, service_info)")
        except Exception as e:
            logger.error(f"Ошибка обновления данных сессии в БД: {e}")

    return should_send_response, file_senders
