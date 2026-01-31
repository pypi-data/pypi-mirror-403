"""Тесты для bot_testing"""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest
import yaml

from smart_bot_factory.creation.bot_testing import (
    BotTesterIntegrated,
    ReportGenerator,
    ScenarioLoader,
    StepResult,
    TestResult,
    TestRunner,
    TestScenario,
    TestStep,
)

# Указываем pytest что эти классы не являются тестовыми
TestStep.__test__ = False
TestScenario.__test__ = False
TestResult.__test__ = False
TestRunner.__test__ = False


class TestTestStep:
    """Тесты для класса TestStep"""

    def test_init(self):
        """Тест инициализации TestStep"""
        step = TestStep(user_input="Привет", expected_keywords=["привет", "здравствуй"], forbidden_keywords=["плохо"])
        assert step.user_input == "Привет"
        assert len(step.expected_keywords) == 2
        assert step.forbidden_keywords == ["плохо"]

    def test_process_keywords_synonyms(self):
        """Тест обработки ключевых слов с синонимами"""
        step = TestStep(user_input="Тест", expected_keywords=[["привет", "здравствуй", "добро пожаловать"]])
        assert len(step.expected_keywords) == 1
        assert isinstance(step.expected_keywords[0], list)
        assert len(step.expected_keywords[0]) == 3

    def test_process_keywords_mixed(self):
        """Тест обработки смешанных ключевых слов"""
        step = TestStep(user_input="Тест", expected_keywords=["привет", ["здравствуй", "добро пожаловать"]])
        assert len(step.expected_keywords) == 2
        assert step.expected_keywords[0] == ["привет"]
        assert isinstance(step.expected_keywords[1], list)


class TestTestScenario:
    """Тесты для класса TestScenario"""

    def test_init(self):
        """Тест инициализации TestScenario"""
        steps = [TestStep(user_input="Привет", expected_keywords=["привет"]), TestStep(user_input="Как дела?", expected_keywords=["дела"])]
        scenario = TestScenario(name="Тест сценария", steps=steps)
        assert scenario.name == "Тест сценария"
        assert len(scenario.steps) == 2


class TestStepResult:
    """Тесты для класса StepResult"""

    def test_init(self):
        """Тест инициализации StepResult"""
        step = TestStep(user_input="Тест", expected_keywords=["тест"])
        result = StepResult(step=step, bot_response="Тестовый ответ", passed=True, missing_keywords=[], found_forbidden=[])
        assert result.step == step
        assert result.bot_response == "Тестовый ответ"
        assert result.passed is True
        assert result.missing_keywords == []
        assert result.found_forbidden == []


class TestTestResult:
    """Тесты для класса TestResult"""

    def test_init_passed(self):
        """Тест инициализации TestResult с пройденным тестом"""
        scenario = TestScenario(name="Тест", steps=[])
        step_results = [StepResult(step=TestStep(user_input="Тест", expected_keywords=["тест"]), bot_response="Ответ", passed=True)]
        result = TestResult(scenario=scenario, step_results=step_results)
        assert result.passed is True
        assert result.total_steps == 1
        assert result.passed_steps == 1
        assert result.failed_steps == 0

    def test_init_failed(self):
        """Тест инициализации TestResult с проваленным тестом"""
        scenario = TestScenario(name="Тест", steps=[])
        step_results = [StepResult(step=TestStep(user_input="Тест", expected_keywords=["тест"]), bot_response="Ответ", passed=False)]
        result = TestResult(scenario=scenario, step_results=step_results)
        assert result.passed is False
        assert result.passed_steps == 0
        assert result.failed_steps == 1


class TestScenarioLoader:
    """Тесты для класса ScenarioLoader"""

    def test_load_scenarios_from_file_new_format(self):
        """Тест загрузки сценариев из файла (новый формат со steps)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.yaml"
            with open(file_path, "w", encoding="utf-8") as f:
                yaml_content = """
scenarios:
  - name: "Тест сценария"
    steps:
      - user_input: "Привет"
        expected_keywords: ["привет"]
      - user_input: "Как дела?"
        expected_keywords: ["дела"]
"""
                f.write(yaml_content)

            scenarios = ScenarioLoader.load_scenarios_from_file(str(file_path))
            assert len(scenarios) == 1
            assert scenarios[0].name == "Тест сценария"
            assert len(scenarios[0].steps) == 2

    def test_load_scenarios_from_file_old_format(self):
        """Тест загрузки сценариев из файла (старый формат)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.yaml"
            with open(file_path, "w", encoding="utf-8") as f:
                yaml_content = """
scenarios:
  - name: "Тест сценария"
    user_input: "Привет"
    expected_keywords: ["привет"]
"""
                f.write(yaml_content)

            scenarios = ScenarioLoader.load_scenarios_from_file(str(file_path))
            assert len(scenarios) == 1
            assert len(scenarios[0].steps) == 1

    def test_load_scenarios_from_file_error(self):
        """Тест обработки ошибки при загрузке сценариев"""
        scenarios = ScenarioLoader.load_scenarios_from_file("nonexistent.yaml")
        assert scenarios == []

    def test_load_all_scenarios_for_bot(self):
        """Тест загрузки всех сценариев для бота"""
        with tempfile.TemporaryDirectory() as tmpdir:
            bot_dir = Path(tmpdir) / "bots" / "test-bot" / "tests"
            bot_dir.mkdir(parents=True)

            scenario_file = bot_dir / "test.yaml"
            with open(scenario_file, "w", encoding="utf-8") as f:
                yaml.dump({"scenarios": [{"name": "Тест", "user_input": "Привет", "expected_keywords": ["привет"]}]}, f, allow_unicode=True)

            scenarios = ScenarioLoader.load_all_scenarios_for_bot("test-bot", Path(tmpdir))
            assert len(scenarios) == 1

    def test_load_all_scenarios_for_bot_no_dir(self):
        """Тест загрузки сценариев когда директория не существует"""
        scenarios = ScenarioLoader.load_all_scenarios_for_bot("nonexistent-bot", Path("/nonexistent"))
        assert scenarios == []


class TestBotTesterIntegrated:
    """Тесты для класса BotTesterIntegrated"""

    @pytest.fixture
    def mock_components(self):
        """Фикстура для мок компонентов"""
        mock_openai = Mock()
        mock_openai.get_completion = AsyncMock(return_value=Mock(user_message="Тестовый ответ", service_info={}))
        mock_openai.estimate_tokens = Mock(return_value=100)

        mock_prompt = Mock()
        mock_prompt.load_system_prompt = AsyncMock(return_value="Системный промпт")
        mock_prompt.load_welcome_message = AsyncMock(return_value="Приветствие")
        mock_prompt.load_final_instructions = AsyncMock(return_value="Финальные инструкции")

        mock_supabase = Mock()
        mock_supabase.create_chat_session = AsyncMock(return_value="session-123")
        mock_supabase.add_message = AsyncMock()
        mock_supabase.get_chat_history = AsyncMock(return_value=[])
        mock_supabase.update_session_stage = AsyncMock()
        mock_supabase.client = Mock()

        return {"openai": mock_openai, "prompt": mock_prompt, "supabase": mock_supabase}

    @pytest.fixture
    def bot_tester(self, mock_components):
        """Фикстура для BotTesterIntegrated"""
        return BotTesterIntegrated(
            bot_id="test-bot",
            openai_client=mock_components["openai"],
            prompt_loader=mock_components["prompt"],
            supabase_client=mock_components["supabase"],
            config_dir=Path("bots/test-bot"),
            message_hooks={},
        )

    @pytest.mark.asyncio
    async def test_create_test_session(self, bot_tester, mock_components):
        """Тест создания тестовой сессии"""
        user_data = {"telegram_id": 123456, "username": "test_user", "first_name": "Test", "last_name": "User", "language_code": "ru"}

        session_id, system_prompt = await bot_tester.create_test_session(user_data)

        assert session_id == "session-123"
        assert system_prompt == "Системный промпт"
        mock_components["supabase"].create_chat_session.assert_called_once()
        mock_components["supabase"].add_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_welcome_file_caption_test_exists(self, bot_tester):
        """Тест получения подписи к приветственному файлу (файл существует)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            welcome_dir = Path(tmpdir) / "welcome_files"
            welcome_dir.mkdir()
            msg_file = welcome_dir / "welcome_file_msg.txt"
            msg_file.write_text("Подпись к файлу", encoding="utf-8")

            bot_tester.config_dir = Path(tmpdir)
            caption = await bot_tester.get_welcome_file_caption_test()

            assert caption == "Подпись к файлу"

    @pytest.mark.asyncio
    async def test_get_welcome_file_caption_test_not_exists(self, bot_tester):
        """Тест получения подписи к приветственному файлу (файл не существует)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            bot_tester.config_dir = Path(tmpdir)
            caption = await bot_tester.get_welcome_file_caption_test()

            assert caption == ""

    @pytest.mark.asyncio
    async def test_process_user_message_test(self, bot_tester, mock_components):
        """Тест обработки сообщения пользователя"""
        response = await bot_tester.process_user_message_test(
            user_message="Привет", session_id="session-123", system_prompt="Системный промпт", user_id=123456
        )

        assert isinstance(response, str)
        mock_components["openai"].get_completion.assert_called_once()
        mock_components["supabase"].add_message.assert_called()

    @pytest.mark.asyncio
    async def test_test_scenario(self, bot_tester, mock_components):
        """Тест выполнения тестового сценария"""
        scenario = TestScenario(name="Тест сценария", steps=[TestStep(user_input="Привет", expected_keywords=["привет"])])

        result = await bot_tester.test_scenario(scenario)

        assert isinstance(result, TestResult)
        assert result.scenario == scenario
        assert len(result.step_results) == 1


class TestReportGenerator:
    """Тесты для класса ReportGenerator"""

    def test_generate_console_report(self):
        """Тест генерации консольного отчета"""
        scenario = TestScenario(name="Тест", steps=[])
        result = TestResult(
            scenario=scenario,
            step_results=[StepResult(step=TestStep(user_input="Тест", expected_keywords=["тест"]), bot_response="Ответ", passed=True)],
        )

        # Просто проверяем, что метод не вызывает ошибку
        ReportGenerator.generate_console_report("test-bot", [result])

    def test_generate_detailed_report(self):
        """Тест генерации подробного отчета"""
        scenario = TestScenario(name="Тест", steps=[])
        result = TestResult(
            scenario=scenario,
            step_results=[StepResult(step=TestStep(user_input="Тест", expected_keywords=["тест"]), bot_response="Ответ", passed=True)],
        )

        report = ReportGenerator.generate_detailed_report("test-bot", [result])

        assert isinstance(report, str)
        assert "TEST-BOT" in report.upper() or "test-bot" in report.lower()
        assert "Тест" in report

    def test_save_report(self):
        """Тест сохранения отчета в файл"""
        with tempfile.TemporaryDirectory() as tmpdir:
            bot_dir = Path(tmpdir) / "bots" / "test-bot"
            bot_dir.mkdir(parents=True)

            scenario = TestScenario(name="Тест", steps=[])
            result = TestResult(
                scenario=scenario,
                step_results=[StepResult(step=TestStep(user_input="Тест", expected_keywords=["тест"]), bot_response="Ответ", passed=True)],
            )

            report_file = ReportGenerator.save_report("test-bot", [result], Path(tmpdir))

            assert Path(report_file).exists()
            assert Path(report_file).suffix == ".txt"

    def test_cleanup_old_reports(self):
        """Тест очистки старых отчетов"""
        with tempfile.TemporaryDirectory() as tmpdir:
            reports_dir = Path(tmpdir)

            # Создаем несколько файлов отчетов
            for i in range(15):
                report_file = reports_dir / f"test_20240101_12000{i}.txt"
                report_file.write_text("Тест", encoding="utf-8")

            ReportGenerator.cleanup_old_reports(str(reports_dir), max_reports=10)

            # Должно остаться не более 10 файлов
            remaining_files = list(reports_dir.glob("test_*.txt"))
            assert len(remaining_files) <= 10


class TestTestRunner:
    """Тесты для класса TestRunner"""

    @pytest.fixture
    def test_runner(self):
        """Фикстура для TestRunner"""
        with patch("smart_bot_factory.creation.bot_testing.BotTester"):
            return TestRunner("test-bot", max_concurrent=2)

    @pytest.mark.asyncio
    async def test_run_tests(self, test_runner):
        """Тест запуска тестов"""
        scenario = TestScenario(name="Тест", steps=[TestStep(user_input="Тест", expected_keywords=["тест"])])

        mock_tester = Mock()
        mock_tester.test_scenario = AsyncMock(
            return_value=TestResult(scenario=scenario, step_results=[StepResult(step=scenario.steps[0], bot_response="Ответ", passed=True)])
        )
        test_runner.bot_tester = mock_tester

        results = await test_runner.run_tests([scenario])

        assert len(results) == 1
        assert results[0].passed is True
