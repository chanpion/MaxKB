#!/usr/bin/env python3
# coding=utf-8
"""CI migration guard for the MaxKB FastAPI backend.

Scans every Alembic migration file under ``alembic/versions`` and FAILS the build
if it detects destructive operations that could corrupt the shared PostgreSQL
data carried over from the legacy Django backend:

  * ``drop_table`` / ``drop_column`` (DropTableOp / DropColumnOp / op.drop_*)
  * column type changes (``alter_column`` carrying ``type_`` / ``existing_type``)

Incremental migrations are only allowed to ADD columns / indexes. Any intended
destructive change requires human review: remove the violating lines, get
approval, then re-run.
"""
import re
import sys
from pathlib import Path

VERSIONS_DIR = Path(__file__).resolve().parents[1] / "alembic" / "versions"

# drop operations
DROP_PATTERN = re.compile(
    r"drop_(table|column)"
    r"|op\.drop_"
    r"|DropTableOp|DropColumnOp"
    r"|\.drop_table\(|\.drop_column\("
)

# column type change inside alter_column
ALTER_TYPE_PATTERN = re.compile(r"alter_column\([^)]*?(type_|existing_type)", re.DOTALL)


def main() -> int:
    if not VERSIONS_DIR.exists():
        print(f"[migration-guard] versions dir not found: {VERSIONS_DIR}")
        return 0

    violations: list[str] = []
    for path in sorted(VERSIONS_DIR.glob("*.py")):
        text = path.read_text(encoding="utf-8")
        for ln, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if DROP_PATTERN.search(line):
                violations.append(f"{path.name}:{ln}: drop operation detected -> {stripped}")
            if ALTER_TYPE_PATTERN.search(line):
                violations.append(f"{path.name}:{ln}: column type change detected -> {stripped}")

    if violations:
        print("[migration-guard] FAILED: destructive migration operations found:")
        for v in violations:
            print("  - " + v)
        print(
            "\nDestructive migrations (drop_/column type change) are blocked by CI.\n"
            "If intentional, remove the violating lines, obtain manual review, then re-run."
        )
        return 1

    print("[migration-guard] OK: no drop_ or column type changes detected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
