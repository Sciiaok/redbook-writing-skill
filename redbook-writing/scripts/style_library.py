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
        "traffic_stage",
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

TRAFFIC_STAGES = frozenset(
    {
        "feed_stop",
        "read_through",
        "save_share",
        "comment_cocreation",
        "profile_follow",
    }
)

LEDGER_TOP_LEVEL_KEYS = frozenset(
    {
        "observation_id", "capture_date", "review_by", "surface",
        "query_context", "query_fingerprint", "source_url", "platform_note_id",
        "note_id_status", "library_post_id", "library_account_id",
        "taxonomy_version", "carrier", "primary_job", "material_codes",
        "production_constraint_codes", "contraindication_codes", "mechanism",
        "page_observations", "performance_recomputability", "derived_tier",
        "baseline_multiple", "performance_receipt", "visible_metrics",
        "asset_sha256s", "visual_observation_ids", "copy_observation_ids",
        "evidence_role", "counterexample_or_boundary_ids", "starter_eligible",
        "qualification_status", "limitations", "taxonomy_notes",
    }
)


def _canonical_json(value: object) -> str:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


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
    if set(data["traffic_stage"]) != TRAFFIC_STAGES:
        raise StyleLibraryError("taxonomy_invalid")
    return data


def _table_count(con: sqlite3.Connection, table: str) -> int:
    exists = con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()
    if exists is None:
        return 0
    return int(con.execute(f'SELECT count(*) FROM "{table}"').fetchone()[0])


def status_db(db_path: Path) -> dict[str, object]:
    """Report what exists without upgrading unverified observations to evidence."""

    taxonomy = load_taxonomy()
    con = connect_db(db_path)
    try:
        ledger_n = _table_count(con, "sanitized_style_ledger_entries")
        counts = {
            "sanitized_ledger_entries": ledger_n,
            "qualified_style_rules": 0,
            "published_baselines": _table_count(
                con, "baseline_snapshot_publications"
            ),
            "draft_bindings": _table_count(con, "draft_style_bindings"),
            "style_assets": _table_count(con, "style_assets"),
        }
    finally:
        con.close()
    return {
        "status": "ok",
        "schema_version": SCHEMA_VERSION,
        "taxonomy_version": taxonomy["taxonomy_version"],
        "counts": counts,
        "traffic_stage_qualified_counts": {
            stage: 0 for stage in sorted(TRAFFIC_STAGES)
        },
        "release_readiness": {
            "state": "needs_style_research",
            "reason_codes": [
                "no_published_qualified_rule",
                "sanitized_ledger_is_candidate_only",
            ],
            "checkpoint": (
                "publish a recomputable same-job contrast with page hashes, "
                "rights status, baseline members, and typed evidence"
            ),
        },
    }


def _require_code_list(
    record: dict[str, object], key: str, allowed: set[str] | frozenset[str]
) -> list[str]:
    values = record.get(key)
    if (
        not isinstance(values, list)
        or not values
        or any(type(item) is not str or item not in allowed for item in values)
        or len(values) != len(set(values))
    ):
        raise StyleLibraryError("ledger_taxonomy_invalid")
    return sorted(values)


def _validate_ledger_record(
    record: object, taxonomy: dict[str, object]
) -> dict[str, object]:
    if not isinstance(record, dict) or not set(record).issubset(LEDGER_TOP_LEVEL_KEYS):
        raise StyleLibraryError("ledger_record_invalid")
    required = LEDGER_TOP_LEVEL_KEYS - {"taxonomy_notes"}
    if not required.issubset(record):
        raise StyleLibraryError("ledger_record_invalid")
    observation_id = record.get("observation_id")
    if (
        type(observation_id) is not str
        or len(observation_id) != 9
        or not observation_id.startswith("O-XHS-")
        or not observation_id[6:].isdigit()
        or not 1 <= int(observation_id[6:]) <= 12
    ):
        raise StyleLibraryError("ledger_observation_id_out_of_scope")
    if record.get("taxonomy_version") != SCHEMA_VERSION:
        raise StyleLibraryError("ledger_taxonomy_invalid")
    if record.get("carrier") not in taxonomy["carrier"]:
        raise StyleLibraryError("ledger_taxonomy_invalid")
    if record.get("primary_job") not in taxonomy["primary_job"]:
        raise StyleLibraryError("ledger_taxonomy_invalid")
    material_codes = _require_code_list(
        record, "material_codes", set(taxonomy["material_code"])
    )
    constraint_codes = _require_code_list(
        record,
        "production_constraint_codes",
        set(taxonomy["production_constraint_code"]),
    )
    contraindication_codes = _require_code_list(
        record, "contraindication_codes", set(taxonomy["contraindication_code"])
    )
    mechanism = record.get("mechanism")
    metrics = record.get("visible_metrics")
    pages = record.get("page_observations")
    if (
        not isinstance(mechanism, dict)
        or mechanism.get("claim_kind") not in {"task_fit", "series_constant"}
        or mechanism.get("performance_evidence_scope")
        not in {"not_performance_evidence", "public_proxy_association"}
        or not isinstance(metrics, dict)
        or metrics.get("visibility_scope") != "public_proxy"
        or metrics.get("traffic_verdict") not in {"unavailable", "not_applicable"}
        or not isinstance(pages, list)
        or not pages
    ):
        raise StyleLibraryError("ledger_record_invalid")
    forbidden = (
        record.get("performance_receipt") is not None
        or record.get("asset_sha256s") != []
        or record.get("visual_observation_ids") != []
        or record.get("copy_observation_ids") != []
        or any(
            not isinstance(page, dict)
            or page.get("asset_sha256") is not None
            or page.get("capture_status") != "observed_unhashed"
            for page in pages
        )
    )
    if forbidden:
        raise StyleLibraryError("ledger_forbidden_evidence_claim")
    if (
        record.get("qualification_status") != "ineligible_unverified"
        or record.get("performance_recomputability") != "unverified"
        or record.get("derived_tier") != "unknown"
        or record.get("starter_eligible") is not False
    ):
        raise StyleLibraryError("ledger_qualification_forgery")
    for key in (
        "library_post_id", "library_account_id", "capture_date", "review_by",
        "query_fingerprint", "evidence_role",
    ):
        if type(record.get(key)) is not str or not str(record[key]).strip():
            raise StyleLibraryError("ledger_record_invalid")
    normalized = dict(record)
    normalized["material_codes"] = material_codes
    normalized["production_constraint_codes"] = constraint_codes
    normalized["contraindication_codes"] = contraindication_codes
    return normalized


def ingest_ledger(db_path: Path, jsonl_path: Path) -> dict[str, object]:
    """Import only sanitized O-XHS-001..012 candidate rows, never evidence assets."""

    taxonomy = load_taxonomy()
    try:
        raw = Path(jsonl_path).read_bytes()
        records = [
            _validate_ledger_record(json.loads(line), taxonomy)
            for line in raw.decode("utf-8").splitlines()
            if line.strip()
        ]
    except StyleLibraryError:
        raise
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise StyleLibraryError("ledger_load_failed") from exc
    if not records:
        raise StyleLibraryError("ledger_empty")
    ids = [str(record["observation_id"]) for record in records]
    if len(ids) != len(set(ids)):
        raise StyleLibraryError("ledger_duplicate_observation_id")
    records = sorted(records, key=lambda record: record["observation_id"])
    canonical_records = [_canonical_json(record) for record in records]
    record_hashes = [_sha256_text(payload) for payload in canonical_records]
    bundle_sha = _sha256_text(_canonical_json(record_hashes))
    source_sha = hashlib.sha256(raw).hexdigest()
    rows = sorted(
        zip(records, canonical_records, record_hashes),
        key=lambda item: item[0]["observation_id"],
    )
    con = connect_db(db_path)
    try:
        con.execute("BEGIN IMMEDIATE")
        receipt = con.execute(
            "SELECT record_count,source_file_sha256 FROM sanitized_ledger_ingests "
            "WHERE input_bundle_sha256=?",
            (bundle_sha,),
        ).fetchone()
        if receipt is not None:
            stored_count = con.execute(
                "SELECT count(*) FROM sanitized_style_ledger_entries "
                "WHERE input_bundle_sha256=?",
                (bundle_sha,),
            ).fetchone()[0]
            if int(receipt["record_count"]) != len(rows) or stored_count != len(rows):
                raise StyleLibraryError("ledger_receipt_mismatch")
            con.rollback()
            return {
                "status": "idempotent",
                "record_count": len(rows),
                "input_bundle_sha256": bundle_sha,
            }
        placeholders = ",".join("?" for _ in ids)
        if con.execute(
            f"SELECT 1 FROM sanitized_style_ledger_entries "
            f"WHERE observation_id IN ({placeholders}) LIMIT 1",
            ids,
        ).fetchone() is not None:
            raise StyleLibraryError("ledger_duplicate_conflict")
        con.execute(
            "INSERT INTO sanitized_ledger_ingests("
            "input_bundle_sha256,source_file_sha256,record_count) VALUES (?,?,?)",
            (bundle_sha, source_sha, len(rows)),
        )
        for record, canonical, record_sha in rows:
            mechanism = record["mechanism"]
            metrics = record["visible_metrics"]
            con.execute(
                """
                INSERT INTO sanitized_style_ledger_entries(
                    observation_id,input_bundle_sha256,library_post_id,
                    library_account_id,capture_date,review_by,query_fingerprint,
                    carrier,primary_job,traffic_stage,material_codes_json,
                    production_constraint_codes_json,contraindication_codes_json,
                    claim_kind,performance_evidence_scope,evidence_role,
                    qualification_status,performance_recomputability,derived_tier,
                    starter_eligible,visibility_scope,traffic_verdict,
                    record_sha256,record_json
                ) VALUES (?,?,?,?,?,?,?,?,?,NULL,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    record["observation_id"], bundle_sha, record["library_post_id"],
                    record["library_account_id"], record["capture_date"],
                    record["review_by"], record["query_fingerprint"],
                    record["carrier"], record["primary_job"],
                    _canonical_json(record["material_codes"]),
                    _canonical_json(record["production_constraint_codes"]),
                    _canonical_json(record["contraindication_codes"]),
                    mechanism["claim_kind"], mechanism["performance_evidence_scope"],
                    record["evidence_role"], record["qualification_status"],
                    record["performance_recomputability"], record["derived_tier"],
                    0, metrics["visibility_scope"], metrics["traffic_verdict"],
                    record_sha, canonical,
                ),
            )
        con.commit()
    except StyleLibraryError:
        con.rollback()
        raise
    except sqlite3.Error as exc:
        con.rollback()
        raise StyleLibraryError("ledger_ingest_failed") from exc
    finally:
        con.close()
    return {
        "status": "imported",
        "record_count": len(rows),
        "input_bundle_sha256": bundle_sha,
    }


def _validate_request_codes(
    values: Sequence[str], allowed: Sequence[str], error: str
) -> list[str]:
    normalized = sorted(set(values))
    if any(value not in allowed for value in normalized):
        raise StyleLibraryError(error)
    return normalized


def query_library(
    db_path: Path,
    *,
    carrier: str,
    primary_job: str,
    available_material_codes: Sequence[str],
    active_constraint_codes: Sequence[str],
    traffic_stage: str | None = None,
) -> dict[str, object]:
    """Audit every candidate; never relax carrier, job, stage, or resources."""

    taxonomy = load_taxonomy()
    if carrier not in taxonomy["carrier"]:
        raise StyleLibraryError("query_carrier_invalid")
    if primary_job not in taxonomy["primary_job"]:
        raise StyleLibraryError("query_primary_job_invalid")
    if traffic_stage is not None and traffic_stage not in TRAFFIC_STAGES:
        raise StyleLibraryError("query_traffic_stage_invalid")
    materials = set(_validate_request_codes(
        available_material_codes, taxonomy["material_code"], "query_material_invalid"
    ))
    constraints = set(_validate_request_codes(
        active_constraint_codes,
        taxonomy["production_constraint_code"],
        "query_constraint_invalid",
    ))
    con = connect_db(db_path)
    try:
        rows = con.execute(
            "SELECT * FROM sanitized_style_ledger_entries ORDER BY observation_id"
        ).fetchall()
    finally:
        con.close()
    audit: list[dict[str, object]] = []
    exact_scope_n = 0
    for row in rows:
        reasons: list[str] = []
        if row["carrier"] != carrier:
            reasons.append("carrier_mismatch")
        if row["primary_job"] != primary_job:
            reasons.append("primary_job_mismatch")
        if traffic_stage is not None:
            if row["traffic_stage"] is None:
                reasons.append("traffic_stage_unverified")
            elif row["traffic_stage"] != traffic_stage:
                reasons.append("traffic_stage_mismatch")
        required_materials = set(json.loads(row["material_codes_json"]))
        required_constraints = set(
            json.loads(row["production_constraint_codes_json"])
        )
        reasons.extend(
            f"material_unavailable:{code}"
            for code in sorted(required_materials - materials)
        )
        reasons.extend(
            f"constraint_inactive:{code}"
            for code in sorted(required_constraints - constraints)
        )
        if not reasons:
            exact_scope_n += 1
        reasons.extend(
            ["qualification_ineligible_unverified", "not_published_qualified_rule"]
        )
        audit.append(
            {
                "observation_id": row["observation_id"],
                "carrier": row["carrier"],
                "primary_job": row["primary_job"],
                "traffic_stage": row["traffic_stage"],
                "reason_codes": reasons,
            }
        )
    return {
        "status": "needs_style_research",
        "requested_scope": {
            "carrier": carrier,
            "primary_job": primary_job,
            "traffic_stage": traffic_stage,
            "available_material_codes": sorted(materials),
            "active_constraint_codes": sorted(constraints),
        },
        "candidate_count": len(audit),
        "exact_scope_candidate_count": exact_scope_n,
        "eligible_count": 0,
        "rejection_audit": audit,
        "checkpoint": (
            "capture and publish a qualified same-stage rule bundle; "
            "candidate ledger rows cannot bind drafts"
        ),
    }


def bind_draft(
    db_path: Path,
    *,
    draft_id: str,
    carrier: str,
    primary_job: str,
    available_material_codes: Sequence[str],
    active_constraint_codes: Sequence[str],
    traffic_stage: str | None = None,
) -> dict[str, object]:
    if not draft_id.strip():
        raise StyleLibraryError("draft_id_invalid")
    query_library(
        db_path,
        carrier=carrier,
        primary_job=primary_job,
        available_material_codes=available_material_codes,
        active_constraint_codes=active_constraint_codes,
        traffic_stage=traffic_stage,
    )
    raise StyleLibraryError("no_published_qualified_rule")


def derive_tier(
    db_path: Path, post_observation_id: str, baseline_snapshot_id: str
) -> dict[str, object]:
    """Derive relative tier from one closed baseline without target leakage."""

    con = connect_db(db_path)
    try:
        target = con.execute(
            """
            SELECT observation.*, post.library_post_id AS target_library_post_id,
                   metric.metric_value AS target_metric_value,
                   metric.visibility_scope, definition.business_objective,
                   definition.primary_job,
                   definition.traffic_stage AS definition_traffic_stage,
                   definition.tier_rules_json,
                   definition.definition_sha256
            FROM style_post_observations AS observation
            JOIN style_posts AS post
              ON post.library_post_id=observation.library_post_id
            JOIN post_metrics AS metric
              ON metric.post_metric_id=observation.target_post_metric_id
             AND metric.post_observation_id=observation.post_observation_id
             AND metric.metric_name=observation.target_metric_name
            JOIN performance_definitions AS definition
              ON definition.performance_definition_id=observation.performance_definition_id
             AND definition.metric_name=observation.target_metric_name
            WHERE observation.post_observation_id=?
              AND observation.observation_state='complete'
            """,
            (post_observation_id,),
        ).fetchone()
        if target is None:
            raise StyleLibraryError("target_observation_not_complete")
        publication = con.execute(
            """
            SELECT publication.*, snapshot.sample_n, snapshot.median_value
            FROM baseline_snapshot_publications AS publication
            JOIN account_baseline_snapshots AS snapshot
              ON snapshot.baseline_snapshot_id=publication.baseline_snapshot_id
            WHERE publication.baseline_snapshot_id=?
              AND publication.library_account_id=?
              AND publication.performance_definition_id=?
              AND publication.metric_name=?
            """,
            (
                baseline_snapshot_id, target["library_account_id"],
                target["performance_definition_id"], target["target_metric_name"],
            ),
        ).fetchone()
        if publication is None:
            raise StyleLibraryError("published_baseline_not_found")
        if (
            target["baseline_snapshot_id"] != baseline_snapshot_id
            or target["baseline_snapshot_sha256"]
            != publication["baseline_snapshot_sha256"]
        ):
            raise StyleLibraryError("target_baseline_binding_mismatch")
        members = con.execute(
            """
            SELECT member.member_post_observation_id,member.member_post_metric_id,
                   observation.library_post_id,metric.visibility_scope
            FROM account_baseline_members AS member
            JOIN style_post_observations AS observation
              ON observation.post_observation_id=member.member_post_observation_id
            JOIN post_metrics AS metric
              ON metric.post_metric_id=member.member_post_metric_id
            WHERE member.baseline_snapshot_id=?
              AND member.inclusion_status='included'
            ORDER BY member.member_ordinal
            """,
            (baseline_snapshot_id,),
        ).fetchall()
        if any(
            member["library_post_id"] == target["target_library_post_id"]
            for member in members
        ):
            raise StyleLibraryError("baseline_target_post_contamination")
        objective = target["business_objective"]
        metric_name = target["target_metric_name"]
        visibility = target["visibility_scope"]
        if objective == "traffic_first":
            if (
                target["primary_job"] != "feed_stop"
                or target["definition_traffic_stage"] != "feed_stop"
                or metric_name not in {"impressions", "reach"}
                or visibility != "first_party_analytics"
                or any(m["visibility_scope"] != "first_party_analytics" for m in members)
            ):
                raise StyleLibraryError("traffic_definition_invalid")
            traffic_stage: str | None = "feed_stop"
        elif objective == "engagement_proxy":
            if (
                metric_name != "engagement_proxy"
                or visibility != "public_proxy"
                or any(m["visibility_scope"] != "public_proxy" for m in members)
            ):
                raise StyleLibraryError("public_proxy_definition_invalid")
            traffic_stage = None
        else:
            raise StyleLibraryError("business_objective_invalid")
        median_value = publication["median_value"]
        if median_value is None or float(median_value) <= 0:
            raise StyleLibraryError("baseline_median_invalid")
        try:
            rules = json.loads(target["tier_rules_json"])
            high_min = float(rules["high_min_multiple"])
            low_max = float(rules["low_max_multiple"])
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise StyleLibraryError("tier_rules_invalid") from exc
        if not high_min > 1 or not 0 <= low_max < 1:
            raise StyleLibraryError("tier_rules_invalid")
        if float(target["target_metric_value"]) < 0:
            raise StyleLibraryError("target_metric_invalid")
        multiple = float(target["target_metric_value"]) / float(median_value)
        tier = "high" if multiple >= high_min else "low" if multiple <= low_max else "ordinary"
        traffic_verdict = (
            "not_applicable"
            if visibility == "public_proxy"
            else "win" if tier == "high" else "loss" if tier == "low" else "inconclusive"
        )
        computation = {
            "post_observation_id": post_observation_id,
            "baseline_snapshot_id": baseline_snapshot_id,
            "baseline_snapshot_sha256": publication["baseline_snapshot_sha256"],
            "definition_sha256": target["definition_sha256"],
            "metric_name": metric_name,
            "target_metric_value": target["target_metric_value"],
            "median_value": median_value,
            "multiple": multiple,
            "performance_tier": tier,
        }
        return {
            "status": "derived",
            **computation,
            "performance_computation_sha256": _sha256_text(
                _canonical_json(computation)
            ),
            "visibility_scope": visibility,
            "traffic_stage": traffic_stage,
            "traffic_verdict": traffic_verdict,
        }
    finally:
        con.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    init_parser = subparsers.add_parser("init", help="initialize a v2 style database")
    init_parser.add_argument("db", type=Path)
    status_parser = subparsers.add_parser("status", help="show evidence readiness")
    status_parser.add_argument("db", type=Path)
    ingest_parser = subparsers.add_parser(
        "ingest-ledger", help="import sanitized candidate-only observation JSONL"
    )
    ingest_parser.add_argument("db", type=Path)
    ingest_parser.add_argument("jsonl", type=Path)
    derive_parser = subparsers.add_parser(
        "derive-tier", help="derive a tier from a published baseline"
    )
    derive_parser.add_argument("db", type=Path)
    derive_parser.add_argument("--post-observation-id", required=True)
    derive_parser.add_argument("--baseline-snapshot-id", required=True)
    for command in ("query", "bind"):
        query_parser = subparsers.add_parser(command)
        query_parser.add_argument("db", type=Path)
        query_parser.add_argument("--carrier", required=True)
        query_parser.add_argument("--primary-job", required=True)
        query_parser.add_argument("--traffic-stage", choices=sorted(TRAFFIC_STAGES))
        query_parser.add_argument("--materials", default="")
        query_parser.add_argument("--constraints", default="")
        if command == "bind":
            query_parser.add_argument("--draft-id", required=True)
    return parser


def _split_cli_codes(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "init":
            result = init_db(args.db)
        elif args.command == "status":
            result = status_db(args.db)
        elif args.command == "ingest-ledger":
            result = ingest_ledger(args.db, args.jsonl)
        elif args.command == "derive-tier":
            result = derive_tier(
                args.db, args.post_observation_id, args.baseline_snapshot_id
            )
        elif args.command == "query":
            result = query_library(
                args.db,
                carrier=args.carrier,
                primary_job=args.primary_job,
                traffic_stage=args.traffic_stage,
                available_material_codes=_split_cli_codes(args.materials),
                active_constraint_codes=_split_cli_codes(args.constraints),
            )
        elif args.command == "bind":
            result = bind_draft(
                args.db,
                draft_id=args.draft_id,
                carrier=args.carrier,
                primary_job=args.primary_job,
                traffic_stage=args.traffic_stage,
                available_material_codes=_split_cli_codes(args.materials),
                active_constraint_codes=_split_cli_codes(args.constraints),
            )
        else:  # pragma: no cover - argparse constrains commands.
            raise StyleLibraryError("unsupported_command")
    except StyleLibraryError as exc:
        print(
            json.dumps({"status": "error", "error": str(exc)}, sort_keys=True),
            file=sys.stderr,
        )
        return 1

    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 2 if result.get("status") == "needs_style_research" else 0


if __name__ == "__main__":
    raise SystemExit(main())
