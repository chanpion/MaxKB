"""Knowledge-write node: ingests text/documents into a knowledge base.

Reuses the existing ingestion pipeline (``app.rag.pipeline.ingest_document``)
which parses -> splits -> embeds -> stores into the shared pgvector tables. This
avoids re-implementing the RAG write path and keeps data compatible with the
legacy Django service.
"""

from __future__ import annotations

from app.workflows.nodes.base import NodeResult, StepNode


class KnowledgeWriteNode(StepNode):
    type = "knowledge-write-node"

    async def execute(self) -> NodeResult:
        knowledge_id = self.resolve(self.node_data.get("knowledge_id")) or ""
        if not knowledge_id:
            return NodeResult(
                {"error": "knowledge_id is required"},
                status=500,
                exception_message="knowledge_id is required",
            )
        text = self.resolve(self.node_data.get("content")) or ""
        if not text:
            return NodeResult(
                {"error": "content is required"},
                status=500,
                exception_message="content is required",
            )

        filename = self.resolve(self.node_data.get("filename")) or "workflow_document.txt"
        embedding_cfg = (
            self.state.params.get("embedding_config") or self.resolve(self.node_data.get("embedding_config")) or {}
        )
        from app.models.base import uuid7

        document_id = str(uuid7())

        from app.core.db import SessionLocal
        from app.rag.pipeline import ingest_document

        async with SessionLocal() as session:
            result = await ingest_document(
                session,
                knowledge_id=str(knowledge_id),
                document_id=document_id,
                user_id=None,
                filename=str(filename),
                content=text.encode("utf-8"),
                embedding=embedding_cfg,
            )

        return NodeResult(
            {
                "document_id": document_id,
                "paragraph_count": result.paragraph_count,
                "embedding_count": result.embedding_count,
            },
            is_result=self.is_result if self.is_result is not None else False,
        )
