# Обновленный prompt_loader.py с поддержкой финальных инструкций

import logging
import os
import tempfile
from pathlib import Path
from typing import Dict, Optional

import aiofiles

logger = logging.getLogger(__name__)


class PromptLoader:
    """Класс для загрузки промптов из локального каталога"""

    def __init__(self, prompts_dir: str):
        self.prompts_dir = Path(prompts_dir)
        self.welcome_file = self.prompts_dir / "welcome_message.txt"
        self.help_file = self.prompts_dir / "help_message.txt"
        self.final_instructions_file = self.prompts_dir / "final_instructions.txt"

        # Информация об инструментах для добавления в финальные инструкции
        self._tools_description: str = ""

        # Временный файл системного промпта
        self._temp_system_prompt_file: Optional[str] = None
        self._cached_system_prompt: Optional[str] = None

        # Автоматически находим все .txt файлы промптов (кроме специальных)
        all_txt_files = list(self.prompts_dir.glob("*.txt"))
        special_files = {
            "welcome_message.txt",
            "help_message.txt",
            "final_instructions.txt",
        }
        self.prompt_files = [f.name for f in all_txt_files if f.name not in special_files]

        logger.debug(f"Инициализирован загрузчик промптов: {self.prompts_dir}")
        logger.debug(f"Найдено файлов промптов: {len(self.prompt_files)}")
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Файлы промптов: {self.prompt_files}")

    async def load_system_prompt(self) -> str:
        """
        Загружает системный промпт из временного файла или создает его

        Returns:
            Системный промпт
        """
        try:
            # Если есть кешированный промпт, возвращаем его
            if self._cached_system_prompt:
                logger.debug(f"Возвращаем кешированный системный промпт ({len(self._cached_system_prompt)} символов)")
                return self._cached_system_prompt

            # Если есть временный файл, загружаем из него
            if self._temp_system_prompt_file and os.path.exists(self._temp_system_prompt_file):
                logger.debug(f"Загружаем системный промпт из временного файла: {self._temp_system_prompt_file}")
                async with aiofiles.open(self._temp_system_prompt_file, "r", encoding="utf-8") as f:
                    self._cached_system_prompt = await f.read()
                return self._cached_system_prompt

            # Создаем системный промпт и временный файл
            logger.info("Создаем новый системный промпт из файлов")
            system_prompt = await self._build_system_prompt()
            await self._create_temp_system_prompt_file(system_prompt)

            self._cached_system_prompt = system_prompt
            logger.info(f"✅ Системный промпт создан и сохранен во временный файл ({len(system_prompt)} символов)")
            return system_prompt

        except Exception as e:
            logger.error(f"Ошибка при загрузке системного промпта: {e}")
            raise

    async def _build_system_prompt(self) -> str:
        """
        Строит системный промпт из файлов с цифрами в названии + JSON инструкции

        Returns:
            Объединенный системный промпт
        """
        try:
            prompt_parts = []

            # Сортируем файлы по цифре в начале названия
            numbered_files = []
            other_files = []

            for filename in self.prompt_files:
                if filename[0].isdigit():
                    numbered_files.append(filename)
                else:
                    other_files.append(filename)

            # Сортируем файлы с цифрами по номеру
            numbered_files.sort(key=lambda x: int(x[0]))

            # Объединяем списки: сначала файлы с цифрами, потом остальные
            all_files = numbered_files + sorted(other_files)

            logger.debug(f"Порядок загрузки файлов: {all_files}")

            # Распараллеливаем загрузку файлов для ускорения
            import asyncio

            async def load_file_with_metadata(filename: str) -> tuple[str, Optional[str]]:
                """Загружает файл и возвращает (filename, content)"""
                logger.debug(f"Загружаем промпт из {filename}")
                content = await self._load_file(filename)
                return (filename, content)

            # Загружаем все файлы параллельно
            load_tasks = [load_file_with_metadata(filename) for filename in all_files]
            loaded_files = await asyncio.gather(*load_tasks, return_exceptions=True)

            # Обрабатываем результаты в правильном порядке
            for result in loaded_files:
                if isinstance(result, Exception):
                    logger.error(f"Ошибка загрузки файла: {result}")
                    continue

                filename, content = result
                if content:
                    # Добавляем заголовок секции
                    section_name = self._get_section_name(filename)
                    prompt_parts.append(f"\n### {section_name} ###\n")
                    prompt_parts.append(content.strip())
                    prompt_parts.append("\n")
                else:
                    logger.warning(f"Файл {filename} пуст")

            if not prompt_parts:
                error_msg = "Не удалось загрузить ни одного промпт файла"
                logger.error(error_msg)
                raise ValueError(error_msg)

            # Добавляем инструкции по JSON метаданным
            json_instructions = self._get_json_instructions()
            prompt_parts.append("\n")
            prompt_parts.append(json_instructions)

            # Объединяем все части
            full_prompt = "".join(prompt_parts).strip()

            logger.debug(f"Системный промпт построен успешно ({len(full_prompt)} символов)")
            return full_prompt

        except Exception as e:
            logger.error(f"Ошибка при построении системного промпта: {e}")
            raise

    async def _create_temp_system_prompt_file(self, system_prompt: str):
        """
        Создает временный файл с системным промптом

        Args:
            system_prompt: Содержимое системного промпта
        """
        try:
            # Создаем временный файл
            fd, temp_path = tempfile.mkstemp(suffix=".txt", prefix="system_prompt_")

            # Записываем содержимое
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(system_prompt)

            self._temp_system_prompt_file = temp_path
            logger.info(f"📄 Создан временный файл системного промпта: {temp_path}")

        except Exception as e:
            logger.error(f"Ошибка создания временного файла системного промпта: {e}")
            raise

    def cleanup_temp_files(self):
        """
        Удаляет временные файлы системного промпта
        """
        if self._temp_system_prompt_file and os.path.exists(self._temp_system_prompt_file):
            try:
                os.remove(self._temp_system_prompt_file)
                self._temp_system_prompt_file = None
                self._cached_system_prompt = None
            except Exception as e:
                logger.error(f"❌ Ошибка удаления временного файла: {e}")

    async def reload_system_prompt(self) -> str:
        """
        Перезагружает системный промпт (пересоздает временный файл)

        Returns:
            Новый системный промпт
        """
        logger.info("🔄 Перезагрузка системного промпта...")

        # Удаляем старый временный файл
        self.cleanup_temp_files()

        # Создаем новый
        system_prompt = await self._build_system_prompt()
        await self._create_temp_system_prompt_file(system_prompt)

        self._cached_system_prompt = system_prompt
        logger.info(f"✅ Системный промпт перезагружен ({len(system_prompt)} символов)")
        return system_prompt

    def set_tools_description(self, tools_description: str):
        """
        Устанавливает описание инструментов для добавления в финальные инструкции

        Args:
            tools_description: Текст с описанием инструментов
        """
        self._tools_description = tools_description
        logger.debug(f"Описание инструментов обновлено ({len(tools_description)} символов)")

        # Логируем содержимое описания инструментов
        if tools_description and logger.isEnabledFor(logging.DEBUG):
            # Подсчитываем количество инструментов по паттерну "1. **название**"
            import re

            tool_pattern = r"\d+\.\s+\*\*[^*]+\*\*"
            tool_matches = re.findall(tool_pattern, tools_description)
            tool_count = len(tool_matches)
            logger.debug(f"Описание инструментов для промпта содержит {tool_count} инструмент(ов)")

            # Логируем первые строки для проверки
            lines = tools_description.split("\n")
            non_empty_lines = [line for line in lines if line.strip()]
            preview_lines = non_empty_lines[:10]  # Первые 10 непустых строк

            logger.info("📋 Превью описания инструментов (первые строки):")
            for line in preview_lines:
                logger.info(f"   {line}")

            if len(non_empty_lines) > 10:
                logger.info(f"   ... (еще {len(non_empty_lines) - 10} строк)")

            # Полное содержимое в debug режиме
            logger.debug(f"📋 Полное содержимое описания инструментов:\n{tools_description}")

    async def load_final_instructions(self) -> str:
        """
        Загружает финальные инструкции из final_instructions.txt
        Автоматически добавляет информацию об инструментах если она установлена

        Returns:
            Финальные инструкции или пустая строка если файла нет
        """
        try:
            logger.debug(f"Загружаем финальные инструкции из {self.final_instructions_file.name}")

            content = ""

            if self.final_instructions_file.exists():
                async with aiofiles.open(self.final_instructions_file, "r", encoding="utf-8") as f:
                    content = await f.read()

            if not content.strip():
                if not self.final_instructions_file.exists():
                    logger.debug(f"Файл {self.final_instructions_file.name} не найден - пропускаем")
                else:
                    logger.debug(f"Файл {self.final_instructions_file.name} пуст - пропускаем")

                # Если есть описание инструментов, возвращаем только его
                if self._tools_description:
                    logger.info(f"Финальные инструкции: только описание инструментов ({len(self._tools_description)} символов)")
                    logger.debug(f"Содержимое описания инструментов (первые 500 символов):\n{self._tools_description[:500]}...")
                    return self._tools_description.strip()

                return ""

            # Добавляем описание инструментов в конец финальных инструкций
            if self._tools_description:
                # Проверяем, не добавлено ли уже описание инструментов
                if "### ДОСТУПНЫЕ ИНСТРУМЕНТЫ ###" not in content:
                    original_length = len(content)
                    content = content.strip() + "\n\n" + self._tools_description
                    added_length = len(content) - original_length
                    logger.info("✅ Описание инструментов добавлено в финальные инструкции")
                    logger.info(f"   Размер исходных инструкций: {original_length} символов")
                    logger.info(f"   Добавлено символов: {added_length}")
                    logger.info(f"   Итоговый размер: {len(content)} символов")
                    logger.debug(f"   Добавленный текст (первые 500 символов):\n{self._tools_description[:500]}...")
                else:
                    logger.debug("Описание инструментов уже присутствует в финальных инструкциях")

            logger.info(f"Финальные инструкции загружены ({len(content)} символов)")
            return content.strip()

        except Exception as e:
            logger.error(f"Ошибка при загрузке финальных инструкций: {e}")
            # Не прерываем работу - финальные инструкции опциональны
            # Но возвращаем описание инструментов если оно есть
            if self._tools_description:
                return self._tools_description.strip()
            return ""

    def _get_json_instructions(self) -> str:
        """Возвращает инструкции по JSON метаданным для ИИ"""
        return """
⚠️ КРИТИЧЕСКИ ВАЖНО: ЛЮБОЙ твой ответ ДОЛЖЕН быть в формате JSON с двумя полями:

{
  "user_message": "Текст сообщения, который увидит пользователь",
  "service_info": {
    "этап": "СТРОГО_ОДИН_ИЗ_СПИСКА",
    "качество": 1-10,
    "события": [
      {
        "тип": "тип события",
        "инфо": "детали события"
      }
    ]
  }
}

Где:
- `user_message` - сообщение для пользователя (текст, который увидит пользователь в Telegram)
- `service_info` - служебная информация (JSON-структура для системы аналитики и администрирования)

НЕ отправляй просто текст! ВСЕГДА используй этот формат JSON для КАЖДОГО ответа.

В `service_info` ОБЯЗАТЕЛЬНО добавляй структуру:

{
  "этап": "introduction|consult|offer|contacts",
  "качество": 1-10,
  "события": [
    {
      "тип": "телефон|консультация|покупка|отказ",
      "инфо": "детали события"
    }
  ]
}


СИСТЕМА ОЦЕНКИ КАЧЕСТВА (1-10):
1-3: низкий интерес, много возражений, скептически настроен
4-6: средний интерес, есть вопросы, обдумывает
7-8: высокий интерес, готов к покупке, активно интересуется
9-10: горячий лид, предоставил контакты или готов к действию


ВАЖНО - ПРАВИЛО ДОБАВЛЕНИЯ СОБЫТИЙ:
- Добавляй события в массив "события" ТОЛЬКО на основе ПОСЛЕДНИХ сообщений в диалоге
- НЕ анализируй всю историю диалога для определения событий
- События должны отражать то, что произошло в ТЕКУЩЕМ или ПРЕДЫДУЩЕМ сообщении пользователя
- Если событие произошло давно в истории - НЕ добавляй его в текущий ответ
- НЕ повторяй события, которые уже были в предыдущей служебной информации (service_info)
- Примеры правильных событий:
  * Пользователь только что предоставил телефон - добавляй событие "телефон"
  * Пользователь только что запросил консультацию - добавляй событие "консультация"
  * Пользователь только что согласился на покупку - добавляй событие "покупка"
- Если в последних сообщениях ничего значимого не произошло - отправляй пустой массив []

ПРИМЕРЫ ПРАВИЛЬНОГО ИСПОЛЬЗОВАНИЯ (полный формат ответа):

Пример 1 - обычный диалог (без ссылки):
{
  "user_message": "Расскажу подробнее о конференции GrowthMED. Она пройдет 24-25 октября...",
  "service_info": {
    "этап": "consult",
    "качество": 6,
    "события": []
  }
}

Пример 2 - получен телефон (без ссылки):
{
  "user_message": "Отлично! Записал ваш номер. Мы перезвоним в течение 10 минут!",
  "service_info": {
    "этап": "contacts",
    "качество": 9,
    "события": [
      {
        "тип": "телефон",
        "инфо": "Иван Петров +79219603144"
      }
    ]
  }
}

Пример 3 - отправка презентации (без ссылки):
{
  "user_message": "Отправляю вам презентацию о нашей компании и прайс-лист с актуальными ценами.",
  "service_info": {
    "этап": "offer",
    "качество": 7,
    "события": [
      {
        "тип": "консультация",
        "инфо": "Запросил материалы"
      }
    ]
  }
}


ТРЕБОВАНИЯ К ФОРМАТУ ОТВЕТА:
- ВСЕГДА используй формат JSON с полями `user_message` и `service_info`
- НЕ отправляй просто текст без JSON структуры
- JSON должен быть валидным
- Всегда используй кавычки для строк
- Массив "события" может быть пустым []
- Если событий нет - не добавляй их в массив
- Качество должно быть числом от 1 до 10

ПОМНИ: 
- Это НЕ опциональный формат - это ОБЯЗАТЕЛЬНЫЙ формат для КАЖДОГО ответа!
- Система ожидает JSON с полями `user_message` и `service_info`
- Без этого формата система не сможет правильно обработать твой ответ
- Этот формат критически важен для работы системы администрирования и аналитики!
"""

    async def load_welcome_message(self) -> str:
        """
        Загружает приветственное сообщение из welcome_message.txt

        Returns:
            Текст приветственного сообщения
        """
        try:
            logger.debug(f"Загружаем приветственное сообщение из {self.welcome_file.name}")

            if not self.welcome_file.exists():
                error_msg = f"Файл приветствия не найден: {self.welcome_file}"
                logger.error(error_msg)
                raise FileNotFoundError(error_msg)

            async with aiofiles.open(self.welcome_file, "r", encoding="utf-8") as f:
                content = await f.read()

            if not content.strip():
                error_msg = f"Файл приветствия пуст: {self.welcome_file}"
                logger.error(error_msg)
                raise ValueError(error_msg)

            logger.info(f"Приветственное сообщение загружено ({len(content)} символов)")
            return content.strip()

        except Exception as e:
            logger.error(f"Ошибка при загрузке приветственного сообщения: {e}")
            raise

    async def load_help_message(self) -> str:
        """
        Загружает справочное сообщение из help_message.txt

        Returns:
            Текст справочного сообщения
        """
        try:
            logger.debug(f"Загружаем справочное сообщение из {self.help_file.name}")

            if self.help_file.exists():
                async with aiofiles.open(self.help_file, "r", encoding="utf-8") as f:
                    content = await f.read()

                if content.strip():
                    logger.info(f"Справочное сообщение загружено ({len(content)} символов)")
                    return content.strip()

            # Fallback если файл не найден или пуст
            logger.warning("Файл help_message.txt не найден или пуст, используем дефолтную справку")
            return "🤖 **Ваш помощник готов к работе!**\n\n**Команды:**\n/start - Начать диалог\n/help - Показать справку\n/status - Проверить статус"

        except Exception as e:
            logger.error(f"Ошибка при загрузке справочного сообщения: {e}")
            # Возвращаем простую справку в случае ошибки
            return "🤖 Ваш помощник готов к работе! Напишите /start для начала диалога."

    async def _load_file(self, filename: str) -> str:
        """Загружает содержимое файла из каталога промптов"""
        file_path = self.prompts_dir / filename

        try:
            if not file_path.exists():
                error_msg = f"Файл промпта не найден: {file_path}"
                logger.error(error_msg)
                raise FileNotFoundError(error_msg)

            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                content = await f.read()

            if not content.strip():
                logger.warning(f"Файл {filename} пуст")
                return ""

            logger.debug(f"Загружен файл {filename} ({len(content)} символов)")
            return content

        except Exception as e:
            logger.error(f"Ошибка чтения файла {file_path}: {e}")
            raise

    def _get_section_name(self, filename: str) -> str:
        """Получает название секции по имени файла"""
        name_mapping = {
            "system_prompt.txt": "СИСТЕМНЫЙ ПРОМПТ",
            "sales_context.txt": "КОНТЕКСТ ПРОДАЖ",
            "product_info.txt": "ИНФОРМАЦИЯ О ПРОДУКТЕ",
            "objection_handling.txt": "ОБРАБОТКА ВОЗРАЖЕНИЙ",
            "1sales_context.txt": "КОНТЕКСТ ПРОДАЖ",
            "2product_info.txt": "ИНФОРМАЦИЯ О ПРОДУКТЕ",
            "3objection_handling.txt": "ОБРАБОТКА ВОЗРАЖЕНИЙ",
            "final_instructions.txt": "ФИНАЛЬНЫЕ ИНСТРУКЦИИ",  # 🆕
        }

        return name_mapping.get(filename, filename.replace(".txt", "").upper())

    async def reload_prompts(self) -> str:
        """Перезагружает промпты (для обновления без перезапуска бота)"""
        logger.info("Перезагрузка промптов...")
        return await self.reload_system_prompt()

    async def validate_prompts(self) -> Dict[str, bool]:
        """Проверяет доступность всех файлов промптов и приветственного сообщения"""
        results = {}

        # Проверяем файлы промптов
        for filename in self.prompt_files:
            file_path = self.prompts_dir / filename
            try:
                if file_path.exists():
                    async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                        content = await f.read()
                    results[filename] = bool(content.strip() and len(content.strip()) > 10)
                else:
                    results[filename] = False
            except Exception:
                results[filename] = False

        # Проверяем файл приветственного сообщения
        try:
            if self.welcome_file.exists():
                async with aiofiles.open(self.welcome_file, "r", encoding="utf-8") as f:
                    content = await f.read()
                results["welcome_message.txt"] = bool(content.strip() and len(content.strip()) > 5)
            else:
                results["welcome_message.txt"] = False
        except Exception:
            results["welcome_message.txt"] = False

        # Проверяем файл справки (опционально)
        try:
            if self.help_file.exists():
                async with aiofiles.open(self.help_file, "r", encoding="utf-8") as f:
                    content = await f.read()
                results["help_message.txt"] = bool(content.strip() and len(content.strip()) > 5)
            else:
                results["help_message.txt"] = False  # Не критично
        except Exception:
            results["help_message.txt"] = False

        # 🆕 Проверяем финальные инструкции (опционально)
        try:
            if self.final_instructions_file.exists():
                async with aiofiles.open(self.final_instructions_file, "r", encoding="utf-8") as f:
                    content = await f.read()
                results["final_instructions.txt"] = bool(content.strip() and len(content.strip()) > 5)
            else:
                results["final_instructions.txt"] = False  # Не критично - опциональный файл
        except Exception:
            results["final_instructions.txt"] = False

        return results

    def get_prompt_info(self) -> Dict[str, any]:
        """Возвращает информацию о конфигурации промптов"""
        return {
            "prompts_dir": str(self.prompts_dir),
            "prompt_files": self.prompt_files,
            "welcome_file": "welcome_message.txt",
            "help_file": "help_message.txt",
            "final_instructions_file": "final_instructions.txt",  # 🆕
            "total_files": len(self.prompt_files) + 1,  # +1 для welcome message
            "json_instructions_included": True,
        }

    async def test_json_parsing(self, test_response: str) -> Dict[str, any]:
        """Тестирует парсинг JSON из ответа ИИ (для отладки)"""
        import json
        import re

        try:
            # Используем тот же алгоритм что и в main.py
            json_pattern = r'\{[^{}]*"этап"[^{}]*\}$'
            match = re.search(json_pattern, test_response.strip())

            if match:
                json_str = match.group(0)
                response_text = test_response[: match.start()].strip()

                try:
                    metadata = json.loads(json_str)
                    return {
                        "success": True,
                        "response_text": response_text,
                        "metadata": metadata,
                        "json_str": json_str,
                    }
                except json.JSONDecodeError as e:
                    return {
                        "success": False,
                        "error": f"JSON decode error: {e}",
                        "json_str": json_str,
                    }
            else:
                return {
                    "success": False,
                    "error": "JSON pattern not found",
                    "response_text": test_response,
                }

        except Exception as e:
            return {"success": False, "error": f"Parse error: {e}"}
