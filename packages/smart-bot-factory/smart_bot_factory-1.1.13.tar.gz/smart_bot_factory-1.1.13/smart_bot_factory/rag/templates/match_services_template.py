"""
Шаблон для генерации SQL функции match_services.
Используйте f-строку для заполнения параметров.
"""


def generate_match_services_sql(
    table_name: str,
    function_name: str,
) -> str:
    """
    Генерирует SQL код для создания функции match_services.

    Args:
        table_name: Название таблицы
        function_name: Название функции

    Returns:
        SQL код для создания функции
    """
    sql = f"""CREATE OR REPLACE FUNCTION {function_name}(
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
    IF filter IS NOT NULL AND filter != '{{}}'::jsonb THEN
        FOR filter_key, filter_value IN SELECT * FROM jsonb_each(filter)
        LOOP
            IF jsonb_typeof(filter_value) = 'array' THEN
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
