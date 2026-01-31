"""Тесты для CLI модуля"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from smart_bot_factory.cli import (
    cli,
    create_basic_prompts,
    create_bot_template,
    create_env_template,
    create_new_bot_structure,
    list_bots_in_bots_folder,
)


class TestCLICommands:
    """Тесты для CLI команд"""

    @pytest.fixture
    def runner(self):
        """Фикстура для CliRunner"""
        return CliRunner()

    @pytest.fixture
    def temp_root(self, monkeypatch):
        """Создает временную директорию для тестов"""
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir)
            # Создаем структуру папок
            (temp_path / "bots").mkdir()
            (temp_path / "smart_bot_factory").mkdir()
            (temp_path / "smart_bot_factory" / "configs").mkdir(parents=True)
            (temp_path / "smart_bot_factory" / "configs" / "growthmed-october-24").mkdir(parents=True)
            (temp_path / "smart_bot_factory" / "configs" / "growthmed-october-24" / "prompts").mkdir(parents=True)

            # Мокаем project_root_finder.root
            with patch("smart_bot_factory.cli.root", temp_path):
                yield temp_path

    def test_cli_group_exists(self, runner):
        """Тест что CLI группа существует"""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Smart Bot Factory" in result.output

    def test_create_command_help(self, runner):
        """Тест справки команды create"""
        result = runner.invoke(cli, ["create", "--help"])
        assert result.exit_code == 0
        assert "Создать нового бота" in result.output

    def test_list_command_help(self, runner):
        """Тест справки команды list"""
        result = runner.invoke(cli, ["list", "--help"])
        assert result.exit_code == 0
        assert "Показать список доступных ботов" in result.output

    def test_run_command_help(self, runner):
        """Тест справки команды run"""
        result = runner.invoke(cli, ["run", "--help"])
        assert result.exit_code == 0
        assert "Запустить бота" in result.output

    def test_test_command_help(self, runner):
        """Тест справки команды test"""
        result = runner.invoke(cli, ["test", "--help"])
        assert result.exit_code == 0
        assert "Запустить тесты бота" in result.output

    def test_config_command_help(self, runner):
        """Тест справки команды config"""
        result = runner.invoke(cli, ["config", "--help"])
        assert result.exit_code == 0
        assert "Настроить конфигурацию бота" in result.output

    def test_prompts_command_help(self, runner):
        """Тест справки команды prompts"""
        result = runner.invoke(cli, ["prompts", "--help"])
        assert result.exit_code == 0
        assert "Управление промптами бота" in result.output

    def test_path_command(self, runner, temp_root):
        """Тест команды path"""
        with patch("smart_bot_factory.cli.root", temp_root):
            result = runner.invoke(cli, ["path"])
            assert result.exit_code == 0
            assert str(temp_root) in result.output

    def test_rm_command_help(self, runner):
        """Тест справки команды rm"""
        result = runner.invoke(cli, ["rm", "--help"])
        assert result.exit_code == 0
        assert "Удалить бота" in result.output

    def test_copy_command_help(self, runner):
        """Тест справки команды copy"""
        result = runner.invoke(cli, ["copy", "--help"])
        assert result.exit_code == 0
        assert "Скопировать существующего бота" in result.output

    def test_link_command_help(self, runner):
        """Тест справки команды link"""
        result = runner.invoke(cli, ["link", "--help"])
        assert result.exit_code == 0
        assert "Создать UTM-ссылку" in result.output


class TestCLIFunctions:
    """Тесты для вспомогательных функций CLI"""

    @pytest.fixture
    def temp_root(self):
        """Создает временную директорию для тестов"""
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir)
            yield temp_path

    def test_create_bot_template(self):
        """Тест создания шаблона файла бота"""
        bot_id = "test_bot"
        template = create_bot_template(bot_id)

        assert bot_id in template
        assert "BotBuilder" in template
        assert "EventRouter" in template
        assert "from smart_bot_factory" in template

    def test_create_env_template(self):
        """Тест создания шаблона .env файла"""
        bot_id = "test_bot"
        env_template = create_env_template(bot_id)

        assert "TELEGRAM_BOT_TOKEN" in env_template
        assert "SUPABASE_URL" in env_template
        assert "OPENAI_API_KEY" in env_template
        assert bot_id in env_template

    def test_list_bots_in_bots_folder_empty(self, temp_root):
        """Тест списка ботов в пустой папке"""
        bots_dir = temp_root / "bots"
        bots_dir.mkdir()

        with patch("smart_bot_factory.cli.root", temp_root):
            bots = list_bots_in_bots_folder()
            assert bots == []

    def test_list_bots_in_bots_folder_with_bots(self, temp_root):
        """Тест списка ботов с существующими ботами"""
        bots_dir = temp_root / "bots"
        bots_dir.mkdir()

        # Создаем ботов
        (bots_dir / "bot1").mkdir()
        (bots_dir / "bot2").mkdir()
        (temp_root / "bot1.py").write_text("# bot1")
        (temp_root / "bot2.py").write_text("# bot2")

        # Мокаем root глобально для функции
        import smart_bot_factory.cli

        original_root = smart_bot_factory.cli.root
        smart_bot_factory.cli.root = temp_root

        try:
            # Мокаем Path чтобы он проверял существование относительно root
            # Функция использует Path(f"{item.name}.py").exists()
            # Нужно чтобы Path создавал путь относительно root
            original_path = Path

            class MockPath(Path):
                def __new__(cls, *args, **kwargs):
                    if len(args) == 1 and isinstance(args[0], str) and args[0].endswith(".py"):
                        # Возвращаем путь относительно root
                        return temp_root / args[0]
                    return original_path(*args, **kwargs)

            with patch("smart_bot_factory.cli.Path", MockPath):
                bots = list_bots_in_bots_folder()
                assert "bot1" in bots
                assert "bot2" in bots
                assert len(bots) == 2
        finally:
            smart_bot_factory.cli.root = original_root

    def test_list_bots_in_bots_folder_only_dirs_with_py_files(self, temp_root):
        """Тест что в список попадают только папки с соответствующими .py файлами"""
        bots_dir = temp_root / "bots"
        bots_dir.mkdir()

        # Создаем бота с .py файлом
        (bots_dir / "valid_bot").mkdir()
        (temp_root / "valid_bot.py").write_text("# valid")

        # Создаем папку без .py файла
        (bots_dir / "invalid_bot").mkdir()

        # Мокаем root глобально для функции
        import smart_bot_factory.cli

        original_root = smart_bot_factory.cli.root
        smart_bot_factory.cli.root = temp_root

        try:
            # Мокаем Path чтобы он проверял существование относительно root
            original_path = Path

            class MockPath(Path):
                def __new__(cls, *args, **kwargs):
                    if len(args) == 1 and isinstance(args[0], str) and args[0].endswith(".py"):
                        # Возвращаем путь относительно root
                        return temp_root / args[0]
                    return original_path(*args, **kwargs)

            with patch("smart_bot_factory.cli.Path", MockPath):
                bots = list_bots_in_bots_folder()
                assert "valid_bot" in bots
                assert "invalid_bot" not in bots
        finally:
            smart_bot_factory.cli.root = original_root

    def test_create_basic_prompts(self, temp_root):
        """Тест создания базовых промптов"""
        prompts_dir = temp_root / "prompts"
        prompts_dir.mkdir()

        create_basic_prompts(prompts_dir)

        # Проверяем что файлы созданы
        assert (prompts_dir / "system_prompt.txt").exists()
        assert (prompts_dir / "welcome_message.txt").exists()
        assert (prompts_dir / "final_instructions.txt").exists()

        # Проверяем содержимое
        system_prompt = (prompts_dir / "system_prompt.txt").read_text(encoding="utf-8")
        assert "помощник" in system_prompt.lower()

        welcome_message = (prompts_dir / "welcome_message.txt").read_text(encoding="utf-8")
        assert "Привет" in welcome_message

        final_instructions = (prompts_dir / "final_instructions.txt").read_text(encoding="utf-8")
        assert "этап" in final_instructions
        assert "качество" in final_instructions
        assert "события" in final_instructions

    @patch("smart_bot_factory.cli.click.echo")
    def test_create_new_bot_structure_base_template(self, mock_echo, temp_root):
        """Тест создания структуры бота с базовым шаблоном"""
        bots_dir = temp_root / "bots"
        bots_dir.mkdir()

        # Создаем структуру для growthmed шаблона
        configs_dir = temp_root / "smart_bot_factory" / "configs" / "growthmed-october-24"
        configs_dir.mkdir(parents=True)
        (configs_dir / "prompts").mkdir()
        (configs_dir / "tests").mkdir()
        (configs_dir / "welcome_file").mkdir()
        (configs_dir / "files").mkdir()

        # Создаем тестовые файлы
        (configs_dir / "prompts" / "test.txt").write_text("test prompt")

        with patch("smart_bot_factory.cli.root", temp_root):
            with patch("smart_bot_factory.cli.copy_from_growthmed_template") as mock_copy:
                success = create_new_bot_structure("base", "test_bot")

                assert success is True
                bot_dir = bots_dir / "test_bot"
                assert bot_dir.exists()
                assert (bot_dir / "prompts").exists()
                assert (bot_dir / "tests").exists()
                assert (bot_dir / "reports").exists()
                assert (bot_dir / "welcome_files").exists()
                assert (bot_dir / "files").exists()
                mock_copy.assert_called_once()

    @patch("smart_bot_factory.cli.click.echo")
    def test_create_new_bot_structure_existing_bot(self, mock_echo, temp_root):
        """Тест создания бота который уже существует"""
        bots_dir = temp_root / "bots"
        bots_dir.mkdir()
        (bots_dir / "existing_bot").mkdir()

        with patch("smart_bot_factory.cli.root", temp_root):
            success = create_new_bot_structure("base", "existing_bot")

            assert success is False
            mock_echo.assert_called()
            assert "уже существует" in str(mock_echo.call_args_list).lower()

    @patch("smart_bot_factory.cli.click.echo")
    def test_create_new_bot_structure_custom_template(self, mock_echo, temp_root):
        """Тест создания бота с кастомным шаблоном"""
        bots_dir = temp_root / "bots"
        bots_dir.mkdir()

        # Создаем шаблон бота
        template_dir = bots_dir / "template_bot"
        template_dir.mkdir()
        (template_dir / "prompts").mkdir()
        (temp_root / "template_bot.py").write_text("# template")

        # Мокаем root глобально
        import smart_bot_factory.cli

        original_root = smart_bot_factory.cli.root
        smart_bot_factory.cli.root = temp_root

        try:
            with patch("smart_bot_factory.cli.copy_from_bot_template") as mock_copy:
                success = create_new_bot_structure("template_bot", "new_bot")

                assert success is True
                # Проверяем что функция вызвана с правильными аргументами
                mock_copy.assert_called_once()
                call_args = mock_copy.call_args
                assert call_args[0][0] == "template_bot"  # template
                assert call_args[0][1] == bots_dir / "new_bot"  # bot_dir
                assert call_args[0][2] == "new_bot"  # bot_id
        finally:
            smart_bot_factory.cli.root = original_root

    def test_create_bot_template_structure(self):
        """Тест структуры шаблона бота"""
        bot_id = "my_bot"
        template = create_bot_template(bot_id)

        # Проверяем обязательные элементы
        assert f'BotBuilder("{bot_id}")' in template
        assert f'EventRouter("{bot_id}")' in template
        assert "@event_router.event_handler" in template
        assert "bot_builder.register_routers" in template
        assert "from smart_bot_factory" in template

    def test_create_env_template_structure(self):
        """Тест структуры шаблона .env"""
        bot_id = "my_bot"
        env_template = create_env_template(bot_id)

        # Проверяем обязательные переменные
        required_vars = [
            "TELEGRAM_BOT_TOKEN",
            "SUPABASE_URL",
            "SUPABASE_KEY",
            "OPENAI_API_KEY",
            "OPENAI_MODEL",
            "ADMIN_TELEGRAM_IDS",
            "DEBUG_MODE",
        ]

        for var in required_vars:
            assert var in env_template

    def test_create_env_template_bot_id_replacement(self):
        """Тест что bot_id правильно подставляется в шаблон"""
        bot_id = "test_bot_123"
        env_template = create_env_template(bot_id)

        # Проверяем что bot_id упоминается в комментариях
        assert bot_id in env_template
        assert f"python {bot_id}.py" in env_template
