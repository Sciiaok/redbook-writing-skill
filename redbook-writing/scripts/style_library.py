#!/usr/bin/env python3
"""Initialize and access the local multimodal style library."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Sequence


SCHEMA_VERSION = 1
ASSETS_DIR = Path(__file__).resolve().parents[1] / "assets"
SCHEMA_PATH = ASSETS_DIR / "style-library-schema.sql"
TAXONOMY_PATH = ASSETS_DIR / "style-taxonomy-v1.json"

TAXONOMY_KEYS = frozenset(
    {
        "taxonomy_version",
        "carrier",
        "slide_role",
        "composition",
        "dominant_material",
        "background_type",
        "subject_presence",
        "layout_structure",
        "text_density",
        "hierarchy_levels",
        "alignment",
        "spacing_pattern",
        "font_feel",
        "decoration_types",
        "annotation_style",
        "imperfection_signals",
        "image_text_relationship",
        "text_surface",
        "point_of_view",
        "audience_address",
        "register",
        "sentence_length_pattern",
        "line_break_pattern",
        "punctuation_pattern",
        "emoji_pattern",
        "hook_move",
        "narrative_moves",
        "evidence_move",
        "payoff_move",
        "cta_move",
        "image_caption_division",
        "rule_type",
    }
)

OPEN_ENDED_TAXONOMY_KEYS = frozenset(
    {
        "carrier",
        "composition",
        "dominant_material",
        "background_type",
        "subject_presence",
        "layout_structure",
        "alignment",
        "spacing_pattern",
        "font_feel",
        "decoration_types",
        "annotation_style",
        "imperfection_signals",
        "image_text_relationship",
        "text_surface",
        "point_of_view",
        "audience_address",
        "register",
        "sentence_length_pattern",
        "line_break_pattern",
        "punctuation_pattern",
        "emoji_pattern",
        "hook_move",
        "narrative_moves",
        "evidence_move",
        "payoff_move",
        "cta_move",
        "image_caption_division",
    }
)


class StyleLibraryError(RuntimeError):
    """Raised when the local style library contract cannot be satisfied."""


def connect_db(db_path: Path) -> sqlite3.Connection:
    """Open a SQLite connection configured for style-library access."""

    con = sqlite3.connect(Path(db_path))
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def _normalized_schema_objects(
    con: sqlite3.Connection,
) -> dict[str, tuple[str, str, str]]:
    objects: dict[str, tuple[str, str, str]] = {}
    rows = con.execute(
        """
        SELECT type, name, tbl_name, sql
        FROM sqlite_master
        WHERE name NOT LIKE 'sqlite_%'
          AND type IN ('table', 'index', 'trigger', 'view')
        """
    )
    for object_type, name, table_name, sql in rows:
        normalized_sql = " ".join((sql or "").split())
        objects[name] = (object_type, table_name, normalized_sql)
    return objects


def _validate_v1_schema(con: sqlite3.Connection, schema_sql: str) -> None:
    expected = connect_db(Path(":memory:"))
    try:
        expected.executescript(schema_sql)
        expected_objects = _normalized_schema_objects(expected)
    finally:
        expected.close()

    actual_objects = _normalized_schema_objects(con)
    if any(
        actual_objects.get(name) != definition
        for name, definition in expected_objects.items()
    ):
        raise StyleLibraryError("schema_v1_invalid")


def init_db(db_path: Path) -> dict[str, object]:
    """Create v1 only in an empty database, or validate an existing v1."""

    db_path = Path(db_path)
    con: sqlite3.Connection | None = None
    try:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        con = connect_db(db_path)
        version = con.execute("PRAGMA user_version").fetchone()[0]

        if version > SCHEMA_VERSION:
            raise StyleLibraryError("schema_version_unsupported")
        if version == 0:
            has_user_objects = con.execute(
                """
                SELECT 1 FROM sqlite_master
                WHERE name NOT LIKE 'sqlite_%'
                LIMIT 1
                """
            ).fetchone()
            if has_user_objects is not None:
                raise StyleLibraryError("unversioned_database_not_empty")

        schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
        if version == SCHEMA_VERSION:
            _validate_v1_schema(con, schema_sql)
        elif version == 0:
            con.executescript(
                "BEGIN IMMEDIATE;\n"
                + schema_sql
                + "\nPRAGMA user_version = 1;\nCOMMIT;"
            )
            version = con.execute("PRAGMA user_version").fetchone()[0]
            _validate_v1_schema(con, schema_sql)
        else:
            raise StyleLibraryError("schema_version_unsupported")
    except StyleLibraryError:
        if con is not None and con.in_transaction:
            con.rollback()
        raise
    except (OSError, sqlite3.Error) as exc:
        if con is not None and con.in_transaction:
            con.rollback()
        raise StyleLibraryError("schema_initialization_failed") from exc
    finally:
        if con is not None:
            con.close()

    if version != SCHEMA_VERSION:
        raise StyleLibraryError("schema_version_mismatch")
    return {"status": "ok", "schema_version": version, "db": str(db_path)}


def load_taxonomy() -> dict[str, object]:
    """Load taxonomy v1 and reject the wrong version or malformed content."""

    try:
        data = json.loads(TAXONOMY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StyleLibraryError("taxonomy_load_failed") from exc

    if not isinstance(data, dict):
        raise StyleLibraryError("taxonomy_invalid")
    if set(data) != TAXONOMY_KEYS:
        raise StyleLibraryError("taxonomy_invalid")
    version = data.get("taxonomy_version")
    if type(version) is not int or version != SCHEMA_VERSION:
        raise StyleLibraryError("taxonomy_version_mismatch")

    for key in TAXONOMY_KEYS - {"taxonomy_version"}:
        values = data[key]
        if not isinstance(values, list) or not values:
            raise StyleLibraryError("taxonomy_invalid")
        if any(type(value) is not str or not value.strip() for value in values):
            raise StyleLibraryError("taxonomy_invalid")
        if len(values) != len(set(values)):
            raise StyleLibraryError("taxonomy_invalid")

    for key in OPEN_ENDED_TAXONOMY_KEYS:
        values = data[key]
        if "unknown" not in values or "other" not in values:
            raise StyleLibraryError("taxonomy_invalid")
    if "other" not in data["slide_role"]:
        raise StyleLibraryError("taxonomy_invalid")
    for key in ("text_density", "hierarchy_levels"):
        if "unknown" not in data[key]:
            raise StyleLibraryError("taxonomy_invalid")
    return data


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    init_parser = subparsers.add_parser("init", help="initialize a v1 style database")
    init_parser.add_argument("db", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "init":
            result = init_db(args.db)
        else:  # pragma: no cover - argparse constrains commands.
            raise StyleLibraryError("unsupported_command")
    except StyleLibraryError as exc:
        print(
            json.dumps({"status": "error", "error": str(exc)}, sort_keys=True),
            file=sys.stderr,
        )
        return 1

    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
