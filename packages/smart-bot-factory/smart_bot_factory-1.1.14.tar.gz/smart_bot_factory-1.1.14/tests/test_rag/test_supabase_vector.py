"""Тесты для SupabaseVectorStore"""

from unittest.mock import Mock

import pytest
from langchain_core.documents import Document

from smart_bot_factory.rag.supabase_vector import SupabaseVectorStore


class TestSupabaseVectorStore:
    """Тесты для класса SupabaseVectorStore"""

    @pytest.fixture
    def mock_supabase_client(self):
        """Фикстура для мок Supabase клиента"""
        client = Mock()
        client.table = Mock(return_value=Mock())
        client.rpc = Mock(return_value=Mock())
        client.from_ = Mock(return_value=Mock())
        return client

    @pytest.fixture
    def mock_embeddings(self):
        """Фикстура для мок embeddings"""
        embeddings = Mock()
        embeddings.embed_query = Mock(return_value=[0.1] * 1536)
        embeddings.embed_documents = Mock(return_value=[[0.1] * 1536])
        return embeddings

    def test_supabase_vectorstore_initialization(self, mock_supabase_client, mock_embeddings):
        """Тест инициализации SupabaseVectorStore"""
        vectorstore = SupabaseVectorStore(client=mock_supabase_client, embedding=mock_embeddings, table_name="test_table")

        assert vectorstore.table_name == "test_table"
        assert vectorstore.query_name == "match_documents"
        assert vectorstore.chunk_size == 500

    def test_supabase_vectorstore_initialization_custom_params(self, mock_supabase_client, mock_embeddings):
        """Тест инициализации с кастомными параметрами"""
        vectorstore = SupabaseVectorStore(
            client=mock_supabase_client, embedding=mock_embeddings, table_name="custom_table", query_name="custom_query", chunk_size=1000
        )

        assert vectorstore.table_name == "custom_table"
        assert vectorstore.query_name == "custom_query"
        assert vectorstore.chunk_size == 1000

    def test_supabase_vectorstore_embeddings_property(self, mock_supabase_client, mock_embeddings):
        """Тест свойства embeddings"""
        vectorstore = SupabaseVectorStore(client=mock_supabase_client, embedding=mock_embeddings, table_name="test_table")

        assert vectorstore.embeddings == mock_embeddings

    def test_supabase_vectorstore_add_texts(self, mock_supabase_client, mock_embeddings):
        """Тест добавления текстов"""
        mock_upsert_result = Mock()
        mock_upsert_result.data = [{"id": "test-id-1"}, {"id": "test-id-2"}]
        mock_upsert = Mock()
        mock_upsert.execute.return_value = mock_upsert_result
        mock_from = Mock()
        mock_from.upsert.return_value = mock_upsert
        mock_supabase_client.from_.return_value = mock_from

        vectorstore = SupabaseVectorStore(client=mock_supabase_client, embedding=mock_embeddings, table_name="test_table")

        texts = ["text1", "text2"]
        ids = vectorstore.add_texts(texts)

        assert len(ids) == 2
        assert ids == ["test-id-1", "test-id-2"]
        mock_embeddings.embed_documents.assert_called_once()

    def test_supabase_vectorstore_similarity_search(self, mock_supabase_client, mock_embeddings):
        """Тест поиска похожих документов"""
        mock_rpc_result = Mock()
        mock_rpc_result.data = [{"content": "test content", "metadata": {"id": 1}, "similarity": 0.8}]
        mock_rpc = Mock()
        mock_rpc.filter.return_value = mock_rpc
        mock_rpc.limit.return_value = mock_rpc
        mock_rpc.execute.return_value = mock_rpc_result
        mock_supabase_client.rpc.return_value = mock_rpc

        vectorstore = SupabaseVectorStore(client=mock_supabase_client, embedding=mock_embeddings, table_name="test_table")

        results = vectorstore.similarity_search("test query", k=1)

        assert len(results) == 1
        assert isinstance(results[0], Document)
        assert results[0].page_content == "test content"
        mock_embeddings.embed_query.assert_called_once_with("test query")

    def test_supabase_vectorstore_similarity_search_with_relevance_scores(self, mock_supabase_client, mock_embeddings):
        """Тест поиска с оценками релевантности"""
        mock_rpc_result = Mock()
        mock_rpc_result.data = [{"content": "test content", "metadata": {"id": 1}, "similarity": 0.8}]
        mock_rpc = Mock()
        mock_rpc.filter.return_value = mock_rpc
        mock_rpc.limit.return_value = mock_rpc
        mock_rpc.execute.return_value = mock_rpc_result
        mock_supabase_client.rpc.return_value = mock_rpc

        vectorstore = SupabaseVectorStore(client=mock_supabase_client, embedding=mock_embeddings, table_name="test_table")

        results = vectorstore.similarity_search_with_relevance_scores("test query", k=1)

        assert len(results) == 1
        assert isinstance(results[0], tuple)
        assert isinstance(results[0][0], Document)
        assert results[0][1] == 0.8

    def test_supabase_vectorstore_match_args(self, mock_supabase_client, mock_embeddings):
        """Тест метода match_args"""
        vectorstore = SupabaseVectorStore(client=mock_supabase_client, embedding=mock_embeddings, table_name="test_table")

        query = [0.1] * 1536
        filter_dict = {"category": "test"}

        args = vectorstore.match_args(query, filter_dict)

        assert args["query_embedding"] == query
        assert args["filter"] == filter_dict

    def test_supabase_vectorstore_match_args_no_filter(self, mock_supabase_client, mock_embeddings):
        """Тест метода match_args без фильтра"""
        vectorstore = SupabaseVectorStore(client=mock_supabase_client, embedding=mock_embeddings, table_name="test_table")

        query = [0.1] * 1536
        args = vectorstore.match_args(query, None)

        assert args["query_embedding"] == query
        assert "filter" not in args

    def test_supabase_vectorstore_similarity_search_by_vector(self, mock_supabase_client, mock_embeddings):
        """Тест поиска по вектору"""
        mock_rpc_result = Mock()
        mock_rpc_result.data = [{"content": "test content", "metadata": {"id": 1}, "similarity": 0.8}]
        mock_rpc = Mock()
        mock_rpc.filter.return_value = mock_rpc
        mock_rpc.limit.return_value = mock_rpc
        mock_rpc.execute.return_value = mock_rpc_result
        mock_supabase_client.rpc.return_value = mock_rpc

        vectorstore = SupabaseVectorStore(client=mock_supabase_client, embedding=mock_embeddings, table_name="test_table")

        query_vector = [0.1] * 1536
        results = vectorstore.similarity_search_by_vector(query_vector, k=1)

        assert len(results) == 1
        assert isinstance(results[0], Document)

    def test_supabase_vectorstore_similarity_search_with_filter(self, mock_supabase_client, mock_embeddings):
        """Тест поиска с фильтром"""
        mock_rpc_result = Mock()
        mock_rpc_result.data = [{"content": "test content", "metadata": {"id": 1, "category": "test"}, "similarity": 0.8}]
        mock_rpc = Mock()
        mock_rpc.filter.return_value = mock_rpc
        mock_rpc.limit.return_value = mock_rpc
        mock_rpc.execute.return_value = mock_rpc_result
        mock_supabase_client.rpc.return_value = mock_rpc

        vectorstore = SupabaseVectorStore(client=mock_supabase_client, embedding=mock_embeddings, table_name="test_table")

        results = vectorstore.similarity_search("test query", k=1, filter={"category": "test"})

        assert len(results) == 1
        mock_supabase_client.rpc.assert_called()

    def test_supabase_vectorstore_similarity_search_with_score_threshold(self, mock_supabase_client, mock_embeddings):
        """Тест поиска с порогом релевантности"""
        mock_rpc_result = Mock()
        mock_rpc_result.data = [
            {"content": "high score", "metadata": {"id": 1}, "similarity": 0.9},
            {"content": "low score", "metadata": {"id": 2}, "similarity": 0.5},
        ]
        mock_rpc = Mock()
        mock_rpc.filter.return_value = mock_rpc
        mock_rpc.limit.return_value = mock_rpc
        mock_rpc.execute.return_value = mock_rpc_result
        mock_supabase_client.rpc.return_value = mock_rpc

        vectorstore = SupabaseVectorStore(client=mock_supabase_client, embedding=mock_embeddings, table_name="test_table")

        query_vector = [0.1] * 1536
        results = vectorstore.similarity_search_by_vector_with_relevance_scores(query_vector, k=2, score_threshold=0.7)

        # Должен вернуться только документ с score >= 0.7
        assert len(results) == 1
        assert results[0][0].page_content == "high score"

    def test_supabase_vectorstore_delete(self, mock_supabase_client, mock_embeddings):
        """Тест удаления документов"""
        mock_delete_result = Mock()
        mock_delete = Mock()
        mock_delete.eq.return_value = mock_delete
        mock_delete.execute.return_value = mock_delete_result
        mock_from = Mock()
        mock_from.delete.return_value = mock_delete
        mock_supabase_client.from_.return_value = mock_from

        vectorstore = SupabaseVectorStore(client=mock_supabase_client, embedding=mock_embeddings, table_name="test_table")

        vectorstore.delete(ids=["id1", "id2"])

        assert mock_from.delete.call_count == 2

    def test_supabase_vectorstore_delete_no_ids(self, mock_supabase_client, mock_embeddings):
        """Тест удаления без указания ids"""
        vectorstore = SupabaseVectorStore(client=mock_supabase_client, embedding=mock_embeddings, table_name="test_table")

        with pytest.raises(ValueError, match="No ids provided"):
            vectorstore.delete(ids=None)

    def test_supabase_vectorstore_texts_to_documents(self, mock_supabase_client, mock_embeddings):
        """Тест преобразования текстов в документы"""
        texts = ["text1", "text2"]
        metadatas = [{"id": 1}, {"id": 2}]

        docs = SupabaseVectorStore._texts_to_documents(texts, metadatas)

        assert len(docs) == 2
        assert docs[0].page_content == "text1"
        assert docs[0].metadata == {"id": 1}
        assert docs[1].page_content == "text2"
        assert docs[1].metadata == {"id": 2}

    def test_supabase_vectorstore_texts_to_documents_no_metadata(self, mock_supabase_client, mock_embeddings):
        """Тест преобразования текстов без метаданных"""
        texts = ["text1", "text2"]

        docs = SupabaseVectorStore._texts_to_documents(texts, None)

        assert len(docs) == 2
        assert docs[0].page_content == "text1"
        assert docs[0].metadata == {}
        assert docs[1].page_content == "text2"
        assert docs[1].metadata == {}
