CREATE FUNCTION {function_name}(
    filter jsonb DEFAULT '{}',
    query_embedding vector({embedding_dim})
)
RETURNS TABLE (
    id bigint,
    content text,
    metadata jsonb,
    similarity float
)
LANGUAGE plpgsql
AS $$
DECLARE
    filter_conditions text := '';
    filter_key text;
    filter_value jsonb;
    array_elements text;
BEGIN
    -- Проверяем, есть ли фильтры
    IF filter IS NOT NULL AND filter != '{}'::jsonb THEN
        FOR filter_key, filter_value IN SELECT * FROM jsonb_each(filter)
        LOOP
            -- Строковые значения
            IF jsonb_typeof(filter_value) = 'string' THEN
                filter_conditions := filter_conditions || 
                    format(' AND metadata->>%L = %L', filter_key, filter_value #>> '{}');
            
            -- Массивы
            ELSIF jsonb_typeof(filter_value) = 'array' THEN
                SELECT string_agg(quote_literal(elem::text), ',')
                INTO array_elements
                FROM jsonb_array_elements_text(filter_value) AS elem;
                
                IF array_elements IS NOT NULL THEN
                    filter_conditions := filter_conditions || 
                        format(' AND metadata->>%L = ANY(ARRAY[%s])', filter_key, array_elements);
                END IF;

            -- Числа и boolean
            ELSIF jsonb_typeof(filter_value) IN ('number', 'boolean') THEN
                filter_conditions := filter_conditions || 
                    format(' AND metadata->>%L = %L', filter_key, filter_value #>> '{}');
            END IF;
        END LOOP;
    END IF;

    -- Выполняем запрос
    RETURN QUERY EXECUTE format(
        'SELECT 
            s.id,
            s.content,
            s.metadata,
            1 - (s.embedding <=> $1) AS similarity
         FROM {table_name} s
         WHERE TRUE %s
         ORDER BY s.embedding <=> $1',
        filter_conditions
    ) USING query_embedding;
END;
$$;

