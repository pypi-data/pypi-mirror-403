"""Общие фикстуры для тестов"""

import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

# Устанавливаем переменные окружения для тестов
os.environ.setdefault("BOT_ID", "test-bot")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test_token")
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test_key")
os.environ.setdefault("OPENAI_API_KEY", "test_openai_key")
os.environ.setdefault("PROMT_FILES_DIR", "prompts")


@pytest.fixture
def mock_bot():
    """Мок бота Telegram"""
    bot = Mock()
    bot.token = "test_token"
    bot.id = 12345
    bot.send_message = AsyncMock()
    bot.send_chat_action = AsyncMock()
    return bot


@pytest.fixture
def mock_message():
    """Мок сообщения Telegram"""
    message = Mock()
    message.text = "test message"
    message.from_user.id = 123456
    message.from_user.username = "test_user"
    message.from_user.first_name = "Test"
    message.from_user.last_name = "User"
    message.chat.id = 123456
    message.message_id = 1
    message.answer = AsyncMock()
    message.answer_document = AsyncMock()
    message.answer_media_group = AsyncMock()
    return message


@pytest.fixture
def mock_supabase_client():
    """Мок клиента Supabase"""
    client = Mock()
    client.bot_id = "test-bot"
    client.client = Mock()
    client.client.table = Mock(return_value=Mock())
    client.get_chat_history = AsyncMock(return_value=[])
    client.get_session_info = AsyncMock(return_value={})
    client.create_chat_session = AsyncMock(return_value="test_session_id")
    client.add_message = AsyncMock(return_value=1)
    client.update_session = AsyncMock(return_value={})
    client.update_session_all = AsyncMock(return_value=True)
    client.get_active_session = AsyncMock(return_value={"id": "test_session_id"})
    # get_sent_files/get_sent_directories больше не используются - убрано для оптимизации
    # add_sent_files/add_sent_directories больше не используются - убрано для оптимизации
    return client


@pytest.fixture
def mock_config():
    """Мок конфигурации"""
    config = Mock()
    config.BOT_ID = "test-bot"
    config.TELEGRAM_BOT_TOKEN = "test_token"
    config.SUPABASE_URL = "https://test.supabase.co"
    config.SUPABASE_KEY = "test_key"
    config.OPENAI_API_KEY = "test_openai_key"
    config.OPENAI_MODEL = "gpt-4"
    config.OPENAI_MAX_TOKENS = 1500
    config.OPENAI_TEMPERATURE = 0.7
    config.MAX_CONTEXT_MESSAGES = 50
    config.HISTORY_MIN_MESSAGES = 4
    config.HISTORY_MAX_TOKENS = 5000
    config.MESSAGE_PARSE_MODE = "Markdown"
    config.PROMT_FILES_DIR = "prompts"
    config.PROMPT_FILES = ["test1.txt", "test2.txt"]
    config.ADMIN_TELEGRAM_IDS = [123456]
    config.DEBUG_MODE = False
    return config


@pytest.fixture
def mock_openai_client():
    """Мок клиента OpenAI"""
    client = Mock()
    client.chat = Mock()
    client.chat.completions = Mock()
    client.chat.completions.create = AsyncMock()
    client.check_api_health = AsyncMock(return_value=True)
    return client


@pytest.fixture
def mock_prompt_loader():
    """Мок загрузчика промптов"""
    loader = Mock()
    loader.load_welcome_message = AsyncMock(return_value="Добро пожаловать!")
    loader.load_help_message = AsyncMock(return_value="Справка")
    loader.validate_prompts = AsyncMock(return_value={"test1.txt": True, "test2.txt": True})
    return loader


@pytest.fixture
def mock_admin_manager():
    """Мок менеджера админов"""
    manager = Mock()
    manager.is_admin = Mock(return_value=False)
    manager.is_in_admin_mode = Mock(return_value=False)
    manager.get_active_admins = AsyncMock(return_value=[])
    manager.get_stats = Mock(return_value={"active_admins": 0, "total_admins": 1})
    return manager


@pytest.fixture
def temp_prompts_dir(tmp_path):
    """Временная директория с промптами"""
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()

    # Создаем обязательный файл welcome_message.txt
    (prompts_dir / "welcome_message.txt").write_text("Добро пожаловать!")
    (prompts_dir / "help_message.txt").write_text("Справка")
    (prompts_dir / "test1.txt").write_text("Тестовый промпт 1")
    (prompts_dir / "test2.txt").write_text("Тестовый промпт 2")

    return prompts_dir


@pytest.fixture
def mock_state():
    """Мок FSM состояния"""
    state = Mock()
    state.get_state = AsyncMock(return_value=None)
    state.set_state = AsyncMock()
    state.clear = AsyncMock()
    state.update_data = AsyncMock()
    return state


@pytest.fixture
def mock_callback_query():
    """Мок callback query"""
    callback = Mock()
    callback.data = "test_callback"
    callback.from_user.id = 123456
    callback.message = Mock()
    callback.message.chat.id = 123456
    callback.answer = AsyncMock()
    return callback


@pytest.fixture(autouse=True)
def cleanup_temp_dirs():
    """Автоматическая очистка временных папок после тестов"""
    yield

    # Очищаем временные папки созданные voice_handler
    temp_audio_dir = Path(tempfile.gettempdir()) / "smart_bot_factory_audio"
    if temp_audio_dir.exists():
        try:
            # Удаляем все файлы в папке
            for file_path in temp_audio_dir.iterdir():
                if file_path.is_file():
                    file_path.unlink(missing_ok=True)
            # Удаляем саму папку если она пуста
            if not any(temp_audio_dir.iterdir()):
                temp_audio_dir.rmdir()
        except Exception:
            # Игнорируем ошибки очистки - не критично для тестов
            pass

    # Очищаем старую папку temp_audio в корне проекта если она существует
    old_temp_audio = Path("temp_audio")
    if old_temp_audio.exists() and old_temp_audio.is_dir():
        try:
            for file_path in old_temp_audio.iterdir():
                if file_path.is_file():
                    file_path.unlink(missing_ok=True)
            if not any(old_temp_audio.iterdir()):
                old_temp_audio.rmdir()
        except Exception:
            # Игнорируем ошибки очистки
            pass
