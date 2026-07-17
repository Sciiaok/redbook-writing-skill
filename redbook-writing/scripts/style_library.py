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


class StyleLibraryError(RuntimeError):
    """Raised when the local style library contract cannot be satisfied."""


def connect_db(db_path: Path) -> sqlite3.Connection:
    """Open a SQLite connection configured for style-library access."""

    con = sqlite3.connect(Path(db_path))
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def init_db(db_path: Path) -> dict[str, object]:
    """Create or idempotently upgrade a database to the v1 schema."""

    db_path = Path(db_path)
    try:
        schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
        db_path.parent.mkdir(parents=True, exist_ok=True)
        con = connect_db(db_path)
        try:
            with con:
                con.executescript(schema_sql)
                version = con.execute("PRAGMA user_version").fetchone()[0]
        finally:
            con.close()
    except (OSError, sqlite3.Error) as exc:
        raise StyleLibraryError("schema_initialization_failed") from exc

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
    if data.get("taxonomy_version") != SCHEMA_VERSION:
        raise StyleLibraryError("taxonomy_version_mismatch")
    if any(
        not isinstance(key, str)
        or (key != "taxonomy_version" and not isinstance(value, list))
        for key, value in data.items()
    ):
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
