"""Shared helper that builds a nested folder tree rooted at a synthetic root.

The legacy MaxKB frontend (tools / knowledge / application pages) expects the
left-side folder tree to start from a single ``根目录`` (root) node whose
``id`` equals the workspace id and whose ``parent_id`` is ``None``. Real folders
then nest underneath it. The refactor storage layer does not keep a physical
row for that root, so we synthesize it here to keep the UI behaviour identical
to the Django backend.
"""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any


def _folder_node(f: Any) -> dict[str, Any]:
    """Serialize a folder ORM row into the node dict the frontend tree expects."""
    return {
        "id": f.id,
        "name": f.name,
        "desc": f.desc,
        "user_id": f.user_id,
        "workspace_id": f.workspace_id,
        "parent_id": f.parent_id,
        "create_time": getattr(f, "create_time", None),
        "update_time": getattr(f, "update_time", None),
        "children": [],
    }


def build_folder_tree(folders: Sequence[Any], workspace_id: str) -> list[dict[str, Any]]:
    """Return ``[root_node]`` — a single tree rooted at the synthetic ``根目录``.

    Each real folder becomes a node; nodes are nested under their ``parent_id``.
    Folders whose ``parent_id`` is null/missing become direct children of the
    root. This mirrors the legacy Django folder serializer exactly so the
    frontend's ``FolderVirtualizedTree`` (which reads ``res.data[0]`` as the
    current folder) works unchanged.
    """
    nodes: dict[str, dict[str, Any]] = {f.id: _folder_node(f) for f in folders}
    roots: list[dict[str, Any]] = []
    for f in folders:
        node = nodes[f.id]
        parent = nodes.get(f.parent_id) if f.parent_id else None
        if parent is not None:
            parent["children"].append(node)
        else:
            roots.append(node)

    root: dict[str, Any] = {
        "id": workspace_id,
        "name": "根目录",
        "desc": "",
        "user_id": None,
        "workspace_id": workspace_id,
        "parent_id": None,
        "create_time": None,
        "update_time": None,
        "children": roots,
    }
    return [root]


def is_root_folder(folder_id: str | None, workspace_id: str = "default") -> bool:
    """True when ``folder_id`` refers to the synthetic root (== workspace id).

    Used by list endpoints so selecting the ``根目录`` node returns *all*
    resources in the workspace — matching the legacy ``get_query_set`` behaviour
    where ``folder_id == workspace_id`` disables the per-folder filter.
    """
    return folder_id is None or folder_id == workspace_id
