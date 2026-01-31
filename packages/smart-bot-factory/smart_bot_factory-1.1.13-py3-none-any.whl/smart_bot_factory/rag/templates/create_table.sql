CREATE TABLE IF NOT EXISTS {table_name} (
    id bigserial PRIMARY KEY,
    content text,
    metadata jsonb,
    embedding vector({embedding_dim})
);

