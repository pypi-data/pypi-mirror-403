import json
import logging
from typing import Any, Dict, List

from langchain.agents import create_agent
from langchain.agents.structured_output import ProviderStrategy
from langchain.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from openai import AsyncOpenAI
from pydantic import ValidationError

from .responce_models import (
    AnalyzeSentimentResponseModel,
    GenerateFollowUpResponseModel,
    MainResponseModel,
)

logger = logging.getLogger(__name__)


class LangChainOpenAIClient:
    """Клиент для работы с OpenAI API через LangChain v1.0"""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-5",
        max_tokens: int = 1500,
        temperature: float = 0.7,
    ):
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

        self.client = AsyncOpenAI(api_key=api_key)

        # Список инструментов для ChatOpenAI
        self._tools: List[Any] = []

        # Инициализируем базовую LangChain модель
        self._base_chat_model = ChatOpenAI(
            model=model,
            api_key=api_key,
            max_tokens=max_tokens,
            temperature=temperature,
            reasoning_effort="minimal" if self._is_gpt5() else None,
            max_retries=3,
        )

        self.chat_model = create_agent(model=self._base_chat_model, tools=self._tools, response_format=ProviderStrategy(MainResponseModel))

        # Получаем лимиты для модели
        self.model_limits = self._get_model_limits()

        # Для диагностики пустых ответов
        self.last_completion_tokens = 0

        logger.info(
            f"""LangChain OpenAI клиент инициализирован с моделью {model}
            (GPT-5: {self._is_gpt5()}, лимит: {self.model_limits
            ['total_context']} токенов)"""
        )

        # Логируем информацию об инструментах
        self._log_tools()

    @property
    def is_gpt5(self) -> bool:
        """Определяет, является ли модель GPT-5"""
        return self._is_gpt5()

    def _is_gpt5(self) -> bool:
        """Определяет, является ли модель GPT-5"""
        return "gpt-5" in self.model.lower()

    def _get_model_limits(self) -> Dict[str, int]:
        """Возвращает лимиты для конкретной модели"""
        model_limits = {
            # GPT-3.5
            "gpt-3.5-turbo": 4096,
            "gpt-3.5-turbo-16k": 16385,
            # GPT-4
            "gpt-4": 8192,
            "gpt-4-32k": 32768,
            "gpt-4-turbo": 128000,
            "gpt-4-turbo-preview": 128000,
            "gpt-4o": 128000,
            "gpt-4o-mini": 128000,
            # GPT-5
            "gpt-5-mini": 128000,
            "gpt-5": 200000,
        }

        # Получаем лимит для текущей модели или используем консервативное значение
        total_limit = model_limits.get(self.model, 8192)

        # Резервируем место для ответа и буфера
        completion_reserve = min(self.max_tokens * 2, total_limit // 4)  # Резервируем место для ответа
        buffer_reserve = 500  # Буфер для безопасности

        return {
            "total_context": total_limit,
            "max_input_tokens": total_limit - completion_reserve - buffer_reserve,
            "completion_reserve": completion_reserve,
        }

    def _convert_messages_to_langchain(self, messages: List[Dict[str, str]]) -> List[Any]:
        """Конвертирует сообщения из формата dict в LangChain messages"""
        langchain_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                langchain_messages.append(SystemMessage(content=content))
            elif role == "user":
                langchain_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                langchain_messages.append(AIMessage(content=content))
            else:
                # По умолчанию считаем user
                langchain_messages.append(HumanMessage(content=content))

        return langchain_messages

    def _convert_langchain_to_dict(self, message: AIMessage) -> Dict[str, Any]:
        """Конвертирует LangChain сообщение обратно в dict для логирования"""
        return {
            "content": message.content if hasattr(message, "content") else str(message),
            "role": "assistant",
        }

    def _log_tools(self):
        """Логирует информацию о всех подключенных инструментах"""
        if not self._tools:
            logger.info("📋 Подключенные инструменты ChatOpenAI: нет инструментов")
            return

        logger.info(f"📋 Подключенные инструменты ChatOpenAI ({len(self._tools)} шт.):")
        for i, tool in enumerate(self._tools, 1):
            tool_name = getattr(tool, "name", "Unknown")
            tool_description = getattr(tool, "description", "Нет описания")
            tool_type = type(tool).__name__

            # Обрезаем описание если слишком длинное
            if len(tool_description) > 100:
                tool_description = tool_description[:97] + "..."

            logger.info(f"   {i}. {tool_name} ({tool_type})")
            logger.info(f"      Описание: {tool_description}")

    def _update_agent(self):
        """Обновляет агента с текущим списком инструментов"""
        self.chat_model = create_agent(model=self._base_chat_model, tools=self._tools)
        logger.info(f"🔄 Агент обновлен с {len(self._tools)} инструментами")

    def add_tool(self, tool: Any, update_agent: bool = True, log_after: bool = True):
        """
        Добавляет инструмент для ChatOpenAI

        Args:
            tool: Инструмент LangChain (например, StructuredTool, FunctionTool и т.д.)
            update_agent: Обновлять ли агента после добавления (по умолчанию True)
            log_after: Логировать ли список инструментов после добавления (по умолчанию True)
        """
        if tool not in self._tools:
            self._tools.append(tool)
            tool_name = getattr(tool, "name", str(tool))
            tool_description = getattr(tool, "description", "Нет описания")
            tool_type = type(tool).__name__

            logger.info(f"✅ Инструмент '{tool_name}' ({tool_type}) добавлен в ChatOpenAI")
            if tool_description and tool_description != "Нет описания":
                # Обрезаем описание если слишком длинное
                desc = tool_description[:100] + "..." if len(tool_description) > 100 else tool_description
                logger.info(f"   Описание: {desc}")

            # Обновляем агента с новым списком инструментов только если нужно
            if update_agent:
                self._update_agent()

            # Логируем обновленный список инструментов только если нужно
            if log_after:
                self._log_tools()
        else:
            tool_name = getattr(tool, "name", str(tool))
            logger.warning(f"⚠️ Инструмент '{tool_name}' уже зарегистрирован")

    def add_tools(self, *tools: Any):
        """
        Добавляет несколько инструментов для ChatOpenAI

        Args:
            *tools: Произвольное количество инструментов LangChain или список(ы) инструментов

        Examples:
            # Отдельные инструменты
            client.add_tools(tool1, tool2, tool3)

            # Список инструментов
            client.add_tools([tool1, tool2, tool3])

            # Комбинация
            client.add_tools([tool1, tool2], tool3)
        """
        if not tools:
            logger.warning("⚠️ add_tools вызван без аргументов")
            return

        # Распаковываем списки инструментов
        unpacked_tools = []
        for tool in tools:
            if isinstance(tool, (list, tuple)):
                # Если это список или кортеж, добавляем все элементы
                unpacked_tools.extend(tool)
            else:
                # Если это отдельный инструмент, добавляем его
                unpacked_tools.append(tool)

        if not unpacked_tools:
            logger.warning("⚠️ Не найдено инструментов для добавления")
            return

        logger.info(f"🔧 Добавление {len(unpacked_tools)} инструментов в ChatOpenAI...")
        # Добавляем инструменты без обновления агента и логирования после каждого
        for tool in unpacked_tools:
            self.add_tool(tool, update_agent=False, log_after=False)

        # Обновляем агента один раз после добавления всех инструментов
        self._update_agent()

        # Логируем финальный список инструментов один раз
        logger.info(f"✅ Все инструменты добавлены. Всего подключено: {len(self._tools)}")
        self._log_tools()

    def get_tools(self) -> List[Any]:
        """Возвращает список зарегистрированных инструментов"""
        return self._tools.copy()

    def get_tools_description_for_prompt(self) -> str:
        """
        Возвращает описание всех инструментов в формате для добавления в промпт

        Returns:
            Текст с описанием всех доступных инструментов
        """
        if not self._tools:
            return ""

        descriptions = []
        descriptions.append("\n### ДОСТУПНЫЕ ИНСТРУМЕНТЫ ###\n")
        descriptions.append("У тебя есть доступ к следующим инструментам. Используй их когда это необходимо:\n")

        for i, tool in enumerate(self._tools, 1):
            tool_name = getattr(tool, "name", "Unknown")
            tool_description = getattr(tool, "description", "Нет описания")

            # Получаем параметры инструмента, если доступны
            tool_args = ""
            if hasattr(tool, "args_schema"):
                try:
                    args_schema = tool.args_schema
                    if hasattr(args_schema, "schema"):
                        schema = args_schema.schema()
                        properties = schema.get("properties", {})
                        if properties:
                            args_list = []
                            for param_name, param_info in properties.items():
                                param_desc = param_info.get("description", "")
                                param_type = param_info.get("type", "string")
                                args_list.append(f"  - {param_name} ({param_type}): {param_desc}")
                            if args_list:
                                tool_args = "\n" + "\n".join(args_list)
                except Exception as e:
                    logger.debug(f"Не удалось получить схему аргументов для {tool_name}: {e}")

            descriptions.append(f"{i}. **{tool_name}**")
            descriptions.append(f"   Описание: {tool_description}")
            if tool_args:
                descriptions.append(f"   Параметры:{tool_args}")
            descriptions.append("")

        descriptions.append("ВАЖНО: Используй инструменты когда это необходимо для ответа на вопрос пользователя.")
        descriptions.append("Например, если пользователь спрашивает о погоде - используй соответствующий инструмент.\n")

        return "\n".join(descriptions)

    async def get_completion(self, messages: List) -> Dict[str, Any]:
        ai_response = await self.chat_model.ainvoke({"messages": messages})
        try:
            json_response = MainResponseModel.model_validate_json(ai_response["messages"][-1].content)
            logger.debug(f"json_response: {json_response}")
            return json_response
        except ValidationError as e:
            logger.error(f"❌ Ошибка парсинга JSON: {e}")
            logger.debug(f"ai_response: {ai_response['messages'][-1].content}")
            return MainResponseModel(user_message="", service_info={})

    async def _prepare_messages(self, messages: List) -> List:
        """
        Подготавливает сообщения для отправки в API
        Обрезает контекст если он слишком большой
        """

        # Более точная оценка токенов для русского текста
        def estimate_message_tokens(msg):
            content = msg.content if hasattr(msg, "content") else str(msg)
            # Для русского текста: примерно 2.5-3 символа на токен
            return len(content) // 2.5

        total_estimated_tokens = sum(estimate_message_tokens(msg) for msg in messages)
        max_input_tokens = self.model_limits["max_input_tokens"]

        if total_estimated_tokens <= max_input_tokens:
            return messages

        logger.info(f"Контекст слишком большой ({int(total_estimated_tokens)} токенов), обрезаем до {max_input_tokens}")

        # Сохраняем системные сообщения
        system_messages = [msg for msg in messages if isinstance(msg, SystemMessage)]
        other_messages = [msg for msg in messages if not isinstance(msg, SystemMessage)]

        # Рассчитываем токены системных сообщений
        system_tokens = sum(estimate_message_tokens(msg.content) for msg in system_messages)
        available_tokens = max_input_tokens - system_tokens

        if available_tokens <= 0:
            logger.warning("Системные сообщения занимают весь доступный контекст")
            return system_messages

        # Берем последние сообщения, помещающиеся в доступные токены
        current_tokens = 0
        trimmed_messages = []

        for msg in reversed(other_messages):
            msg_tokens = estimate_message_tokens(msg)
            if current_tokens + msg_tokens > available_tokens:
                break
            trimmed_messages.insert(0, msg)
            current_tokens += msg_tokens

        result_messages = system_messages + trimmed_messages
        logger.info(f"Контекст обрезан до {len(result_messages)} сообщений (~{int(current_tokens + system_tokens)} токенов)")

        return result_messages

    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Анализирует настроение и намерения сообщения

        Args:
            text: Текст для анализа

        Returns:
            Словарь с результатами анализа
        """
        analysis_prompt = f"""
        Проанализируй следующее сообщение пользователя и определи:
        1. Настроение (позитивное/нейтральное/негативное)
        2. Уровень заинтересованности (1-10)
        3. Готовность к покупке (1-10)
        4. Основные возражения или вопросы
        5. Рекомендуемая стратегия ответа
        
        Сообщение: "{text}"
        
        Ответь в формате JSON:
        {{
            "sentiment": "positive/neutral/negative",
            "interest_level": 1-10,
            "purchase_readiness": 1-10,
            "objections": ["список возражений"],
            "key_questions": ["ключевые вопросы"],
            "response_strategy": "рекомендуемая стратегия"
        }}
        """

        try:
            # Для анализа настроения используем более низкую температуру если поддерживается
            temp = 0.3 if not self.is_gpt5 else None

            model = ChatOpenAI(
                model=self.model,
                api_key=self.api_key,
                max_tokens=self.max_tokens,
                temperature=temp,
                reasoning_effort="minimal" if self._is_gpt5() else None,
                max_retries=3,
            ).with_structured_output(AnalyzeSentimentResponseModel)

            response = await model.ainvoke(
                [
                    SystemMessage(content="Ты эксперт по анализу намерений клиентов в продажах."),
                    HumanMessage(content=analysis_prompt),
                ]
            )

            return json.loads(response)

        except Exception as e:
            logger.error(f"Ошибка при анализе настроения: {e}")
            # Возвращаем дефолтные значения
            return {
                "sentiment": "neutral",
                "interest_level": 5,
                "purchase_readiness": 5,
                "objections": [],
                "key_questions": [],
                "response_strategy": "continue_conversation",
            }

    async def generate_follow_up(self, conversation_history: List, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Генерирует персонализированное продолжение разговора

        Args:
            conversation_history: История разговора
            analysis: Результат анализа последнего сообщения

        Returns:
            Персонализированный ответ
        """
        strategy_prompt = f"""
        На основе анализа сообщения клиента:
        - Настроение: {analysis['sentiment']}
        - Уровень заинтересованности: {analysis['interest_level']}/10
        - Готовность к покупке: {analysis['purchase_readiness']}/10
        - Возражения: {analysis['objections']}
        - Стратегия: {analysis['response_strategy']}
        
        Сгенерируй персонализированный ответ, который:
        1. Учитывает текущее настроение клиента
        2. Отвечает на его ключевые вопросы и возражения
        3. Мягко направляет к следующему этапу воронки продаж
        4. Сохраняет доверительный тон общения
        """

        temp = 0.8 if not self.is_gpt5 else None

        model = ChatOpenAI(
            model=self.model,
            api_key=self.api_key,
            max_tokens=self.max_tokens,
            temperature=temp,
            reasoning_effort="minimal" if self._is_gpt5() else None,
            max_retries=3,
        ).with_structured_output(GenerateFollowUpResponseModel)

        response = await model.ainvoke(conversation_history + [SystemMessage(strategy_prompt)])
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"❌ Ошибка парсинга JSON: {e}")
            return {}

    async def check_api_health(self) -> bool:
        """Проверяет доступность OpenAI API"""
        try:
            test_messages = [HumanMessage(content="Привет")]

            model = (
                ChatOpenAI(
                    model=self.model, api_key=self.api_key, max_tokens=10, reasoning_effort="minimal" if self._is_gpt5() else None, max_retries=3
                )
                | StrOutputParser()
            )

            await model.ainvoke(test_messages)
            return True
        except Exception as e:
            logger.error(f"OpenAI API недоступен: {e}")
            return False

    def estimate_tokens(self, text: str) -> int:
        """Более точная оценка количества токенов в тексте"""
        # Для русского текста: примерно 2.5-3 символа на токен
        return int(len(text) / 2.5)

    async def get_available_models(self) -> List[str]:
        """Получает список доступных моделей"""
        # LangChain не предоставляет прямой доступ к списку моделей
        # Возвращаем стандартный список моделей OpenAI
        return [
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k",
            "gpt-4",
            "gpt-4-32k",
            "gpt-4-turbo",
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-5-mini",
            "gpt-5",
        ]

    async def transcribe_audio(self, audio_file_path: str) -> str:
        """
        Распознает голосовое сообщение через Whisper API

        Args:
            audio_file_path: Путь к аудио файлу

        Returns:
            Распознанный текст
        """
        try:
            logger.info(f"🎤 Отправка аудио на распознавание: {audio_file_path}")

            with open(audio_file_path, "rb") as audio_file:
                transcript = await self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="ru",  # Русский язык
                )

            text = transcript.text
            logger.info(f"✅ Распознано {len(text)} символов: '{text[:100]}...'")
            return text

        except Exception as e:
            logger.error(f"❌ Ошибка распознавания аудио: {e}")
            return ""
