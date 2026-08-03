-- MaxKB FastAPI Backend — Database initialization script.
--
-- Purpose:
--   Enable the `vector` extension (pgvector) required by the embeddings / RAG
--   subsystem. The extension must be created in the target database before the
--   application starts (alembic only stamps the empty baseline and never creates
--   tables; tables come from the legacy Django service or `schema.sql`).
--
-- How it is used:
--   1. Manual:  psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f init.sql
--   2. Docker:  postgres auto-runs any *.sql in /docker-entrypoint-initdb.d/ on
--              first container start (see docker-compose.yml `postgres` service).
--
-- Note: the `vector` extension requires the `pgvector` contrib package, which is
-- already present in the `pgvector/pgvector:pg17` image used by docker-compose.

CREATE EXTENSION IF NOT EXISTS vector;
