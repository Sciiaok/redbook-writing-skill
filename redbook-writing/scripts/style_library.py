#!/usr/bin/env python3
"""Initialize and access the local multimodal style library."""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from statistics import median
from pathlib import Path
from typing import Sequence
from urllib.parse import quote


SCHEMA_VERSION = 2
ASSETS_DIR = Path(__file__).resolve().parents[1] / "assets"
LEGACY_SCHEMA_PATH = ASSETS_DIR / "style-library-schema.sql"
LEGACY_TAXONOMY_PATH = ASSETS_DIR / "style-taxonomy-v1.json"
SCHEMA_PATH = ASSETS_DIR / "style-library-schema-v2.sql"
TAXONOMY_PATH = ASSETS_DIR / "style-taxonomy-v2.json"

TAXONOMY_KEYS = frozenset(
    {
        "taxonomy_version",
        "primary_job",
        "material_code",
        "production_constraint_code",
        "contraindication_code",
        "motive_code",
        "distribution_mode",
        "model_lifecycle_stage",
        "reviewer_independence_status",
        "asset_origin_code",
        "rights_basis_code",
        "authorization_status",
        "delivery_surface",
        "production_gate_status",
        "account_capability_code",
        "visual_feedback_reason_code",
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
        "material_code",
        "production_constraint_code",
        "contraindication_code",
        "motive_code",
        "distribution_mode",
        "asset_origin_code",
        "rights_basis_code",
        "delivery_surface",
        "account_capability_code",
        "visual_feedback_reason_code",
    }
)

REQUIRED_PRIMARY_JOBS = frozenset(
    {
        "feed_stop",
        "search_answer",
        "explain",
        "trust_build",
        "decision_support",
        "relationship_build",
        "conversion",
        "authority_statement",
    }
)


class StyleLibraryError(RuntimeError):
    """Raised when the local style library contract cannot be satisfied."""


class _CanonicalSha256AggregateV2:
    """Hash an ordered sequence using the documented compact JSON encoding."""

    def __init__(self) -> None:
        self._values: list[object] = []

    def step(self, value: object) -> None:
        self._values.append(value)

    def finalize(self) -> str:
        encoded = json.dumps(
            self._values,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()


class _MedianAggregateV2:
    """Return the numeric median while ignoring unavailable (NULL) values."""

    def __init__(self) -> None:
        self._values: list[float] = []

    def step(self, value: object) -> None:
        if value is not None:
            self._values.append(float(value))

    def finalize(self) -> float | None:
        if not self._values:
            return None
        return float(median(self._values))


def _configure_connection(con: sqlite3.Connection) -> None:
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.execute("PRAGMA recursive_triggers = ON")
    con.create_aggregate(
        "canonical_sha256_agg_v2", 1, _CanonicalSha256AggregateV2
    )
    con.create_aggregate("median_agg_v2", 1, _MedianAggregateV2)


def connect_db(db_path: Path) -> sqlite3.Connection:
    """Open a configured v2 connection; legacy databases fail closed."""

    con = sqlite3.connect(Path(db_path))
    _configure_connection(con)
    try:
        version = con.execute("PRAGMA user_version").fetchone()[0]
    except sqlite3.Error as exc:
        con.close()
        raise StyleLibraryError("schema_preflight_failed") from exc
    if version == 1:
        con.close()
        raise StyleLibraryError("schema_upgrade_required")
    if version != SCHEMA_VERSION:
        con.close()
        raise StyleLibraryError("schema_version_mismatch")
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


def _execute_sql_script(con: sqlite3.Connection, schema_sql: str) -> None:
    """Execute complete SQLite statements without executescript auto-commits."""

    pending = ""
    for line in schema_sql.splitlines(keepends=True):
        pending += line
        if sqlite3.complete_statement(pending):
            statement = pending.strip()
            pending = ""
            if statement:
                con.execute(statement)
    if pending.strip():
        raise StyleLibraryError("schema_sql_incomplete")


def _validate_schema(
    con: sqlite3.Connection, schema_sql: str, error_code: str
) -> None:
    expected = sqlite3.connect(":memory:")
    _configure_connection(expected)
    try:
        _execute_sql_script(expected, schema_sql)
        expected_objects = _normalized_schema_objects(expected)
    finally:
        expected.close()

    actual_objects = _normalized_schema_objects(con)
    if actual_objects != expected_objects:
        raise StyleLibraryError(error_code)


def _open_read_only(db_path: Path) -> sqlite3.Connection:
    uri_path = quote(str(db_path.resolve()), safe="/")
    con = sqlite3.connect(f"file:{uri_path}?mode=ro", uri=True)
    _configure_connection(con)
    return con


def _preflight_existing_database(db_path: Path) -> int:
    """Inspect an existing file read-only before any initialization write."""

    try:
        con = _open_read_only(db_path)
        try:
            version = con.execute("PRAGMA user_version").fetchone()[0]
            integrity = con.execute("PRAGMA quick_check").fetchone()[0]
            if integrity != "ok":
                raise StyleLibraryError("schema_preflight_failed")
            objects = _normalized_schema_objects(con)
            if version == 0:
                if objects:
                    raise StyleLibraryError("unversioned_database_not_empty")
                return 0
            if version == 1:
                legacy_sql = LEGACY_SCHEMA_PATH.read_text(encoding="utf-8")
                _validate_schema(con, legacy_sql, "schema_v1_invalid")
                raise StyleLibraryError("schema_upgrade_required")
            if version == SCHEMA_VERSION:
                schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
                _validate_schema(con, schema_sql, "schema_v2_invalid")
                if con.execute("PRAGMA foreign_key_check").fetchone() is not None:
                    raise StyleLibraryError("schema_v2_invalid")
                return version
            if version > SCHEMA_VERSION:
                raise StyleLibraryError("schema_version_unsupported")
            raise StyleLibraryError("schema_version_unsupported")
        finally:
            con.close()
    except StyleLibraryError:
        raise
    except (OSError, sqlite3.Error) as exc:
        raise StyleLibraryError("schema_preflight_failed") from exc


def init_db(db_path: Path) -> dict[str, object]:
    """Create v2 only in a genuinely empty v0 file, after read-only preflight."""

    # Fail before touching the database when the active vocabulary is absent,
    # malformed, or not exactly v2.
    load_taxonomy()
    db_path = Path(db_path)
    con: sqlite3.Connection | None = None
    existed_before = db_path.exists()
    before_bytes = db_path.read_bytes() if existed_before and db_path.is_file() else None
    write_started = False
    try:
        if existed_before:
            version = _preflight_existing_database(db_path)
            if version == SCHEMA_VERSION:
                return {
                    "status": "ok",
                    "schema_version": version,
                    "db": str(db_path),
                }

        db_path.parent.mkdir(parents=True, exist_ok=True)
        write_started = True
        con = sqlite3.connect(db_path)
        _configure_connection(con)
        schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
        con.execute("BEGIN IMMEDIATE")
        _execute_sql_script(con, schema_sql)
        con.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        con.commit()
        version = con.execute("PRAGMA user_version").fetchone()[0]
        _validate_schema(con, schema_sql, "schema_v2_invalid")
        if con.execute("PRAGMA foreign_key_check").fetchone() is not None:
            raise StyleLibraryError("schema_v2_invalid")
    except StyleLibraryError:
        if con is not None and con.in_transaction:
            con.rollback()
        if con is not None:
            con.close()
            con = None
        if write_started and existed_before and before_bytes is not None:
            db_path.write_bytes(before_bytes)
        elif write_started and not existed_before:
            db_path.unlink(missing_ok=True)
        raise
    except (OSError, sqlite3.Error) as exc:
        if con is not None and con.in_transaction:
            con.rollback()
        if con is not None:
            con.close()
            con = None
        if write_started and existed_before and before_bytes is not None:
            db_path.write_bytes(before_bytes)
        elif write_started and not existed_before:
            db_path.unlink(missing_ok=True)
        raise StyleLibraryError("schema_initialization_failed") from exc
    finally:
        if con is not None:
            con.close()

    if version != SCHEMA_VERSION:
        if existed_before and before_bytes is not None:
            db_path.write_bytes(before_bytes)
        elif not existed_before:
            db_path.unlink(missing_ok=True)
        raise StyleLibraryError("schema_version_mismatch")

    return {"status": "ok", "schema_version": version, "db": str(db_path)}


def load_taxonomy() -> dict[str, object]:
    """Load the exact v2 controlled vocabulary contract."""

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
    if not REQUIRED_PRIMARY_JOBS.issubset(data["primary_job"]):
        raise StyleLibraryError("taxonomy_invalid")
    return data


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    init_parser = subparsers.add_parser("init", help="initialize a v2 style database")
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
