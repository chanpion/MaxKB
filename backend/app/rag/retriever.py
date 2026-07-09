# coding=utf-8
"""PgVectorRetriever: Agno-compatible retriever reusing MaxKB's pgvector SQL.

The retrieval SQL mirrors apps/knowledge/sql/embedding_search.sql and
blend_search.sql, executed via asyncpg against the EXISTING `embedding` /
`paragraph` tables. We deliberately do NOT use Agno's PgVector store so legacy
vector data stays fully compatible.
"""
from __future__ import annotations

import json
from typing import Any, Sequence

from sqlalchemy import Engine

from app.core.db import engine

_SQL_EMBEDDING = """
WITH vector_top AS (
    SELECT e.id, e.paragraph_id, (e.embedding::vector($1) <=> $2::vector) AS distance
    FROM embedding e
    WHERE e.knowledge_id::text = ANY($6::text[]) AND e.is_active = TRUE
    ORDER BY (e.embedding::vector($1) <=> $2::vector)
    LIMIT LEAST($3 * 10, 500)
)
SELECT p.id AS paragraph_id, p.content, p.title, (1 - vc.distance) AS similarity
FROM vector_top vc
JOIN embedding e2 ON e2.id = vc.id
JOIN paragraph p ON p.id = vc.paragraph_id
WHERE (1 - vc.distance) > $4
ORDER BY similarity DESC
LIMIT $5
"""

_SQL_BLEND = """
WITH vector_top AS (
    SELECT e.id, e.paragraph_id, (e.embedding::vector($1) <=> $2::vector) AS distance
    FROM embedding e
    WHERE e.knowledge_id::text = ANY($6::text[]) AND e.is_active = TRUE
    ORDER BY (e.embedding::vector($1) <=> $2::vector)
    LIMIT LEAST($3 * 10, 500)
)
SELECT p.id AS paragraph_id, p.content, p.title,
       (1 - vc.distance + COALESCE(ts_rank_cd(e2.search_vector, websearch_to_tsquery('simple', $7), 32), 0)) AS similarity
FROM vector_top vc
JOIN embedding e2 ON e2.id = vc.id
JOIN paragraph p ON p.id = vc.paragraph_id
WHERE (1 - vc.distance + COALESCE(ts_rank_cd(e2.search_vector, websearch_to_tsquery('simple', $7), 32), 0)) > $4
ORDER BY similarity DESC
LIMIT $5
"""


class PgVectorRetriever:
    """Custom retriever compatible with Agno Agent's `retriever` interface.

    Call ``search(query_embedding=..., knowledge_ids=..., search_mode=...)`` to
    get ranked paragraphs. The query vector is computed by the caller (via
    ``app.providers.get_embedder``) so this class stays provider-agnostic.
    """

    def __init__(self, engine: Engine | None = None) -> None:
        self._engine = engine or engine

    async def search(
        self,
        query_embedding: Sequence[float],
        knowledge_ids: Sequence[str],
        top_n: int = 5,
        similarity: float = 0.5,
        search_mode: str = "embedding",
        query_text: str | None = None,
    ) -> list[dict[str, Any]]:
        dim = len(query_embedding)
        vec = json.dumps(list(query_embedding))
        kids = list(knowledge_ids)
        if search_mode == "blend":
            sql = _SQL_BLEND
            params = (dim, vec, top_n, similarity, top_n, kids, query_text or "")
        else:
            sql = _SQL_EMBEDDING
            params = (dim, vec, top_n, similarity, top_n, kids)

        async with self._engine.connect() as conn:
            result = await conn.exec_driver_sql(sql, params)
            rows = result.mappings().all()
        return [dict(r) for r in rows]
