import asyncio
import logging
import os
from pathlib import Path
from typing import Any, List, Optional, Tuple

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from project_root_finder import root
from supabase import Client, create_client

from .supabase_vector import SupabaseVectorStore

logger = logging.getLogger(__name__)


class VectorStore(SupabaseVectorStore):
    """Векторное хранилище с автоматической загрузкой настроек бота."""

    def __init__(self, bot_id: str, table_name: str = "vectorstore", query_name: Optional[str] = None) -> None:
        self.bot_id = bot_id
        self.table_name = table_name

        # Если query_name не указан, используем стандартное имя функции
        if not query_name:
            query_name = f"match_{table_name}"

        self.query_name = query_name

        self.supabase_client: Optional[Client] = None
        self.url: Optional[str] = None
        self.key: Optional[str] = None
        self.openai_api_key: Optional[str] = None

        self._load_env_config()
        self.supabase_client = create_client(self.url, self.key)

        embedding_model = "text-embedding-3-small"
        embedding = OpenAIEmbeddings(api_key=self.openai_api_key, model=embedding_model)
        self.embedding = embedding

        super().__init__(client=self.supabase_client, embedding=embedding, table_name=table_name, query_name=query_name)

    # ======================================================================
    # Методы загрузки ENV (оставлены для доступа к настройкам из .env)
    # ======================================================================
    def _load_env_config(self) -> None:
        """Загружает конфигурацию из .env файла."""
        try:
            env_path = self._find_env_file()

            if not env_path or not env_path.exists():
                raise FileNotFoundError(f".env файл не найден: {env_path}")

            load_dotenv(env_path)

            self.url = os.getenv("SUPABASE_URL")
            self.key = os.getenv("SUPABASE_KEY")
            self.openai_api_key = os.getenv("OPENAI_API_KEY")

            missing_vars = []
            if not self.url:
                missing_vars.append("SUPABASE_URL")
            if not self.key:
                missing_vars.append("SUPABASE_KEY")
            if not self.openai_api_key:
                missing_vars.append("OPENAI_API_KEY")

            if missing_vars:
                raise ValueError(f"Отсутствуют обязательные переменные в .env: {', '.join(missing_vars)}")

            logger.info("✅ Настройки Supabase загружены из %s", env_path)

        except Exception as exc:
            logger.error("❌ Ошибка загрузки конфигурации Supabase: %s", exc)
            raise

    def _find_env_file(self) -> Optional[Path]:
        """Автоматически находит .env файл для указанного бота."""
        bot_env_path = root / "bots" / self.bot_id / ".env"

        if bot_env_path.exists():
            logger.info("🔍 Найден .env файл для бота %s: %s", self.bot_id, bot_env_path)
            return bot_env_path

        logger.error("❌ .env файл не найден для бота %s", self.bot_id)
        logger.error("   Искали в: %s", bot_env_path)
        return None

    def _check_table_and_function(self) -> None:
        """
        Проверяет наличие таблицы и функции при инициализации класса.
        Если таблицы нет - генерирует SQL файл и выбрасывает исключение, останавливающее код.
        Если функции нет - генерирует SQL файл и выводит инструкции.
        """
        # Проверяем наличие таблицы
        try:
            # Пробуем выполнить простой запрос к таблице
            self.supabase_client.table(self.table_name).select("id").limit(1).execute()
            logger.info("✅ Таблица '%s' найдена в Supabase", self.table_name)
        except Exception as table_error:
            # Если есть ошибка при запросе к таблице - значит таблицы нет или она неправильная
            # Генерируем SQL с таблицей и функцией и выбрасываем исключение
            self._handle_table_not_found_error(table_error, self.table_name)
            # Исключение уже выброшено в _handle_table_not_found_error

        # Если таблица есть, проверяем функцию через попытку простого поиска
        # Используем минимальный запрос, который вызовет функцию
        try:
            # Пробуем выполнить простой поиск с минимальными параметрами
            # Это вызовет функцию, если она существует
            test_query = "test"
            # Пробуем вызвать через родительский класс - это вызовет функцию
            super().similarity_search(query=test_query, k=1)
            logger.info("✅ Функция '%s' найдена в Supabase", self.query_name)
        except Exception as function_error:
            # Если есть ошибка при запросе к функции - значит функции нет или она неправильная
            # Генерируем SQL файл для создания функции
            self._handle_function_not_found_error(function_error, self.query_name)

    def _is_table_not_found_error(self, error: Exception) -> bool:
        """Проверяет, является ли ошибка ошибкой отсутствия таблицы в Supabase."""
        error_str = str(error).lower()
        # Проверяем, что это ошибка таблицы (relation), а не функции
        # Если в ошибке есть "relation" и "does not exist", но нет "function" - это таблица
        has_relation_error = "relation" in error_str and "does not exist" in error_str
        has_function_error = "function" in error_str

        # Если ошибка содержит название таблицы - точно таблица
        if has_relation_error and self.table_name.lower() in error_str and not has_function_error:
            return True

        # Если это ошибка relation, но не функция, и мы пытаемся работать с таблицей - вероятно таблица
        if has_relation_error and not has_function_error:
            return True

        return False

    def _is_function_not_found_error(self, error: Exception) -> bool:
        """Проверяет, является ли ошибка ошибкой отсутствия функции в Supabase."""
        error_str = str(error).lower()
        return (
            ("function" in error_str and "does not exist" in error_str)
            or ("function" in error_str and "not found" in error_str)
            or ("relation" in error_str and "does not exist" in error_str and "function" in error_str)
        )

    def _generate_sql_file_for_table_and_function(self, table_name: str) -> Path:
        """
        Генерирует SQL файл для создания таблицы и функции в Supabase.

        Args:
            table_name: Название таблицы

        Returns:
            Path к созданному SQL файлу
        """
        from .templates.create_table_and_function_template import generate_table_and_function_sql

        # Получаем размерность embedding из модели
        # text-embedding-3-small имеет размерность 1536
        embedding_dim = 1536

        # Генерируем SQL
        sql_content = generate_table_and_function_sql(
            table_name=table_name,
            embedding_dim=embedding_dim,
        )

        # Создаем директорию для SQL файлов, если её нет
        sql_dir = root / "sql_functions"
        sql_dir.mkdir(exist_ok=True)

        # Создаем файл с именем таблицы
        sql_file = sql_dir / f"create_{table_name}_table_and_function.sql"

        # Записываем SQL в файл
        sql_file.write_text(sql_content, encoding="utf-8")

        logger.info("📝 SQL файл создан: %s", sql_file)

        return sql_file

    def _generate_sql_file_for_function(self, function_name: str) -> Path:
        """
        Генерирует SQL файл для создания функции в Supabase.

        Args:
            function_name: Название функции (например, "match_services")

        Returns:
            Path к созданному SQL файлу
        """
        from .templates.match_services_template import generate_match_services_sql

        # Определяем название таблицы из имени функции
        # Если функция match_services, то таблица services
        if function_name.startswith("match_"):
            table_name = function_name.replace("match_", "")
        else:
            table_name = self.table_name

        # Генерируем SQL
        sql_content = generate_match_services_sql(
            table_name=table_name,
            function_name=function_name,
        )

        # Создаем директорию для SQL файлов, если её нет
        sql_dir = root / "sql_functions"
        sql_dir.mkdir(exist_ok=True)

        # Создаем файл с именем функции
        sql_file = sql_dir / f"{function_name}.sql"

        # Записываем SQL в файл
        sql_file.write_text(sql_content, encoding="utf-8")

        logger.info("📝 SQL файл создан: %s", sql_file)

        return sql_file

    def _handle_table_not_found_error(self, error: Exception, table_name: str) -> None:
        """
        Обрабатывает ошибку отсутствия таблицы: генерирует SQL файл с таблицей и функцией.
        Выбрасывает исключение, которое останавливает выполнение кода.

        Args:
            error: Исключение с ошибкой
            table_name: Название отсутствующей таблицы

        Raises:
            RuntimeError: Всегда выбрасывается после генерации SQL файла
        """
        logger.error("❌ Таблица %s не найдена в Supabase: %s", table_name, error)

        # Генерируем SQL файл с таблицей и функцией
        sql_file = self._generate_sql_file_for_table_and_function(table_name)

        function_name = f"match_{table_name}"

        # Выводим понятное сообщение пользователю
        print("\n" + "=" * 80)
        print("⚠️  ОШИБКА: Таблица не найдена в Supabase")
        print("=" * 80)
        print(f"\nТаблица '{table_name}' отсутствует в вашей базе данных Supabase.")
        print(f"Скорее всего, также отсутствует функция '{function_name}'.")
        print("\n✅ SQL файл для создания таблицы и функции был автоматически сгенерирован:")
        print(f"   📁 {sql_file}")
        print("\n📋 ЧТО НУЖНО СДЕЛАТЬ:")
        print(f"   1. Откройте файл: {sql_file}")
        print("   2. Скопируйте содержимое SQL файла")
        print("   3. Выполните SQL команду в Supabase:")
        print("      - Откройте Supabase Dashboard")
        print("      - Перейдите в SQL Editor")
        print("      - Вставьте SQL код из файла")
        print("      - Нажмите 'Run' для выполнения")
        print(f"\nSQL файл создаст таблицу '{table_name}' и функцию '{function_name}'.")
        print("После создания таблицы и функции в Supabase, повторите операцию.")
        print("=" * 80 + "\n")

        # Выбрасываем исключение, которое останавливает выполнение кода
        raise RuntimeError(f"Таблица '{table_name}' не найдена в Supabase. " f"SQL файл для создания таблицы и функции сохранен в: {sql_file}")

    def _handle_function_not_found_error(self, error: Exception, function_name: str) -> None:
        """
        Обрабатывает ошибку отсутствия функции: генерирует SQL файл и выводит инструкции.

        Args:
            error: Исключение с ошибкой
            function_name: Название отсутствующей функции
        """
        logger.error("❌ Функция %s не найдена в Supabase: %s", function_name, error)

        # Генерируем SQL файл
        sql_file = self._generate_sql_file_for_function(function_name)

        # Выводим понятное сообщение пользователю
        print("\n" + "=" * 80)
        print("⚠️  ОШИБКА: Функция не найдена в Supabase")
        print("=" * 80)
        print(f"\nФункция '{function_name}' отсутствует в вашей базе данных Supabase.")
        print("\n✅ SQL файл для создания функции был автоматически сгенерирован:")
        print(f"   📁 {sql_file}")
        print("\n📋 ЧТО НУЖНО СДЕЛАТЬ:")
        print(f"   1. Откройте файл: {sql_file}")
        print("   2. Скопируйте содержимое SQL файла")
        print("   3. Выполните SQL команду в Supabase:")
        print("      - Откройте Supabase Dashboard")
        print("      - Перейдите в SQL Editor")
        print("      - Вставьте SQL код из файла")
        print("      - Нажмите 'Run' для выполнения")
        print("\nПосле создания функции в Supabase, повторите операцию.")
        print("=" * 80 + "\n")

    def as_retriever(self, **kwargs):
        """
        Returns a retriever for the vector store.
        """
        kwargs.setdefault("search_kwargs", {})
        search_kwargs = kwargs["search_kwargs"]
        filter_payload = search_kwargs.get("filter", {})

        # Обеспечиваем, что filter_payload - это словарь
        if not isinstance(filter_payload, dict):
            filter_payload = {}

        # Добавляем bot_id в фильтр
        filter_payload = filter_payload.copy()  # Копируем, чтобы не модифицировать оригинал
        filter_payload["bot_id"] = self.bot_id

        search_kwargs["filter"] = filter_payload
        kwargs["search_kwargs"] = search_kwargs

        logger.info("JSONB фильтр для поиска: %s", filter_payload)

        return super().as_retriever(**kwargs)

    def similarity_search(
        self,
        query: str,
        k: int = 4,
        filter: Optional[dict] = None,
        score: float = 0.6,
        **kwargs: Any,
    ) -> List[Document]:
        """
        Поиск похожих документов с фильтрацией по минимальному score.

        Args:
            query: Поисковый запрос
            k: Количество результатов для получения
            filter: Фильтр по metadata
            score: Минимальный score релевантности (по умолчанию 0.6)
            **kwargs: Дополнительные аргументы

        Returns:
            Список документов с score >= указанного значения
        """
        # Подготавливаем фильтр
        if filter is None:
            filter = {}
        filter = filter.copy()
        filter["bot_id"] = self.bot_id

        logger.info("Запрос: %s, score: %.2f", query, score)

        try:
            # Вызываем метод родительского класса для получения результатов с scores
            results_with_scores: List[Tuple[Document, float]] = super().similarity_search_with_relevance_scores(query, k=k, filter=filter)

            # Фильтруем по score
            filtered_results = [(doc, doc_score) for doc, doc_score in results_with_scores if doc_score >= score]

            # Возвращаем только документы (без scores)
            return [doc for doc, _ in filtered_results]

        except NotImplementedError:
            # Fallback на обычный поиск, если метод не поддерживается
            return super().similarity_search(query, k=k, filter=filter, **kwargs)
        except Exception as exc:
            # Проверяем, является ли это ошибкой отсутствия таблицы
            if self._is_table_not_found_error(exc):
                self._handle_table_not_found_error(exc, self.table_name)
            # Проверяем, является ли это ошибкой отсутствия функции
            elif self._is_function_not_found_error(exc):
                self._handle_function_not_found_error(exc, self.query_name)
            logger.error("❌ Ошибка при поиске: %s", exc)
            raise

    async def asimilarity_search(
        self,
        query: str,
        k: int = 4,
        filter: Optional[dict] = None,
        score: float = 0.6,
        **kwargs: Any,
    ) -> List[Document]:
        """
        Асинхронный поиск похожих документов с фильтрацией по минимальному score.

        Args:
            query: Поисковый запрос
            k: Количество результатов для получения
            filter: Фильтр по metadata
            score: Минимальный score релевантности (по умолчанию 0.6)
            **kwargs: Дополнительные аргументы

        Returns:
            Список документов с score >= указанного значения
        """
        # Подготавливаем фильтр
        if filter is None:
            filter = {}
        filter = filter.copy()
        filter["bot_id"] = self.bot_id

        logger.info("Запрос: %s, score: %.2f", query, score)

        try:
            # Вызываем синхронный метод в отдельном потоке, так как async версии нет
            results_with_scores: List[Tuple[Document, float]] = await asyncio.to_thread(
                super().similarity_search_with_relevance_scores, query, k=k, filter=filter, **kwargs
            )

            # Фильтруем по score
            filtered_results = [(doc, doc_score) for doc, doc_score in results_with_scores if doc_score >= score]

            # Возвращаем только документы (без scores)
            return [doc for doc, _ in filtered_results]

        except NotImplementedError:
            # Fallback на обычный async поиск, если метод не поддерживается
            return await super().asimilarity_search(query, k=k, filter=filter, **kwargs)
        except Exception as exc:
            # Проверяем, является ли это ошибкой отсутствия таблицы
            if self._is_table_not_found_error(exc):
                self._handle_table_not_found_error(exc, self.table_name)
            # Проверяем, является ли это ошибкой отсутствия функции
            elif self._is_function_not_found_error(exc):
                self._handle_function_not_found_error(exc, self.query_name)
            logger.error("❌ Ошибка при асинхронном поиске: %s", exc)
            raise
