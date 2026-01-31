"""Тесты для utm_link_generator"""

from unittest.mock import patch

from smart_bot_factory.utm_link_generator import (
    check_size_and_validate,
    create_utm_string,
    generate_telegram_link,
    get_user_input,
    main,
)


class TestCreateUtmString:
    """Тесты для функции create_utm_string"""

    def test_create_utm_string_full(self):
        """Тест создания UTM строки со всеми параметрами"""
        utm_data = {
            "utm_source": "vk",
            "utm_medium": "social",
            "utm_campaign": "summer2025",
            "utm_content": "banner",
            "utm_term": "promo",
            "segment": "premium",
        }

        result = create_utm_string(utm_data)

        assert "source-vk" in result
        assert "medium-social" in result
        assert "campaign-summer2025" in result
        assert "content-banner" in result
        assert "term-promo" in result
        assert "seg-premium" in result

    def test_create_utm_string_partial(self):
        """Тест создания UTM строки с частичными параметрами"""
        utm_data = {
            "utm_source": "vk",
            "utm_campaign": "summer2025",
        }

        result = create_utm_string(utm_data)

        assert result == "source-vk_campaign-summer2025"

    def test_create_utm_string_with_segment(self):
        """Тест создания UTM строки с сегментом"""
        utm_data = {
            "utm_source": "vk",
            "segment": "premium",
        }

        result = create_utm_string(utm_data)

        assert result == "source-vk_seg-premium"

    def test_create_utm_string_empty(self):
        """Тест создания UTM строки без параметров"""
        utm_data = {}

        result = create_utm_string(utm_data)

        assert result == ""

    def test_create_utm_string_only_segment(self):
        """Тест создания UTM строки только с сегментом"""
        utm_data = {
            "segment": "premium",
        }

        result = create_utm_string(utm_data)

        assert result == "seg-premium"

    def test_create_utm_string_order(self):
        """Тест порядка параметров в UTM строке"""
        utm_data = {
            "utm_source": "vk",
            "utm_medium": "social",
            "utm_campaign": "summer2025",
        }

        result = create_utm_string(utm_data)

        # Проверяем что параметры идут в правильном порядке
        parts = result.split("_")
        assert parts[0] == "source-vk"
        assert parts[1] == "medium-social"
        assert parts[2] == "campaign-summer2025"


class TestGenerateTelegramLink:
    """Тесты для функции generate_telegram_link"""

    def test_generate_telegram_link_basic(self):
        """Тест генерации базовой ссылки"""
        link = generate_telegram_link("test_bot", "source-vk")

        assert link == "https://t.me/test_bot?start=source-vk"

    def test_generate_telegram_link_with_utm(self):
        """Тест генерации ссылки с UTM параметрами"""
        utm_string = "source-vk_campaign-summer2025"
        link = generate_telegram_link("test_bot", utm_string)

        assert link == "https://t.me/test_bot?start=source-vk_campaign-summer2025"

    def test_generate_telegram_link_empty_utm(self):
        """Тест генерации ссылки с пустой UTM строкой"""
        link = generate_telegram_link("test_bot", "")

        assert link == "https://t.me/test_bot?start="

    def test_generate_telegram_link_special_chars(self):
        """Тест генерации ссылки со специальными символами"""
        utm_string = "source-vk_campaign-summer-2025"
        link = generate_telegram_link("test_bot", utm_string)

        assert "source-vk_campaign-summer-2025" in link


class TestCheckSizeAndValidate:
    """Тесты для функции check_size_and_validate"""

    def test_check_size_valid(self):
        """Тест проверки валидного размера"""
        utm_string = "source-vk_campaign-summer2025"

        is_valid, message = check_size_and_validate(utm_string)

        assert is_valid is True
        assert "OK" in message
        assert len(utm_string) > 0

    def test_check_size_max_size(self):
        """Тест проверки максимального размера"""
        # Создаем строку ровно 64 символа
        utm_string = "a" * 64

        is_valid, message = check_size_and_validate(utm_string)

        assert is_valid is True
        assert "OK" in message

    def test_check_size_too_large(self):
        """Тест проверки слишком большого размера"""
        # Создаем строку больше 64 символов
        utm_string = "a" * 65

        is_valid, message = check_size_and_validate(utm_string)

        assert is_valid is False
        assert "слишком большая" in message
        assert "65" in message
        assert "64" in message

    def test_check_size_empty(self):
        """Тест проверки пустой строки"""
        utm_string = ""

        is_valid, message = check_size_and_validate(utm_string)

        assert is_valid is True
        assert "OK" in message


class TestGetUserInput:
    """Тесты для функции get_user_input"""

    @patch("builtins.input")
    def test_get_user_input_full(self, mock_input):
        """Тест получения полных данных от пользователя"""
        mock_input.side_effect = [
            "test_bot",  # bot_username
            "vk",  # utm_source
            "social",  # utm_medium
            "summer2025",  # utm_campaign
            "banner",  # utm_content
            "promo",  # utm_term
            "premium",  # segment
        ]

        result = get_user_input()

        assert result is not None
        assert result["bot_username"] == "test_bot"
        assert result["utm_source"] == "vk"
        assert result["utm_medium"] == "social"
        assert result["utm_campaign"] == "summer2025"
        assert result["utm_content"] == "banner"
        assert result["utm_term"] == "promo"
        assert result["segment"] == "premium"

    @patch("builtins.input")
    def test_get_user_input_partial(self, mock_input):
        """Тест получения частичных данных"""
        mock_input.side_effect = [
            "test_bot",  # bot_username
            "vk",  # utm_source
            "",  # utm_medium (пусто)
            "summer2025",  # utm_campaign
            "",  # utm_content (пусто)
            "",  # utm_term (пусто)
            "",  # segment (пусто)
        ]

        result = get_user_input()

        assert result is not None
        assert result["bot_username"] == "test_bot"
        assert result["utm_source"] == "vk"
        assert result["utm_medium"] == ""
        assert result["utm_campaign"] == "summer2025"
        assert result["utm_content"] == ""
        assert result["utm_term"] == ""
        assert result["segment"] == ""

    @patch("builtins.input")
    def test_get_user_input_no_bot_username(self, mock_input):
        """Тест когда не указан username бота"""
        mock_input.return_value = ""  # Пустой username

        result = get_user_input()

        assert result is None

    @patch("builtins.input")
    def test_get_user_input_stripped(self, mock_input):
        """Тест что пробелы обрезаются"""
        mock_input.side_effect = [
            "  test_bot  ",  # bot_username с пробелами
            "  vk  ",  # utm_source с пробелами
            "summer2025",
            "",
            "",
            "",
            "",
        ]

        result = get_user_input()

        assert result is not None
        assert result["bot_username"] == "test_bot"
        assert result["utm_source"] == "vk"


class TestMain:
    """Тесты для функции main"""

    @patch("smart_bot_factory.utm_link_generator.generate_telegram_link")
    @patch("smart_bot_factory.utm_link_generator.check_size_and_validate")
    @patch("smart_bot_factory.utm_link_generator.create_utm_string")
    @patch("smart_bot_factory.utm_link_generator.get_user_input")
    @patch("builtins.print")
    def test_main_success(self, mock_print, mock_get_input, mock_create_utm, mock_check_size, mock_generate_link):
        """Тест успешного выполнения main"""
        mock_get_input.return_value = {
            "bot_username": "test_bot",
            "utm_source": "vk",
            "utm_campaign": "summer2025",
        }
        mock_create_utm.return_value = "source-vk_campaign-summer2025"
        mock_check_size.return_value = (True, "Размер OK: 30 символов")
        mock_generate_link.return_value = "https://t.me/test_bot?start=source-vk_campaign-summer2025"

        main()

        mock_get_input.assert_called_once()
        mock_create_utm.assert_called_once()
        mock_check_size.assert_called_once()
        mock_generate_link.assert_called_once()
        assert any("Сгенерированная ссылка" in str(call) for call in mock_print.call_args_list)

    @patch("smart_bot_factory.utm_link_generator.get_user_input")
    @patch("builtins.print")
    def test_main_no_input(self, mock_print, mock_get_input):
        """Тест когда пользователь не ввел данные"""
        mock_get_input.return_value = None

        main()

        mock_get_input.assert_called_once()
        # Не должно быть вызовов генерации ссылки

    @patch("smart_bot_factory.utm_link_generator.create_utm_string")
    @patch("smart_bot_factory.utm_link_generator.get_user_input")
    @patch("builtins.print")
    def test_main_empty_utm(self, mock_print, mock_get_input, mock_create_utm):
        """Тест когда UTM строка пустая"""
        mock_get_input.return_value = {
            "bot_username": "test_bot",
        }
        mock_create_utm.return_value = ""

        main()

        assert any("Не указано ни одной UTM-метки" in str(call) for call in mock_print.call_args_list)

    @patch("smart_bot_factory.utm_link_generator.check_size_and_validate")
    @patch("smart_bot_factory.utm_link_generator.create_utm_string")
    @patch("smart_bot_factory.utm_link_generator.get_user_input")
    @patch("builtins.print")
    def test_main_too_large(self, mock_print, mock_get_input, mock_create_utm, mock_check_size):
        """Тест когда UTM строка слишком большая"""
        mock_get_input.return_value = {
            "bot_username": "test_bot",
            "utm_source": "vk",
        }
        mock_create_utm.return_value = "a" * 65
        mock_check_size.return_value = (False, "Строка слишком большая: 65 символов (максимум 64)")

        main()

        assert any("превышает максимальный размер" in str(call) for call in mock_print.call_args_list)

    @patch("smart_bot_factory.utm_link_generator.get_user_input")
    def test_main_keyboard_interrupt(self, mock_get_input):
        """Тест обработки KeyboardInterrupt"""
        mock_get_input.side_effect = KeyboardInterrupt()

        with patch("builtins.print") as mock_print:
            main()

            assert any("Отменено пользователем" in str(call) for call in mock_print.call_args_list)

    @patch("smart_bot_factory.utm_link_generator.get_user_input")
    def test_main_exception(self, mock_get_input):
        """Тест обработки исключений"""
        mock_get_input.side_effect = Exception("Test error")

        with patch("builtins.print") as mock_print:
            main()

            assert any("Ошибка" in str(call) for call in mock_print.call_args_list)
            assert any("Test error" in str(call) for call in mock_print.call_args_list)
