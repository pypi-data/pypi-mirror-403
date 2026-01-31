"""Тесты для модуля bot_utils"""

from smart_bot_factory.utils.bot_utils import (
    _get_media_type,
    _is_bot_blocked_error,
    _validate_text,
    parse_utm_from_start_param,
)


class TestParseUtmFromStartParam:
    """Тесты для функции parse_utm_from_start_param"""

    def test_parse_utm_simple(self):
        """Тест парсинга простых UTM параметров"""
        result = parse_utm_from_start_param("source-vk_campaign-summer2025_seg-premium")
        assert result["utm_source"] == "vk"
        assert result["utm_campaign"] == "summer2025"
        assert result["segment"] == "premium"

    def test_parse_utm_from_url(self):
        """Тест парсинга UTM из полной ссылки"""
        url = "https://t.me/bot?start=source-vk_campaign-summer2025_seg-vip"
        result = parse_utm_from_start_param(url)
        assert result["utm_source"] == "vk"
        assert result["utm_campaign"] == "summer2025"
        assert result["segment"] == "vip"

    def test_parse_utm_empty(self):
        """Тест парсинга пустой строки"""
        result = parse_utm_from_start_param("")
        assert result == {}

    def test_parse_utm_only_segment(self):
        """Тест парсинга только сегмента"""
        result = parse_utm_from_start_param("seg-premium")
        assert result["segment"] == "premium"
        assert "utm_source" not in result

    def test_parse_utm_multiple_params(self):
        """Тест парсинга множественных параметров"""
        result = parse_utm_from_start_param("source-vk_medium-web_campaign-test_seg-premium")
        assert result["utm_source"] == "vk"
        assert result["utm_medium"] == "web"
        assert result["utm_campaign"] == "test"
        assert result["segment"] == "premium"


class TestGetMediaType:
    """Тесты для функции _get_media_type"""

    def test_get_media_type_photo(self):
        """Тест определения типа фото"""

        assert _get_media_type("test.jpg") == "photo"
        assert _get_media_type("test.png") == "photo"
        assert _get_media_type("test.webp") == "photo"

    def test_get_media_type_video(self):
        """Тест определения типа видео"""

        assert _get_media_type("test.mp4") == "video"
        assert _get_media_type("test.mov") == "video"
        assert _get_media_type("test.avi") == "video"

    def test_get_media_type_document(self):
        """Тест определения типа документа"""

        assert _get_media_type("test.pdf") == "document"
        assert _get_media_type("test.txt") == "document"
        assert _get_media_type("test.doc") == "document"


class TestValidateText:
    """Тесты для функции _validate_text"""

    def test_validate_text_valid(self):
        """Тест валидации валидного текста"""

        text = "Valid text"
        result = _validate_text(text)
        assert result == text

    def test_validate_text_empty(self):
        """Тест валидации пустого текста"""

        result = _validate_text("")
        assert "Ошибка формирования ответа" in result

    def test_validate_text_whitespace(self):
        """Тест валидации текста только с пробелами"""

        result = _validate_text("   ")
        assert "Ошибка формирования ответа" in result


class TestIsBotBlockedError:
    """Тесты для функции _is_bot_blocked_error"""

    def test_is_bot_blocked_error_true(self):
        """Тест определения блокировки бота"""

        error = Exception("Forbidden: bot was blocked by the user")
        assert _is_bot_blocked_error(error) is True

    def test_is_bot_blocked_error_false(self):
        """Тест определения не-блокировки"""

        error = Exception("Some other error")
        assert _is_bot_blocked_error(error) is False
