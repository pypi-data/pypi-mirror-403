"""Тесты для prompt_loader"""

import os
import tempfile
from pathlib import Path

import pytest

from smart_bot_factory.integrations.openai.prompt_loader import PromptLoader


class TestPromptLoader:
    """Тесты для PromptLoader"""

    @pytest.fixture
    def temp_prompts_dir(self, tmp_path):
        """Фикстура для временной директории промптов"""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()

        # Создаем тестовые файлы с явной кодировкой UTF-8
        (prompts_dir / "welcome_message.txt").write_text("Добро пожаловать!", encoding="utf-8")
        (prompts_dir / "help_message.txt").write_text("Справка", encoding="utf-8")
        (prompts_dir / "1sales_context.txt").write_text("Контекст продаж", encoding="utf-8")
        (prompts_dir / "2product_info.txt").write_text("Информация о продукте", encoding="utf-8")
        (prompts_dir / "final_instructions.txt").write_text("Финальные инструкции", encoding="utf-8")

        return str(prompts_dir)

    @pytest.fixture
    def prompt_loader(self, temp_prompts_dir):
        """Фикстура для PromptLoader"""
        return PromptLoader(temp_prompts_dir)

    @pytest.mark.asyncio
    async def test_load_welcome_message(self, prompt_loader):
        """Тест загрузки приветственного сообщения"""
        message = await prompt_loader.load_welcome_message()

        assert "Добро пожаловать" in message
        assert len(message) > 0

    @pytest.mark.asyncio
    async def test_load_welcome_message_not_found(self, tmp_path):
        """Тест загрузки когда файл не найден"""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        loader = PromptLoader(str(prompts_dir))

        with pytest.raises(FileNotFoundError):
            await loader.load_welcome_message()

    @pytest.mark.asyncio
    async def test_load_help_message(self, prompt_loader):
        """Тест загрузки справочного сообщения"""
        message = await prompt_loader.load_help_message()

        assert len(message) > 0

    @pytest.mark.asyncio
    async def test_load_help_message_fallback(self, tmp_path):
        """Тест fallback для справочного сообщения"""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        loader = PromptLoader(str(prompts_dir))

        message = await loader.load_help_message()

        assert len(message) > 0
        assert "помощник" in message.lower() or "start" in message.lower()

    @pytest.mark.asyncio
    async def test_load_final_instructions(self, prompt_loader):
        """Тест загрузки финальных инструкций"""
        instructions = await prompt_loader.load_final_instructions()

        assert "Финальные инструкции" in instructions

    @pytest.mark.asyncio
    async def test_load_final_instructions_with_tools(self, prompt_loader):
        """Тест загрузки финальных инструкций с описанием инструментов"""
        tools_description = "### ДОСТУПНЫЕ ИНСТРУМЕНТЫ ###\n\n1. **test_tool**"
        prompt_loader.set_tools_description(tools_description)

        instructions = await prompt_loader.load_final_instructions()

        assert "ДОСТУПНЫЕ ИНСТРУМЕНТЫ" in instructions
        assert "test_tool" in instructions

    @pytest.mark.asyncio
    async def test_load_system_prompt(self, prompt_loader):
        """Тест загрузки системного промпта"""
        prompt = await prompt_loader.load_system_prompt()

        assert len(prompt) > 0
        assert "Контекст продаж" in prompt or "product_info" in prompt.lower()
        assert "JSON" in prompt or "json" in prompt.lower()

    @pytest.mark.asyncio
    async def test_load_system_prompt_cached(self, prompt_loader):
        """Тест кеширования системного промпта"""
        prompt1 = await prompt_loader.load_system_prompt()
        prompt2 = await prompt_loader.load_system_prompt()

        assert prompt1 == prompt2

    @pytest.mark.asyncio
    async def test_reload_system_prompt(self, prompt_loader):
        """Тест перезагрузки системного промпта"""
        prompt1 = await prompt_loader.load_system_prompt()

        # Изменяем файл
        prompts_dir = Path(prompt_loader.prompts_dir)
        (prompts_dir / "1sales_context.txt").write_text("Новый контекст", encoding="utf-8")

        prompt2 = await prompt_loader.reload_system_prompt()

        assert prompt1 != prompt2
        assert "Новый контекст" in prompt2

    def test_set_tools_description(self, prompt_loader):
        """Тест установки описания инструментов"""
        tools_description = "Описание инструментов"
        prompt_loader.set_tools_description(tools_description)

        assert prompt_loader._tools_description == tools_description

    def test_get_prompt_info(self, prompt_loader):
        """Тест получения информации о промптах"""
        info = prompt_loader.get_prompt_info()

        assert "prompts_dir" in info
        assert "prompt_files" in info
        assert "welcome_file" in info
        assert info["json_instructions_included"] is True

    @pytest.mark.asyncio
    async def test_validate_prompts(self, prompt_loader):
        """Тест валидации промптов"""
        results = await prompt_loader.validate_prompts()

        assert isinstance(results, dict)
        assert "welcome_message.txt" in results
        assert results["welcome_message.txt"] is True

    def test_cleanup_temp_files(self, prompt_loader):
        """Тест очистки временных файлов"""
        # Создаем временный файл
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".txt", prefix="system_prompt_")
        temp_file.write(b"test")
        temp_file.close()

        prompt_loader._temp_system_prompt_file = temp_file.name

        # Проверяем что файл существует
        assert os.path.exists(temp_file.name)

        # Очищаем
        prompt_loader.cleanup_temp_files()

        # Проверяем что файл удален
        assert not os.path.exists(temp_file.name)

    @pytest.mark.asyncio
    async def test_test_json_parsing(self, prompt_loader):
        """Тест парсинга JSON из ответа"""
        # Формат который ожидает метод: текст + JSON в конце
        test_response = 'Тестовый ответ {"этап": "introduction"}'

        result = await prompt_loader.test_json_parsing(test_response)

        assert result["success"] is True
        assert "metadata" in result
        assert result["metadata"]["этап"] == "introduction"

    @pytest.mark.asyncio
    async def test_test_json_parsing_invalid(self, prompt_loader):
        """Тест парсинга невалидного JSON"""
        test_response = "Просто текст без JSON"

        result = await prompt_loader.test_json_parsing(test_response)

        assert result["success"] is False
        assert "error" in result
