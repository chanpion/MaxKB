# coding=utf-8
"""Knowledge search node: embeds the (templated) question and retrieves the top-k
paragraphs through :class:`app.rag.retriever.PgVectorRetriever` (reusing the
existing ``embedding`` / ``paragraph`` tables — no Agno PgVector rewrite).
"""
from __future__ import annotations

from typing import Any, Dict, List

from app.workflows.nodes.base import NodeResult, StepNode


def _reset_title(title: str) -> str:
    if not title or not title.strip():
        return ""
    return f"#### {title}\n"


class SearchKnowledgeNode(StepNode):
    type = "search-knowledge-node"

    async def execute(self) -> NodeResult:
        knowledge_setting = self.node_data.get("knowledge_setting", {}) or {}
        top_n = int(knowledge_setting.get("top_n", 5))
        similarity = float(knowledge_setting.get("similarity", 0.5))
        search_mode = knowledge_setting.get("search_mode", "embedding")
        max_chars = int(knowledge_setting.get("max_paragraph_char_number", 5000))

        knowledge_id_list = self.resolve(self.node_data.get("knowledge_id_list")) or []
        if isinstance(knowledge_id_list, str):
            knowledge_id_list = [knowledge_id_list]
        knowledge_id_list = [str(k) for k in knowledge_id_list]
        if not knowledge_id_list:
            return NodeResult(
                {"paragraph_list": [], "data": "", "directly_return": "", "question": ""},
                is_result=False,
            )

        question = self.resolve_template(self.node_data.get("question", ""))
        self.context["question"] = question

        embedding_cfg = self.state.params.get("embedding_config", {})
        from app.rag.embed import embed_texts, normalize_for_embedding
        from app.rag.retriever import PgVectorRetriever

        vectors = await embed_texts(
            embedding_cfg["provider"],
            embedding_cfg["model_name"],
            embedding_cfg.get("credential", {}),
            [normalize_for_embedding(question)],
            dimensions=embedding_cfg.get("dimensions"),
        )
        if not vectors:
            return NodeResult(
                {"paragraph_list": [], "data": "", "directly_return": "", "question": question},
                is_result=False,
            )

        retriever = PgVectorRetriever()
        rows = await retriever.search(
            query_embedding=vectors[0],
            knowledge_ids=knowledge_id_list,
            top_n=top_n,
            similarity=similarity,
            search_mode=search_mode,
            query_text=question,
        )
        paragraph_list: List[Dict[str, Any]] = []
        for r in rows:
            paragraph_list.append(
                {
                    "id": str(r.get("paragraph_id")),
                    "title": r.get("title"),
                    "content": r.get("content"),
                    "similarity": r.get("similarity"),
                }
            )
        data = "\n".join(
            f"{_reset_title(p.get('title', ''))}{p.get('content')}" for p in paragraph_list
        )[:max_chars]
        return NodeResult(
            {
                "paragraph_list": paragraph_list,
                "data": data,
                "question": question,
                "show_knowledge": self.node_data.get("show_knowledge", False),
            },
            is_result=False,
        )
