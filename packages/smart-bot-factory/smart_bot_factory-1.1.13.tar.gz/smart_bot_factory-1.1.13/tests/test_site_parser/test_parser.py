"""Тесты для SiteParser"""

from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from smart_bot_factory.site_parser.parser import SiteParser


class TestSiteParser:
    """Тесты для класса SiteParser"""

    @pytest.fixture
    def mock_env_file(self, tmp_path, monkeypatch):
        """Фикстура для создания мок .env файла"""
        bot_dir = tmp_path / "bots" / "test-bot"
        bot_dir.mkdir(parents=True)
        env_file = bot_dir / ".env"
        env_file.write_text("OPENAI_API_KEY=test_openai_key\n")
        return env_file

    @pytest.fixture
    def mock_openai_api_key(self, monkeypatch):
        """Фикстура для установки OPENAI_API_KEY в окружении"""
        monkeypatch.setenv("OPENAI_API_KEY", "test_openai_key")

    @patch("smart_bot_factory.site_parser.parser.ChatOpenAI")
    @patch("smart_bot_factory.site_parser.parser.root")
    def test_siteparser_initialization_without_bot_id(self, mock_root, mock_chat_openai, mock_openai_api_key, tmp_path):
        """Тест инициализации SiteParser без bot_id"""
        mock_root.__truediv__ = lambda self, other: tmp_path / other
        mock_root.__str__ = lambda self: str(tmp_path)

        mock_model = Mock()
        mock_chain = Mock()
        mock_model.__or__ = Mock(return_value=mock_chain)
        mock_chat_openai.return_value = mock_model

        parser = SiteParser()

        assert parser.bot_id is None
        assert parser.api_key == "test_openai_key"
        assert parser.additional_instructions is None

    @patch("smart_bot_factory.site_parser.parser.ChatOpenAI")
    @patch("smart_bot_factory.site_parser.parser.root")
    def test_siteparser_initialization_with_bot_id(self, mock_root, mock_chat_openai, mock_env_file, tmp_path):
        """Тест инициализации SiteParser с bot_id"""
        mock_root.__truediv__ = lambda self, other: tmp_path / other
        mock_root.__str__ = lambda self: str(tmp_path)

        mock_model = Mock()
        mock_chain = Mock()
        mock_model.__or__ = Mock(return_value=mock_chain)
        mock_chat_openai.return_value = mock_model

        parser = SiteParser(bot_id="test-bot")

        assert parser.bot_id == "test-bot"
        assert parser.api_key == "test_openai_key"

    @patch("smart_bot_factory.site_parser.parser.ChatOpenAI")
    @patch("smart_bot_factory.site_parser.parser.root")
    def test_siteparser_initialization_with_additional_instructions(self, mock_root, mock_chat_openai, mock_openai_api_key, tmp_path):
        """Тест инициализации SiteParser с дополнительными инструкциями"""
        mock_root.__truediv__ = lambda self, other: tmp_path / other
        mock_root.__str__ = lambda self: str(tmp_path)

        mock_model = Mock()
        mock_chain = Mock()
        mock_model.__or__ = Mock(return_value=mock_chain)
        mock_chat_openai.return_value = mock_model

        parser = SiteParser(additional_instructions="Тестовые инструкции")

        assert parser.additional_instructions == "Тестовые инструкции"

    @patch("smart_bot_factory.site_parser.parser.ChatOpenAI")
    @patch("smart_bot_factory.site_parser.parser.root")
    def test_siteparser_load_api_key_from_bot_env(self, mock_root, mock_chat_openai, mock_env_file, tmp_path):
        """Тест загрузки API ключа из .env файла бота"""
        mock_root.__truediv__ = lambda self, other: tmp_path / other
        mock_root.__str__ = lambda self: str(tmp_path)

        mock_model = Mock()
        mock_chain = Mock()
        mock_model.__or__ = Mock(return_value=mock_chain)
        mock_chat_openai.return_value = mock_model

        parser = SiteParser(bot_id="test-bot")

        assert parser.api_key == "test_openai_key"

    @patch("smart_bot_factory.site_parser.parser.ChatOpenAI")
    @patch("smart_bot_factory.site_parser.parser.root")
    def test_siteparser_load_api_key_fails(self, mock_root, mock_chat_openai, tmp_path):
        """Тест ошибки при отсутствии API ключа"""
        mock_root.__truediv__ = lambda self, other: tmp_path / other
        mock_root.__str__ = lambda self: str(tmp_path)

        with patch("smart_bot_factory.site_parser.parser.os.getenv", return_value=None):
            with pytest.raises(ValueError, match="OPENAI_API_KEY не найден"):
                SiteParser()

    @patch("smart_bot_factory.site_parser.parser.fetch_url")
    @patch("smart_bot_factory.site_parser.parser.html2txt")
    def test_siteparser_text_from_site_success(self, mock_html2txt, mock_fetch_url):
        """Тест успешного извлечения текста с сайта"""
        mock_fetch_url.return_value = "<html><body>Test</body></html>"
        mock_html2txt.return_value = "Test text"

        parser = SiteParser.__new__(SiteParser)
        text = parser._text_from_site("https://example.com")

        assert text == "Test text"
        mock_fetch_url.assert_called_once_with("https://example.com")
        mock_html2txt.assert_called_once()

    @patch("smart_bot_factory.site_parser.parser.fetch_url")
    def test_siteparser_text_from_site_empty_html(self, mock_fetch_url):
        """Тест обработки пустого HTML"""
        mock_fetch_url.return_value = None

        parser = SiteParser.__new__(SiteParser)
        text = parser._text_from_site("https://example.com")

        assert text == ""

    @patch("smart_bot_factory.site_parser.parser.fetch_url")
    @patch("smart_bot_factory.site_parser.parser.html2txt")
    def test_siteparser_text_from_site_empty_text(self, mock_html2txt, mock_fetch_url):
        """Тест обработки пустого текста"""
        mock_fetch_url.return_value = "<html><body>Test</body></html>"
        mock_html2txt.return_value = None

        parser = SiteParser.__new__(SiteParser)
        text = parser._text_from_site("https://example.com")

        assert text == ""

    @patch("smart_bot_factory.site_parser.parser.fetch_url")
    def test_siteparser_text_from_site_exception(self, mock_fetch_url):
        """Тест обработки исключения при парсинге"""
        mock_fetch_url.side_effect = Exception("Network error")

        parser = SiteParser.__new__(SiteParser)
        text = parser._text_from_site("https://example.com")

        assert text == ""

    @pytest.mark.asyncio
    async def test_siteparser_clean_text(self):
        """Тест очистки текста"""
        mock_chain = AsyncMock()
        mock_chain.ainvoke = AsyncMock(return_value="Cleaned text")

        parser = SiteParser.__new__(SiteParser)
        parser.chain = mock_chain
        parser.additional_instructions = None

        result = await parser._clean_text("Raw text")

        assert result == "Cleaned text"
        mock_chain.ainvoke.assert_called_once()

    @pytest.mark.asyncio
    async def test_siteparser_clean_text_with_additional_instructions(self):
        """Тест очистки текста с дополнительными инструкциями"""
        mock_chain = AsyncMock()
        mock_chain.ainvoke = AsyncMock(return_value="Cleaned text")

        parser = SiteParser.__new__(SiteParser)
        parser.chain = mock_chain
        parser.additional_instructions = "Custom instructions"

        result = await parser._clean_text("Raw text")

        assert result == "Cleaned text"
        call_args = mock_chain.ainvoke.call_args[0][0]
        assert call_args["additional_instructions"] == "Custom instructions"

    def test_siteparser_build_filename_from_url(self):
        """Тест построения имени файла из URL"""
        parser = SiteParser.__new__(SiteParser)

        filename = parser._build_filename_from_url("https://example.com/page")
        assert filename == "page"

        filename = parser._build_filename_from_url("https://example.com/services/consultation")
        assert filename == "consultation"

        filename = parser._build_filename_from_url("https://example.com/")
        assert filename == "index"

    @pytest.mark.asyncio
    @patch("smart_bot_factory.site_parser.parser.fetch_url")
    @patch("smart_bot_factory.site_parser.parser.html2txt")
    @patch("smart_bot_factory.site_parser.parser.ChatOpenAI")
    @patch("smart_bot_factory.site_parser.parser.root")
    async def test_siteparser_parser_single_url(self, mock_root, mock_chat_openai, mock_html2txt, mock_fetch_url, mock_openai_api_key, tmp_path):
        """Тест парсинга одного URL"""
        mock_root.__truediv__ = lambda self, other: tmp_path / other
        mock_root.__str__ = lambda self: str(tmp_path)

        # Мокируем внешние зависимости
        mock_fetch_url.return_value = "<html><body>Test</body></html>"
        mock_html2txt.return_value = "Raw text"

        # Правильно мокируем цепочку LangChain
        mock_model = Mock()
        mock_output_parser = Mock()
        mock_chain = Mock()
        mock_chain.ainvoke = AsyncMock(return_value="Cleaned text")
        # Мокируем оператор | для создания цепочки: prompt | model | parser
        mock_model.__or__ = Mock(return_value=mock_output_parser)
        mock_output_parser.__or__ = Mock(return_value=mock_chain)
        mock_chat_openai.return_value = mock_model

        parser = SiteParser()

        # Заменяем chain на мок, чтобы избежать проблем с валидацией
        parser.chain = mock_chain

        # Теперь _text_from_site и _clean_text работают реально
        result = await parser.parser("https://example.com")

        assert result == "Cleaned text"
        mock_fetch_url.assert_called_once_with("https://example.com")
        mock_html2txt.assert_called_once()
        mock_chain.ainvoke.assert_called_once()

    @pytest.mark.asyncio
    @patch("smart_bot_factory.site_parser.parser.fetch_url")
    @patch("smart_bot_factory.site_parser.parser.html2txt")
    @patch("smart_bot_factory.site_parser.parser.ChatOpenAI")
    @patch("smart_bot_factory.site_parser.parser.root")
    async def test_siteparser_parser_multiple_urls(self, mock_root, mock_chat_openai, mock_html2txt, mock_fetch_url, mock_openai_api_key, tmp_path):
        """Тест парсинга нескольких URL"""
        mock_root.__truediv__ = lambda self, other: tmp_path / other
        mock_root.__str__ = lambda self: str(tmp_path)

        # Мокируем внешние зависимости
        mock_fetch_url.return_value = "<html><body>Test</body></html>"
        mock_html2txt.return_value = "Raw text"

        # Правильно мокируем цепочку LangChain
        mock_model = Mock()
        mock_output_parser = Mock()
        mock_chain = Mock()
        mock_chain.ainvoke = AsyncMock(return_value="Cleaned text")
        mock_model.__or__ = Mock(return_value=mock_output_parser)
        mock_output_parser.__or__ = Mock(return_value=mock_chain)
        mock_chat_openai.return_value = mock_model

        parser = SiteParser()
        parser.chain = mock_chain

        # Теперь _text_from_site и _clean_text работают реально
        result = await parser.parser(["https://example.com/page1", "https://example.com/page2"])

        assert isinstance(result, str)
        assert "Cleaned text" in result
        assert mock_fetch_url.call_count == 2
        assert mock_chain.ainvoke.call_count == 2

    @pytest.mark.asyncio
    @patch("smart_bot_factory.site_parser.parser.ChatOpenAI")
    @patch("smart_bot_factory.site_parser.parser.root")
    async def test_siteparser_parser_empty_urls(self, mock_root, mock_chat_openai, mock_openai_api_key, tmp_path):
        """Тест парсинга пустого списка URL"""
        mock_root.__truediv__ = lambda self, other: tmp_path / other
        mock_root.__str__ = lambda self: str(tmp_path)

        mock_model = Mock()
        mock_chain = Mock()
        mock_model.__or__ = Mock(return_value=mock_chain)
        mock_chat_openai.return_value = mock_model

        parser = SiteParser()

        result = await parser.parser([])

        assert result == ""

    @pytest.mark.asyncio
    @patch("smart_bot_factory.site_parser.parser.fetch_url")
    @patch("smart_bot_factory.site_parser.parser.html2txt")
    @patch("smart_bot_factory.site_parser.parser.ChatOpenAI")
    @patch("smart_bot_factory.site_parser.parser.root")
    async def test_siteparser_parser_to_files(self, mock_root, mock_chat_openai, mock_html2txt, mock_fetch_url, mock_openai_api_key, tmp_path):
        """Тест парсинга с сохранением в файлы"""
        mock_root.__truediv__ = lambda self, other: tmp_path / other
        mock_root.__str__ = lambda self: str(tmp_path)

        # Мокируем внешние зависимости
        mock_fetch_url.return_value = "<html><body>Test</body></html>"
        mock_html2txt.return_value = "Raw text"

        # Правильно мокируем цепочку LangChain
        mock_model = Mock()
        mock_output_parser = Mock()
        mock_chain = Mock()
        mock_chain.ainvoke = AsyncMock(return_value="Cleaned text")
        mock_model.__or__ = Mock(return_value=mock_output_parser)
        mock_output_parser.__or__ = Mock(return_value=mock_chain)
        mock_chat_openai.return_value = mock_model

        parser = SiteParser(bot_id="test-bot")
        parser.chain = mock_chain

        # Теперь _text_from_site и _clean_text работают реально
        result = await parser.parser("https://example.com/page", to_files=True)

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], Path)
        mock_fetch_url.assert_called_once_with("https://example.com/page")
        mock_chain.ainvoke.assert_called_once()

    @pytest.mark.asyncio
    @patch("smart_bot_factory.site_parser.parser.fetch_url")
    @patch("smart_bot_factory.site_parser.parser.html2txt")
    @patch("smart_bot_factory.site_parser.parser.ChatOpenAI")
    @patch("smart_bot_factory.site_parser.parser.root")
    async def test_siteparser_parser_to_files_no_bot_id(
        self, mock_root, mock_chat_openai, mock_html2txt, mock_fetch_url, mock_openai_api_key, tmp_path
    ):
        """Тест ошибки при сохранении в файлы без bot_id"""
        mock_root.__truediv__ = lambda self, other: tmp_path / other
        mock_root.__str__ = lambda self: str(tmp_path)

        # Мокируем внешние зависимости
        mock_fetch_url.return_value = "<html><body>Test</body></html>"
        mock_html2txt.return_value = "Raw text"

        # Правильно мокируем цепочку LangChain
        mock_model = Mock()
        mock_output_parser = Mock()
        mock_chain = Mock()
        mock_chain.ainvoke = AsyncMock(return_value="Cleaned text")
        mock_model.__or__ = Mock(return_value=mock_output_parser)
        mock_output_parser.__or__ = Mock(return_value=mock_chain)
        mock_chat_openai.return_value = mock_model

        parser = SiteParser()
        parser.chain = mock_chain

        # Теперь _text_from_site работает реально, но ошибка должна возникнуть при сохранении
        with pytest.raises(ValueError):
            await parser.parser("https://example.com", to_files=True)

    @pytest.mark.asyncio
    @patch("smart_bot_factory.site_parser.parser.fetch_url")
    @patch("smart_bot_factory.site_parser.parser.html2txt")
    @patch("smart_bot_factory.site_parser.parser.ChatOpenAI")
    @patch("smart_bot_factory.site_parser.parser.root")
    async def test_siteparser_parser_max_workers(self, mock_root, mock_chat_openai, mock_html2txt, mock_fetch_url, mock_openai_api_key, tmp_path):
        """Тест парсинга с ограничением количества воркеров"""
        mock_root.__truediv__ = lambda self, other: tmp_path / other
        mock_root.__str__ = lambda self: str(tmp_path)

        # Мокируем внешние зависимости
        mock_fetch_url.return_value = "<html><body>Test</body></html>"
        mock_html2txt.return_value = "Raw text"

        # Правильно мокируем цепочку LangChain
        mock_model = Mock()
        mock_output_parser = Mock()
        mock_chain = Mock()
        mock_chain.ainvoke = AsyncMock(return_value="Cleaned text")
        mock_model.__or__ = Mock(return_value=mock_output_parser)
        mock_output_parser.__or__ = Mock(return_value=mock_chain)
        mock_chat_openai.return_value = mock_model

        parser = SiteParser()
        parser.chain = mock_chain

        # Теперь _text_from_site и _clean_text работают реально
        result = await parser.parser(["https://example.com/page1", "https://example.com/page2"], max_workers=1)

        assert isinstance(result, str)
        assert mock_fetch_url.call_count == 2
        assert mock_chain.ainvoke.call_count == 2

    @pytest.mark.asyncio
    @patch("smart_bot_factory.site_parser.parser.fetch_url")
    @patch("smart_bot_factory.site_parser.parser.html2txt")
    @patch("smart_bot_factory.site_parser.parser.ChatOpenAI")
    @patch("smart_bot_factory.site_parser.parser.root")
    async def test_siteparser_parser_failed_urls(self, mock_root, mock_chat_openai, mock_html2txt, mock_fetch_url, mock_openai_api_key, tmp_path):
        """Тест обработки неудачных URL"""
        mock_root.__truediv__ = lambda self, other: tmp_path / other
        mock_root.__str__ = lambda self: str(tmp_path)

        # Мокируем внешние зависимости для возврата пустого результата
        mock_fetch_url.return_value = None  # Или можно вернуть пустой HTML
        mock_html2txt.return_value = None

        # Правильно мокируем цепочку LangChain
        mock_model = Mock()
        mock_output_parser = Mock()
        mock_chain = Mock()
        mock_chain.ainvoke = AsyncMock(return_value="Cleaned text")
        mock_model.__or__ = Mock(return_value=mock_output_parser)
        mock_output_parser.__or__ = Mock(return_value=mock_chain)
        mock_chat_openai.return_value = mock_model

        parser = SiteParser()
        parser.chain = mock_chain

        # Теперь _text_from_site работает реально и вернет пустую строку при ошибке
        result = await parser.parser("https://example.com")

        assert result == ""
        mock_fetch_url.assert_called_once_with("https://example.com")
        # _clean_text не должен вызываться, так как _text_from_site вернул пустую строку
        mock_chain.ainvoke.assert_not_called()
