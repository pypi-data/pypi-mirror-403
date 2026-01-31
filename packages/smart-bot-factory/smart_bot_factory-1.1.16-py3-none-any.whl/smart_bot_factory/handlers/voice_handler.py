"""
Обработчики голосовых сообщений и связанных callback-ов.
"""

import logging
import tempfile
from datetime import datetime
from pathlib import Path

from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sulguk import SULGUK_PARSE_MODE

from ..utils.context import ctx
from .states import UserStates

logger = logging.getLogger(__name__)


async def voice_handler(message: Message, state: FSMContext):
    """Обработчик голосовых и аудио сообщений"""
    processing_msg = None

    try:
        # Проверяем что это не админ в режиме администратора
        if ctx.admin_manager.is_admin(message.from_user.id):
            if ctx.admin_manager.is_in_admin_mode(message.from_user.id):
                return  # Админы работают с текстом

        logger.info(f"🎤 Получено голосовое сообщение от {message.from_user.id}")

        # Получаем файл
        if message.voice:
            file_id = message.voice.file_id
            duration = message.voice.duration
        else:
            file_id = message.audio.file_id
            duration = message.audio.duration

        # Показываем что обрабатываем
        processing_msg = await message.answer("🎤 Распознаю голос...")

        file_path = None
        temp_dir = None
        recognized_text = None

        try:
            # Скачиваем файл
            file = await ctx.bot.get_file(file_id)

            # Используем системную временную директорию
            temp_dir = Path(tempfile.gettempdir()) / "smart_bot_factory_audio"
            temp_dir.mkdir(exist_ok=True, mode=0o700)

            file_path = temp_dir / f"{message.from_user.id}_{int(datetime.now().timestamp())}.ogg"

            # Скачиваем
            await ctx.bot.download_file(file.file_path, file_path)
            logger.info(f"📥 Файл скачан: {file_path} ({duration} сек)")

            # Распознаем через Whisper
            recognized_text = await ctx.openai_client.transcribe_audio(str(file_path))

        finally:
            # Гарантированная очистка временного файла
            if file_path and file_path.exists():
                try:
                    file_path.unlink(missing_ok=True)
                except Exception:
                    pass  # Тихая очистка без логирования

            # Пытаемся удалить папку если она пуста (не критично если не получится)
            if temp_dir and temp_dir.exists():
                try:
                    # Проверяем что папка пуста перед удалением
                    if not any(temp_dir.iterdir()):
                        temp_dir.rmdir()
                except Exception:
                    pass  # Тихая очистка без логирования

        if not recognized_text:
            await processing_msg.edit_text("❌ Не удалось распознать голос. Попробуйте еще раз.")
            return

        logger.info(f"✅ Текст распознан успешно: '{recognized_text[:100]}...'")

        # Получаем данные сессии
        current_state = await state.get_state()
        data = await state.get_data()

        logger.info(f"🔍 Текущее состояние: {current_state}")
        logger.info(f"🔍 Данные в state: {data}")

        session_id = data.get("session_id")

        logger.info(f"📝 session_id из state: {session_id}")

        # Если session_id нет в state, пытаемся получить из БД
        if not session_id:
            logger.warning("⚠️ session_id не найден в state, ищем активную сессию в БД...")

            session_info = await ctx.supabase_client.get_active_session(message.from_user.id)
            if session_info:
                session_id = session_info["id"]

                # Сохраняем в state для следующих сообщений
                await state.update_data(session_id=session_id)
                await state.set_state(UserStates.waiting_for_message)

                logger.info(f"✅ Сессия восстановлена из БД: {session_id}")
            else:
                logger.error("❌ Активная сессия не найдена в БД")

        if session_id:
            # Сохраняем распознанный текст в state
            await state.update_data(voice_recognized_text=recognized_text)
            await state.set_state(UserStates.voice_confirmation)

            # Показываем распознанный текст с кнопками выбора
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="✅ Отправить", callback_data="voice_send")],
                    [InlineKeyboardButton(text="✏️ Изменить текст", callback_data="voice_edit")],
                    [
                        InlineKeyboardButton(
                            text="🎤 Надиктовать заново",
                            callback_data="voice_retry",
                        )
                    ],
                ]
            )

            # Удаляем сообщение "Обрабатываю"
            try:
                await processing_msg.delete()
            except Exception:
                pass

            # Показываем результат с кнопками
            # Используем SULGUK_PARSE_MODE если в конфиге HTML, иначе обычный HTML
            parse_mode = SULGUK_PARSE_MODE if ctx.config and ctx.config.MESSAGE_PARSE_MODE.upper() == "HTML" else "HTML"
            
            await message.answer(
                f"✅ Распознано:\n\n<i>{recognized_text}</i>\n\n" f"Выберите действие:",
                reply_markup=keyboard,
                parse_mode=parse_mode,
            )

            logger.info("✅ Показаны кнопки подтверждения голосового сообщения")
        else:
            logger.warning("❌ Нет session_id в состоянии")
            await processing_msg.edit_text(f"✅ Распознано:\n\n{recognized_text}\n\n" f"Сессия не найдена. Напишите /start")

    except Exception as e:
        logger.error(f"❌ КРИТИЧЕСКАЯ ошибка обработки голоса: {e}")
        logger.exception("Полный стек критической ошибки:")
        try:
            if processing_msg:
                await processing_msg.edit_text("❌ Ошибка распознавания. Попробуйте написать текстом.")
            else:
                await message.answer("❌ Ошибка распознавания. Попробуйте написать текстом.")
        except Exception:
            pass


async def voice_send_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки 'Отправить' для голосового сообщения"""
    # Отвечаем на callback сразу, чтобы не истек таймаут
    try:
        await callback.answer()
    except TelegramBadRequest:
        # Query уже истек, игнорируем
        pass

    try:
        data = await state.get_data()
        recognized_text = data.get("voice_recognized_text")
        session_id = data.get("session_id")

        if not recognized_text or not session_id:
            # Пытаемся показать alert, но не критично если не получится
            try:
                await callback.answer("❌ Ошибка: текст не найден", show_alert=True)
            except TelegramBadRequest:
                pass
            return

        # Удаляем сообщение с кнопками
        try:
            await callback.message.delete()
        except Exception as e:
            logger.warning(f"⚠️ Не удалось удалить сообщение: {e}")

        # Обрабатываем текст сразу без промежуточного сообщения
        # Ленивый импорт для избежания циклического импорта
        from .handlers import process_user_message

        await process_user_message(callback.message, state, session_id, recognized_text=recognized_text)

        # Возвращаем в обычное состояние
        await state.set_state(UserStates.waiting_for_message)
        await state.update_data(voice_recognized_text=None)

    except Exception as e:
        logger.error(f"❌ Ошибка отправки голосового: {e}")
        # Пытаемся показать alert, но не критично если query уже истек
        try:
            await callback.answer("❌ Ошибка обработки", show_alert=True)
        except TelegramBadRequest:
            # Query истек, просто логируем
            logger.warning("⚠️ Не удалось ответить на callback query (истек таймаут)")


async def voice_edit_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки 'Изменить текст' для голосового сообщения"""
    # Отвечаем на callback сразу, чтобы не истек таймаут
    try:
        await callback.answer()
    except TelegramBadRequest:
        # Query уже истек, игнорируем
        pass

    try:
        data = await state.get_data()
        recognized_text = data.get("voice_recognized_text")

        if not recognized_text:
            # Пытаемся показать alert, но не критично если не получится
            try:
                await callback.answer("❌ Ошибка: текст не найден", show_alert=True)
            except TelegramBadRequest:
                pass
            return

        # Переводим в режим редактирования
        await state.set_state(UserStates.voice_editing)

        # Показываем текст для редактирования (обычный формат)
        await callback.message.edit_text(f"✏️ Отредактируйте распознанный текст:\n\n" f"{recognized_text}\n\n" f"Напишите исправленный текст:")

    except Exception as e:
        logger.error(f"❌ Ошибка редактирования: {e}")
        # Пытаемся показать alert, но не критично если query уже истек
        try:
            await callback.answer("❌ Ошибка", show_alert=True)
        except TelegramBadRequest:
            # Query истек, просто логируем
            logger.warning("⚠️ Не удалось ответить на callback query (истек таймаут)")


async def voice_retry_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки 'Надиктовать заново' для голосового сообщения"""
    # Отвечаем на callback сразу, чтобы не истек таймаут
    try:
        await callback.answer()
    except TelegramBadRequest:
        # Query уже истек, игнорируем
        pass

    try:
        # Удаляем сообщение с кнопками
        try:
            await callback.message.delete()
        except Exception as e:
            logger.warning(f"⚠️ Не удалось удалить сообщение: {e}")

        # Возвращаем в обычное состояние
        await state.set_state(UserStates.waiting_for_message)
        await state.update_data(voice_recognized_text=None)

        # Просим отправить заново
        await callback.message.answer("🎤 Отправьте голосовое сообщение заново")

    except Exception as e:
        logger.error(f"❌ Ошибка повтора: {e}")
        # Пытаемся показать alert, но не критично если query уже истек
        try:
            await callback.answer("❌ Ошибка", show_alert=True)
        except TelegramBadRequest:
            # Query истек, просто логируем
            logger.warning("⚠️ Не удалось ответить на callback query (истек таймаут)")


async def voice_edit_text_handler(message: Message, state: FSMContext):
    """Обработчик получения отредактированного текста"""
    try:
        edited_text = message.text.strip()

        if not edited_text:
            await message.answer("⚠️ Текст не может быть пустым. Напишите текст:")
            return

        # Получаем данные сессии
        data = await state.get_data()
        session_id = data.get("session_id")

        if not session_id:
            await message.answer("❌ Сессия не найдена. Напишите /start")
            return

        # Обрабатываем отредактированный текст сразу
        # Ленивый импорт для избежания циклического импорта
        from .handlers import process_user_message

        await process_user_message(message, state, session_id, recognized_text=edited_text)

        # Возвращаем в обычное состояние
        await state.set_state(UserStates.waiting_for_message)
        await state.update_data(voice_recognized_text=None)

    except Exception as e:
        logger.error(f"❌ Ошибка обработки отредактированного текста: {e}")
        await message.answer("❌ Ошибка обработки. Попробуйте еще раз или напишите /start")
