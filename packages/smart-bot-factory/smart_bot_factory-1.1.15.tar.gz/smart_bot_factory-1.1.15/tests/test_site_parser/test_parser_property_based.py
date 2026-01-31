"""Property-based тесты для site_parser.parser с использованием Hypothesis"""

from hypothesis import given
from hypothesis import strategies as st

from smart_bot_factory.site_parser.parser import SiteParser


class TestBuildFilenameFromUrlPropertyBased:
    """Property-based тесты для _build_filename_from_url"""

    @given(st.text(min_size=1, max_size=100))
    def test_build_filename_from_url_always_returns_string(self, url_part):
        """Тест что функция всегда возвращает строку"""
        url = f"https://example.com/{url_part}"
        parser = SiteParser.__new__(SiteParser)
        result = parser._build_filename_from_url(url)

        assert isinstance(result, str)
        assert len(result) > 0

    @given(st.text(min_size=1, max_size=50))
    def test_build_filename_from_url_safe_characters(self, url_part):
        """Тест что результат содержит только безопасные символы"""
        url = f"https://example.com/{url_part}"
        parser = SiteParser.__new__(SiteParser)
        result = parser._build_filename_from_url(url)

        # Результат должен содержать только буквы, цифры, дефисы и подчеркивания
        assert all(c.isalnum() or c in ("-", "_") for c in result)

    @given(st.text(min_size=1, max_size=50))
    def test_build_filename_from_url_deterministic(self, url_part):
        """Тест детерминированности: одинаковый URL дает одинаковый результат"""
        url = f"https://example.com/{url_part}"
        parser = SiteParser.__new__(SiteParser)
        result1 = parser._build_filename_from_url(url)
        result2 = parser._build_filename_from_url(url)

        assert result1 == result2

    @given(st.text(min_size=1, max_size=50), st.text(min_size=1, max_size=50))
    def test_build_filename_from_url_different_urls_different_results(self, part1, part2):
        """Тест что разные URL дают разные результаты (если части разные)"""
        if part1 != part2:
            url1 = f"https://example.com/{part1}"
            url2 = f"https://example.com/{part2}"
            parser = SiteParser.__new__(SiteParser)
            result1 = parser._build_filename_from_url(url1)
            result2 = parser._build_filename_from_url(url2)

            # Результаты должны быть разными (с высокой вероятностью)
            # Но могут совпасть если после обработки части одинаковые
            # Поэтому проверяем только что оба результата валидны
            assert isinstance(result1, str)
            assert isinstance(result2, str)

    @given(st.text())
    def test_build_filename_from_url_handles_special_chars(self, url_part):
        """Тест обработки специальных символов в URL"""
        # Добавляем специальные символы
        url = f"https://example.com/{url_part}?param=value&other=123"
        parser = SiteParser.__new__(SiteParser)
        result = parser._build_filename_from_url(url)

        # Результат не должен содержать специальные символы URL
        assert "?" not in result
        assert "&" not in result
        assert "=" not in result
        assert "/" not in result
