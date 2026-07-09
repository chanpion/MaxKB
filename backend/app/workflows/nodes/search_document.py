"""Search-document node: vector search over a knowledge base.

Reuses the existing ``PgVectorRetriever`` (MaxKB's pgvector SQL) together with
the embedder from ``app.providers.get_embedder`` — no re-implementation of the
RAG retrieval path, keeping data compatible with the legacy Django service.
Mirrors ``application.flow.step_node.search_document_node``.
"""

from __future__ import annotations

from app.workflows.nodes.base import NodeResult, StepNode


class SearchDocumentNode(StepNode):
    type = "search-document-node"

    async def execute(self) -> NodeResult:
        query = self.resolve_template(self.node_data.get("query", "")) or ""
        if not query:
            return NodeResult(
                {"exception_message": "query is required"},
                status=500,
                exception_message="query is required",
            )
        knowledge_ids = self.resolve(self.node_data.get("knowledge_ids")) or []
        if isinstance(knowledge_ids, str):
            knowledge_ids = [knowledge_ids]
        top_n = int(self.node_data.get("top_n", 5) or 5)
        similarity = float(self.node_data.get("similarity", 0.5) or 0.5)
        search_mode = self.node_data.get("search_mode", "embedding") or "embedding"

        embedding_cfg = (
            self.state.params.get("embedding_config") or self.resolve(self.node_data.get("embedding_config")) or {}
        )
        if not embedding_cfg.get("provider"):
            return NodeResult(
                {"exception_message": "embedding_config is required"},
                status=500,
                exception_message="embedding_config is required",
            )

        from app.core.db import engine as db_engine
        from app.providers import get_embedder
        from app.rag.retriever import PgVectorRetriever

        embedder = get_embedder(
            embedding_cfg["provider"],
            embedding_cfg["model_name"],
            embedding_cfg.get("credential", {}),
            dimensions=embedding_cfg.get("dimensions"),
        )
        try:
            q_emb = await embedder.embed([query])
        except (AttributeError, TypeError):
            q_emb = await embedder.aembed([query])  # type: ignore[attr-defined]
        vector = q_emb[0] if isinstance(q_emb, list) else q_emb

        retriever = PgVectorRetriever(db_engine)
        rows = await retriever.search(
            query_embedding=vector,
            knowledge_ids=knowledge_ids,
            top_n=top_n,
            similarity=similarity,
            search_mode=search_mode,
            query_text=query,
        )

        return NodeResult(
            {"result": rows, "document_list": rows},
            is_result=self.is_result if self.is_result is not None else False,
        )
