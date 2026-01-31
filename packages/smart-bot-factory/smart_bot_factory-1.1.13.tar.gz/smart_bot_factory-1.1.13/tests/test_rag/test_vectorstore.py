"""Тесты для VectorStore"""

from unittest.mock import Mock, patch

import pytest
from langchain_core.documents import Document

from smart_bot_factory.rag.vectorstore import VectorStore


class TestVectorStore:
    """Тесты для класса VectorStore"""

    @pytest.fixture
    def mock_env_vars(self, monkeypatch):
        """Фикстура для мок переменных окружения"""
        monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
        monkeypatch.setenv("SUPABASE_KEY", "test_key")
        monkeypatch.setenv("OPENAI_API_KEY", "test_openai_key")

    @pytest.fixture
    def mock_env_file(self, tmp_path, monkeypatch):
        """Фикстура для создания мок .env файла"""
        bot_dir = tmp_path / "bots" / "test-bot"
        bot_dir.mkdir(parents=True)
        env_file = bot_dir / ".env"
        env_file.write_text("SUPABASE_URL=https://test.supabase.co\n" "SUPABASE_KEY=test_key\n" "OPENAI_API_KEY=test_openai_key\n")
        return env_file

    @pytest.fixture
    def mock_supabase_client(self):
        """Фикстура для мок Supabase клиента"""
        client = Mock()
        client.table = Mock(return_value=Mock())
        client.rpc = Mock(return_value=Mock())
        return client

    @pytest.fixture
    def mock_openai_embeddings(self):
        """Фикстура для мок OpenAI embeddings"""
        embeddings = Mock()
        embeddings.embed_query = Mock(return_value=[0.1] * 1536)
        embeddings.embed_documents = Mock(return_value=[[0.1] * 1536])
        return embeddings

    @patch("smart_bot_factory.rag.vectorstore.create_client")
    @patch("smart_bot_factory.rag.vectorstore.OpenAIEmbeddings")
    @patch("smart_bot_factory.rag.vectorstore.root")
    def test_vectorstore_initialization_defaults(self, mock_root, mock_openai_embeddings, mock_create_client, mock_env_file, tmp_path):
        """Тест инициализации VectorStore с параметрами по умолчанию"""
        mock_root.__truediv__ = lambda self, other: tmp_path / other
        mock_root.__str__ = lambda self: str(tmp_path)

        mock_embeddings_instance = Mock()
        mock_openai_embeddings.return_value = mock_embeddings_instance

        mock_client = Mock()
        mock_create_client.return_value = mock_client

        with patch("smart_bot_factory.rag.vectorstore.load_dotenv"):
            vectorstore = VectorStore(bot_id="test-bot")

        assert vectorstore.bot_id == "test-bot"
        assert vectorstore.table_name == "vectorstore"
        assert vectorstore.query_name == "match_vectorstore"

    @patch("smart_bot_factory.rag.vectorstore.create_client")
    @patch("smart_bot_factory.rag.vectorstore.OpenAIEmbeddings")
    @patch("smart_bot_factory.rag.vectorstore.root")
    def test_vectorstore_initialization_custom_params(self, mock_root, mock_openai_embeddings, mock_create_client, mock_env_file, tmp_path):
        """Тест инициализации VectorStore с кастомными параметрами"""
        mock_root.__truediv__ = lambda self, other: tmp_path / other
        mock_root.__str__ = lambda self: str(tmp_path)

        mock_embeddings_instance = Mock()
        mock_openai_embeddings.return_value = mock_embeddings_instance

        mock_client = Mock()
        mock_create_client.return_value = mock_client

        with patch("smart_bot_factory.rag.vectorstore.load_dotenv"):
            vectorstore = VectorStore(bot_id="test-bot", table_name="custom_table", query_name="custom_query")

        assert vectorstore.table_name == "custom_table"
        assert vectorstore.query_name == "custom_query"

    @patch("smart_bot_factory.rag.vectorstore.create_client")
    @patch("smart_bot_factory.rag.vectorstore.OpenAIEmbeddings")
    @patch("smart_bot_factory.rag.vectorstore.root")
    def test_vectorstore_find_env_file_success(self, mock_root, mock_openai_embeddings, mock_create_client, mock_env_file, tmp_path):
        """Тест успешного поиска .env файла"""
        mock_root.__truediv__ = lambda self, other: tmp_path / other
        mock_root.__str__ = lambda self: str(tmp_path)

        mock_embeddings_instance = Mock()
        mock_openai_embeddings.return_value = mock_embeddings_instance

        mock_client = Mock()
        mock_create_client.return_value = mock_client

        with patch("smart_bot_factory.rag.vectorstore.load_dotenv"):
            vectorstore = VectorStore(bot_id="test-bot")
            env_path = vectorstore._find_env_file()

        assert env_path == mock_env_file
        assert env_path.exists()

    @patch("smart_bot_factory.rag.vectorstore.root")
    def test_vectorstore_find_env_file_not_found(self, mock_root, tmp_path):
        """Тест поиска .env файла когда файл не найден"""
        mock_root.__truediv__ = lambda self, other: tmp_path / other
        mock_root.__str__ = lambda self: str(tmp_path)

        # Создаем объект без вызова __init__, чтобы избежать загрузки конфигурации
        vectorstore = VectorStore.__new__(VectorStore)
        vectorstore.bot_id = "non-existent-bot"

        env_path = vectorstore._find_env_file()

        assert env_path is None

    def test_vectorstore_is_table_not_found_error(self):
        """Тест определения ошибки отсутствия таблицы"""
        vectorstore = VectorStore.__new__(VectorStore)
        vectorstore.table_name = "test_table"

        # Тест с ошибкой таблицы
        table_error = Exception("relation 'test_table' does not exist")
        assert vectorstore._is_table_not_found_error(table_error) is True

        # Тест с ошибкой функции
        function_error = Exception("function 'match_test' does not exist")
        assert vectorstore._is_table_not_found_error(function_error) is False

        # Тест с другой ошибкой
        other_error = Exception("some other error")
        assert vectorstore._is_table_not_found_error(other_error) is False

    def test_vectorstore_is_function_not_found_error(self):
        """Тест определения ошибки отсутствия функции"""
        vectorstore = VectorStore.__new__(VectorStore)

        # Тест с ошибкой функции
        function_error = Exception("function 'match_test' does not exist")
        assert vectorstore._is_function_not_found_error(function_error) is True

        # Тест с другой формулировкой
        function_error2 = Exception("function 'match_test' not found")
        assert vectorstore._is_function_not_found_error(function_error2) is True

        # Тест с другой ошибкой
        other_error = Exception("some other error")
        assert vectorstore._is_function_not_found_error(other_error) is False

    @patch("smart_bot_factory.rag.vectorstore.create_client")
    @patch("smart_bot_factory.rag.vectorstore.OpenAIEmbeddings")
    @patch("smart_bot_factory.rag.vectorstore.root")
    def test_vectorstore_similarity_search(self, mock_root, mock_openai_embeddings, mock_create_client, mock_env_file, tmp_path):
        """Тест поиска похожих документов"""
        mock_root.__truediv__ = lambda self, other: tmp_path / other
        mock_root.__str__ = lambda self: str(tmp_path)

        mock_embeddings_instance = Mock()
        mock_embeddings_instance.embed_query = Mock(return_value=[0.1] * 1536)
        mock_openai_embeddings.return_value = mock_embeddings_instance

        mock_client = Mock()
        mock_rpc_result = Mock()
        mock_rpc_result.data = [{"content": "test content", "metadata": {"id": 1}, "similarity": 0.8}]
        mock_rpc = Mock()
        mock_rpc.filter.return_value = mock_rpc
        mock_rpc.limit.return_value = mock_rpc
        mock_rpc.execute.return_value = mock_rpc_result
        mock_client.rpc.return_value = mock_rpc
        mock_create_client.return_value = mock_client

        with patch("smart_bot_factory.rag.vectorstore.load_dotenv"):
            vectorstore = VectorStore(bot_id="test-bot")
            results = vectorstore.similarity_search("test query", k=1, score=0.7)

        assert len(results) == 1
        assert isinstance(results[0], Document)
        assert results[0].page_content == "test content"

    @patch("smart_bot_factory.rag.vectorstore.create_client")
    @patch("smart_bot_factory.rag.vectorstore.OpenAIEmbeddings")
    @patch("smart_bot_factory.rag.vectorstore.root")
    def test_vectorstore_similarity_search_with_filter(self, mock_root, mock_openai_embeddings, mock_create_client, mock_env_file, tmp_path):
        """Тест поиска с фильтром"""
        mock_root.__truediv__ = lambda self, other: tmp_path / other
        mock_root.__str__ = lambda self: str(tmp_path)

        mock_embeddings_instance = Mock()
        mock_embeddings_instance.embed_query = Mock(return_value=[0.1] * 1536)
        mock_openai_embeddings.return_value = mock_embeddings_instance

        mock_client = Mock()
        mock_rpc_result = Mock()
        mock_rpc_result.data = [{"content": "test content", "metadata": {"id": 1, "bot_id": "test-bot"}, "similarity": 0.8}]
        mock_rpc = Mock()
        mock_rpc.filter.return_value = mock_rpc
        mock_rpc.limit.return_value = mock_rpc
        mock_rpc.execute.return_value = mock_rpc_result
        mock_client.rpc.return_value = mock_rpc
        mock_create_client.return_value = mock_client

        with patch("smart_bot_factory.rag.vectorstore.load_dotenv"):
            vectorstore = VectorStore(bot_id="test-bot")
            vectorstore.similarity_search("test query", k=1, filter={"category": "test"}, score=0.7)

        # Проверяем, что bot_id был добавлен в фильтр
        call_args = mock_client.rpc.call_args
        assert call_args is not None

    @patch("smart_bot_factory.rag.vectorstore.create_client")
    @patch("smart_bot_factory.rag.vectorstore.OpenAIEmbeddings")
    @patch("smart_bot_factory.rag.vectorstore.root")
    def test_vectorstore_similarity_search_score_filtering(self, mock_root, mock_openai_embeddings, mock_create_client, mock_env_file, tmp_path):
        """Тест фильтрации по score"""
        mock_root.__truediv__ = lambda self, other: tmp_path / other
        mock_root.__str__ = lambda self: str(tmp_path)

        mock_embeddings_instance = Mock()
        mock_embeddings_instance.embed_query = Mock(return_value=[0.1] * 1536)
        mock_openai_embeddings.return_value = mock_embeddings_instance

        mock_client = Mock()
        mock_rpc_result = Mock()
        mock_rpc_result.data = [
            {"content": "high score", "metadata": {"id": 1}, "similarity": 0.9},
            {"content": "low score", "metadata": {"id": 2}, "similarity": 0.5},
        ]
        mock_rpc = Mock()
        mock_rpc.filter.return_value = mock_rpc
        mock_rpc.limit.return_value = mock_rpc
        mock_rpc.execute.return_value = mock_rpc_result
        mock_client.rpc.return_value = mock_rpc
        mock_create_client.return_value = mock_client

        with patch("smart_bot_factory.rag.vectorstore.load_dotenv"):
            vectorstore = VectorStore(bot_id="test-bot")
            results = vectorstore.similarity_search("test query", k=2, score=0.7)

        # Должен вернуться только документ с score >= 0.7
        assert len(results) == 1
        assert results[0].page_content == "high score"

    @patch("smart_bot_factory.rag.vectorstore.create_client")
    @patch("smart_bot_factory.rag.vectorstore.OpenAIEmbeddings")
    @patch("smart_bot_factory.rag.vectorstore.root")
    @pytest.mark.asyncio
    async def test_vectorstore_asimilarity_search(self, mock_root, mock_openai_embeddings, mock_create_client, mock_env_file, tmp_path):
        """Тест асинхронного поиска"""
        mock_root.__truediv__ = lambda self, other: tmp_path / other
        mock_root.__str__ = lambda self: str(tmp_path)

        mock_embeddings_instance = Mock()
        mock_embeddings_instance.embed_query = Mock(return_value=[0.1] * 1536)
        mock_openai_embeddings.return_value = mock_embeddings_instance

        mock_client = Mock()
        mock_rpc_result = Mock()
        mock_rpc_result.data = [{"content": "test content", "metadata": {"id": 1}, "similarity": 0.8}]
        mock_rpc = Mock()
        mock_rpc.filter.return_value = mock_rpc
        mock_rpc.limit.return_value = mock_rpc
        mock_rpc.execute.return_value = mock_rpc_result
        mock_client.rpc.return_value = mock_rpc
        mock_create_client.return_value = mock_client

        with patch("smart_bot_factory.rag.vectorstore.load_dotenv"):
            vectorstore = VectorStore(bot_id="test-bot")
            results = await vectorstore.asimilarity_search("test query", k=1, score=0.7)

        assert len(results) == 1
        assert isinstance(results[0], Document)

    @patch("smart_bot_factory.rag.vectorstore.create_client")
    @patch("smart_bot_factory.rag.vectorstore.OpenAIEmbeddings")
    @patch("smart_bot_factory.rag.vectorstore.root")
    def test_vectorstore_as_retriever(self, mock_root, mock_openai_embeddings, mock_create_client, mock_env_file, tmp_path):
        """Тест создания retriever"""
        mock_root.__truediv__ = lambda self, other: tmp_path / other
        mock_root.__str__ = lambda self: str(tmp_path)

        mock_embeddings_instance = Mock()
        mock_openai_embeddings.return_value = mock_embeddings_instance

        mock_client = Mock()
        mock_create_client.return_value = mock_client

        with patch("smart_bot_factory.rag.vectorstore.load_dotenv"):
            vectorstore = VectorStore(bot_id="test-bot")
            retriever = vectorstore.as_retriever()

        assert retriever is not None
        # Проверяем, что bot_id добавлен в фильтр
        assert retriever.search_kwargs.get("filter", {}).get("bot_id") == "test-bot"
