"""
Модуль для работы со статической памятью бота из текстовых файлов.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

from project_root_finder import root

logger = logging.getLogger(__name__)


def _get_bot_id_from_globals() -> Optional[str]:
    """
    Пытается получить bot_id из глобальных переменных.
    Сначала пробует supabase_client, затем config.

    Returns:
        bot_id если найден, None в противном случае
    """
    try:
        from ..utils.context import ctx

        # Пробуем получить из supabase_client
        if ctx.supabase_client and hasattr(ctx.supabase_client, "bot_id") and ctx.supabase_client.bot_id:
            logger.debug(f"[StaticMemoryManager] bot_id получен из supabase_client: {ctx.supabase_client.bot_id}")
            return ctx.supabase_client.bot_id

        # Пробуем получить из config
        if ctx.config and hasattr(ctx.config, "BOT_ID") and ctx.config.BOT_ID:
            logger.debug(f"[StaticMemoryManager] bot_id получен из config: {ctx.config.BOT_ID}")
            return ctx.config.BOT_ID

        logger.warning("[StaticMemoryManager] bot_id не найден в глобальных переменных")
        return None
    except Exception as e:
        logger.debug(f"[StaticMemoryManager] Ошибка при получении bot_id из глобальных переменных: {e}")
        return None


class StaticMemoryManager:
    """
    Класс для работы со статической памятью бота из текстовых файлов.

    Автоматически ищет папку 'memory' в конфигурации бота (bots/{bot_id}/memory)
    и предоставляет удобный интерфейс для чтения текстовых файлов.

    Пример использования:
        # С автоматическим определением bot_id из глобальных переменных
        memory = StaticMemoryManager()  # bot_id будет взят из supabase_client или config

        # Или с явным указанием bot_id
        memory = StaticMemoryManager("mdclinica")

        # Чтение файлов
        actions_info = memory.get("actions")  # Читает файл actions.txt
        promotions = memory.get("promotions")  # Читает файл promotions.txt
        all_files = memory.list_all()  # Список всех доступных файлов
    """

    def __init__(self, bot_id: Optional[str] = None):
        """
        Инициализация менеджера статической памяти.

        Args:
            bot_id: Идентификатор бота. Если не указан, будет попытка получить из глобальных переменных
                   (supabase_client или config через ctx)

        Raises:
            ValueError: Если bot_id не указан и не найден в глобальных переменных
        """
        # Если bot_id не указан, пытаемся получить из глобальных переменных
        if bot_id is None:
            bot_id = _get_bot_id_from_globals()
            if bot_id is None:
                raise ValueError(
                    "bot_id не указан и не найден в глобальных переменных. "
                    "Укажите bot_id явно или убедитесь, что supabase_client или config инициализированы."
                )

        self.bot_id = bot_id
        self.memory_dir = root / "bots" / bot_id / "memory"
        self._cache: Dict[str, str] = {}

        if not self.memory_dir.exists():
            logger.warning(f"[StaticMemoryManager] Папка memory не найдена для бота {bot_id}: {self.memory_dir}")
            logger.info(f"[StaticMemoryManager] Создайте папку {self.memory_dir} для использования статической памяти")
        else:
            logger.info(f"[StaticMemoryManager] Инициализирован для бота {bot_id}, папка: {self.memory_dir}")

    def get(self, name: str, use_cache: bool = True) -> Optional[str]:
        """
        Читает содержимое текстового файла по имени.

        Args:
            name: Имя файла без расширения (например, "actions" для файла actions.txt)
            use_cache: Использовать ли кэш для повторных запросов (по умолчанию True)

        Returns:
            Содержимое файла как строка, или None если файл не найден

        Examples:
            >>> memory = StaticMemoryManager()  # или StaticMemoryManager("mdclinica")
            >>> actions = memory.get("actions")  # Читает bots/{bot_id}/memory/actions.txt
        """
        # Проверяем кэш
        if use_cache and name in self._cache:
            logger.debug(f"[StaticMemoryManager] Возвращаем из кэша: {name}")
            return self._cache[name]

        # Проверяем существование папки
        if not self.memory_dir.exists():
            logger.warning(f"[StaticMemoryManager] Папка memory не существует: {self.memory_dir}")
            return None

        # Формируем путь к файлу
        file_path = self.memory_dir / f"{name}.txt"

        if not file_path.exists():
            logger.warning(f"[StaticMemoryManager] Файл не найден: {file_path}")
            return None

        try:
            content = file_path.read_text(encoding="utf-8")
            logger.debug(f"[StaticMemoryManager] Прочитан файл {name}: {len(content)} символов")

            # Сохраняем в кэш
            if use_cache:
                self._cache[name] = content

            return content
        except Exception as e:
            logger.error(f"[StaticMemoryManager] Ошибка при чтении файла {file_path}: {e}")
            return None

    def list_all(self) -> List[str]:
        """
        Возвращает список всех доступных файлов памяти (без расширения .txt).

        Returns:
            Список имен файлов без расширения

        Examples:
            >>> memory = StaticMemoryManager()  # или StaticMemoryManager("mdclinica")
            >>> files = memory.list_all()  # ["actions", "promotions", "faq"]
        """
        if not self.memory_dir.exists():
            logger.warning(f"[StaticMemoryManager] Папка memory не существует: {self.memory_dir}")
            return []

        files = []
        for file_path in self.memory_dir.glob("*.txt"):
            files.append(file_path.stem)

        logger.debug(f"[StaticMemoryManager] Найдено файлов: {len(files)}")
        return sorted(files)

    def exists(self, name: str) -> bool:
        """
        Проверяет, существует ли файл с указанным именем.

        Args:
            name: Имя файла без расширения

        Returns:
            True если файл существует, False в противном случае
        """
        if not self.memory_dir.exists():
            return False

        file_path = self.memory_dir / f"{name}.txt"
        return file_path.exists()

    def clear_cache(self):
        """
        Очищает кэш загруженных файлов.
        Полезно, если файлы были изменены и нужно перезагрузить их.
        """
        self._cache.clear()
        logger.debug("[StaticMemoryManager] Кэш очищен")

    def reload(self, name: str) -> Optional[str]:
        """
        Принудительно перезагружает файл из диска, игнорируя кэш.

        Args:
            name: Имя файла без расширения

        Returns:
            Содержимое файла как строка, или None если файл не найден
        """
        # Удаляем из кэша если есть
        if name in self._cache:
            del self._cache[name]

        # Читаем заново
        return self.get(name, use_cache=True)

    def get_memory_dir(self) -> Path:
        """
        Возвращает путь к папке memory.

        Returns:
            Path объект с путем к папке memory
        """
        return self.memory_dir
