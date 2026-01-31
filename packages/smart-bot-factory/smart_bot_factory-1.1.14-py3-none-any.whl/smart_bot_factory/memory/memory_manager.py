import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from langchain.messages import SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)


class MemoryManager:
    def __init__(self, supabase_client=None, config=None):
        """
        Инициализация MemoryManager.

        Args:
            supabase_client: Клиент Supabase. Если None, будет попытка получить через ctx (lazy import)
            config: Конфигурация бота. Если None, будет попытка получить через ctx (lazy import)
        """
        # Отложенный импорт для избежания циклических зависимостей
        if supabase_client is None or config is None:
            try:
                from ..utils.context import ctx

                if supabase_client is None:
                    supabase_client = ctx.supabase_client
                if config is None:
                    config = ctx.config
            except (ImportError, AttributeError):
                pass

        if supabase_client is None:
            raise ValueError("supabase_client должен быть передан или доступен через ctx")
        if config is None:
            raise ValueError("config должен быть передан или доступен через ctx")

        self.supabase_client = supabase_client

        self.max_memory_messages = config.MAX_CONTEXT_MESSAGES
        self.min_memory_messages = config.HISTORY_MIN_MESSAGES if config.HISTORY_MIN_MESSAGES else 4
        self.token_limit = config.HISTORY_MAX_TOKENS if config.HISTORY_MAX_TOKENS else 5000

        self.chat_model = ChatOpenAI(model="gpt-5-mini", api_key=config.OPENAI_API_KEY) | StrOutputParser()

        # Словарь для отслеживания активных фоновых задач суммаризации по session_id
        self._active_summarization_tasks: Dict[str, asyncio.Task] = {}

    async def get_memory_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """Возвращает историю сообщений в формате OpenAI (список словарей с role и content)"""
        chat_messages: List[Dict[str, Any]] = []

        logger.debug(f"[MemoryManager] Запрос истории для сессии {session_id}")
        session_info = await self.supabase_client.get_session_info(session_id)
        messages_len = session_info.get("messages_len", self.min_memory_messages)
        logger.debug(f"[MemoryManager] Текущий messages_len={messages_len}, min={self.min_memory_messages}, max={self.max_memory_messages}")

        stored_summary = session_info.get("summary", "")
        last_session_info = session_info.get("service_info", {})

        # Получаем обработанные события для сессии (максимум 5 последних)
        processed_events = await self.supabase_client.get_session_processed_events(session_id, limit=5)

        # Формируем контент для system сообщения
        system_content_parts = []

        if stored_summary:
            logger.debug("[MemoryManager] Найдена сохраненная суммаризация — добавляем в контекст")
            formatted_summary = self._format_summary(stored_summary)
            logger.debug(f"[MemoryManager] Форматированная суммаризация: {formatted_summary[:200]}...")
            system_content_parts.append(formatted_summary)
        else:
            logger.debug("[MemoryManager] Суммаризация не найдена в сессии")

        if last_session_info:
            formatted_service_info = self._format_service_info(last_session_info)
            if formatted_service_info:
                system_content_parts.append(f"\n## Информация о последней сессии:\n{formatted_service_info}")

        if processed_events:
            formatted_processed_events = self._format_processed_events(processed_events)
            if formatted_processed_events:
                system_content_parts.append(f"\n## Недавно обработанные события:\n{formatted_processed_events}")

        # Добавляем system сообщение только если есть что добавить
        if system_content_parts:
            combined_content = "\n\n".join(system_content_parts)
            chat_messages.append({"role": "system", "content": combined_content})
            logger.debug(f"[MemoryManager] Добавлено system сообщение с суммаризацией и service_info ({len(combined_content)} символов)")

        messages = await self.supabase_client.get_chat_history(session_id, limit=messages_len)
        logger.debug(f"[MemoryManager] Получено {len(messages)} сообщений из истории (limit={messages_len})")

        added_count = 0
        for msg in messages:
            if msg["role"] in ("user", "assistant"):
                chat_messages.append({"role": msg["role"], "content": msg["content"]})
                added_count += 1
            else:
                logger.debug(f"[MemoryManager] Пропущено сообщение с ролью: {msg['role']}")

        logger.debug(f"[MemoryManager] Добавлено {added_count} сообщений из истории в контекст")

        total_tokens = self._count_tokens(chat_messages)
        logger.debug(f"[MemoryManager] Подготовлено сообщений: {len(chat_messages)}, оценка токенов: {total_tokens}")

        # Проверяем, нужно ли обрезать (исключаем суммаризацию из подсчета для проверки лимита сообщений)
        has_summary = chat_messages and chat_messages[0].get("role") == "system" and self._is_summary_message(chat_messages[0])
        effective_messages_count = len(chat_messages) - (1 if has_summary else 0)

        # Если нужно обрезать, делаем быструю обрезку без суммаризации и запускаем фоновую задачу
        if total_tokens > self.token_limit or effective_messages_count > self.max_memory_messages - 1:
            logger.warning(
                f"""[MemoryManager] История превышает лимиты (tokens>{self.
                token_limit} или messages>{effective_messages_count}>{self.
                max_memory_messages - 1}). Делаем быструю обрезку и запускаем 
                фоновую суммаризацию."""
            )
            # Быстрая обрезка: просто берем последние сообщения
            history_tail_size = max(self.min_memory_messages - 1, 0)
            if has_summary:
                # Сохраняем суммаризацию и берем хвост истории
                summary_msg = chat_messages[0]
                history_messages = chat_messages[1:]
                history_tail = history_messages[-history_tail_size:] if history_tail_size else []
                chat_messages = [summary_msg] + history_tail
            else:
                # Берем только хвост истории
                chat_messages = chat_messages[-history_tail_size:] if history_tail_size else []

            logger.debug(f"[MemoryManager] Быстрая обрезка выполнена: {len(chat_messages)} сообщений")

            # Очищаем завершенные задачи из словаря (предотвращаем утечки памяти)
            completed_sessions = [sid for sid, task in self._active_summarization_tasks.items() if task.done()]
            for sid in completed_sessions:
                del self._active_summarization_tasks[sid]
                logger.debug(f"[MemoryManager] Удалена завершенная задача для сессии {sid}")

            # Проверяем, не запущена ли уже фоновая суммаризация для этой сессии
            if session_id in self._active_summarization_tasks:
                existing_task = self._active_summarization_tasks[session_id]
                if not existing_task.done():
                    logger.debug(f"[MemoryManager] Фоновая суммаризация уже выполняется для сессии {session_id}, пропускаем запуск новой")
                    # Не запускаем новую задачу, существующая уже обработает все сообщения из БД
                else:
                    # Задача завершена (не должна быть здесь после очистки, но на всякий случай)
                    del self._active_summarization_tasks[session_id]
                    task = asyncio.create_task(self._background_summarize(session_id))
                    self._active_summarization_tasks[session_id] = task
                    logger.debug(f"[MemoryManager] Запущена новая фоновая задача суммаризации для сессии {session_id}")
            else:
                # Нет активной задачи, запускаем новую
                task = asyncio.create_task(self._background_summarize(session_id))
                self._active_summarization_tasks[session_id] = task
                logger.info(f"[MemoryManager] Запущена фоновая задача суммаризации для сессии {session_id}")

        # Извлекаем суммаризацию из финального списка сообщений
        summary_for_storage = self._extract_summary(chat_messages)
        messages_len = self._calculate_messages_len(chat_messages)

        # Обновляем сессию в фоне (не блокируем возврат контекста)
        async def _update_session_background():
            try:
                await self.supabase_client.update_session(session_id, {"messages_len": messages_len, "summary": summary_for_storage})
                logger.info(f"[MemoryManager] Сессия {session_id} обновлена в БД (фоновая задача)")
            except Exception as e:
                logger.error(f"[MemoryManager] Ошибка фонового обновления сессии {session_id}: {e}")

        # Запускаем обновление в фоне, не ждем завершения
        asyncio.create_task(_update_session_background())
        logger.debug(f"[MemoryManager] Запущена фоновая задача обновления сессии {session_id}")

        return chat_messages

    async def _background_summarize(self, session_id: str):
        """
        Фоновая задача для создания суммаризации истории диалога.
        Выполняется асинхронно, не блокирует основной поток.
        """
        try:
            logger.info(f"[MemoryManager] 🔄 Начало фоновой суммаризации для сессии {session_id}")

            # Получаем полную историю из БД для суммаризации
            session_info = await self.supabase_client.get_session_info(session_id)
            messages_len = session_info.get("messages_len", self.min_memory_messages)

            # Получаем больше сообщений для суммаризации (берем больше, чем обычно)
            full_messages = await self.supabase_client.get_chat_history(session_id, limit=messages_len * 2)

            # Формируем список сообщений для суммаризации
            messages_for_summary: List[Dict[str, Any]] = []
            existing_summary = session_info.get("summary", "")

            if existing_summary:
                formatted_summary = self._format_summary(existing_summary)
                messages_for_summary.append({"role": "system", "content": formatted_summary})

            for msg in full_messages:
                if msg["role"] in ("user", "assistant"):
                    messages_for_summary.append({"role": msg["role"], "content": msg["content"]})

            logger.info(f"[MemoryManager] 📚 Получено {len(messages_for_summary)} сообщений для суммаризации")

            # Создаем суммаризацию
            trimmed_messages = await self._trim_messages(messages_for_summary, existing_summary)

            # Извлекаем новую суммаризацию
            new_summary = self._extract_summary(trimmed_messages)
            new_messages_len = self._calculate_messages_len(trimmed_messages)

            # Сохраняем результат в БД
            await self.supabase_client.update_session(session_id, {"messages_len": new_messages_len, "summary": new_summary})

            logger.info(
                f"[MemoryManager] ✅ Фоновая суммаризация завершена для сессии {session_id}. "
                f"Новая суммаризация: {len(new_summary)} символов, messages_len={new_messages_len}"
            )

        except Exception as e:
            logger.error(f"[MemoryManager] ❌ Ошибка в фоновой суммаризации для сессии {session_id}: {e}")
            logger.exception("Полный стек ошибки:")
        finally:
            # Удаляем задачу из словаря активных задач после завершения (успешного или с ошибкой)
            if session_id in self._active_summarization_tasks:
                del self._active_summarization_tasks[session_id]
                logger.debug(f"[MemoryManager] Задача суммаризации для сессии {session_id} удалена из активных")

    async def _trim_messages(
        self,
        messages: List[Dict[str, Any]],
        summary: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Обрезает сообщения, создавая суммаризацию. Работает со словарями OpenAI."""
        existing_summary = summary or self._extract_summary(messages)
        logger.info(f"[MemoryManager] Извлечена существующая суммаризация: {len(existing_summary) if existing_summary else 0} символов")

        messages_history: List[Dict[str, Any]] = (
            messages[1:] if messages and messages[0].get("role") == "system" and self._is_summary_message(messages[0]) else messages
        )
        logger.info(f"[MemoryManager] История для суммаризации: {len(messages_history)} сообщений (исходно было {len(messages)})")

        summary_prompt = SystemMessage(
            content=f"""
Ты — ассистент для суммаризации диалогов.

Твоя задача — объединить уже существующую суммаризацию с новыми сообщениями из истории.
ВАЖНО: суммаризация описывает ТОЛЬКО **действия, намерения и факты, предоставленные пользователем**, 
НИКОГДА не включай действия или шаги бота.

Прошлая суммаризация: {existing_summary if existing_summary else ""}

Правила суммаризации:
- Не включай действия бота (например: "Бот отправил ссылку", "Бот создал заказ") — это запрещено.
- Опиши только **пользовательские намерения, запросы и факты**.
- Суммаризация должна быть компактной и связной.
- Не добавляй советов, объяснений или будущих шагов.
- Максимальный размер: 500 токенов.

Примеры:
Плохо: "Бот отправил ссылку, пользователь прочитал сообщение"
Хорошо: "Пользователь оформляет заказ, ожидает оплаты"

Возвращай только текст суммаризации, без любых других комментариев или JSON.

Новые сообщения будут добавлены ниже --------------------------------------------------------------
"""
        )

        # Конвертируем словари OpenAI в LangChain сообщения для вызова модели
        from ..handlers.converters import MessageConverter

        langchain_history = MessageConverter.openai_messages_to_langchain(messages_history)
        prompt_messages = [summary_prompt] + langchain_history

        logger.info(f"[MemoryManager] Отправляем {len(messages_history)} сообщений на суммаризацию")
        new_summary_text = await self.chat_model.ainvoke(prompt_messages)
        logger.info(f"[MemoryManager] Получена новая суммаризация: {len(new_summary_text)} символов")

        formatted_summary = self._format_summary(new_summary_text)
        new_summary = {"role": "system", "content": formatted_summary}
        logger.info(f"[MemoryManager] Форматированная суммаризация: {len(formatted_summary)} символов")

        history_tail_size = max(self.min_memory_messages - 1, 0)
        history_tail = messages_history[-history_tail_size:] if history_tail_size else []
        logger.info(f"[MemoryManager] Новая суммаризация создана. Возвращаем {1 + len(history_tail)} сообщений (summary + хвост).")

        return [new_summary] + history_tail

    def _calculate_messages_len(self, messages: List[Dict[str, Any]]) -> int:
        """Вычисляет messages_len для словарей OpenAI"""
        effective_len = len(messages)

        if messages and messages[0].get("role") == "system" and self._is_summary_message(messages[0]):
            effective_len -= 1

        result = max(effective_len, 0) + 2
        logger.debug(f"[MemoryManager] Расчет messages_len: исходно={len(messages)}, эффективно={effective_len}, итог={result}")
        return result

    def _count_tokens(self, messages: List[Dict[str, Any]]) -> int:
        """Подсчитывает токены для словарей OpenAI"""
        tokens = 0
        for msg in messages:
            content = msg.get("content", "")
            tokens += max(1, len(content) // 4)
        logger.debug(f"[MemoryManager] Оценка токенов для {len(messages)} сообщений: {tokens}")
        return tokens

    def _format_summary(self, summary: str) -> str:
        header = "## Суммаризация истории диалога (предыдущие сообщения до текущего момента):"
        summary_body = summary.strip()
        if not summary_body:
            return header
        return f"{header}\n{summary_body}"

    def _format_service_info(self, service_info: Dict[str, Any]) -> str:
        """Форматирует service_info, извлекая только этап и события для промпта."""
        parts = []

        # Извлекаем этап
        stage = service_info.get("этап")
        if stage:
            parts.append(f"Этап: {stage}")

        # Извлекаем события
        events = service_info.get("события", [])
        if events:
            events_text = []
            for event in events:
                event_type = event.get("тип", "")
                event_info = event.get("инфо", "")
                if event_type:
                    event_str = f"- {event_type}"
                    if event_info:
                        event_str += f": {event_info}"
                    events_text.append(event_str)

            if events_text:
                parts.append("События:\n" + "\n".join(events_text))

        return "\n".join(parts) if parts else ""

    def _format_processed_events(self, events: List[Dict[str, Any]]) -> str:
        """Форматирует обработанные события с датой и временем для промпта."""
        if not events:
            return ""

        # Разворачиваем список, чтобы события шли в хронологическом порядке (от старых к новым)
        events = list(reversed(events))

        events_text = []
        for event in events:
            event_type = event.get("event_type", "")
            executed_at_str = event.get("executed_at", "")

            if not event_type:
                continue

            # Форматируем дату/время
            datetime_str = ""
            if executed_at_str:
                try:
                    # Парсим ISO формат даты
                    if isinstance(executed_at_str, str):
                        # Заменяем Z на +00:00 для совместимости с fromisoformat
                        iso_str = executed_at_str.replace("Z", "+00:00")
                        # Убираем миллисекунды если есть
                        if "." in iso_str and "+" in iso_str:
                            iso_str = iso_str.split(".")[0] + iso_str[iso_str.index("+") :]
                        dt = datetime.fromisoformat(iso_str)
                    elif isinstance(executed_at_str, datetime):
                        dt = executed_at_str
                    else:
                        dt = None

                    if dt:
                        # Форматируем в читаемый вид: ДД.ММ.ГГГГ ЧЧ:ММ
                        datetime_str = dt.strftime("%d.%m.%Y %H:%M")
                except (ValueError, AttributeError, TypeError) as e:
                    logger.debug(f"Не удалось распарсить дату события: {executed_at_str}, ошибка: {e}")
                    # Если не удалось распарсить, просто пропускаем дату

            # Формируем строку события
            event_str = f"- {event_type}"
            if datetime_str:
                event_str += f" {datetime_str}"

            events_text.append(event_str)

        return "\n".join(events_text) if events_text else ""

    def _is_summary_message(self, message: Dict[str, Any]) -> bool:
        """Проверяет, является ли сообщение суммаризацией (для словаря OpenAI)."""
        if message.get("role") != "system":
            return False
        content = message.get("content", "").strip()
        return content.startswith("## Суммаризация истории диалога")

    def _extract_summary(self, messages: List[Dict[str, Any]]) -> str:
        """Извлекает суммаризацию из первого сообщения (для словарей OpenAI)."""
        if not messages or messages[0].get("role") != "system" or not self._is_summary_message(messages[0]):
            return ""

        content = messages[0].get("content", "").strip()
        header = "## Суммаризация истории диалога (предыдущие сообщения до текущего момента):"
        if content.startswith(header):
            summary_text = content[len(header) :].lstrip()
            # Возвращаем пустую строку, если суммаризация содержит только заголовок
            return summary_text if summary_text else ""
        return content
