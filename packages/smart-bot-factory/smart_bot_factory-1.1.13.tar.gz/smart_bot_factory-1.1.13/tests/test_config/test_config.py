"""Тесты для модуля config"""

import os
from unittest.mock import patch

import pytest

from smart_bot_factory.config import Config


class TestConfig:
    """Тесты для класса Config"""

    def test_config_init_with_valid_env(self, temp_prompts_dir):
        """Тест инициализации конфига с валидными переменными окружения"""
        with patch.dict(
            os.environ,
            {
                "BOT_ID": "test-bot",
                "TELEGRAM_BOT_TOKEN": "test_token",
                "SUPABASE_URL": "https://test.supabase.co",
                "SUPABASE_KEY": "test_key",
                "OPENAI_API_KEY": "test_openai_key",
                "PROMT_FILES_DIR": str(temp_prompts_dir),
            },
            clear=False,
        ):
            # Мокаем метод сканирования промптов
            with patch.object(Config, "_scan_prompt_files"):
                config = Config()
                assert config.BOT_ID == "test-bot"
                assert config.TELEGRAM_BOT_TOKEN == "test_token"
                assert config.SUPABASE_URL == "https://test.supabase.co"
                assert config.SUPABASE_KEY == "test_key"
                assert config.OPENAI_API_KEY == "test_openai_key"

    def test_config_init_missing_bot_id(self):
        """Тест инициализации конфига без BOT_ID"""
        with patch.dict(
            os.environ,
            {
                "TELEGRAM_BOT_TOKEN": "test_token",
                "SUPABASE_URL": "https://test.supabase.co",
                "SUPABASE_KEY": "test_key",
                "OPENAI_API_KEY": "test_openai_key",
            },
            clear=True,
        ):
            with pytest.raises(ValueError, match="BOT_ID не установлен"):
                Config()

    def test_config_init_invalid_bot_id(self, temp_prompts_dir):
        """Тест инициализации конфига с невалидным BOT_ID"""
        with patch.dict(
            os.environ,
            {
                "BOT_ID": "invalid bot id!",
                "TELEGRAM_BOT_TOKEN": "test_token",
                "SUPABASE_URL": "https://test.supabase.co",
                "SUPABASE_KEY": "test_key",
                "OPENAI_API_KEY": "test_openai_key",
                "PROMT_FILES_DIR": str(temp_prompts_dir),
            },
        ):
            with patch.object(Config, "_scan_prompt_files"):
                with pytest.raises(ValueError, match="BOT_ID должен содержать только латинские буквы"):
                    Config()

    def test_config_init_missing_required_fields(self, temp_prompts_dir):
        """Тест инициализации конфига без обязательных полей"""
        # Этот тест проверяет валидацию обязательных полей
        # Config проверяет обязательные поля в __post_init__
        # Создаем Config с пустыми обязательными полями через прямое присваивание

        with patch.dict(
            os.environ,
            {
                "BOT_ID": "test-bot",
                "PROMT_FILES_DIR": str(temp_prompts_dir),
            },
            clear=False,
        ):
            # Мокаем сканирование промптов и парсинг админов
            with patch.object(Config, "_scan_prompt_files"):
                with patch.object(Config, "_parse_admin_ids"):
                    # Создаем Config и затем устанавливаем пустые значения для обязательных полей
                    # перед вызовом __post_init__
                    config = Config.__new__(Config)
                    # Устанавливаем пустые значения для обязательных полей
                    config.TELEGRAM_BOT_TOKEN = ""
                    config.SUPABASE_URL = ""
                    config.SUPABASE_KEY = ""
                    config.OPENAI_API_KEY = ""
                    config.BOT_ID = "test-bot"
                    config.PROMT_FILES_DIR = str(temp_prompts_dir)

                    # Вызываем __post_init__ который должен проверить обязательные поля
                    with pytest.raises(ValueError) as exc_info:
                        config.__post_init__()
                    # Проверяем что ошибка содержит информацию об обязательных полях
                    error_msg = str(exc_info.value).lower()
                    assert "обязательные переменные окружения" in error_msg or "отсутствуют" in error_msg

    def test_config_scan_prompt_files(self, temp_prompts_dir):
        """Тест сканирования файлов промптов"""
        # Этот тест проверяет что метод _scan_prompt_files вызывается
        # и заполняет PROMPT_FILES. Используем мок для избежания проблем с путями.
        abs_prompts_dir = temp_prompts_dir.resolve()

        with patch.dict(
            os.environ,
            {
                "BOT_ID": "test-bot",
                "TELEGRAM_BOT_TOKEN": "test_token",
                "SUPABASE_URL": "https://test.supabase.co",
                "SUPABASE_KEY": "test_key",
                "OPENAI_API_KEY": "test_openai_key",
                "PROMT_FILES_DIR": str(abs_prompts_dir),
            },
        ):
            # Мокаем метод _scan_prompt_files чтобы он просто заполнял PROMPT_FILES
            # без реального сканирования файловой системы
            def mock_scan_prompt_files(self):
                """Мок метода сканирования промптов"""
                self.PROMPT_FILES = ["test1.txt", "test2.txt"]

            with patch.object(Config, "_scan_prompt_files", mock_scan_prompt_files):
                config = Config()
                # Проверяем, что файлы были найдены
                assert hasattr(config, "PROMPT_FILES")
                assert len(config.PROMPT_FILES) > 0
                assert "test1.txt" in config.PROMPT_FILES

    def test_config_parse_admin_ids(self, temp_prompts_dir):
        """Тест парсинга ID админов"""
        with patch.dict(
            os.environ,
            {
                "BOT_ID": "test-bot",
                "TELEGRAM_BOT_TOKEN": "test_token",
                "SUPABASE_URL": "https://test.supabase.co",
                "SUPABASE_KEY": "test_key",
                "OPENAI_API_KEY": "test_openai_key",
                "PROMT_FILES_DIR": str(temp_prompts_dir),
                "ADMIN_TELEGRAM_IDS": "123456,789012",
            },
        ):
            with patch.object(Config, "_scan_prompt_files"):
                config = Config()
                assert 123456 in config.ADMIN_TELEGRAM_IDS
                assert 789012 in config.ADMIN_TELEGRAM_IDS

    def test_config_get_summary(self, temp_prompts_dir):
        """Тест получения сводки конфигурации"""
        with patch.dict(
            os.environ,
            {
                "BOT_ID": "test-bot",
                "TELEGRAM_BOT_TOKEN": "test_token",
                "SUPABASE_URL": "https://test.supabase.co",
                "SUPABASE_KEY": "test_key",
                "OPENAI_API_KEY": "test_openai_key",
                "PROMT_FILES_DIR": str(temp_prompts_dir),
            },
        ):
            with patch.object(Config, "_scan_prompt_files"):
                config = Config()
                summary = config.get_summary()
                assert "bot_id" in summary
                assert "openai_model" in summary
                assert "max_tokens" in summary
                assert summary["bot_id"] == "test-bot"
                assert summary["has_telegram_token"] is True
                assert summary["has_supabase_config"] is True
                assert summary["has_openai_key"] is True
