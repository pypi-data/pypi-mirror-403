"""Тесты для search_sitemap"""

from unittest.mock import patch

import pytest

from smart_bot_factory.site_parser.sitemap import search_sitemap


class TestSearchSitemap:
    """Тесты для функции search_sitemap"""

    @patch("smart_bot_factory.site_parser.sitemap.sitemaps")
    def test_search_sitemap_basic(self, mock_sitemaps):
        """Тест базового поиска в sitemap"""
        mock_sitemaps.sitemap_search.return_value = ["https://example.com/page1", "https://example.com/page2", "https://example.com/page3"]

        result = search_sitemap("https://example.com/sitemap.xml")

        assert len(result) == 3
        assert "https://example.com/page1" in result
        mock_sitemaps.sitemap_search.assert_called_once_with("https://example.com/sitemap.xml")

    @patch("smart_bot_factory.site_parser.sitemap.sitemaps")
    def test_search_sitemap_with_regex(self, mock_sitemaps):
        """Тест поиска с фильтрацией по regex"""
        mock_sitemaps.sitemap_search.return_value = [
            "https://example.com/services/page1",
            "https://example.com/blog/post1",
            "https://example.com/services/page2",
        ]

        result = search_sitemap("https://example.com/sitemap.xml", regex=r"https://example\.com/services/.*")

        assert len(result) == 2
        assert "https://example.com/services/page1" in result
        assert "https://example.com/services/page2" in result
        assert "https://example.com/blog/post1" not in result

    @patch("smart_bot_factory.site_parser.sitemap.sitemaps")
    def test_search_sitemap_with_limit(self, mock_sitemaps):
        """Тест поиска с лимитом"""
        mock_sitemaps.sitemap_search.return_value = [
            "https://example.com/page1",
            "https://example.com/page2",
            "https://example.com/page3",
            "https://example.com/page4",
            "https://example.com/page5",
        ]

        result = search_sitemap("https://example.com/sitemap.xml", limit=3)

        assert len(result) == 3
        assert result == ["https://example.com/page1", "https://example.com/page2", "https://example.com/page3"]

    @patch("smart_bot_factory.site_parser.sitemap.sitemaps")
    def test_search_sitemap_with_regex_and_limit(self, mock_sitemaps):
        """Тест поиска с regex и лимитом"""
        mock_sitemaps.sitemap_search.return_value = [
            "https://example.com/services/page1",
            "https://example.com/services/page2",
            "https://example.com/services/page3",
            "https://example.com/services/page4",
        ]

        result = search_sitemap("https://example.com/sitemap.xml", regex=r"https://example\.com/services/.*", limit=2)

        assert len(result) == 2
        assert result == ["https://example.com/services/page1", "https://example.com/services/page2"]

    @patch("smart_bot_factory.site_parser.sitemap.sitemaps")
    def test_search_sitemap_empty_result(self, mock_sitemaps):
        """Тест поиска с пустым результатом"""
        mock_sitemaps.sitemap_search.return_value = []

        result = search_sitemap("https://example.com/sitemap.xml")

        assert len(result) == 0
        assert result == []

    @patch("smart_bot_factory.site_parser.sitemap.sitemaps")
    def test_search_sitemap_limit_zero(self, mock_sitemaps):
        """Тест поиска с лимитом 0 (не применяется, так как limit > 0)"""
        mock_sitemaps.sitemap_search.return_value = ["https://example.com/page1", "https://example.com/page2"]

        result = search_sitemap("https://example.com/sitemap.xml", limit=0)

        # Лимит 0 не применяется, так как проверка limit > 0
        assert len(result) == 2

    @patch("smart_bot_factory.site_parser.sitemap.sitemaps")
    def test_search_sitemap_limit_none(self, mock_sitemaps):
        """Тест поиска с limit=None"""
        mock_sitemaps.sitemap_search.return_value = ["https://example.com/page1", "https://example.com/page2"]

        result = search_sitemap("https://example.com/sitemap.xml", limit=None)

        assert len(result) == 2

    def test_search_sitemap_empty_url(self):
        """Тест ошибки при пустом URL"""
        with pytest.raises(ValueError, match="Не указан URL"):
            search_sitemap("")

    def test_search_sitemap_none_url(self):
        """Тест ошибки при None URL"""
        with pytest.raises(ValueError, match="Не указан URL"):
            search_sitemap(None)

    @patch("smart_bot_factory.site_parser.sitemap.sitemaps")
    def test_search_sitemap_regex_no_matches(self, mock_sitemaps):
        """Тест поиска с regex без совпадений"""
        mock_sitemaps.sitemap_search.return_value = ["https://example.com/page1", "https://example.com/page2"]

        result = search_sitemap("https://example.com/sitemap.xml", regex=r"https://other\.com/.*")

        assert len(result) == 0

    @patch("smart_bot_factory.site_parser.sitemap.sitemaps")
    def test_search_sitemap_limit_greater_than_results(self, mock_sitemaps):
        """Тест лимита больше количества результатов"""
        mock_sitemaps.sitemap_search.return_value = ["https://example.com/page1", "https://example.com/page2"]

        result = search_sitemap("https://example.com/sitemap.xml", limit=10)

        assert len(result) == 2
