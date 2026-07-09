"""Rerank node: re-orders upstream retrieved paragraphs by relevance to the question.

Mirrors ``application.flow.step_node.reranker_node``. The legacy node calls a
dedicated reranker model; in the refactor we order by the upstream similarity
score when no reranker model is configured (a valid baseline), and plug into a
reranker provider via ``params["reranker_config"]`` when present.
"""

from __future__ import annotations

from typing import Any

from app.workflows.nodes.base import NodeResult, StepNode


def _flatten_docs(refs: Any) -> list[dict[str, Any]]:
    """Flatten a (possibly nested) list of paragraph references into doc dicts."""
    docs: list[dict[str, Any]] = []
    if isinstance(refs, dict):
        refs = [refs]
    if not isinstance(refs, list):
        return docs
    for r in refs:
        if isinstance(r, list):
            docs.extend(_flatten_docs(r))
        elif isinstance(r, dict):
            docs.append(
                {
                    "title": r.get("title", "") or "",
                    "content": r.get("content") or r.get("page_content") or "",
                    "similarity": r.get("similarity"),
                }
            )
        elif isinstance(r, str):
            docs.append({"title": "", "content": r, "similarity": None})
    return docs


def _score_sort(docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Baseline rerank: sort by similarity desc (None scores go last)."""
    ordered = sorted(
        docs,
        key=lambda d: (d.get("similarity") is None, -(d.get("similarity") or 0)),
    )
    return [
        {
            "content": d["content"],
            "relevance_score": d.get("similarity"),
            "metadata": {"title": d["title"], "relevance_score": d.get("similarity")},
        }
        for d in ordered
    ]


class RerankNode(StepNode):
    type = "reranker-node"

    async def execute(self) -> NodeResult:
        setting = self.node_data.get("reranker_setting", {}) or {}
        top_n = int(setting.get("top_n", 3))
        similarity = float(setting.get("similarity", 0.6))
        max_chars = int(setting.get("max_paragraph_char_number", 5000))
        show_knowledge = self.node_data.get("show_knowledge", False)

        question = self.resolve(self.node_data.get("question"))
        if isinstance(question, str):
            question = self.resolve_template(question)

        refs = self.node_data.get("reranker_reference_list") or []
        if isinstance(refs, list):
            resolved_refs = [self.resolve(r) for r in refs]
        else:
            resolved_refs = [self.resolve(refs)]
        docs = _flatten_docs(resolved_refs)
        docs = [d for d in docs if d["content"]]
        if not docs:
            return NodeResult(
                {"document_list": [], "result_list": [], "result": "", "question": question},
                is_result=False,
            )

        # True reranker if configured; otherwise score-based ordering.
        reranker_cfg = self.state.params.get("reranker_config")
        if reranker_cfg:
            reranked = await self._rerank_with_provider(reranker_cfg, question, docs)
        else:
            reranked = _score_sort(docs)

        document_list = [{"content": d["content"], "metadata": {"title": d.get("title", "")}} for d in docs]

        result_list: list[dict[str, Any]] = []
        used = 0
        for d in reranked:
            score = d.get("relevance_score")
            if score is not None and score < similarity:
                continue
            content = d["content"][: max(0, max_chars - used)]
            if not content:
                continue
            used += len(content)
            result_list.append({"content": content, "metadata": d.get("metadata", {}), "relevance_score": score})
            if used >= max_chars or len(result_list) >= top_n:
                break

        result = "\n".join(item["content"] for item in result_list)
        return NodeResult(
            {
                "document_list": document_list,
                "result_list": result_list,
                "result": result,
                "question": question,
                "show_knowledge": show_knowledge,
            },
            is_result=False,
        )

    async def _rerank_with_provider(
        self, cfg: dict[str, Any], question: str, docs: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Re-rank via a configured reranker provider (best-effort).

        Falls back to score-based ordering if no reranker provider is wired in
        ``app.providers`` yet (the refactor ships the score-based baseline).
        """
        try:
            from app.providers import get_reranker
        except ImportError:
            return _score_sort(docs)

        try:
            ordered = await get_reranker(cfg["provider"], cfg["model_name"], cfg.get("credential", {})).arun(
                query=question, documents=[d["content"] for d in docs]
            )
            out: list[dict[str, Any]] = []
            for idx, item in enumerate(ordered):
                score = item.get("relevance_score") if isinstance(item, dict) else None
                out.append(
                    {
                        "content": docs[idx]["content"],
                        "relevance_score": score,
                        "metadata": {
                            "title": docs[idx]["title"],
                            "relevance_score": score,
                        },
                    }
                )
            return out
        except Exception:
            # Fall back to score-based ordering if the reranker is unavailable.
            return _score_sort(docs)
