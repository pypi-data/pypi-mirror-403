"""Тесты для memory.static_memory"""

from pathlib import Path
from unittest.mock import Mock, PropertyMock, patch

import pytest

from smart_bot_factory.memory.static_memory import StaticMemoryManager, _get_bot_id_from_globals


class TestGetBotIdFromGlobals:
    """Тесты для функции _get_bot_id_from_globals"""

    def test_get_bot_id_from_supabase_client(self):
        """Тест получения bot_id из supabase_client (строки 26-28)"""
        with patch("smart_bot_factory.utils.context.ctx") as mock_ctx:
            mock_ctx.supabase_client = Mock()
            mock_ctx.supabase_client.bot_id = "test-bot"
            mock_ctx.config = None

            result = _get_bot_id_from_globals()

            assert result == "test-bot"

    def test_get_bot_id_from_config(self):
        """Тест получения bot_id из config (строки 31-33)"""
        with patch("smart_bot_factory.utils.context.ctx") as mock_ctx:
            mock_ctx.supabase_client = None
            mock_ctx.config = Mock()
            mock_ctx.config.BOT_ID = "config-bot"

            result = _get_bot_id_from_globals()

            assert result == "config-bot"

    def test_get_bot_id_not_found(self):
        """Тест когда bot_id не найден (строки 35-36)"""
        with patch("smart_bot_factory.utils.context.ctx") as mock_ctx:
            mock_ctx.supabase_client = None
            mock_ctx.config = None

            result = _get_bot_id_from_globals()

            assert result is None

    def test_get_bot_id_exception_handling(self):
        """Тест обработки исключения при получении bot_id (строки 37-39)"""
        # Мокируем так, чтобы при доступе к ctx.supabase_client возникало исключение
        with patch("smart_bot_factory.utils.context.ctx") as mock_ctx:
            # При доступе к supabase_client возникает исключение
            type(mock_ctx).supabase_client = PropertyMock(side_effect=Exception("Error"))
            type(mock_ctx).config = PropertyMock(return_value=None)

            result = _get_bot_id_from_globals()

            assert result is None


class TestStaticMemoryManager:
    """Тесты для класса StaticMemoryManager"""

    @pytest.fixture
    def temp_memory_dir(self, tmp_path):
        """Фикстура для временной директории memory"""
        memory_dir = tmp_path / "bots" / "test-bot" / "memory"
        memory_dir.mkdir(parents=True)
        return memory_dir

    def test_init_with_bot_id(self, temp_memory_dir, tmp_path):
        """Тест инициализации с указанным bot_id (строки 62-83)"""
        with patch("smart_bot_factory.memory.static_memory.root", tmp_path):
            memory = StaticMemoryManager(bot_id="test-bot")

            assert memory.bot_id == "test-bot"
            assert memory.memory_dir == temp_memory_dir
            assert isinstance(memory._cache, dict)

    def test_init_without_bot_id_from_supabase(self, temp_memory_dir, tmp_path):
        """Тест инициализации без bot_id, получение из supabase_client (строки 74-80)"""
        with (
            patch("smart_bot_factory.memory.static_memory.root", tmp_path),
            patch("smart_bot_factory.memory.static_memory._get_bot_id_from_globals", return_value="test-bot"),
        ):
            memory = StaticMemoryManager()

            assert memory.bot_id == "test-bot"
            assert memory.memory_dir == temp_memory_dir

    def test_init_without_bot_id_error(self, tmp_path):
        """Тест ошибки инициализации без bot_id (строки 76-80)"""
        with (
            patch("smart_bot_factory.memory.static_memory.root", tmp_path),
            patch("smart_bot_factory.memory.static_memory._get_bot_id_from_globals", return_value=None),
        ):
            with pytest.raises(ValueError) as exc_info:
                StaticMemoryManager()

            assert "bot_id" in str(exc_info.value).lower()

    def test_init_memory_dir_not_exists(self, tmp_path):
        """Тест инициализации когда папка memory не существует (строки 86-90)"""
        with patch("smart_bot_factory.memory.static_memory.root", tmp_path):
            memory = StaticMemoryManager(bot_id="test-bot")

            # Папка не должна существовать
            assert not memory.memory_dir.exists()

    def test_get_file_exists(self, temp_memory_dir, tmp_path):
        """Тест чтения существующего файла (строки 92-135)"""
        test_file = temp_memory_dir / "actions.txt"
        test_file.write_text("Test content", encoding="utf-8")

        with patch("smart_bot_factory.memory.static_memory.root", tmp_path):
            memory = StaticMemoryManager(bot_id="test-bot")

            result = memory.get("actions")

            assert result == "Test content"

    def test_get_file_not_exists(self, temp_memory_dir, tmp_path):
        """Тест чтения несуществующего файла (строки 120-122)"""
        with patch("smart_bot_factory.memory.static_memory.root", tmp_path):
            memory = StaticMemoryManager(bot_id="test-bot")

            result = memory.get("nonexistent")

            assert result is None

    def test_get_file_caching(self, temp_memory_dir, tmp_path):
        """Тест кэширования файлов (строки 108-110, 129-130)"""
        test_file = temp_memory_dir / "actions.txt"
        test_file.write_text("Original content", encoding="utf-8")

        with patch("smart_bot_factory.memory.static_memory.root", tmp_path):
            memory = StaticMemoryManager(bot_id="test-bot")

            # Первое чтение
            result1 = memory.get("actions")
            assert result1 == "Original content"
            assert "actions" in memory._cache

            # Изменяем файл
            test_file.write_text("Modified content", encoding="utf-8")

            # Второе чтение с кэшем - должно вернуть старое значение
            result2 = memory.get("actions", use_cache=True)
            assert result2 == "Original content"  # Из кэша

    def test_get_file_without_cache(self, temp_memory_dir, tmp_path):
        """Тест чтения файла без кэша (строки 108-110)"""
        test_file = temp_memory_dir / "actions.txt"
        test_file.write_text("Original content", encoding="utf-8")

        with patch("smart_bot_factory.memory.static_memory.root", tmp_path):
            memory = StaticMemoryManager(bot_id="test-bot")

            # Первое чтение
            memory.get("actions")

            # Изменяем файл
            test_file.write_text("Modified content", encoding="utf-8")

            # Чтение без кэша - должно вернуть новое значение
            result = memory.get("actions", use_cache=False)
            assert result == "Modified content"

    def test_get_memory_dir_not_exists(self, tmp_path):
        """Тест чтения когда папка memory не существует (строки 113-115)"""
        with patch("smart_bot_factory.memory.static_memory.root", tmp_path):
            memory = StaticMemoryManager(bot_id="test-bot")

            result = memory.get("actions")

            assert result is None

    def test_get_file_read_error(self, temp_memory_dir, tmp_path):
        """Тест обработки ошибки при чтении файла (строки 133-135)"""
        test_file = temp_memory_dir / "actions.txt"
        test_file.write_text("Test", encoding="utf-8")

        with patch("smart_bot_factory.memory.static_memory.root", tmp_path), patch("pathlib.Path.read_text", side_effect=Exception("Read error")):
            memory = StaticMemoryManager(bot_id="test-bot")

            result = memory.get("actions")

            assert result is None

    def test_list_all_files(self, temp_memory_dir, tmp_path):
        """Тест получения списка всех файлов (строки 137-157)"""
        # Создаем несколько файлов
        (temp_memory_dir / "actions.txt").write_text("Actions")
        (temp_memory_dir / "promotions.txt").write_text("Promotions")
        (temp_memory_dir / "faq.txt").write_text("FAQ")
        # Создаем файл не .txt - не должен попасть в список
        (temp_memory_dir / "other.json").write_text("{}")

        with patch("smart_bot_factory.memory.static_memory.root", tmp_path):
            memory = StaticMemoryManager(bot_id="test-bot")

            files = memory.list_all()

            assert len(files) == 3
            assert "actions" in files
            assert "promotions" in files
            assert "faq" in files
            assert "other" not in files  # Не .txt файл
            # Проверяем сортировку
            assert files == sorted(files)

    def test_list_all_empty_dir(self, temp_memory_dir, tmp_path):
        """Тест получения списка из пустой директории (строки 148-150)"""
        with patch("smart_bot_factory.memory.static_memory.root", tmp_path):
            memory = StaticMemoryManager(bot_id="test-bot")

            files = memory.list_all()

            assert files == []

    def test_list_all_dir_not_exists(self, tmp_path):
        """Тест получения списка когда папка не существует (строки 148-150)"""
        with patch("smart_bot_factory.memory.static_memory.root", tmp_path):
            memory = StaticMemoryManager(bot_id="test-bot")

            files = memory.list_all()

            assert files == []

    def test_exists_file_exists(self, temp_memory_dir, tmp_path):
        """Тест проверки существования файла (строки 159-173)"""
        (temp_memory_dir / "actions.txt").write_text("Test")

        with patch("smart_bot_factory.memory.static_memory.root", tmp_path):
            memory = StaticMemoryManager(bot_id="test-bot")

            assert memory.exists("actions") is True
            assert memory.exists("nonexistent") is False

    def test_exists_dir_not_exists(self, tmp_path):
        """Тест проверки существования когда папка не существует (строки 169-170)"""
        with patch("smart_bot_factory.memory.static_memory.root", tmp_path):
            memory = StaticMemoryManager(bot_id="test-bot")

            assert memory.exists("actions") is False

    def test_clear_cache(self, temp_memory_dir, tmp_path):
        """Тест очистки кэша (строки 175-181)"""
        (temp_memory_dir / "actions.txt").write_text("Test")

        with patch("smart_bot_factory.memory.static_memory.root", tmp_path):
            memory = StaticMemoryManager(bot_id="test-bot")

            # Загружаем файл в кэш
            memory.get("actions")
            assert "actions" in memory._cache

            # Очищаем кэш
            memory.clear_cache()

            assert len(memory._cache) == 0

    def test_reload_file(self, temp_memory_dir, tmp_path):
        """Тест перезагрузки файла (строки 183-198)"""
        test_file = temp_memory_dir / "actions.txt"
        test_file.write_text("Original", encoding="utf-8")

        with patch("smart_bot_factory.memory.static_memory.root", tmp_path):
            memory = StaticMemoryManager(bot_id="test-bot")

            # Первое чтение
            memory.get("actions")
            assert memory._cache["actions"] == "Original"

            # Изменяем файл
            test_file.write_text("Modified", encoding="utf-8")

            # Перезагружаем
            result = memory.reload("actions")

            assert result == "Modified"
            assert memory._cache["actions"] == "Modified"

    def test_reload_file_not_in_cache(self, temp_memory_dir, tmp_path):
        """Тест перезагрузки файла, которого нет в кэше"""
        test_file = temp_memory_dir / "actions.txt"
        test_file.write_text("Test", encoding="utf-8")

        with patch("smart_bot_factory.memory.static_memory.root", tmp_path):
            memory = StaticMemoryManager(bot_id="test-bot")

            # Перезагружаем без предварительной загрузки
            result = memory.reload("actions")

            assert result == "Test"

    def test_get_memory_dir(self, tmp_path):
        """Тест получения пути к папке memory (строки 200-207)"""
        with patch("smart_bot_factory.memory.static_memory.root", tmp_path):
            memory = StaticMemoryManager(bot_id="test-bot")

            memory_dir = memory.get_memory_dir()

            assert isinstance(memory_dir, Path)
            assert memory_dir == tmp_path / "bots" / "test-bot" / "memory"
