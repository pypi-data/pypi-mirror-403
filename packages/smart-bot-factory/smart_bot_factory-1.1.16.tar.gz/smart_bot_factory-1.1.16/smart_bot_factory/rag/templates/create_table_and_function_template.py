"""
Шаблон для генерации SQL создания таблицы и функции match.
Используйте f-строку для заполнения параметров.
"""


def generate_table_and_function_sql(
    table_name: str,
    embedding_dim: int = 1536,
) -> str:
    """
    Генерирует SQL код для создания таблицы и функции match.

    Args:
        table_name: Название таблицы
        embedding_dim: Размерность вектора embedding (по умолчанию 1536 для text-embedding-3-small)

    Returns:
        SQL код для создания таблицы и функции
    """
    function_name = f"match_{table_name}"

    sql = f"""-- Создание таблицы {table_name}
CREATE TABLE {table_name} (
    id uuid PRIMARY KEY,
    content text, -- corresponds to Document.pageContent
    metadata jsonb, -- corresponds to Document.metadata
    embedding vector({embedding_dim}) -- {embedding_dim} works for OpenAI embeddings, change if needed
);

-- Индекс для metadata (GIN)
CREATE INDEX {table_name}_metadata_idx
  ON {table_name}
  USING gin (metadata);

-- Индекс для embedding (HNSW)
CREATE INDEX {table_name}_embedding_idx
  ON {table_name}
  USING hnsw (embedding vector_cosine_ops);

-- Создание функции {function_name}
CREATE OR REPLACE FUNCTION {function_name}(
    query_embedding vector,
    filter jsonb DEFAULT '{{}}'::jsonb
)
RETURNS TABLE(
    id uuid,
    content text,
    metadata jsonb,
    similarity double precision
)
LANGUAGE plpgsql
AS $function$
DECLARE
    filter_clauses text := '';
    filter_key text;
    filter_value jsonb;
    array_elements text;
    first_clause boolean := true;
BEGIN
    -- Разбираем фильтр
    IF filter IS NOT NULL AND filter != '{{}}'::jsonb THEN
        FOR filter_key, filter_value IN SELECT * FROM jsonb_each(filter)
        LOOP
            IF jsonb_typeof(filter_value) = 'array' THEN
                -- Если массив, OR по элементам
                SELECT string_agg(quote_literal(elem::text), ',')
                INTO array_elements
                FROM jsonb_array_elements_text(filter_value) AS elem;

                IF array_elements IS NOT NULL THEN
                    IF first_clause THEN
                        filter_clauses := format('(metadata->>%L)::text = ANY(ARRAY[%s])', filter_key, array_elements);
                        first_clause := false;
                    ELSE
                        filter_clauses := filter_clauses || ' OR ' ||
                            format('(metadata->>%L)::text = ANY(ARRAY[%s])', filter_key, array_elements);
                    END IF;
                END IF;

            ELSIF jsonb_typeof(filter_value) = 'string' THEN
                IF first_clause THEN
                    filter_clauses := format('metadata->>%L = %L', filter_key, filter_value #>> '{{}}');
                    first_clause := false;
                ELSE
                    filter_clauses := filter_clauses || ' OR ' ||
                        format('metadata->>%L = %L', filter_key, filter_value #>> '{{}}');
                END IF;

            ELSIF jsonb_typeof(filter_value) IN ('number','boolean') THEN
                IF first_clause THEN
                    filter_clauses := format('metadata->>%L = %L', filter_key, filter_value #>> '{{}}');
                    first_clause := false;
                ELSE
                    filter_clauses := filter_clauses || ' OR ' ||
                        format('metadata->>%L = %L', filter_key, filter_value #>> '{{}}');
                END IF;
            END IF;
        END LOOP;
    END IF;

    -- Основной запрос
    RETURN QUERY EXECUTE format(
        'SELECT
            v.id,
            v.content,
            v.metadata,
            1 - (v.embedding <=> $1) AS similarity
         FROM {table_name} v
         WHERE TRUE %s
         ORDER BY v.embedding <=> $1
         LIMIT 20',
        CASE WHEN filter_clauses = '' THEN '' ELSE ' AND (' || filter_clauses || ')' END
    ) USING query_embedding;
END;
$function$;
"""
    return sql
