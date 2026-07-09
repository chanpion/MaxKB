# coding=utf-8
"""Condition/assertion comparators ported from ``apps/application/flow/compare``.

These are pure functions so the workflow engine can evaluate condition-node
branches without the Django/DRF stack. Each handler implements ``compare(source,
value) -> bool``; ``do_assertion`` mirrors ``flow.compare.do_assertion``.
"""
from __future__ import annotations

import re
from typing import Any, Callable, Dict, List


class _Compare:
    def compare(self, source: Any, value: Any) -> bool:  # pragma: no cover - overridden
        raise NotImplementedError


class IsNullCompare(_Compare):
    def compare(self, source, value):
        return source is None or source == ""


class IsNotNullCompare(_Compare):
    def compare(self, source, value):
        return not IsNullCompare().compare(source, value)


class ContainCompare(_Compare):
    def compare(self, source, value):
        return str(value) in str(source or "")


class NotContainCompare(_Compare):
    def compare(self, source, value):
        return not ContainCompare().compare(source, value)


class EqualCompare(_Compare):
    def compare(self, source, value):
        left, right = _coerce(source), _coerce(value)
        if isinstance(left, (int, float)) and isinstance(right, (int, float)):
            return left == right
        return str(source) == str(value)


class NotEqualCompare(_Compare):
    def compare(self, source, value):
        return not EqualCompare().compare(source, value)


class _NumCompare(_Compare):
    _op: Callable[[Any, Any], bool]

    def compare(self, source, value):
        try:
            return self._op(float(source), float(value))
        except (TypeError, ValueError):
            return False


class GECompare(_NumCompare):
    _op = staticmethod(lambda a, b: a >= b)


class GTCompare(_NumCompare):
    _op = staticmethod(lambda a, b: a > b)


class LECompare(_NumCompare):
    _op = staticmethod(lambda a, b: a <= b)


class LTCompare(_NumCompare):
    _op = staticmethod(lambda a, b: a < b)


class LenEqualCompare(_Compare):
    def compare(self, source, value):
        try:
            return len(str(source)) == int(value)
        except (TypeError, ValueError):
            return False


class LenGECompare(_Compare):
    def compare(self, source, value):
        try:
            return len(str(source)) >= int(value)
        except (TypeError, ValueError):
            return False


class LenGTCompare(_Compare):
    def compare(self, source, value):
        try:
            return len(str(source)) > int(value)
        except (TypeError, ValueError):
            return False


class LenLECompare(_Compare):
    def compare(self, source, value):
        try:
            return len(str(source)) <= int(value)
        except (TypeError, ValueError):
            return False


class LenLTCompare(_Compare):
    def compare(self, source, value):
        try:
            return len(str(source)) < int(value)
        except (TypeError, ValueError):
            return False


class IsTrueCompare(_Compare):
    def compare(self, source, value):
        return source is True or str(source).lower() == "true"


class IsNotTrueCompare(_Compare):
    def compare(self, source, value):
        return not IsTrueCompare().compare(source, value)


class StartWithCompare(_Compare):
    def compare(self, source, value):
        return str(source or "").startswith(str(value))


class EndWithCompare(_Compare):
    def compare(self, source, value):
        return str(source or "").endswith(str(value))


class RegexCompare(_Compare):
    def compare(self, source, value):
        try:
            return re.search(str(value), str(source or "")) is not None
        except re.error:
            return False


class WildcardCompare(_Compare):
    """Support ``*`` (any chars) and ``?`` (single char) wildcards."""

    def compare(self, source, value):
        pattern = "^" + re.escape(str(value)).replace(r"\*", ".*").replace(r"\?", ".") + "$"
        try:
            return re.match(pattern, str(source or "")) is not None
        except re.error:
            return False


_COMPARE_HANDLERS: Dict[str, _Compare] = {
    "is_null": IsNullCompare(),
    "is_not_null": IsNotNullCompare(),
    "contain": ContainCompare(),
    "not_contain": NotContainCompare(),
    "eq": EqualCompare(),
    "not_eq": NotEqualCompare(),
    "ge": GECompare(),
    "gt": GTCompare(),
    "le": LECompare(),
    "lt": LTCompare(),
    "len_eq": LenEqualCompare(),
    "len_ge": LenGECompare(),
    "len_gt": LenGTCompare(),
    "len_le": LenLECompare(),
    "len_lt": LenLTCompare(),
    "is_true": IsTrueCompare(),
    "is_not_true": IsNotTrueCompare(),
    "start_with": StartWithCompare(),
    "end_with": EndWithCompare(),
    "regex": RegexCompare(),
    "wildcard": WildcardCompare(),
}


def _coerce(value: Any):
    try:
        if isinstance(value, str) and value.strip() != "":
            if "." in value:
                return float(value)
            return int(value)
    except (TypeError, ValueError):
        pass
    return value


def compare(source_value: Any, compare_type: str, target_value: Any) -> bool:
    handler = _COMPARE_HANDLERS.get(compare_type)
    if handler is None:
        raise RuntimeError(f"Unknown compare handler '{compare_type}'")
    return handler.compare(source_value, target_value)


def do_assertion(
    get_field: Callable[[List[str]], Any],
    resolve_template: Callable[[str], str],
    condition: str,
    condition_list: List[Dict[str, Any]],
) -> bool:
    """Mirror ``flow.compare.do_assertion``.

    ``get_field`` resolves a reference field list to its value; ``resolve_template``
    renders a value that may itself contain ``{Node.field}`` placeholders.
    """
    b = False if condition == "and" else True
    for row in condition_list:
        value = row.get("value")
        if isinstance(value, str):
            try:
                value = resolve_template(value)
            except Exception:
                pass
        field_value = None
        try:
            field_value = get_field(row.get("field"))
        except Exception:
            pass
        if compare(field_value, row.get("compare"), value) is b:
            return b
    return not b
