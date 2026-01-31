"""
Утилиты для обработчиков сообщений.
"""

import logging
import re

from aiogram.types import Message
from sulguk import SULGUK_PARSE_MODE

from ..utils.bot_utils import send_message
from ..utils.context import ctx
from .constants import HookType

logger = logging.getLogger(__name__)


def fix_html_markup(text: str) -> str:
    """
    Исправляет HTML разметку в тексте, экранируя неправильные теги.
    Экранирует < и >, которые не являются частью валидных HTML тегов Telegram.

    Args:
        text: Текст с возможными проблемными HTML тегами

    Returns:
        str: Текст с исправленной HTML разметкой
    """
    if not text:
        return text

    # Валидные HTML теги Telegram
    valid_tags = ["b", "i", "u", "s", "code", "pre", "a"]

    # Создаем паттерн для всех валидных тегов (открывающих и закрывающих)
    valid_tag_patterns = []
    for tag in valid_tags:
        # Открывающие теги: <b>, <i>, <code>, <pre>, <a href="...">
        if tag == "a":
            # Для тега <a> учитываем атрибут href
            valid_tag_patterns.append(r'<a\s+href="[^"]*">')
        else:
            valid_tag_patterns.append(f"<{tag}>")
        # Закрывающие теги: </b>, </i>, </code>, </pre>, </a>
        valid_tag_patterns.append(f"</{tag}>")

    # Объединяем все паттерны
    combined_pattern = "|".join(valid_tag_patterns)

    # Находим все валидные теги и заменяем их на плейсхолдеры
    placeholders = {}
    placeholder_counter = 0

    def replace_valid_tag(match):
        nonlocal placeholder_counter
        placeholder = f"__VALID_TAG_{placeholder_counter}__"
        placeholders[placeholder] = match.group()
        placeholder_counter += 1
        return placeholder

    # Заменяем валидные теги на плейсхолдеры
    text_with_placeholders = re.sub(combined_pattern, replace_valid_tag, text, flags=re.IGNORECASE)

    # Экранируем все оставшиеся < и >
    text_escaped = text_with_placeholders.replace("<", "&lt;").replace(">", "&gt;")

    # Восстанавливаем валидные теги
    for placeholder, tag in placeholders.items():
        text_escaped = text_escaped.replace(placeholder, tag)

    return text_escaped


async def send_message_in_parts(
    message: Message,
    text: str,
    files_list: list = [],
    directories_list: list = [],
    max_length: int = 4090,
    parse_mode: str | None = None,
) -> int | None:
    """
    Отправляет сообщение, разбивая его на части, если оно превышает максимальную длину.

    Args:
        message: Message объект от aiogram
        text: Текст сообщения для отправки
        files_list: Список файлов для отправки (отправляются только с первой частью)
        directories_list: Список каталогов для отправки (отправляются только с первой частью)
        max_length: Максимальная длина одного сообщения (по умолчанию 4090)
        parse_mode: Режим парсинга текста (опционально)

    Returns:
        int | None: message_id первого отправленного сообщения или None если не удалось отправить
    """
    # Проверяем, что текст не пустой
    if not text or not text.strip():
        logger.warning("⚠️ Попытка отправить пустое сообщение")
        return 0

    if len(text) <= max_length:
        # Сообщение нормального размера, отправляем как обычно
        sent_message = await send_message(
            message,
            text,
            files_list=files_list,
            directories_list=directories_list,
            parse_mode=parse_mode,
        )
        logger.info(f"✅ Сообщение отправлено ({len(text)} символов)")
        # Возвращаем message_id первого сообщения
        if sent_message and hasattr(sent_message, 'message_id'):
            return sent_message.message_id
        elif isinstance(sent_message, list) and len(sent_message) > 0 and hasattr(sent_message[0], 'message_id'):
            return sent_message[0].message_id
        return None

    logger.info(f"📏 Сообщение слишком длинное ({len(text)} символов), разбиваем на части")

    # Разбиваем текст на части
    parts = []
    current_part = ""

    # Разбиваем по строкам, чтобы не разрывать слова
    lines = text.split("\n")

    for line in lines:
        # Если добавление текущей строки не превысит лимит
        if len(current_part) + len(line) + 1 <= max_length:
            if current_part:
                current_part += "\n" + line
            else:
                current_part = line
        else:
            # Сохраняем текущую часть
            if current_part:
                parts.append(current_part)

            # Если сама строка длиннее лимита, разбиваем её по словам
            if len(line) > max_length:
                words = line.split(" ")
                current_part = ""
                for word in words:
                    if len(current_part) + len(word) + 1 <= max_length:
                        if current_part:
                            current_part += " " + word
                        else:
                            current_part = word
                    else:
                        if current_part:
                            parts.append(current_part)
                        current_part = word
            else:
                current_part = line

    # Добавляем последнюю часть
    if current_part:
        parts.append(current_part)

    logger.info(f"📦 Сообщение разбито на {len(parts)} частей")

    # Отправляем каждую часть отдельным сообщением
    first_message_id = None
    try:
        for idx, part in enumerate(parts, 1):
            # Файлы отправляем только с первой частью
            if idx == 1:
                sent_message = await send_message(
                    message,
                    part,
                    files_list=files_list,
                    directories_list=directories_list,
                    parse_mode=parse_mode,
                )
                # Сохраняем message_id первого сообщения
                if sent_message and hasattr(sent_message, 'message_id'):
                    first_message_id = sent_message.message_id
                elif isinstance(sent_message, list) and len(sent_message) > 0 and hasattr(sent_message[0], 'message_id'):
                    first_message_id = sent_message[0].message_id
            else:
                await send_message(message, part, parse_mode=parse_mode)
            logger.info(f"✅ Часть {idx}/{len(parts)} отправлена ({len(part)} символов)")

        logger.info(f"✅ Все {len(parts)} частей успешно отправлены пользователю {message.from_user.id}")
        return first_message_id
    except Exception as e:
        logger.error(f"❌ ОШИБКА ОТПРАВКИ СООБЩЕНИЯ: {e}")
        # Пытаемся отправить простое сообщение об ошибке
        try:
            await message.answer("Произошла ошибка при отправке ответа. Попробуйте еще раз.")
        except Exception as e2:
            logger.error(f"❌ Не удалось отправить даже сообщение об ошибке: {e2}")
        return None


def prepare_final_response(response_text: str, ai_response: str, debug_mode: bool) -> str:
    """
    Подготавливает финальный ответ для пользователя на основе режима отладки.

    Args:
        response_text: Очищенный текст ответа
        ai_response: Полный ответ с JSON метаданными
        debug_mode: Флаг режима отладки

    Returns:
        str: Финальный ответ для отправки пользователю
    """
    if debug_mode:
        # В режиме отладки показываем полный ответ с JSON
        final_response = ai_response
        logger.debug("Режим отладки: отправляем полный ответ с JSON")
    else:
        # В обычном режиме показываем только текст без JSON
        final_response = response_text
        logger.debug("Обычный режим: отправляем очищенный текст")

    # Проверяем, что есть что отправлять
    if not final_response or not final_response.strip():
        logger.error("❌ КРИТИЧЕСКАЯ ОШИБКА: Финальный ответ пуст!")
        final_response = "Извините, произошла ошибка при формировании ответа. Попробуйте еще раз."

    return final_response


def get_parse_mode_and_fix_html(final_response: str) -> tuple[str, str]:
    """
    Получает parse_mode из конфига и возвращает SULGUK_PARSE_MODE для HTML.

    Args:
        final_response: Текст ответа (может содержать HTML)

    Returns:
        tuple: (parse_mode, текст)
        - Если HTML: (SULGUK_PARSE_MODE, текст) - middleware автоматически обработает HTML
        - Если не HTML: (parse_mode, текст)
    """
    parse_mode = ctx.config.MESSAGE_PARSE_MODE
    if parse_mode.upper() == "HTML":
        logger.debug("Используется SULGUK_PARSE_MODE для HTML - middleware обработает автоматически")
        return SULGUK_PARSE_MODE, final_response
    
    return parse_mode, final_response


async def send_critical_error_message(message: Message) -> None:
    """
    Отправляет пользователю сообщение о критической ошибке.

    Args:
        message: Message объект от aiogram
    """
    try:
        await message.answer("Произошла критическая ошибка. Попробуйте написать /start для перезапуска.")
    except Exception:
        logger.error("❌ Не удалось отправить сообщение об критической ошибке", exc_info=True)


async def apply_send_filters(user_id: int) -> bool:
    """
    Применяет фильтры отправки сообщений.

    Args:
        user_id: ID пользователя

    Returns:
        bool: True если отправка заблокирована, False если можно отправлять
    """
    send_filters = (ctx.message_hooks or {}).get(HookType.SEND_FILTERS, [])
    for filter_func in send_filters:
        try:
            if await filter_func(user_id):
                logger.debug(f"Фильтр '{filter_func.__name__}' заблокировал отправку")
                return True
        except Exception as e:
            logger.error(f"❌ Ошибка в фильтре отправки '{filter_func.__name__}': {e}")

    return False
