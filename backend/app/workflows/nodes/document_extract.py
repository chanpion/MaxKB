"""Document-extract node: parses a raw document into plain text.

Reuses ``app.rag.parsers.parse_file`` (the same parser suite used by the
ingestion pipeline — PDF / DOCX / XLSX / HTML / CSV / ZIP / markdown). The
extracted text is surfaced for downstream nodes (e.g. knowledge-write or an LLM
node) without duplicating parsing logic.
"""

from __future__ import annotations

from app.workflows.nodes.base import NodeResult, StepNode


class DocumentExtractNode(StepNode):
    type = "document-extract-node"

    async def execute(self) -> NodeResult:
        filename = self.resolve(self.node_data.get("filename")) or "document.txt"
        content = self.resolve(self.node_data.get("content"))
        if isinstance(content, str):
            content = content.encode("utf-8")
        elif content is None:
            content = b""

        from app.rag.parsers import parse_file

        parsed = parse_file(str(filename), content)
        text = "\n\n".join(p.content for p in parsed)

        return NodeResult(
            {
                "result": text,
                "content": text,
                "document_list": [p.name for p in parsed],
            },
            is_result=self.is_result if self.is_result is not None else False,
        )
