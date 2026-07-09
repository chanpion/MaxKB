"""Tests for trigger handler wiring (no DB / no network required)."""

from app.trigger.handlers import _parameter_to_inputs, _to_uuid, register_trigger_handlers
from app.trigger.manager import manager


def test_to_uuid_accepts_variants():
    import uuid

    raw = uuid.uuid4()
    assert _to_uuid(raw) == raw
    assert _to_uuid(str(raw)) == raw
    assert _to_uuid(None) is None
    assert _to_uuid("not-a-uuid") is None


def test_parameter_to_inputs_flatten():
    params = [
        {"name": "q", "value": "hello"},
        {"single": 1},
    ]
    assert _parameter_to_inputs(params) == {"q": "hello", "single": 1}
    assert _parameter_to_inputs(None) == {}
    assert _parameter_to_inputs("x") == {}


def test_register_trigger_handlers_wires_both_cases():
    # manager is a process-wide singleton; registration is idempotent.
    register_trigger_handlers()
    for key in ("APPLICATION", "TOOL", "application", "tool"):
        assert key in manager._handlers
