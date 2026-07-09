"""End-to-end test for form-node interrupt + resume (no DB / no LLM).

A form node configured with ``need_user_input`` suspends the workflow when a
referenced field is missing, and the engine reports a suspended result
(``status == 423``, ``interrupted`` flag + form schema). Re-running the engine
with the missing value supplied via params clears the interrupt and the flow
completes normally — exercising the resume path.
"""

from __future__ import annotations

import asyncio

from app.workflows.engine import WorkflowEngine


def _flow() -> dict:
    return {
        "nodes": [
            {"id": "s1", "type": "start-node", "properties": {"stepName": "开始"}},
            {
                "id": "nf",
                "type": "form-node",
                "properties": {
                    "stepName": "表单",
                    "node_data": {
                        "need_user_input": True,
                        "form_field_list": [
                            {"name": "name", "value": {"node_id": "global", "fields": ["name"]}},
                        ],
                        "form_content_format": "你好 {name}",
                    },
                },
            },
            {
                "id": "r1",
                "type": "direct-reply-node",
                "properties": {"stepName": "回复", "node_data": {"content": "提交成功"}},
            },
        ],
        "edges": [
            {"sourceNodeId": "s1", "targetNodeId": "nf", "sourceAnchorId": "s1_right"},
            {"sourceNodeId": "nf", "targetNodeId": "r1", "sourceAnchorId": "nf_right"},
        ],
    }


def test_form_interrupts_when_field_missing():
    result = asyncio.run(WorkflowEngine(_flow(), {}).run())
    assert result["interrupted"] is True
    assert result["status"] == 423
    assert result["form"]["missing"] == ["name"]
    assert result["form"]["form_data"]["name"] is None


def test_form_resume_completes_with_value():
    # First run suspends.
    first = asyncio.run(WorkflowEngine(_flow(), {}).run())
    assert first["interrupted"] is True

    # Resume: supply the missing value via params (resolved as global.name).
    resumed = asyncio.run(WorkflowEngine(_flow(), {"name": "Alice"}).run())
    assert resumed.get("interrupted") is not True
    assert resumed["status"] == 200
    form_ctx = resumed["details"]["nf"]["context"]
    assert form_ctx["form_data"]["name"] == "Alice"
    assert "提交成功" in resumed["answer"]


def test_form_no_interrupt_when_not_required():
    flow = _flow()
    flow["nodes"][1]["properties"]["node_data"]["need_user_input"] = False
    result = asyncio.run(WorkflowEngine(flow, {}).run())
    assert result.get("interrupted") is not True
    assert result["status"] == 200
