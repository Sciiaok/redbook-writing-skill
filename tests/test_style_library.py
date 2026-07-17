from __future__ import annotations

import importlib.util
import hashlib
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STYLE_CLI = ROOT / "redbook-writing" / "scripts" / "style_library.py"
SCHEMA_PATH = ROOT / "redbook-writing" / "assets" / "style-library-schema.sql"
SCHEMA_V2_PATH = ROOT / "redbook-writing" / "assets" / "style-library-schema-v2.sql"
TAXONOMY_V1_PATH = ROOT / "redbook-writing" / "assets" / "style-taxonomy-v1.json"
TAXONOMY_V2_PATH = ROOT / "redbook-writing" / "assets" / "style-taxonomy-v2.json"
LIVE_LEDGER_PATH = (
    ROOT / "docs" / "research" / "2026-07-17-live-xhs-style-observations.jsonl"
)

FROZEN_V1_SHA256 = {
    "style-library-schema.sql": "0264abffb60ef6e00b4ea64dbcfbd445c085df24bf24550c1021d0197d70d991",
    "style-taxonomy-v1.json": "cad827b3a5278e459dabc5c5eaf71a5d8957e4f0a8e0d037fae0a8ddef3be739",
}

EXPECTED_TABLES = {
    "style_schema_metadata",
    "style_accounts",
    "style_posts",
    "run_account_refs",
    "run_post_refs",
    "run_query_refs",
    "style_assets",
    "style_post_observations",
    "post_metrics",
    "account_baseline_snapshots",
    "style_slides",
    "visual_observations",
    "copy_observations",
    "feature_observation_links",
    "style_archetypes",
    "archetype_publications",
    "archetype_rule_publications",
    "archetype_review_receipts",
    "qualified_style_publications",
    "starter_pack_publications",
    "archetype_rules",
    "rule_evidence",
    "draft_style_bindings",
    "draft_binding_publications",
    "draft_binding_review_receipts",
    "draft_assets",
    "draft_outcomes",
    "ingest_receipts",
    "sanitized_ledger_ingests",
    "sanitized_style_ledger_entries",
    "performance_definitions",
    "account_baseline_members",
    "baseline_snapshot_publications",
    "post_performance_publications",
    "draft_experiments",
    "draft_experiment_assignments",
    "draft_experiment_publications",
    "draft_publish_events",
    "draft_outcome_checkpoints",
    "draft_outcome_metrics",
    "draft_outcome_publications",
}

EXPECTED_TAXONOMY: dict[str, object] = {
    "taxonomy_version": 1,
    "carrier": [
        "real_photo_diary",
        "photo_annotation",
        "screenshot_markup",
        "chat_dramatization",
        "text_card",
        "checklist_steps",
        "comparison_warning",
        "collage_journal",
        "single_image_reminder",
        "unknown",
        "other",
    ],
    "slide_role": [
        "cover",
        "scene",
        "context",
        "evidence",
        "comparison",
        "step",
        "boundary",
        "transition",
        "summary",
        "cta",
        "other",
    ],
    "composition": [
        "single_focus",
        "split",
        "grid",
        "layered_collage",
        "full_bleed",
        "interface_capture",
        "unknown",
        "other",
    ],
    "dominant_material": [
        "real_photo",
        "screenshot",
        "chat_ui",
        "paper_note",
        "illustration",
        "type_only",
        "mixed",
        "unknown",
        "other",
    ],
    "background_type": [
        "photo",
        "paper",
        "screenshot",
        "solid",
        "texture",
        "interface",
        "mixed",
        "unknown",
        "other",
    ],
    "subject_presence": [
        "person",
        "hand",
        "object",
        "environment",
        "interface_only",
        "none",
        "unknown",
        "other",
    ],
    "layout_structure": [
        "freeform",
        "stacked",
        "split",
        "grid",
        "full_bleed_overlay",
        "chat_flow",
        "list",
        "unknown",
        "other",
    ],
    "text_density": ["sparse", "medium", "dense", "variable", "unknown"],
    "hierarchy_levels": ["one", "two", "three_plus", "variable", "unknown"],
    "alignment": [
        "left",
        "center",
        "right",
        "mixed",
        "organic",
        "unknown",
        "other",
    ],
    "spacing_pattern": [
        "tight",
        "even",
        "variable",
        "edge_to_edge",
        "unknown",
        "other",
    ],
    "font_feel": [
        "system",
        "editorial",
        "handwritten",
        "display",
        "mixed",
        "unknown",
        "other",
    ],
    "decoration_types": [
        "none",
        "sticker",
        "tape",
        "doodle",
        "shape",
        "emoji",
        "mixed",
        "unknown",
        "other",
    ],
    "annotation_style": [
        "none",
        "circle",
        "arrow",
        "underline",
        "highlight",
        "handwritten",
        "mixed",
        "unknown",
        "other",
    ],
    "imperfection_signals": [
        "none",
        "uneven_crop",
        "off_grid",
        "natural_shadow",
        "hand_mark",
        "mixed",
        "unknown",
        "other",
    ],
    "image_text_relationship": [
        "image_leads",
        "text_leads",
        "complementary",
        "redundant",
        "unknown",
        "other",
    ],
    "text_surface": [
        "title",
        "cover",
        "slide",
        "caption",
        "cta",
        "unknown",
        "other",
    ],
    "point_of_view": [
        "first_person",
        "second_person",
        "third_person",
        "mixed",
        "unknown",
        "other",
    ],
    "audience_address": [
        "direct",
        "collective",
        "implicit",
        "none",
        "unknown",
        "other",
    ],
    "register": [
        "spoken",
        "plain_explanatory",
        "professional",
        "diary",
        "playful",
        "sales",
        "mixed",
        "unknown",
        "other",
    ],
    "sentence_length_pattern": [
        "short",
        "medium",
        "long",
        "mixed",
        "unknown",
        "other",
    ],
    "line_break_pattern": [
        "sentence",
        "phrase",
        "dense_paragraph",
        "mixed",
        "unknown",
        "other",
    ],
    "punctuation_pattern": [
        "light",
        "standard",
        "expressive",
        "fragmented",
        "mixed",
        "unknown",
        "other",
    ],
    "emoji_pattern": [
        "none",
        "sparse",
        "structural",
        "dense",
        "mixed",
        "unknown",
        "other",
    ],
    "hook_move": [
        "name_scene",
        "state_conflict",
        "give_answer",
        "show_evidence",
        "ask_question",
        "unknown",
        "other",
    ],
    "narrative_moves": [
        "setup",
        "turn",
        "contrast",
        "reveal",
        "reflection",
        "none",
        "unknown",
        "other",
    ],
    "evidence_move": [
        "show_process",
        "show_example",
        "compare",
        "cite_source",
        "state_limit",
        "none",
        "unknown",
        "other",
    ],
    "payoff_move": [
        "answer",
        "framework",
        "script",
        "decision",
        "boundary",
        "none",
        "unknown",
        "other",
    ],
    "cta_move": [
        "none",
        "question",
        "save",
        "follow",
        "native_action",
        "commercial",
        "unknown",
        "other",
    ],
    "image_caption_division": [
        "image_core_caption_context",
        "image_summary_caption_detail",
        "image_evidence_caption_interpretation",
        "redundant",
        "unknown",
        "other",
    ],
    "rule_type": [
        "cover",
        "rhythm",
        "visual",
        "copy",
        "material",
        "anti_pattern",
    ],
}

# The long literal above remains a readable record of the frozen v1 vocabulary.
# Active tests exercise the strict v2 file selected by the CLI.
EXPECTED_TAXONOMY = json.loads(TAXONOMY_V2_PATH.read_text(encoding="utf-8"))

VISUAL_CONTROLLED_COLUMNS = {
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
}

COPY_CONTROLLED_COLUMNS = {
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

OPEN_ENDED_TAXONOMY_KEYS = (
    VISUAL_CONTROLLED_COLUMNS | COPY_CONTROLLED_COLUMNS | {"carrier"}
) - {"text_density", "hierarchy_levels"}


def run_cli(*args: object) -> dict[str, object]:
    assert STYLE_CLI.exists(), f"missing style library CLI: {STYLE_CLI}"
    completed = subprocess.run(
        [sys.executable, str(STYLE_CLI), *map(str, args)],
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(completed.stdout)


def load_style_module():
    assert STYLE_CLI.exists(), f"missing style library CLI: {STYLE_CLI}"
    spec = importlib.util.spec_from_file_location("redbook_style_library", STYLE_CLI)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load style library module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def seed_style_graph(con: sqlite3.Connection) -> None:
    """Insert one complete, valid graph for integrity-focused tests."""

    con.execute("PRAGMA foreign_keys = ON")
    con.executemany(
        "INSERT INTO style_accounts(library_account_id, platform) VALUES (?, ?)",
        [("ACC-A", "xiaohongshu"), ("ACC-B", "xiaohongshu")],
    )
    con.executemany(
        """
        INSERT INTO style_assets(
            asset_id, asset_kind, asset_path, asset_sha256
        ) VALUES (?, ?, ?, ?)
        """,
        [
            ("ASSET-IMAGE", "image", "raw/images/post-a.png", "sha-image"),
            (
                "ASSET-DRAFT-1",
                "generated",
                "derived/drafts/draft-1.png",
                "sha-draft-1",
            ),
            (
                "ASSET-DRAFT-2",
                "generated",
                "derived/drafts/draft-2.png",
                "sha-draft-2",
            ),
            (
                "ASSET-DRAFT-3",
                "generated",
                "derived/drafts/draft-3.png",
                "sha-draft-3",
            ),
        ],
    )
    con.executemany(
        """
        INSERT INTO style_posts(
            library_post_id, platform, library_account_id, status
        ) VALUES (?, 'xiaohongshu', ?, 'active')
        """,
        [("POST-A", "ACC-A"), ("POST-B", "ACC-B")],
    )
    con.execute(
        """
        INSERT INTO run_post_refs(run_id, run_post_id, library_post_id)
        VALUES ('RUN-A', 'POST-001', 'POST-A')
        """
    )
    con.execute(
        """
        INSERT INTO account_baseline_snapshots(
            baseline_snapshot_id, library_account_id, metric_name,
            sample_n, median_value, source_run_id
        ) VALUES ('BASELINE-A', 'ACC-A', 'saves', 10, 5, 'RUN-A')
        """
    )
    con.execute(
        """
        INSERT INTO style_post_observations(
            post_observation_id, library_post_id, run_id, run_post_id,
            source_csv_sha256, baseline_snapshot_id
        ) VALUES (
            'POST-OBS-A', 'POST-A', 'RUN-A', 'POST-001',
            'sha-source-csv', 'BASELINE-A'
        )
        """
    )
    con.execute(
        """
        INSERT INTO post_metrics(
            post_metric_id, post_observation_id, metric_name, metric_value
        ) VALUES ('METRIC-A', 'POST-OBS-A', 'saves', 12)
        """
    )
    con.execute(
        """
        INSERT INTO style_slides(
            slide_id, library_post_id, slide_index, slide_role, asset_id
        ) VALUES ('SLIDE-A', 'POST-A', 0, 'cover', 'ASSET-IMAGE')
        """
    )
    con.execute(
        """
        INSERT INTO visual_observations(
            visual_observation_id, slide_id, library_post_id, observation_sha256
        ) VALUES ('VISUAL-A', 'SLIDE-A', 'POST-A', 'sha-visual-a')
        """
    )
    con.execute(
        """
        INSERT INTO copy_observations(
            observation_id, library_post_id, slide_id, observation_sha256
        ) VALUES ('COPY-A', 'POST-A', 'SLIDE-A', 'sha-copy-a')
        """
    )
    con.executemany(
        """
        INSERT INTO style_archetypes(
            archetype_id, name, status, current_version, snapshot_sha256
        ) VALUES (?, ?, ?, ?, ?)
        """,
        [
            ("ARCH-A", "Diary", "supported", 1, "unpublished-arch-a"),
            ("ARCH-B", "Checklist", "reusable", 1, "unpublished-arch-b"),
            ("ARCH-CANDIDATE", "Candidate", "candidate", 1, "snapshot-c-v1"),
        ],
    )
    con.executemany(
        """
        INSERT INTO archetype_rules(
            rule_id, archetype_id, archetype_version, rule_type
        ) VALUES (?, ?, ?, ?)
        """,
        [
            ("RULE-A", "ARCH-A", 1, "visual"),
            ("RULE-B", "ARCH-A", 1, "copy"),
            ("RULE-A-V2", "ARCH-A", 2, "visual"),
            ("RULE-OTHER", "ARCH-B", 1, "visual"),
            ("RULE-CANDIDATE", "ARCH-CANDIDATE", 1, "visual"),
        ],
    )
    con.executemany(
        """
        INSERT INTO style_slides(
            slide_id,library_post_id,slide_index,slide_role,asset_id
        ) VALUES (?, ?, ?, 'evidence', 'ASSET-IMAGE')
        """,
        [
            ("SLIDE-SUPPORT-A", "POST-A", 1),
            ("SLIDE-COUNTER-B", "POST-B", 0),
        ],
    )
    con.executemany(
        """
        INSERT INTO visual_observations(
            visual_observation_id,slide_id,library_post_id,observation_sha256
        ) VALUES (?, ?, ?, ?)
        """,
        [
            ("VISUAL-SUPPORT-A", "SLIDE-SUPPORT-A", "POST-A", "sha-support-a"),
            ("VISUAL-COUNTER-B", "SLIDE-COUNTER-B", "POST-B", "sha-counter-b"),
        ],
    )
    evidence_rows = []
    for rule_id in ("RULE-A", "RULE-B", "RULE-OTHER"):
        evidence_rows.extend(
            [
                (
                    f"EVIDENCE-{rule_id}-SUPPORT",
                    rule_id,
                    "VISUAL-SUPPORT-A",
                    "support",
                ),
                (
                    f"EVIDENCE-{rule_id}-COUNTER",
                    rule_id,
                    "VISUAL-COUNTER-B",
                    "counterexample",
                ),
            ]
        )
    con.executemany(
        """
        INSERT INTO rule_evidence(
            rule_evidence_id,rule_id,observation_type,observation_id,evidence_role
        ) VALUES (?,?,'visual',?,?)
        """,
        evidence_rows,
    )


def publish_test_archetype_rules(
    con: sqlite3.Connection,
    archetype_id: str,
    archetype_version: int,
    selected_rule_ids: str,
) -> str | None:
    """Use the real v2 hash functions to publish fixtures, never fake receipts."""

    module = load_style_module()
    original_row_factory = con.row_factory
    module._configure_connection(con)
    archetype = con.execute(
        "SELECT * FROM style_archetypes WHERE archetype_id=?",
        (archetype_id,),
    ).fetchone()
    if (
        archetype is None
        or archetype["status"] not in {"supported", "reusable"}
        or archetype["current_version"] != archetype_version
    ):
        con.row_factory = original_row_factory
        return None
    snapshot_sha = module._canonical_row_sha256_v2(
        archetype["archetype_id"],
        archetype["name"],
        archetype["category_scope"],
        archetype["carrier"],
        archetype["primary_job_scope"],
        archetype["audience_state"],
        archetype["description"],
        archetype["production_cost"],
        archetype["confidence"],
        archetype["status"],
        archetype["current_version"],
        archetype["taxonomy_version"],
    )
    publication = con.execute(
        """
        SELECT archetype_snapshot_sha256 FROM archetype_publications
        WHERE archetype_id=? AND archetype_version=?
        """,
        (archetype_id, archetype_version),
    ).fetchone()
    if publication is None:
        con.execute(
            "UPDATE style_archetypes SET snapshot_sha256=? WHERE archetype_id=?",
            (snapshot_sha, archetype_id),
        )
        con.execute(
            """
            INSERT INTO archetype_publications(
                archetype_id,archetype_version,archetype_snapshot_sha256
            ) VALUES (?,?,?)
            """,
            (archetype_id, archetype_version, snapshot_sha),
        )
    elif publication["archetype_snapshot_sha256"] != snapshot_sha:
        raise AssertionError("fixture archetype publication drifted")

    for rule_id in json.loads(selected_rule_ids):
        rule = con.execute(
            """
            SELECT * FROM archetype_rules
            WHERE rule_id=? AND archetype_id=? AND archetype_version=?
            """,
            (rule_id, archetype_id, archetype_version),
        ).fetchone()
        if rule is None:
            continue
        evidence = con.execute(
            """
            SELECT evidence.rule_evidence_id,evidence.observation_type,
                   evidence.observation_id,evidence.evidence_role,
                   evidence.limitations,
                   CASE evidence.observation_type
                       WHEN 'visual' THEN visual.observation_sha256
                       WHEN 'copy' THEN copy.observation_sha256
                       WHEN 'post_metric' THEN
                           performance.performance_computation_sha256
                   END AS target_sha256
            FROM rule_evidence AS evidence
            LEFT JOIN visual_observations AS visual
              ON evidence.observation_type='visual'
             AND visual.visual_observation_id=evidence.observation_id
            LEFT JOIN copy_observations AS copy
              ON evidence.observation_type='copy'
             AND copy.observation_id=evidence.observation_id
            LEFT JOIN post_metrics AS metric
              ON evidence.observation_type='post_metric'
             AND metric.post_metric_id=evidence.observation_id
            LEFT JOIN post_performance_publications AS performance
              ON performance.target_post_metric_id=metric.post_metric_id
            WHERE evidence.rule_id=? ORDER BY evidence.rule_evidence_id
            """,
            (rule_id,),
        ).fetchall()
        if not evidence:
            continue
        rule_sha = module._canonical_row_sha256_v2(
            rule["rule_id"],
            rule["archetype_id"],
            rule["archetype_version"],
            rule["rule_type"],
            module._canonical_json(json.loads(rule["rule_payload_json"])),
            rule["applicability_scope"],
            rule["status"],
        )
        evidence_preimages = [
            "|".join(
                str(row[key])
                for key in (
                    "rule_evidence_id",
                    "observation_type",
                    "observation_id",
                    "evidence_role",
                    "limitations",
                    "target_sha256",
                )
            )
            for row in evidence
        ]
        evidence_sha = module._sha256_text(module._canonical_json(evidence_preimages))
        con.execute(
            """
            INSERT OR IGNORE INTO archetype_rule_publications(
                rule_id,archetype_id,archetype_version,
                archetype_snapshot_sha256,rule_sha256,
                evidence_set_sha256,evidence_count
            ) VALUES (?,?,?,?,?,?,?)
            """,
            (
                rule_id,
                archetype_id,
                archetype_version,
                snapshot_sha,
                rule_sha,
                evidence_sha,
                len(evidence),
            ),
        )
    con.row_factory = original_row_factory
    return snapshot_sha


def publish_test_starter_pack(con: sqlite3.Connection) -> str:
    module = load_style_module()
    original_row_factory = con.row_factory
    module._configure_connection(con)
    manifest_json = '{"fixture_assets":["cover"]}'
    starter_sha = module._canonical_row_sha256_v2(
        "STARTER-WARM", 1, "PROMPT-COVER", manifest_json
    )
    con.execute(
        """
        INSERT OR IGNORE INTO starter_pack_publications(
            starter_pack_id,starter_pack_version,starter_prompt_id,
            manifest_json,starter_pack_sha256
        ) VALUES ('STARTER-WARM',1,'PROMPT-COVER',?,?)
        """,
        (manifest_json, starter_sha),
    )
    con.row_factory = original_row_factory
    return starter_sha


def add_test_rule_post_evidence(
    con: sqlite3.Connection, rule_id: str, post_id: str, role: str
) -> None:
    suffix = f"{rule_id}-{post_id}-{role}".replace("_", "-")
    slide_index = con.execute(
        "SELECT coalesce(max(slide_index),-1)+1 FROM style_slides "
        "WHERE library_post_id=?",
        (post_id,),
    ).fetchone()[0]
    con.execute(
        """
        INSERT INTO style_slides(
            slide_id,library_post_id,slide_index,slide_role,asset_id
        ) VALUES (?,?,?,'evidence','ASSET-IMAGE')
        """,
        (f"SLIDE-{suffix}", post_id, slide_index),
    )
    con.execute(
        """
        INSERT INTO visual_observations(
            visual_observation_id,slide_id,library_post_id,observation_sha256
        ) VALUES (?,?,?,?)
        """,
        (
            f"VISUAL-{suffix}",
            f"SLIDE-{suffix}",
            post_id,
            f"sha-{suffix}",
        ),
    )
    con.execute(
        """
        INSERT INTO rule_evidence(
            rule_evidence_id,rule_id,observation_type,observation_id,evidence_role
        ) VALUES (?,?,'visual',?,?)
        """,
        (f"EVIDENCE-{suffix}", rule_id, f"VISUAL-{suffix}", role),
    )


def insert_binding(
    con: sqlite3.Connection,
    binding_id: str,
    draft_id: str,
    *,
    archetype_id: str = "ARCH-A",
    binding_role: str = "primary",
    archetype_version: int = 1,
    selected_rule_ids: str = '["RULE-A"]',
    reference_post_ids: str = '["POST-A"]',
    counterexample_post_ids: str = '["POST-B"]',
    material_plan_json: str = "{}",
    intentional_deviations_json: str = "[]",
    anti_patterns_checked_json: str = "[]",
) -> None:
    snapshot_sha = publish_test_archetype_rules(
        con, archetype_id, archetype_version, selected_rule_ids
    )
    con.execute(
        """
        INSERT INTO draft_style_bindings(
            draft_binding_id, draft_id, archetype_id, binding_role,
            archetype_version, archetype_snapshot_sha256,
            selected_rule_ids, reference_library_post_ids,
            counterexample_library_post_ids, material_plan_json,
            intentional_deviations_json, anti_patterns_checked_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            binding_id,
            draft_id,
            archetype_id,
            binding_role,
            archetype_version,
            snapshot_sha or f"snapshot-{archetype_id}-{archetype_version}",
            selected_rule_ids,
            reference_post_ids,
            counterexample_post_ids,
            material_plan_json,
            intentional_deviations_json,
            anti_patterns_checked_json,
        ),
    )


class StyleLibrarySchemaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.db = Path(self.temp_dir.name) / "style-library.sqlite3"

    def test_init_creates_v2_schema_without_blob_columns(self) -> None:
        result = run_cli("init", self.db)
        self.assertEqual(result["schema_version"], 2)
        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)
        self.assertEqual(con.execute("PRAGMA user_version").fetchone()[0], 2)
        tables = {
            row[0]
            for row in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        self.assertTrue(
            {
                "style_assets",
                "style_posts",
                "run_post_refs",
                "style_slides",
                "visual_observations",
                "copy_observations",
                "archetype_rules",
                "rule_evidence",
                "draft_style_bindings",
            }.issubset(tables)
        )
        ddl = " ".join(
            row[0] or "" for row in con.execute("SELECT sql FROM sqlite_master")
        )
        self.assertNotRegex(ddl.upper(), r"\bBLOB\b")

    def test_same_local_post_id_in_two_runs_maps_without_collision(self) -> None:
        run_cli("init", self.db)
        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)
        con.executemany(
            "INSERT INTO style_accounts(library_account_id,platform) VALUES (?,?)",
            [("XHS-ACC-A", "xiaohongshu"), ("XHS-ACC-B", "xiaohongshu")],
        )
        con.executemany(
            """
            INSERT INTO style_posts(
                library_post_id, platform, library_account_id, status
            ) VALUES (?,?,?,?)
            """,
            [
                ("XHS-NOTE-A", "xiaohongshu", "XHS-ACC-A", "active"),
                ("XHS-NOTE-B", "xiaohongshu", "XHS-ACC-B", "active"),
            ],
        )
        con.executemany(
            """
            INSERT INTO run_post_refs(run_id,run_post_id,library_post_id)
            VALUES (?,?,?)
            """,
            [
                ("RUN-A", "POST-001", "XHS-NOTE-A"),
                ("RUN-B", "POST-001", "XHS-NOTE-B"),
            ],
        )
        con.commit()
        rows = con.execute(
            """
            SELECT run_id, run_post_id, library_post_id
            FROM run_post_refs
            ORDER BY run_id
            """
        ).fetchall()
        self.assertEqual(len(rows), 2)
        self.assertEqual(len({row[2] for row in rows}), 2)

    def test_schema_contains_complete_v2_table_set_and_is_idempotent(self) -> None:
        first = run_cli("init", self.db)
        second = run_cli("init", self.db)
        self.assertEqual(first["schema_version"], 2)
        self.assertEqual(second["schema_version"], 2)

        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)
        tables = {
            row[0]
            for row in con.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
                """
            )
        }
        self.assertEqual(tables, EXPECTED_TABLES)

    def test_schema_asset_does_not_unconditionally_set_user_version(self) -> None:
        schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
        self.assertNotRegex(schema_sql, r"(?i)PRAGMA\s+user_version\s*=")

    def test_init_rejects_future_schema_without_mutation(self) -> None:
        con = sqlite3.connect(self.db)
        con.execute("CREATE TABLE future_marker(value TEXT NOT NULL)")
        con.execute("INSERT INTO future_marker(value) VALUES ('preserve-me')")
        con.execute("PRAGMA user_version = 3")
        con.commit()
        con.close()

        module = load_style_module()
        with self.assertRaisesRegex(
            module.StyleLibraryError, "schema_version_unsupported"
        ):
            module.init_db(self.db)

        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)
        self.assertEqual(con.execute("PRAGMA user_version").fetchone()[0], 3)
        self.assertEqual(
            con.execute("SELECT value FROM future_marker").fetchone()[0],
            "preserve-me",
        )
        self.assertIsNone(
            con.execute(
                "SELECT 1 FROM sqlite_master WHERE name='style_accounts'"
            ).fetchone()
        )

    def test_init_rejects_nonempty_unversioned_database_without_mutation(self) -> None:
        con = sqlite3.connect(self.db)
        con.execute("CREATE TABLE legacy_marker(value TEXT NOT NULL)")
        con.execute("INSERT INTO legacy_marker(value) VALUES ('preserve-me')")
        con.commit()
        con.close()

        module = load_style_module()
        with self.assertRaisesRegex(
            module.StyleLibraryError, "unversioned_database_not_empty"
        ):
            module.init_db(self.db)

        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)
        self.assertEqual(con.execute("PRAGMA user_version").fetchone()[0], 0)
        tables = {
            row[0]
            for row in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        self.assertEqual(tables, {"legacy_marker"})

    def test_init_rejects_fake_v1_database_without_mutation(self) -> None:
        con = sqlite3.connect(self.db)
        con.execute("CREATE TABLE fake_v1_marker(value TEXT NOT NULL)")
        con.execute("INSERT INTO fake_v1_marker(value) VALUES ('preserve-me')")
        con.execute("PRAGMA user_version = 1")
        con.commit()
        con.close()

        module = load_style_module()
        with self.assertRaisesRegex(module.StyleLibraryError, "schema_v1_invalid"):
            module.init_db(self.db)

        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)
        self.assertEqual(con.execute("PRAGMA user_version").fetchone()[0], 1)
        tables = {
            row[0]
            for row in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        self.assertEqual(tables, {"fake_v1_marker"})

    def test_all_v1_tables_use_sqlite_strict_typing(self) -> None:
        run_cli("init", self.db)
        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)
        strict_flags = {
            row[1]: row[5]
            for row in con.execute("PRAGMA table_list")
            if row[1] in EXPECTED_TABLES
        }
        self.assertEqual(set(strict_flags), EXPECTED_TABLES)
        self.assertEqual(set(strict_flags.values()), {1})

    def test_strict_identity_column_rejects_binary_storage(self) -> None:
        run_cli("init", self.db)
        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)
        with self.assertRaisesRegex(sqlite3.IntegrityError, r"BLOB"):
            con.execute(
                """
                INSERT INTO style_accounts(library_account_id, platform)
                VALUES (?, ?)
                """,
                ("ACC-BINARY", sqlite3.Binary(b"xiaohongshu")),
            )

    def test_strict_run_fingerprint_rejects_binary_storage(self) -> None:
        run_cli("init", self.db)
        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)
        with self.assertRaisesRegex(sqlite3.IntegrityError, r"BLOB"):
            con.execute(
                """
                INSERT INTO run_query_refs(run_id, run_query_id, query_fingerprint)
                VALUES (?, ?, ?)
                """,
                ("RUN-A", "QUERY-A", sqlite3.Binary(b"sha")),
            )

    def test_connect_db_enables_foreign_keys_and_row_access(self) -> None:
        module = load_style_module()
        module.init_db(self.db)
        con = module.connect_db(self.db)
        self.addCleanup(con.close)
        self.assertEqual(con.execute("PRAGMA foreign_keys").fetchone()[0], 1)
        self.assertIsInstance(
            con.execute("SELECT 1 AS value").fetchone(), sqlite3.Row
        )
        with self.assertRaises(sqlite3.IntegrityError):
            con.execute(
                """
                INSERT INTO style_posts(
                    library_post_id, platform, library_account_id, status
                ) VALUES ('POST-MISSING-ACCOUNT', 'xiaohongshu', 'NOPE', 'active')
                """
            )

    def test_each_run_local_identifier_is_unique_only_within_its_run(self) -> None:
        run_cli("init", self.db)
        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)
        con.execute("PRAGMA foreign_keys = ON")
        con.executemany(
            "INSERT INTO style_accounts(library_account_id, platform) VALUES (?, ?)",
            [("ACC-A", "xiaohongshu"), ("ACC-B", "xiaohongshu")],
        )
        con.executemany(
            """
            INSERT INTO run_account_refs(run_id, run_account_id, library_account_id)
            VALUES (?, ?, ?)
            """,
            [
                ("RUN-A", "ACC-001", "ACC-A"),
                ("RUN-B", "ACC-001", "ACC-B"),
            ],
        )
        con.executemany(
            """
            INSERT INTO run_query_refs(run_id, run_query_id, query_fingerprint)
            VALUES (?, ?, ?)
            """,
            [
                ("RUN-A", "QUERY-001", "sha-a"),
                ("RUN-B", "QUERY-001", "sha-b"),
            ],
        )
        with self.assertRaises(sqlite3.IntegrityError):
            con.execute(
                """
                INSERT INTO run_account_refs(
                    run_id, run_account_id, library_account_id
                ) VALUES ('RUN-A', 'ACC-001', 'ACC-B')
                """
            )
        with self.assertRaises(sqlite3.IntegrityError):
            con.execute(
                """
                INSERT INTO run_query_refs(
                    run_id, run_query_id, query_fingerprint
                ) VALUES ('RUN-A', 'QUERY-001', 'sha-c')
                """
            )

    def test_declared_sql_enums_reject_unknown_values(self) -> None:
        run_cli("init", self.db)
        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)
        seed_style_graph(con)
        insert_binding(con, "BIND-A", "DRAFT-A")

        invalid_statements = [
            (
                """
                INSERT INTO style_assets(asset_id, asset_kind, asset_sha256)
                VALUES (?, ?, ?)
                """,
                ("ASSET-BAD", "video", "asset-bad"),
            ),
            (
                """
                INSERT INTO style_post_observations(
                    post_observation_id, library_post_id, run_id, run_post_id,
                    source_csv_sha256, performance_tier
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                ("OBS-BAD", "POST-A", "RUN-A", "POST-001", "csv-a", "viral"),
            ),
            (
                """
                INSERT INTO style_archetypes(
                    archetype_id, name, status, snapshot_sha256
                ) VALUES (?, ?, ?, ?)
                """,
                ("ARCH-BAD", "Bad", "active", "snapshot-bad"),
            ),
            (
                """
                INSERT INTO archetype_rules(
                    rule_id, archetype_id, archetype_version, rule_type
                ) VALUES (?, ?, ?, ?)
                """,
                ("RULE-BAD", "ARCH-A", 1, "tone"),
            ),
            (
                """
                INSERT INTO rule_evidence(
                    rule_evidence_id, rule_id, observation_type,
                    observation_id, evidence_role
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    "EVIDENCE-BAD-TYPE",
                    "RULE-A",
                    "slide",
                    "VISUAL-A",
                    "support",
                ),
            ),
            (
                """
                INSERT INTO rule_evidence(
                    rule_evidence_id, rule_id, observation_type,
                    observation_id, evidence_role
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    "EVIDENCE-BAD-ROLE",
                    "RULE-A",
                    "visual",
                    "VISUAL-A",
                    "neutral",
                ),
            ),
            (
                """
                INSERT INTO draft_style_bindings(
                    draft_binding_id, draft_id, archetype_id, binding_role,
                    archetype_version, archetype_snapshot_sha256
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    "BIND-BAD-ROLE",
                    "DRAFT-B",
                    "ARCH-A",
                    "fallback",
                    1,
                    "snapshot-a",
                ),
            ),
            (
                """
                INSERT INTO draft_style_bindings(
                    draft_binding_id, draft_id, archetype_id, binding_role,
                    archetype_version, archetype_snapshot_sha256, review_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "BIND-BAD-REVIEW",
                    "DRAFT-C",
                    "ARCH-A",
                    "primary",
                    1,
                    "snapshot-a",
                    "approved",
                ),
            ),
            (
                """
                INSERT INTO draft_outcomes(
                    draft_outcome_id, draft_binding_id, metric_name,
                    metric_value, decision
                ) VALUES (?, ?, ?, ?, ?)
                """,
                ("OUTCOME-BAD", "BIND-A", "saves", 1, "tie"),
            ),
        ]
        for statement, params in invalid_statements:
            with self.subTest(params=params):
                with self.assertRaises(sqlite3.IntegrityError):
                    con.execute(statement, params)

    def test_rule_evidence_duplicate_key_is_rejected(self) -> None:
        run_cli("init", self.db)
        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)
        seed_style_graph(con)
        con.execute(
            """
            INSERT INTO rule_evidence(
                rule_evidence_id, rule_id, observation_type,
                observation_id, evidence_role
            ) VALUES ('E-A', 'RULE-A', 'visual', 'VISUAL-A', 'support')
            """
        )
        with self.assertRaises(sqlite3.IntegrityError):
            con.execute(
                """
                INSERT INTO rule_evidence(
                    rule_evidence_id, rule_id, observation_type,
                    observation_id, evidence_role
                ) VALUES ('E-DUP', 'RULE-A', 'visual', 'VISUAL-A', 'support')
                """
            )

    def test_rule_evidence_same_rule_observation_cannot_change_role(self) -> None:
        run_cli("init", self.db)
        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)
        seed_style_graph(con)
        con.execute(
            """
            INSERT INTO rule_evidence(
                rule_evidence_id, rule_id, observation_type,
                observation_id, evidence_role
            ) VALUES ('E-A', 'RULE-A', 'visual', 'VISUAL-A', 'support')
            """
        )
        with self.assertRaises(sqlite3.IntegrityError):
            con.execute(
                """
                INSERT INTO rule_evidence(
                    rule_evidence_id, rule_id, observation_type,
                    observation_id, evidence_role
                ) VALUES (
                    'E-CONFLICT', 'RULE-A', 'visual',
                    'VISUAL-A', 'counterexample'
                )
                """
            )
        con.execute(
            """
            INSERT INTO rule_evidence(
                rule_evidence_id, rule_id, observation_type,
                observation_id, evidence_role
            ) VALUES ('E-B', 'RULE-B', 'visual', 'VISUAL-A', 'counterexample')
            """
        )

    def test_rule_evidence_insert_requires_matching_typed_observation(self) -> None:
        run_cli("init", self.db)
        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)
        seed_style_graph(con)
        con.executemany(
            """
            INSERT INTO rule_evidence(
                rule_evidence_id, rule_id, observation_type,
                observation_id, evidence_role
            ) VALUES (?, ?, ?, ?, 'support')
            """,
            [
                ("E-VISUAL", "RULE-A", "visual", "VISUAL-A"),
                ("E-COPY", "RULE-B", "copy", "COPY-A"),
                ("E-METRIC", "RULE-A", "post_metric", "METRIC-A"),
            ],
        )
        invalid = [
            ("E-MISSING-V", "RULE-A", "visual", "MISSING"),
            ("E-MISSING-C", "RULE-B", "copy", "MISSING"),
            ("E-MISSING-M", "RULE-A", "post_metric", "MISSING"),
            ("E-WRONG-TYPE", "RULE-A", "visual", "COPY-A"),
        ]
        for params in invalid:
            with self.subTest(params=params):
                with self.assertRaises(sqlite3.IntegrityError):
                    con.execute(
                        """
                        INSERT INTO rule_evidence(
                            rule_evidence_id, rule_id, observation_type,
                            observation_id, evidence_role
                        ) VALUES (?, ?, ?, ?, 'boundary')
                        """,
                        params,
                    )

    def test_rule_evidence_update_requires_matching_typed_observation(self) -> None:
        run_cli("init", self.db)
        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)
        seed_style_graph(con)
        con.execute(
            """
            INSERT INTO rule_evidence(
                rule_evidence_id, rule_id, observation_type,
                observation_id, evidence_role
            ) VALUES ('E-A', 'RULE-A', 'visual', 'VISUAL-A', 'support')
            """
        )
        with self.assertRaises(sqlite3.IntegrityError):
            con.execute(
                """
                UPDATE rule_evidence SET observation_id = 'MISSING'
                WHERE rule_evidence_id = 'E-A'
                """
            )
        with self.assertRaises(sqlite3.IntegrityError):
            con.execute(
                """
                UPDATE rule_evidence SET observation_type = 'copy'
                WHERE rule_evidence_id = 'E-A'
                """
            )

    def test_rule_evidence_targets_cannot_be_deleted(self) -> None:
        run_cli("init", self.db)
        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)
        seed_style_graph(con)
        con.executemany(
            """
            INSERT INTO rule_evidence(
                rule_evidence_id, rule_id, observation_type,
                observation_id, evidence_role
            ) VALUES (?, ?, ?, ?, 'support')
            """,
            [
                ("E-VISUAL", "RULE-A", "visual", "VISUAL-A"),
                ("E-COPY", "RULE-B", "copy", "COPY-A"),
                ("E-METRIC", "RULE-A", "post_metric", "METRIC-A"),
            ],
        )

        targets = [
            ("visual_observations", "visual_observation_id", "VISUAL-A"),
            ("copy_observations", "observation_id", "COPY-A"),
            ("post_metrics", "post_metric_id", "METRIC-A"),
        ]
        for table, primary_key, target_id in targets:
            with self.subTest(table=table):
                with self.assertRaisesRegex(
                    sqlite3.IntegrityError, "rule_evidence"
                ):
                    con.execute(
                        f"DELETE FROM {table} WHERE {primary_key} = ?",
                        (target_id,),
                    )

    def test_rule_evidence_target_primary_keys_cannot_be_updated(self) -> None:
        run_cli("init", self.db)
        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)
        seed_style_graph(con)
        con.executemany(
            """
            INSERT INTO rule_evidence(
                rule_evidence_id, rule_id, observation_type,
                observation_id, evidence_role
            ) VALUES (?, ?, ?, ?, 'support')
            """,
            [
                ("E-VISUAL", "RULE-A", "visual", "VISUAL-A"),
                ("E-COPY", "RULE-B", "copy", "COPY-A"),
                ("E-METRIC", "RULE-A", "post_metric", "METRIC-A"),
            ],
        )

        targets = [
            ("visual_observations", "visual_observation_id", "VISUAL-A"),
            ("copy_observations", "observation_id", "COPY-A"),
            ("post_metrics", "post_metric_id", "METRIC-A"),
        ]
        for table, primary_key, target_id in targets:
            with self.subTest(table=table):
                with self.assertRaisesRegex(
                    sqlite3.IntegrityError, "rule_evidence"
                ):
                    con.execute(
                        f"UPDATE {table} SET {primary_key} = ? "
                        f"WHERE {primary_key} = ?",
                        (f"{target_id}-RENAMED", target_id),
                    )

    def test_each_draft_allows_at_most_one_primary_binding(self) -> None:
        run_cli("init", self.db)
        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)
        seed_style_graph(con)
        insert_binding(con, "BIND-PRIMARY-A", "DRAFT-A")
        with self.assertRaises(sqlite3.IntegrityError):
            insert_binding(con, "BIND-PRIMARY-B", "DRAFT-A")

    def test_v2_rejects_secondary_binding_even_when_primary_exists(self) -> None:
        run_cli("init", self.db)
        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)
        seed_style_graph(con)
        insert_binding(con, "BIND-PRIMARY", "DRAFT-A")
        with self.assertRaises(sqlite3.IntegrityError):
            insert_binding(
                con,
                "BIND-SECONDARY",
                "DRAFT-A",
                archetype_id="ARCH-B",
                binding_role="secondary",
                selected_rule_ids='["RULE-OTHER"]',
            )

    def test_secondary_binding_requires_existing_primary(self) -> None:
        run_cli("init", self.db)
        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)
        seed_style_graph(con)
        with self.assertRaises(sqlite3.IntegrityError):
            insert_binding(
                con,
                "BIND-SECONDARY",
                "DRAFT-NO-PRIMARY",
                archetype_id="ARCH-B",
                binding_role="secondary",
                selected_rule_ids='["RULE-OTHER"]',
            )

    def test_unpublished_primary_binding_can_be_deleted(self) -> None:
        run_cli("init", self.db)
        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)
        seed_style_graph(con)
        insert_binding(con, "BIND-PRIMARY", "DRAFT-A")
        con.execute(
            "DELETE FROM draft_style_bindings WHERE draft_binding_id='BIND-PRIMARY'"
        )
        self.assertEqual(
            con.execute(
                "SELECT count(*) FROM draft_style_bindings WHERE draft_id='DRAFT-A'"
            ).fetchone()[0],
            0,
        )

    def test_primary_binding_cannot_move_onto_another_bound_draft(self) -> None:
        run_cli("init", self.db)
        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)
        seed_style_graph(con)
        insert_binding(con, "BIND-PRIMARY", "DRAFT-A")
        insert_binding(con, "BIND-OTHER", "DRAFT-B")
        with self.assertRaises(sqlite3.IntegrityError):
            con.execute(
                """
                UPDATE draft_style_bindings SET draft_id='DRAFT-A'
                WHERE draft_binding_id='BIND-OTHER'
                """
            )

    def test_binding_json_columns_require_intended_container_shapes(self) -> None:
        run_cli("init", self.db)
        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)
        seed_style_graph(con)
        invalid = [
            {"selected_rule_ids": "{}"},
            {"reference_post_ids": "{}"},
            {"counterexample_post_ids": "not-json"},
            {"material_plan_json": "[]"},
            {"intentional_deviations_json": "{}"},
            {"anti_patterns_checked_json": "{}"},
        ]
        for index, overrides in enumerate(invalid):
            with self.subTest(overrides=overrides):
                with self.assertRaises(sqlite3.IntegrityError):
                    insert_binding(
                        con,
                        f"BIND-BAD-JSON-{index}",
                        f"DRAFT-BAD-JSON-{index}",
                        **overrides,
                    )

    def test_binding_ids_resolve_to_owned_rules_and_existing_posts(self) -> None:
        run_cli("init", self.db)
        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)
        seed_style_graph(con)
        invalid = [
            {"selected_rule_ids": '["MISSING"]'},
            {"selected_rule_ids": '["RULE-OTHER"]'},
            {"selected_rule_ids": '["RULE-A-V2"]'},
            {"selected_rule_ids": "[1]"},
            {"reference_post_ids": '["MISSING"]'},
            {"reference_post_ids": "[1]"},
            {"counterexample_post_ids": '["MISSING"]'},
        ]
        for index, overrides in enumerate(invalid):
            with self.subTest(overrides=overrides):
                with self.assertRaises(sqlite3.IntegrityError):
                    insert_binding(
                        con,
                        f"BIND-BAD-ID-{index}",
                        f"DRAFT-BAD-ID-{index}",
                        **overrides,
                    )
        insert_binding(con, "BIND-VALID", "DRAFT-VALID")

    def test_library_binding_requires_an_exact_published_archetype_snapshot(self) -> None:
        run_cli("init", self.db)
        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)
        seed_style_graph(con)

        with self.assertRaisesRegex(
            sqlite3.IntegrityError, "binding_archetype_unpublished"
        ):
            con.execute(
                """
                INSERT INTO draft_style_bindings(
                    draft_binding_id,draft_id,binding_role,binding_source,
                    archetype_id,archetype_version,archetype_snapshot_sha256,
                    selected_rule_ids
                ) VALUES (
                    'BIND-UNPUBLISHED','DRAFT-UNPUBLISHED','primary','library',
                    'ARCH-A',1,'unpublished-arch-a','["RULE-A"]'
                )
                """
            )

    def test_binding_rejects_existing_posts_without_published_rule_association(self) -> None:
        run_cli("init", self.db)
        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)
        seed_style_graph(con)
        con.execute(
            """
            INSERT INTO style_posts(
                library_post_id,platform,library_account_id,status
            ) VALUES ('POST-UNRELATED','xiaohongshu','ACC-A','active')
            """
        )

        with self.assertRaisesRegex(
            sqlite3.IntegrityError, "binding_reference_association_unpublished"
        ):
            insert_binding(
                con,
                "BIND-UNRELATED",
                "DRAFT-UNRELATED",
                reference_post_ids='["POST-UNRELATED"]',
            )

    def test_published_rule_evidence_target_is_frozen(self) -> None:
        run_cli("init", self.db)
        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)
        seed_style_graph(con)
        insert_binding(con, "BIND-FROZEN-EVIDENCE", "DRAFT-FROZEN-EVIDENCE")

        with self.assertRaisesRegex(
            sqlite3.IntegrityError, "published_rule_evidence_target_frozen"
        ):
            con.execute(
                """
                UPDATE visual_observations SET composition='grid'
                WHERE visual_observation_id='VISUAL-SUPPORT-A'
                """
            )

    def test_archetype_publication_recomputes_its_snapshot_hash(self) -> None:
        module = load_style_module()
        module.init_db(self.db)
        con = module.connect_db(self.db)
        self.addCleanup(con.close)
        seed_style_graph(con)

        with self.assertRaisesRegex(
            sqlite3.IntegrityError, "archetype_snapshot_hash_mismatch"
        ):
            con.execute(
                """
                INSERT INTO archetype_publications(
                    archetype_id,archetype_version,archetype_snapshot_sha256
                ) VALUES ('ARCH-A',1,'unpublished-arch-a')
                """
            )

    def test_binding_rejects_rules_missing_an_exact_publication_receipt(self) -> None:
        module = load_style_module()
        module.init_db(self.db)
        con = module.connect_db(self.db)
        self.addCleanup(con.close)
        seed_style_graph(con)
        row = con.execute(
            "SELECT * FROM style_archetypes WHERE archetype_id='ARCH-B'"
        ).fetchone()
        snapshot_sha = module._canonical_row_sha256_v2(
            row["archetype_id"], row["name"], row["category_scope"],
            row["carrier"], row["primary_job_scope"], row["audience_state"],
            row["description"], row["production_cost"], row["confidence"],
            row["status"], row["current_version"], row["taxonomy_version"],
        )
        con.execute(
            "UPDATE style_archetypes SET snapshot_sha256=? WHERE archetype_id='ARCH-B'",
            (snapshot_sha,),
        )
        con.execute(
            """
            INSERT INTO archetype_publications(
                archetype_id,archetype_version,archetype_snapshot_sha256
            ) VALUES ('ARCH-B',1,?)
            """,
            (snapshot_sha,),
        )
        with self.assertRaisesRegex(
            sqlite3.IntegrityError, "rule_publication_hash_mismatch"
        ):
            con.execute(
                """
                INSERT INTO archetype_rule_publications(
                    rule_id,archetype_id,archetype_version,
                    archetype_snapshot_sha256,rule_sha256,
                    evidence_set_sha256,evidence_count
                ) VALUES (
                    'RULE-OTHER','ARCH-B',1,?,
                    'made-up-rule-hash','made-up-evidence-hash',2
                )
                """,
                (snapshot_sha,),
            )

        with self.assertRaisesRegex(
            sqlite3.IntegrityError, "binding_rule_unpublished"
        ):
            con.execute(
                """
                INSERT INTO draft_style_bindings(
                    draft_binding_id,draft_id,binding_role,binding_source,
                    archetype_id,archetype_version,archetype_snapshot_sha256,
                    selected_rule_ids,reference_library_post_ids,
                    counterexample_library_post_ids
                ) VALUES (
                    'BIND-NO-RULE-RECEIPT','DRAFT-NO-RULE-RECEIPT',
                    'primary','library','ARCH-B',1,?,
                    '["RULE-OTHER"]','["POST-A"]','["POST-B"]'
                )
                """,
                (snapshot_sha,),
            )

    def test_starter_binding_requires_an_exact_published_manifest(self) -> None:
        module = load_style_module()
        module.init_db(self.db)
        con = module.connect_db(self.db)
        self.addCleanup(con.close)
        with self.assertRaisesRegex(
            sqlite3.IntegrityError, "starter_pack_manifest_hash_mismatch"
        ):
            con.execute(
                """
                INSERT INTO starter_pack_publications(
                    starter_pack_id,starter_pack_version,starter_prompt_id,
                    manifest_json,starter_pack_sha256
                ) VALUES (
                    'STARTER-WARM',1,'PROMPT-COVER','{}','made-up-sha'
                )
                """
            )
        with self.assertRaisesRegex(
            sqlite3.IntegrityError, "binding_starter_unpublished"
        ):
            con.execute(
                """
                INSERT INTO draft_style_bindings(
                    draft_binding_id,draft_id,binding_role,binding_source,
                    starter_pack_id,starter_pack_version,
                    starter_pack_sha256,starter_prompt_id,selected_rule_ids
                ) VALUES (
                    'BIND-FAKE-STARTER','DRAFT-FAKE-STARTER','primary',
                    'starter_pack','STARTER-WARM',1,'made-up-sha',
                    'PROMPT-COVER','[]'
                )
                """
            )

    def test_draft_binding_publication_hashes_and_freezes_exact_binding(self) -> None:
        module = load_style_module()
        module.init_db(self.db)
        con = module.connect_db(self.db)
        seed_style_graph(con)
        insert_binding(con, "BIND-FINAL", "DRAFT-FINAL")
        with self.assertRaisesRegex(
            sqlite3.IntegrityError, "binding_publication_hash_mismatch"
        ):
            con.execute(
                """
                INSERT INTO draft_binding_publications(
                    draft_binding_id,draft_id,binding_sha256
                ) VALUES ('BIND-FINAL','DRAFT-FINAL','made-up-binding-hash')
                """
            )
        con.commit()
        con.close()
        with self.assertRaisesRegex(
            module.StyleLibraryError, "draft_binding_review_not_pass"
        ):
            module.publish_draft_binding(self.db, "BIND-FINAL")
        con = module.connect_db(self.db)
        pending = con.execute(
            "SELECT * FROM draft_style_bindings WHERE draft_binding_id='BIND-FINAL'"
        ).fetchone()
        pending_sha = module._draft_binding_sha256(pending)
        con.close()
        with self.assertRaisesRegex(
            module.StyleLibraryError, "qualified_publication_missing"
        ):
            module.review_draft_binding(
                self.db,
                {
                    "draft_binding_id": "BIND-FINAL",
                    "decision": "PASS",
                    "expected_pending_binding_sha256": pending_sha,
                    "content_owner_id": "OWNER-1",
                    "reviewer_ids": ["REVIEWER-2"],
                    "reviewer_independence_status": "independent",
                    "reviewed_at": "2026-07-18",
                },
            )
        con = module.connect_db(self.db)
        self.addCleanup(con.close)
        self.assertEqual(
            con.execute(
                "SELECT count(*) FROM draft_binding_publications"
            ).fetchone()[0],
            0,
        )

    def test_selected_rules_cannot_be_deleted_or_primary_key_updated(self) -> None:
        run_cli("init", self.db)
        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)
        seed_style_graph(con)
        insert_binding(
            con,
            "BIND-A",
            "DRAFT-A",
            selected_rule_ids='["RULE-A", "RULE-B"]',
        )

        operations = [
            ("delete", "DELETE FROM archetype_rules WHERE rule_id = 'RULE-A'"),
            (
                "primary-key update",
                """
                UPDATE archetype_rules SET rule_id = 'RULE-B-RENAMED'
                WHERE rule_id = 'RULE-B'
                """,
            ),
        ]
        for operation, statement in operations:
            with self.subTest(operation=operation):
                with self.assertRaisesRegex(
                    sqlite3.IntegrityError, "binding_rule"
                ):
                    con.execute(statement)

    def test_draft_asset_rules_cannot_be_deleted_or_primary_key_updated(self) -> None:
        run_cli("init", self.db)
        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)
        seed_style_graph(con)
        con.executemany(
            """
            INSERT INTO archetype_rules(
                rule_id, archetype_id, archetype_version, rule_type
            ) VALUES (?, 'ARCH-A', 1, 'visual')
            """,
            [("RULE-ASSET-DELETE",), ("RULE-ASSET-UPDATE",)],
        )
        for rule_id in ("RULE-ASSET-DELETE", "RULE-ASSET-UPDATE"):
            add_test_rule_post_evidence(con, rule_id, "POST-A", "support")
            add_test_rule_post_evidence(
                con, rule_id, "POST-B", "counterexample"
            )
        insert_binding(
            con,
            "BIND-A",
            "DRAFT-A",
            selected_rule_ids='["RULE-ASSET-DELETE", "RULE-ASSET-UPDATE"]',
        )
        con.execute(
            """
            INSERT INTO draft_assets(
                draft_asset_id, draft_binding_id, asset_id,
                slide_index, style_rule_ids
            ) VALUES (
                'DRAFT-ASSET-A', 'BIND-A', 'ASSET-DRAFT-1', 1,
                '["RULE-ASSET-DELETE", "RULE-ASSET-UPDATE"]'
            )
            """
        )

        operations = [
            (
                "delete",
                "DELETE FROM archetype_rules "
                "WHERE rule_id = 'RULE-ASSET-DELETE'",
            ),
            (
                "primary-key update",
                """
                UPDATE archetype_rules SET rule_id = 'RULE-ASSET-RENAMED'
                WHERE rule_id = 'RULE-ASSET-UPDATE'
                """,
            ),
        ]
        for operation, statement in operations:
            with self.subTest(operation=operation):
                with self.assertRaisesRegex(
                    sqlite3.IntegrityError, "draft_asset_rule"
                ):
                    con.execute(statement)

    def test_referenced_posts_cannot_be_deleted(self) -> None:
        run_cli("init", self.db)
        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)
        seed_style_graph(con)
        con.executemany(
            """
            INSERT INTO style_posts(
                library_post_id, platform, library_account_id, status
            ) VALUES (?, 'xiaohongshu', 'ACC-A', 'active')
            """,
            [("POST-REF-DELETE",), ("POST-COUNTER-DELETE",)],
        )
        add_test_rule_post_evidence(
            con, "RULE-A", "POST-REF-DELETE", "support"
        )
        add_test_rule_post_evidence(
            con, "RULE-A", "POST-COUNTER-DELETE", "counterexample"
        )
        insert_binding(
            con,
            "BIND-A",
            "DRAFT-A",
            reference_post_ids='["POST-REF-DELETE"]',
            counterexample_post_ids='["POST-COUNTER-DELETE"]',
        )

        for post_id in ("POST-REF-DELETE", "POST-COUNTER-DELETE"):
            with self.subTest(post_id=post_id):
                with self.assertRaisesRegex(
                    sqlite3.IntegrityError, "binding_.*post"
                ):
                    con.execute(
                        "DELETE FROM style_posts WHERE library_post_id = ?",
                        (post_id,),
                    )

    def test_referenced_post_primary_keys_cannot_be_updated(self) -> None:
        run_cli("init", self.db)
        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)
        seed_style_graph(con)
        con.executemany(
            """
            INSERT INTO style_posts(
                library_post_id, platform, library_account_id, status
            ) VALUES (?, 'xiaohongshu', 'ACC-A', 'active')
            """,
            [("POST-REF-UPDATE",), ("POST-COUNTER-UPDATE",)],
        )
        add_test_rule_post_evidence(
            con, "RULE-A", "POST-REF-UPDATE", "support"
        )
        add_test_rule_post_evidence(
            con, "RULE-A", "POST-COUNTER-UPDATE", "counterexample"
        )
        insert_binding(
            con,
            "BIND-A",
            "DRAFT-A",
            reference_post_ids='["POST-REF-UPDATE"]',
            counterexample_post_ids='["POST-COUNTER-UPDATE"]',
        )

        for post_id in ("POST-REF-UPDATE", "POST-COUNTER-UPDATE"):
            with self.subTest(post_id=post_id):
                with self.assertRaisesRegex(
                    sqlite3.IntegrityError, "binding_.*post"
                ):
                    con.execute(
                        """
                        UPDATE style_posts SET library_post_id = ?
                        WHERE library_post_id = ?
                        """,
                        (f"{post_id}-RENAMED", post_id),
                    )

    def test_primary_binding_requires_supported_or_reusable_archetype(self) -> None:
        run_cli("init", self.db)
        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)
        seed_style_graph(con)
        with self.assertRaisesRegex(
            sqlite3.IntegrityError, "primary_archetype_not_supported"
        ):
            insert_binding(
                con,
                "BIND-CANDIDATE",
                "DRAFT-CANDIDATE",
                archetype_id="ARCH-CANDIDATE",
                selected_rule_ids='["RULE-CANDIDATE"]',
            )
        insert_binding(con, "BIND-SUPPORTED", "DRAFT-SUPPORTED")

    def test_binding_source_requires_one_complete_unmixed_source(self) -> None:
        run_cli("init", self.db)
        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)
        columns = {
            row[1] for row in con.execute("PRAGMA table_info(draft_style_bindings)")
        }
        self.assertTrue(
            {
                "binding_source",
                "starter_pack_id",
                "starter_pack_version",
                "starter_pack_sha256",
                "starter_prompt_id",
            }.issubset(columns)
        )
        seed_style_graph(con)
        insert_binding(con, "BIND-LIBRARY", "DRAFT-LIBRARY")
        starter_sha = publish_test_starter_pack(con)
        con.execute(
            """
            INSERT INTO draft_style_bindings(
                draft_binding_id, draft_id, binding_role, binding_source,
                starter_pack_id, starter_pack_version,
                starter_pack_sha256, starter_prompt_id,
                selected_rule_ids, archetype_id, archetype_version,
                archetype_snapshot_sha256
            ) VALUES (
                'BIND-STARTER', 'DRAFT-STARTER', 'primary', 'starter_pack',
                'STARTER-WARM', 1, ?, 'PROMPT-COVER',
                '[]', NULL, NULL, NULL
            )
            """,
            (starter_sha,),
        )

        invalid_statements = [
            """
            INSERT INTO draft_style_bindings(
                draft_binding_id, draft_id, binding_role, binding_source,
                archetype_id, archetype_version, archetype_snapshot_sha256,
                selected_rule_ids
            ) VALUES (
                'BIND-UNKNOWN-SOURCE', 'DRAFT-BAD-0', 'primary', 'other',
                'ARCH-A', 1, 'snapshot-a', '["RULE-A"]'
            )
            """,
            """
            INSERT INTO draft_style_bindings(
                draft_binding_id, draft_id, binding_role, binding_source,
                archetype_id, archetype_version, archetype_snapshot_sha256,
                selected_rule_ids
            ) VALUES (
                'BIND-LIBRARY-NO-RULE', 'DRAFT-BAD-1', 'primary', 'library',
                'ARCH-A', 1, 'snapshot-a', '[]'
            )
            """,
            """
            INSERT INTO draft_style_bindings(
                draft_binding_id, draft_id, binding_role, binding_source,
                starter_pack_id, starter_pack_version,
                starter_pack_sha256, starter_prompt_id,
                archetype_id, archetype_version, archetype_snapshot_sha256,
                selected_rule_ids
            ) VALUES (
                'BIND-STARTER-MIXED', 'DRAFT-BAD-2', 'primary', 'starter_pack',
                'STARTER-WARM', 1, 'starter-sha', 'PROMPT-COVER',
                'ARCH-A', 1, 'snapshot-a', '["RULE-A"]'
            )
            """,
            """
            INSERT INTO draft_style_bindings(
                draft_binding_id, draft_id, binding_role, binding_source,
                starter_pack_id, starter_pack_version,
                starter_pack_sha256, starter_prompt_id,
                selected_rule_ids
            ) VALUES (
                'BIND-STARTER-INCOMPLETE', 'DRAFT-BAD-3',
                'primary', 'starter_pack',
                'STARTER-WARM', 1, NULL, 'PROMPT-COVER', '[]'
            )
            """,
            """
            INSERT INTO draft_style_bindings(
                draft_binding_id, draft_id, binding_role, binding_source,
                archetype_id, archetype_version, archetype_snapshot_sha256,
                selected_rule_ids, starter_pack_id
            ) VALUES (
                'BIND-LIBRARY-MIXED', 'DRAFT-BAD-4', 'primary', 'library',
                'ARCH-A', 1, 'snapshot-a', '["RULE-A"]', 'STARTER-WARM'
            )
            """,
        ]
        for statement in invalid_statements:
            with self.subTest(statement=statement):
                with self.assertRaises(sqlite3.IntegrityError):
                    con.execute(statement)

    def test_binding_source_update_cannot_mix_library_and_starter(self) -> None:
        run_cli("init", self.db)
        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)
        columns = {
            row[1] for row in con.execute("PRAGMA table_info(draft_style_bindings)")
        }
        self.assertIn("binding_source", columns)
        seed_style_graph(con)
        insert_binding(con, "BIND-LIBRARY", "DRAFT-LIBRARY")
        with self.assertRaises(sqlite3.IntegrityError):
            con.execute(
                """
                UPDATE draft_style_bindings
                SET starter_pack_id='STARTER-WARM',
                    starter_pack_version=1,
                    starter_pack_sha256='starter-sha',
                    starter_prompt_id='PROMPT-COVER'
                WHERE draft_binding_id='BIND-LIBRARY'
                """
            )

    def test_binding_source_is_pinned_after_a_draft_asset_exists(self) -> None:
        run_cli("init", self.db)
        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)
        seed_style_graph(con)
        insert_binding(con, "BIND-LIBRARY", "DRAFT-LIBRARY")
        starter_sha = publish_test_starter_pack(con)
        con.execute(
            """
            INSERT INTO draft_style_bindings(
                draft_binding_id, draft_id, binding_role, binding_source,
                starter_pack_id, starter_pack_version,
                starter_pack_sha256, starter_prompt_id,
                selected_rule_ids
            ) VALUES (
                'BIND-STARTER', 'DRAFT-STARTER', 'primary', 'starter_pack',
                'STARTER-WARM', 1, ?, 'PROMPT-COVER', '[]'
            )
            """,
            (starter_sha,),
        )
        con.execute(
            """
            INSERT INTO draft_assets(
                draft_asset_id, draft_binding_id, asset_id,
                slide_index, style_rule_ids
            ) VALUES (
                'DRAFT-ASSET-LIBRARY','BIND-LIBRARY','ASSET-DRAFT-1',
                1,'["RULE-A"]'
            )
            """,
        )

        switches = [
            (
                "library-to-starter",
                """
                UPDATE draft_style_bindings
                SET binding_source = 'starter_pack',
                    archetype_id = NULL,
                    archetype_version = NULL,
                    archetype_snapshot_sha256 = NULL,
                    selected_rule_ids = '[]',
                    starter_pack_id = 'STARTER-WARM',
                    starter_pack_version = 1,
                    starter_pack_sha256 = 'starter-sha',
                    starter_prompt_id = 'PROMPT-COVER'
                WHERE draft_binding_id = 'BIND-LIBRARY'
                """,
            ),
        ]
        for direction, statement in switches:
            with self.subTest(direction=direction):
                with self.assertRaisesRegex(
                    sqlite3.IntegrityError,
                    "binding_fields_pinned_by_draft_assets",
                ):
                    con.execute(statement)

    def test_binding_archetype_fields_are_pinned_after_assets_exist(self) -> None:
        run_cli("init", self.db)
        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)
        seed_style_graph(con)
        bindings = [
            ("BIND-ARCHETYPE", "DRAFT-ARCHETYPE"),
            ("BIND-VERSION", "DRAFT-VERSION"),
            ("BIND-RULES", "DRAFT-RULES"),
        ]
        for binding_id, draft_id in bindings:
            insert_binding(con, binding_id, draft_id)
        con.executemany(
            """
            INSERT INTO draft_assets(
                draft_asset_id, draft_binding_id, asset_id,
                slide_index, style_rule_ids
            ) VALUES (?, ?, 'ASSET-DRAFT-1', 1, '["RULE-A"]')
            """,
            [
                ("DRAFT-ASSET-ARCHETYPE", "BIND-ARCHETYPE"),
                ("DRAFT-ASSET-VERSION", "BIND-VERSION"),
                ("DRAFT-ASSET-RULES", "BIND-RULES"),
            ],
        )

        valid_rebindings = [
            (
                "BIND-ARCHETYPE",
                """
                archetype_id = 'ARCH-B', archetype_version = 1,
                archetype_snapshot_sha256 = 'snapshot-b-v1',
                selected_rule_ids = '["RULE-OTHER"]'
                """,
            ),
            (
                "BIND-VERSION",
                """
                archetype_version = 2,
                archetype_snapshot_sha256 = 'snapshot-a-v2',
                selected_rule_ids = '["RULE-A-V2"]'
                """,
            ),
            ("BIND-RULES", "selected_rule_ids = '[\"RULE-B\"]'"),
        ]
        for binding_id, assignments in valid_rebindings:
            with self.subTest(binding_id=binding_id):
                with self.assertRaisesRegex(
                    sqlite3.IntegrityError,
                    "binding_fields_pinned_by_draft_assets",
                ):
                    con.execute(
                        f"""
                        UPDATE draft_style_bindings SET {assignments}
                        WHERE draft_binding_id = ?
                        """,
                        (binding_id,),
                    )

    def test_draft_assets_keep_one_current_revision_per_binding_slide(self) -> None:
        run_cli("init", self.db)
        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)
        columns = {row[1] for row in con.execute("PRAGMA table_info(draft_assets)")}
        self.assertTrue(
            {
                "render_method",
                "style_rule_ids",
                "revision_of",
                "notes",
                "is_current",
            }.issubset(columns)
        )
        seed_style_graph(con)
        insert_binding(con, "BIND-A", "DRAFT-A")
        con.execute(
            """
            INSERT INTO draft_assets(
                draft_asset_id, draft_binding_id, asset_id, slide_index,
                asset_role, render_method, style_rule_ids, is_current, notes
            ) VALUES (
                'DRAFT-ASSET-1', 'BIND-A', 'ASSET-DRAFT-1', 1,
                'cover', 'template', '["RULE-A"]', 1, 'first revision'
            )
            """
        )
        with self.assertRaises(sqlite3.IntegrityError):
            con.execute(
                """
                INSERT INTO draft_assets(
                    draft_asset_id, draft_binding_id, asset_id, slide_index,
                    asset_role, render_method, style_rule_ids, is_current
                ) VALUES (
                    'DRAFT-ASSET-CONFLICT', 'BIND-A', 'ASSET-DRAFT-2', 1,
                    'cover', 'template', '["RULE-A"]', 1
                )
                """
            )
        con.execute(
            "UPDATE draft_assets SET is_current=0 WHERE draft_asset_id='DRAFT-ASSET-1'"
        )
        con.execute(
            """
            INSERT INTO draft_assets(
                draft_asset_id, draft_binding_id, asset_id, slide_index,
                asset_role, render_method, style_rule_ids, revision_of,
                is_current, notes
            ) VALUES (
                'DRAFT-ASSET-2', 'BIND-A', 'ASSET-DRAFT-2', 1,
                'cover', 'manual', '["RULE-A"]', 'DRAFT-ASSET-1',
                1, 'current revision'
            )
            """
        )
        rows = con.execute(
            """
            SELECT draft_asset_id, is_current, render_method, notes
            FROM draft_assets ORDER BY draft_asset_id
            """
        ).fetchall()
        self.assertEqual(
            rows,
            [
                ("DRAFT-ASSET-1", 0, "template", "first revision"),
                ("DRAFT-ASSET-2", 1, "manual", "current revision"),
            ],
        )

    def test_draft_asset_rule_ids_match_binding_archetype_version(self) -> None:
        run_cli("init", self.db)
        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)
        columns = {row[1] for row in con.execute("PRAGMA table_info(draft_assets)")}
        self.assertIn("style_rule_ids", columns)
        seed_style_graph(con)
        insert_binding(con, "BIND-A", "DRAFT-A")
        invalid_rule_ids = [
            "not-json",
            "{}",
            '["MISSING"]',
            '["RULE-OTHER"]',
            '["RULE-A-V2"]',
            "[1]",
        ]
        for index, rule_ids in enumerate(invalid_rule_ids, start=1):
            with self.subTest(rule_ids=rule_ids):
                with self.assertRaises(sqlite3.IntegrityError):
                    con.execute(
                        """
                        INSERT INTO draft_assets(
                            draft_asset_id, draft_binding_id, asset_id,
                            slide_index, style_rule_ids, is_current
                        ) VALUES (?, 'BIND-A', 'ASSET-DRAFT-1', ?, ?, 0)
                        """,
                        (f"DRAFT-ASSET-BAD-{index}", index, rule_ids),
                    )
        con.execute(
            """
            INSERT INTO draft_assets(
                draft_asset_id, draft_binding_id, asset_id,
                slide_index, style_rule_ids, is_current
            ) VALUES (
                'DRAFT-ASSET-VALID', 'BIND-A', 'ASSET-DRAFT-1',
                1, '["RULE-A"]', 1
            )
            """
        )

    def test_starter_pack_draft_asset_cannot_claim_library_rule_ids(self) -> None:
        run_cli("init", self.db)
        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)
        seed_style_graph(con)
        starter_sha = publish_test_starter_pack(con)
        con.execute(
            """
            INSERT INTO draft_style_bindings(
                draft_binding_id, draft_id, binding_role, binding_source,
                starter_pack_id, starter_pack_version,
                starter_pack_sha256, starter_prompt_id,
                selected_rule_ids
            ) VALUES (
                'BIND-STARTER', 'DRAFT-STARTER', 'primary', 'starter_pack',
                'STARTER-WARM', 1, ?, 'PROMPT-COVER', '[]'
            )
            """,
            (starter_sha,),
        )
        with self.assertRaises(sqlite3.IntegrityError):
            con.execute(
                """
                INSERT INTO draft_assets(
                    draft_asset_id, draft_binding_id, asset_id,
                    slide_index, style_rule_ids
                ) VALUES (
                    'DRAFT-ASSET-STARTER', 'BIND-STARTER', 'ASSET-DRAFT-1',
                    1, '["RULE-A"]'
                )
                """
            )

    def test_draft_asset_revision_stays_with_its_binding_and_slide(self) -> None:
        run_cli("init", self.db)
        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)
        columns = {row[1] for row in con.execute("PRAGMA table_info(draft_assets)")}
        self.assertIn("revision_of", columns)
        seed_style_graph(con)
        insert_binding(con, "BIND-A", "DRAFT-A")
        insert_binding(con, "BIND-B", "DRAFT-B")
        con.execute(
            """
            INSERT INTO draft_assets(
                draft_asset_id, draft_binding_id, asset_id,
                slide_index, style_rule_ids, is_current
            ) VALUES (
                'DRAFT-ASSET-BASE', 'BIND-A', 'ASSET-DRAFT-1',
                1, '["RULE-A"]', 0
            )
            """
        )
        with self.assertRaises(sqlite3.IntegrityError):
            con.execute(
                """
                INSERT INTO draft_assets(
                    draft_asset_id, draft_binding_id, asset_id,
                    slide_index, style_rule_ids, revision_of, is_current
                ) VALUES (
                    'DRAFT-ASSET-WRONG-BINDING', 'BIND-B', 'ASSET-DRAFT-2',
                    1, '["RULE-A"]', 'DRAFT-ASSET-BASE', 1
                )
                """
            )
        with self.assertRaises(sqlite3.IntegrityError):
            con.execute(
                """
                INSERT INTO draft_assets(
                    draft_asset_id, draft_binding_id, asset_id,
                    slide_index, style_rule_ids, revision_of, is_current
                ) VALUES (
                    'DRAFT-ASSET-WRONG-SLIDE', 'BIND-A', 'ASSET-DRAFT-3',
                    2, '["RULE-A"]', 'DRAFT-ASSET-BASE', 1
                )
                """
            )

    def test_style_assets_reject_paths_outside_raw_or_derived(self) -> None:
        run_cli("init", self.db)
        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)
        con.executemany(
            """
            INSERT INTO style_assets(
                asset_id, asset_kind, asset_path, asset_sha256
            ) VALUES (?, 'image', ?, ?)
            """,
            [
                ("ASSET-RAW", "raw/images/a.png", "sha-raw"),
                ("ASSET-DERIVED", "derived/thumbs/a.png", "sha-derived"),
            ],
        )
        for index, path in enumerate(
            [
                "/tmp/a.png",
                "../raw/a.png",
                "raw/../a.png",
                r"derived\..\a.png",
                "other/a.png",
                "C:/raw/a.png",
                "RAW/a.png",
                "Derived/a.png",
            ]
        ):
            with self.subTest(path=path):
                with self.assertRaises(sqlite3.IntegrityError):
                    con.execute(
                        """
                        INSERT INTO style_assets(
                            asset_id, asset_kind, asset_path, asset_sha256
                        ) VALUES (?, 'image', ?, ?)
                        """,
                        (f"ASSET-BAD-{index}", path, f"sha-bad-{index}"),
                    )

    def test_slide_role_and_archetype_carrier_use_taxonomy_values(self) -> None:
        run_cli("init", self.db)
        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)
        seed_style_graph(con)
        with self.assertRaises(sqlite3.IntegrityError):
            con.execute(
                "UPDATE style_slides SET slide_role='not-in-taxonomy'"
            )
        with self.assertRaises(sqlite3.IntegrityError):
            con.execute(
                "UPDATE style_archetypes SET carrier='not-in-taxonomy'"
            )

    def test_visual_controlled_columns_reject_values_outside_taxonomy(self) -> None:
        run_cli("init", self.db)
        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)
        seed_style_graph(con)
        for column in sorted(VISUAL_CONTROLLED_COLUMNS):
            with self.subTest(column=column):
                with self.assertRaises(sqlite3.IntegrityError):
                    con.execute(
                        f"""
                        UPDATE visual_observations
                        SET {column}='not-in-taxonomy'
                        WHERE visual_observation_id='VISUAL-A'
                        """
                    )

    def test_copy_controlled_columns_reject_values_outside_taxonomy(self) -> None:
        run_cli("init", self.db)
        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)
        seed_style_graph(con)
        for column in sorted(COPY_CONTROLLED_COLUMNS):
            with self.subTest(column=column):
                with self.assertRaises(sqlite3.IntegrityError):
                    con.execute(
                        f"""
                        UPDATE copy_observations
                        SET {column}='not-in-taxonomy'
                        WHERE observation_id='COPY-A'
                        """
                    )

    def test_database_accepts_every_declared_taxonomy_value(self) -> None:
        run_cli("init", self.db)
        module = load_style_module()
        taxonomy = module.load_taxonomy()
        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)
        seed_style_graph(con)

        for value in taxonomy["slide_role"]:
            with self.subTest(column="slide_role", value=value):
                con.execute(
                    "UPDATE style_slides SET slide_role=? WHERE slide_id='SLIDE-A'",
                    (value,),
                )
        for value in taxonomy["carrier"]:
            with self.subTest(column="carrier", value=value):
                con.execute(
                    """
                    UPDATE style_archetypes SET carrier=?
                    WHERE archetype_id='ARCH-A'
                    """,
                    (value,),
                )
        for column in sorted(VISUAL_CONTROLLED_COLUMNS):
            for value in taxonomy[column]:
                with self.subTest(table="visual", column=column, value=value):
                    con.execute(
                        f"""
                        UPDATE visual_observations SET {column}=?
                        WHERE visual_observation_id='VISUAL-A'
                        """,
                        (value,),
                    )
        for column in sorted(COPY_CONTROLLED_COLUMNS):
            for value in taxonomy[column]:
                with self.subTest(table="copy", column=column, value=value):
                    con.execute(
                        f"""
                        UPDATE copy_observations SET {column}=?
                        WHERE observation_id='COPY-A'
                        """,
                        (value,),
                    )

    def test_database_taxonomy_version_is_exactly_v2(self) -> None:
        run_cli("init", self.db)
        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)
        seed_style_graph(con)
        updates = [
            "UPDATE style_slides SET taxonomy_version=1 WHERE slide_id='SLIDE-A'",
            """
            UPDATE visual_observations SET taxonomy_version=1
            WHERE visual_observation_id='VISUAL-A'
            """,
            """
            UPDATE copy_observations SET taxonomy_version=1
            WHERE observation_id='COPY-A'
            """,
            """
            UPDATE style_archetypes SET taxonomy_version=1
            WHERE archetype_id='ARCH-A'
            """,
        ]
        for statement in updates:
            with self.subTest(statement=statement):
                with self.assertRaises(sqlite3.IntegrityError):
                    con.execute(statement)

    def test_taxonomy_v2_is_exact_and_loadable(self) -> None:
        module = load_style_module()
        self.assertEqual(module.load_taxonomy(), EXPECTED_TAXONOMY)

    def test_load_taxonomy_rejects_malformed_contracts(self) -> None:
        module = load_style_module()

        def fresh_taxonomy() -> dict[str, object]:
            return json.loads(json.dumps(EXPECTED_TAXONOMY))

        malformed: list[tuple[str, dict[str, object]]] = []

        payload = fresh_taxonomy()
        payload.pop("carrier")
        malformed.append(("missing_key", payload))

        payload = fresh_taxonomy()
        payload["extra_key"] = ["unknown", "other"]
        malformed.append(("extra_key", payload))

        payload = fresh_taxonomy()
        payload["carrier"] = []
        malformed.append(("empty_list", payload))

        payload = fresh_taxonomy()
        payload["carrier"].append(payload["carrier"][0])
        malformed.append(("duplicate_value", payload))

        payload = fresh_taxonomy()
        payload["carrier"].append(7)
        malformed.append(("non_string_value", payload))

        payload = fresh_taxonomy()
        payload["carrier"].append("")
        malformed.append(("empty_string_value", payload))

        payload = fresh_taxonomy()
        payload["carrier"].append("   ")
        malformed.append(("whitespace_string_value", payload))

        payload = fresh_taxonomy()
        payload["carrier"].remove("unknown")
        malformed.append(("open_key_missing_unknown", payload))

        payload = fresh_taxonomy()
        payload["carrier"].remove("other")
        malformed.append(("open_key_missing_other", payload))

        payload = fresh_taxonomy()
        payload["slide_role"].remove("other")
        malformed.append(("slide_role_missing_other", payload))

        payload = fresh_taxonomy()
        payload["text_density"].remove("unknown")
        malformed.append(("closed_scale_missing_unknown", payload))

        payload = fresh_taxonomy()
        payload["taxonomy_version"] = True
        malformed.append(("boolean_version", payload))

        original_path = module.TAXONOMY_PATH
        try:
            for index, (case, payload) in enumerate(malformed):
                with self.subTest(case=case):
                    taxonomy_path = (
                        Path(self.temp_dir.name) / f"taxonomy-invalid-{index}.json"
                    )
                    taxonomy_path.write_text(
                        json.dumps(payload), encoding="utf-8"
                    )
                    module.TAXONOMY_PATH = taxonomy_path
                    with self.assertRaises(module.StyleLibraryError):
                        module.load_taxonomy()
        finally:
            module.TAXONOMY_PATH = original_path

    def test_observation_controlled_columns_are_covered_by_taxonomy(self) -> None:
        run_cli("init", self.db)
        module = load_style_module()
        taxonomy = module.load_taxonomy()
        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)

        for table, controlled in (
            ("visual_observations", VISUAL_CONTROLLED_COLUMNS),
            ("copy_observations", COPY_CONTROLLED_COLUMNS),
        ):
            columns = {
                row[1] for row in con.execute(f"PRAGMA table_info({table})")
            }
            self.assertTrue(controlled.issubset(columns), table)
            self.assertTrue(controlled.issubset(taxonomy), table)

    def test_open_ended_taxonomy_values_have_unknown_and_other(self) -> None:
        module = load_style_module()
        taxonomy = module.load_taxonomy()
        for key in OPEN_ENDED_TAXONOMY_KEYS:
            with self.subTest(key=key):
                values = taxonomy[key]
                self.assertIn("unknown", values)
                self.assertIn("other", values)


class StyleLibraryV2CoreContractTests(unittest.TestCase):
    """Small, high-value contract suite for the v2 activation boundary."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.db = Path(self.temp_dir.name) / "style-library.sqlite3"

    @staticmethod
    def _ordered_hash(values: list[str]) -> str:
        encoded = json.dumps(
            values, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def _seed_publishable_baseline(self, con: sqlite3.Connection) -> tuple[str, str]:
        included_rows = [
            "0|OBS-1|METRIC-1|10.0||{}|[]",
            "1|OBS-2|METRIC-2|20.0||{}|[]",
        ]
        all_rows = [
            "0|OBS-1|METRIC-1|included||10.0||{}|[]",
            "1|OBS-2|METRIC-2|included||20.0||{}|[]",
        ]
        included_hash = self._ordered_hash(included_rows)
        all_hash = self._ordered_hash(all_rows)
        con.execute(
            "INSERT INTO style_accounts(library_account_id,platform) VALUES ('ACC','xiaohongshu')"
        )
        con.executemany(
            """
            INSERT INTO style_posts(
                library_post_id,platform,library_account_id,status
            ) VALUES (?,'xiaohongshu','ACC','active')
            """,
            [("POST-1",), ("POST-2",)],
        )
        con.executemany(
            "INSERT INTO run_post_refs(run_id,run_post_id,library_post_id) VALUES ('RUN',?,?)",
            [("LOCAL-1", "POST-1"), ("LOCAL-2", "POST-2")],
        )
        con.execute(
            """
            INSERT INTO performance_definitions(
                performance_definition_id,definition_version,metric_name,
                business_objective,primary_job,metric_selection_reason,
                comparison_design,min_baseline_n,paid_or_pinned_policy,
                missing_value_policy,tier_rules_json,as_of,review_by,
                definition_sha256
            ) VALUES (
                'DEF',1,'engagement_proxy','engagement_proxy','feed_stop',
                'public visible engagement proxy only','account_baseline',2,
                'exclude','exclude',
                '{"high_min_multiple":2.0,"low_max_multiple":0.5}',
                '2026-07-18','2026-08-18','sha-def'
            )
            """
        )
        con.execute(
            """
            INSERT INTO account_baseline_snapshots(
                baseline_snapshot_id,library_account_id,metric_name,sample_n,
                median_value,performance_definition_id,included_members_sha256,
                all_members_sha256,baseline_snapshot_sha256,source_run_id
            ) VALUES (
                'BASE','ACC','engagement_proxy',2,15.0,'DEF',?,?,
                'sha-baseline','RUN'
            )
            """,
            (included_hash, all_hash),
        )
        for ordinal, value in enumerate((10.0, 20.0), start=1):
            con.execute(
                """
                INSERT INTO style_post_observations(
                    post_observation_id,library_post_id,library_account_id,
                    run_id,run_post_id,source_csv_sha256,observation_state,
                    performance_definition_id,target_metric_name
                ) VALUES (?,?,?,?,?,'sha-source','building','DEF','engagement_proxy')
                """,
                (
                    f"OBS-{ordinal}",
                    f"POST-{ordinal}",
                    "ACC",
                    "RUN",
                    f"LOCAL-{ordinal}",
                ),
            )
            con.execute(
                """
                INSERT INTO post_metrics(
                    post_metric_id,post_observation_id,metric_name,metric_value,
                    visibility_scope,metric_sha256
                ) VALUES (?,?, 'engagement_proxy',?,'public_proxy',?)
                """,
                (
                    f"METRIC-{ordinal}",
                    f"OBS-{ordinal}",
                    value,
                    f"sha-metric-{ordinal}",
                ),
            )
            con.execute(
                """
                UPDATE style_post_observations
                SET observation_state='complete',target_post_metric_id=?
                WHERE post_observation_id=?
                """,
                (f"METRIC-{ordinal}", f"OBS-{ordinal}"),
            )
            con.execute(
                """
                INSERT INTO account_baseline_members(
                    baseline_snapshot_id,library_account_id,
                    performance_definition_id,metric_name,
                    member_post_observation_id,member_post_metric_id,
                    inclusion_status,metric_value,member_ordinal
                ) VALUES ('BASE','ACC','DEF','engagement_proxy',?,?,'included',?,?)
                """,
                (
                    f"OBS-{ordinal}",
                    f"METRIC-{ordinal}",
                    value,
                    ordinal - 1,
                ),
            )
        return included_hash, all_hash

    def test_frozen_v1_assets_remain_byte_identical(self) -> None:
        for path in (SCHEMA_PATH, TAXONOMY_V1_PATH):
            with self.subTest(path=path.name):
                self.assertEqual(
                    hashlib.sha256(path.read_bytes()).hexdigest(),
                    FROZEN_V1_SHA256[path.name],
                )

    def test_init_creates_v2_core_schema(self) -> None:
        result = run_cli("init", self.db)
        self.assertEqual(result["schema_version"], 2)
        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)
        self.assertEqual(con.execute("PRAGMA user_version").fetchone()[0], 2)
        tables = {
            row[0]
            for row in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        self.assertTrue(
            {
                "style_accounts",
                "style_assets",
                "style_posts",
                "style_post_observations",
                "post_metrics",
                "performance_definitions",
                "account_baseline_snapshots",
                "account_baseline_members",
                "baseline_snapshot_publications",
                "style_slides",
                "visual_observations",
                "copy_observations",
                "draft_experiments",
                "draft_outcome_checkpoints",
                "draft_outcome_metrics",
                "draft_outcome_publications",
            }.issubset(tables)
        )
        ddl = " ".join(
            row[0] or "" for row in con.execute("SELECT sql FROM sqlite_master")
        )
        self.assertNotRegex(ddl.upper(), r"\bBLOB\b")

    def test_connect_db_registers_v2_pragmas_and_aggregates(self) -> None:
        module = load_style_module()
        module.init_db(self.db)
        con = module.connect_db(self.db)
        self.addCleanup(con.close)
        self.assertEqual(con.execute("PRAGMA foreign_keys").fetchone()[0], 1)
        self.assertEqual(con.execute("PRAGMA recursive_triggers").fetchone()[0], 1)
        con.execute("CREATE TEMP TABLE values_for_test(ord INTEGER, value REAL)")
        con.executemany(
            "INSERT INTO values_for_test VALUES (?, ?)",
            [(3, 9), (1, 1), (2, 5), (4, 13)],
        )
        row = con.execute(
            """
            SELECT median_agg_v2(value), canonical_sha256_agg_v2(value)
            FROM (SELECT value FROM values_for_test ORDER BY ord)
            """
        ).fetchone()
        self.assertEqual(row[0], 7.0)
        self.assertRegex(row[1], r"^[0-9a-f]{64}$")

    def test_post_observation_finalize_is_one_way_and_fk_clean(self) -> None:
        module = load_style_module()
        module.init_db(self.db)
        con = module.connect_db(self.db)
        self.addCleanup(con.close)
        self._seed_publishable_baseline(con)
        with self.assertRaises(sqlite3.IntegrityError):
            con.execute(
                """
                UPDATE style_post_observations SET known_confounds='["late"]'
                WHERE post_observation_id='OBS-1'
                """
            )
        self.assertEqual(con.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_baseline_marker_recomputes_and_freezes_exact_children(self) -> None:
        module = load_style_module()
        module.init_db(self.db)
        con = module.connect_db(self.db)
        included_hash, all_hash = self._seed_publishable_baseline(con)
        con.commit()
        con.close()

        raw = sqlite3.connect(self.db)
        with self.assertRaisesRegex(
            sqlite3.OperationalError, r"no such function: (median|canonical_sha256)_agg_v2"
        ):
            raw.execute(
                """
                INSERT INTO baseline_snapshot_publications(
                    baseline_snapshot_id,library_account_id,
                    performance_definition_id,metric_name,
                    baseline_snapshot_sha256,included_members_sha256,
                    all_members_sha256
                ) VALUES ('BASE','ACC','DEF','engagement_proxy',
                          'sha-baseline',?,?)
                """,
                (included_hash, all_hash),
            )
        raw.close()

        con = module.connect_db(self.db)
        self.addCleanup(con.close)
        con.execute(
            """
            INSERT INTO baseline_snapshot_publications(
                baseline_snapshot_id,library_account_id,
                performance_definition_id,metric_name,
                baseline_snapshot_sha256,included_members_sha256,
                all_members_sha256
            ) VALUES ('BASE','ACC','DEF','engagement_proxy',
                      'sha-baseline',?,?)
            """,
            (included_hash, all_hash),
        )
        with self.assertRaisesRegex(
            sqlite3.IntegrityError, "immutable_account_baseline_members"
        ):
            con.execute(
                """
                UPDATE account_baseline_members SET metric_value=11
                WHERE baseline_snapshot_id='BASE' AND member_ordinal=0
                """
            )
        with self.assertRaisesRegex(
            sqlite3.IntegrityError, "published_baseline_metric_frozen"
        ):
            con.execute(
                "UPDATE post_metrics SET metric_value=11 WHERE post_metric_id='METRIC-1'"
            )

    def test_recursive_triggers_block_insert_or_replace_on_immutable_snapshot(self) -> None:
        module = load_style_module()
        module.init_db(self.db)
        con = module.connect_db(self.db)
        self.addCleanup(con.close)
        self._seed_publishable_baseline(con)
        self.assertEqual(con.execute("PRAGMA recursive_triggers").fetchone()[0], 1)
        with self.assertRaisesRegex(
            sqlite3.IntegrityError, "immutable_account_baseline_snapshots"
        ):
            con.execute(
                """
                INSERT OR REPLACE INTO account_baseline_snapshots(
                    baseline_snapshot_id,library_account_id,metric_name,
                    sample_n,median_value,performance_definition_id,
                    included_members_sha256,all_members_sha256,
                    baseline_snapshot_sha256,source_run_id
                )
                SELECT baseline_snapshot_id,library_account_id,metric_name,
                       sample_n,99,performance_definition_id,
                       included_members_sha256,all_members_sha256,
                       baseline_snapshot_sha256,source_run_id
                FROM account_baseline_snapshots
                WHERE baseline_snapshot_id='BASE'
                """
            )

    def test_production_init_never_uses_executescript(self) -> None:
        source = STYLE_CLI.read_text(encoding="utf-8")
        self.assertNotIn(".executescript(", source)

    def test_real_v1_requires_explicit_upgrade_without_mutation(self) -> None:
        legacy_sql = SCHEMA_PATH.read_text(encoding="utf-8")
        con = sqlite3.connect(self.db)
        con.executescript(legacy_sql)
        con.execute("PRAGMA user_version=1")
        con.commit()
        con.close()
        before = self.db.read_bytes()

        module = load_style_module()
        with self.assertRaisesRegex(
            module.StyleLibraryError, "schema_upgrade_required"
        ):
            module.init_db(self.db)

        self.assertEqual(self.db.read_bytes(), before)

    def test_corrupt_database_fails_preflight_without_mutation(self) -> None:
        corrupt = b"not-a-sqlite-database\x00preserve"
        self.db.write_bytes(corrupt)
        module = load_style_module()
        with self.assertRaisesRegex(
            module.StyleLibraryError, "schema_preflight_failed"
        ):
            module.init_db(self.db)
        self.assertEqual(self.db.read_bytes(), corrupt)

    def test_v2_taxonomy_is_strict_and_has_retrieval_codes(self) -> None:
        module = load_style_module()
        taxonomy = module.load_taxonomy()
        self.assertEqual(taxonomy["taxonomy_version"], 2)
        for key in (
            "primary_job",
            "material_code",
            "production_constraint_code",
            "contraindication_code",
        ):
            self.assertIn(key, taxonomy)
        self.assertTrue(
            {
                "feed_stop",
                "search_answer",
                "explain",
                "trust_build",
                "decision_support",
                "relationship_build",
                "conversion",
                "authority_statement",
            }.issubset(taxonomy["primary_job"])
        )
        self.assertEqual(
            set(taxonomy["traffic_stage"]),
            {
                "feed_stop",
                "read_through",
                "save_share",
                "comment_cocreation",
                "profile_follow",
            },
        )

    def test_init_validates_taxonomy_before_creating_database(self) -> None:
        module = load_style_module()
        invalid_taxonomy = Path(self.temp_dir.name) / "invalid-taxonomy.json"
        invalid_taxonomy.write_text(
            json.dumps({"taxonomy_version": 2}), encoding="utf-8"
        )
        original = module.TAXONOMY_PATH
        try:
            module.TAXONOMY_PATH = invalid_taxonomy
            with self.assertRaisesRegex(module.StyleLibraryError, "taxonomy_invalid"):
                module.init_db(self.db)
        finally:
            module.TAXONOMY_PATH = original
        self.assertFalse(self.db.exists())

    def test_style_slides_reject_duplicate_post_index(self) -> None:
        run_cli("init", self.db)
        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)
        con.execute("PRAGMA foreign_keys=ON")
        con.execute(
            "INSERT INTO style_accounts(library_account_id,platform) VALUES ('A','xiaohongshu')"
        )
        con.execute(
            """
            INSERT INTO style_posts(library_post_id,platform,library_account_id,status)
            VALUES ('P','xiaohongshu','A','active')
            """
        )
        con.execute(
            """
            INSERT INTO style_assets(asset_id,asset_kind,asset_path,asset_sha256)
            VALUES ('IMG','image','raw/p.png','sha-p')
            """
        )
        con.execute(
            """
            INSERT INTO style_slides(slide_id,library_post_id,slide_index,slide_role,asset_id)
            VALUES ('S1','P',1,'cover','IMG')
            """
        )
        with self.assertRaises(sqlite3.IntegrityError):
            con.execute(
                """
                INSERT INTO style_slides(slide_id,library_post_id,slide_index,slide_role,asset_id)
                VALUES ('S2','P',1,'scene','IMG')
                """
            )

    def test_visual_observation_cannot_claim_a_different_post(self) -> None:
        run_cli("init", self.db)
        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)
        seed_style_graph(con)
        with self.assertRaises(sqlite3.IntegrityError):
            con.execute(
                """
                INSERT INTO visual_observations(
                    visual_observation_id,slide_id,library_post_id,
                    observation_sha256
                ) VALUES ('VISUAL-CROSS','SLIDE-A','POST-B','sha-cross')
                """
            )

    def test_post_observation_account_must_match_post_owner(self) -> None:
        run_cli("init", self.db)
        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)
        con.execute("PRAGMA foreign_keys=ON")
        con.executemany(
            "INSERT INTO style_accounts(library_account_id,platform) VALUES (?,'xiaohongshu')",
            [("ACC-A",), ("ACC-B",)],
        )
        con.execute(
            """
            INSERT INTO style_posts(library_post_id,platform,library_account_id,status)
            VALUES ('POST-A','xiaohongshu','ACC-A','active')
            """
        )
        con.execute(
            "INSERT INTO run_post_refs VALUES ('RUN','LOCAL','POST-A')"
        )
        with self.assertRaises(sqlite3.IntegrityError):
            con.execute(
                """
                INSERT INTO style_post_observations(
                    post_observation_id,library_post_id,library_account_id,
                    run_id,run_post_id,source_csv_sha256
                ) VALUES ('OBS','POST-A','ACC-B','RUN','LOCAL','sha')
                """
            )

    def test_status_and_sanitized_ledger_ingest_are_honest_and_idempotent(self) -> None:
        module = load_style_module()
        module.init_db(self.db)
        before = module.status_db(self.db)
        self.assertEqual(before["counts"]["sanitized_ledger_entries"], 0)
        self.assertEqual(
            before["release_readiness"]["state"], "needs_style_research"
        )

        imported = module.ingest_ledger(self.db, LIVE_LEDGER_PATH)
        self.assertEqual(imported["status"], "imported")
        self.assertEqual(imported["record_count"], 12)
        repeated = module.ingest_ledger(self.db, LIVE_LEDGER_PATH)
        self.assertEqual(repeated["status"], "idempotent")

        after = module.status_db(self.db)
        self.assertEqual(after["counts"]["sanitized_ledger_entries"], 12)
        self.assertEqual(after["counts"]["qualified_style_rules"], 0)
        con = module.connect_db(self.db)
        self.addCleanup(con.close)
        self.assertEqual(con.execute("SELECT count(*) FROM style_assets").fetchone()[0], 0)
        self.assertEqual(con.execute("SELECT count(*) FROM style_posts").fetchone()[0], 0)

    def test_ingest_ledger_rejects_fake_asset_or_performance_receipt_atomically(self) -> None:
        module = load_style_module()
        module.init_db(self.db)
        record = json.loads(LIVE_LEDGER_PATH.read_text(encoding="utf-8").splitlines()[0])
        record["asset_sha256s"] = ["f" * 64]
        record["performance_receipt"] = {"claimed": True}
        bad = Path(self.temp_dir.name) / "bad-ledger.jsonl"
        bad.write_text(json.dumps(record) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(
            module.StyleLibraryError, "ledger_forbidden_evidence_claim"
        ):
            module.ingest_ledger(self.db, bad)
        self.assertEqual(
            module.status_db(self.db)["counts"]["sanitized_ledger_entries"], 0
        )

    def test_query_audits_every_candidate_and_cli_exits_needs_research(self) -> None:
        module = load_style_module()
        module.init_db(self.db)
        module.ingest_ledger(self.db, LIVE_LEDGER_PATH)
        result = module.query_library(
            self.db,
            category="未验证类目",
            carrier="chat_dramatization",
            primary_job="feed_stop",
            traffic_stage="feed_stop",
            available_material_codes=["unknown"],
            active_constraint_codes=["no_generated_evidence"],
        )
        self.assertEqual(result["status"], "needs_style_research")
        self.assertEqual(len(result["rejection_audit"]), 12)
        self.assertEqual(
            [row["observation_id"] for row in result["rejection_audit"]],
            sorted(row["observation_id"] for row in result["rejection_audit"]),
        )
        first = next(
            row for row in result["rejection_audit"]
            if row["observation_id"] == "O-XHS-001"
        )
        self.assertIn("qualification_ineligible_unverified", first["reason_codes"])
        self.assertIn("not_published_qualified_rule", first["reason_codes"])
        self.assertIn("traffic_stage_unverified", first["reason_codes"])

        completed = subprocess.run(
            [
                sys.executable,
                str(STYLE_CLI),
                "query",
                str(self.db),
                "--category",
                "未验证类目",
                "--carrier",
                "chat_dramatization",
                "--primary-job",
                "feed_stop",
                "--traffic-stage",
                "feed_stop",
                "--materials",
                "unknown",
                "--constraints",
                "no_generated_evidence",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(json.loads(completed.stdout)["status"], "needs_style_research")

    def test_bind_fails_closed_without_published_qualified_rule(self) -> None:
        module = load_style_module()
        module.init_db(self.db)
        module.ingest_ledger(self.db, LIVE_LEDGER_PATH)
        with self.assertRaisesRegex(
            module.StyleLibraryError, "no_published_qualified_rule"
        ):
            module.bind_draft(
                self.db,
                draft_id="DRAFT-FAST-PATH",
                draft_binding_id="BIND-FAST-PATH",
                category="未验证类目",
                carrier="chat_dramatization",
                primary_job="feed_stop",
                business_objective="engagement_proxy",
                available_material_codes=["unknown"],
                active_constraint_codes=["no_generated_evidence"],
            )
        con = module.connect_db(self.db)
        self.addCleanup(con.close)
        self.assertEqual(
            con.execute("SELECT count(*) FROM draft_style_bindings").fetchone()[0],
            0,
        )

    def test_researcher_cannot_write_a_performance_tier_directly(self) -> None:
        module = load_style_module()
        module.init_db(self.db)
        con = module.connect_db(self.db)
        self.addCleanup(con.close)
        con.execute(
            "INSERT INTO style_accounts(library_account_id,platform) "
            "VALUES ('ACC-TIER','xiaohongshu')"
        )
        con.execute(
            "INSERT INTO style_posts(library_post_id,platform,library_account_id) "
            "VALUES ('POST-TIER','xiaohongshu','ACC-TIER')"
        )
        con.execute(
            "INSERT INTO run_post_refs VALUES ('RUN-TIER','LOCAL-TIER','POST-TIER')"
        )

        with self.assertRaisesRegex(
            sqlite3.IntegrityError, "performance_tier_requires_publication"
        ):
            con.execute(
                """
                INSERT INTO style_post_observations(
                    post_observation_id,library_post_id,run_id,run_post_id,
                    source_csv_sha256,performance_tier
                ) VALUES (
                    'OBS-TIER','POST-TIER','RUN-TIER','LOCAL-TIER','sha','high'
                )
                """
            )

    def test_derive_tier_uses_published_baseline_and_never_calls_proxy_traffic(self) -> None:
        module = load_style_module()
        module.init_db(self.db)
        con = module.connect_db(self.db)
        included_hash, all_hash = self._seed_publishable_baseline(con)
        con.execute(
            """
            INSERT INTO baseline_snapshot_publications(
                baseline_snapshot_id,library_account_id,
                performance_definition_id,metric_name,
                baseline_snapshot_sha256,included_members_sha256,
                all_members_sha256
            ) VALUES ('BASE','ACC','DEF','engagement_proxy',
                      'sha-baseline',?,?)
            """,
            (included_hash, all_hash),
        )
        con.execute(
            """
            INSERT INTO style_posts(library_post_id,platform,library_account_id,status)
            VALUES ('POST-T','xiaohongshu','ACC','active')
            """
        )
        con.execute(
            "INSERT INTO run_post_refs VALUES ('RUN-T','LOCAL-T','POST-T')"
        )
        con.execute(
            """
            INSERT INTO style_post_observations(
                post_observation_id,library_post_id,library_account_id,
                run_id,run_post_id,source_csv_sha256,observation_state,
                performance_definition_id,target_metric_name,
                baseline_snapshot_id,baseline_snapshot_sha256
            ) VALUES ('OBS-T','POST-T','ACC','RUN-T','LOCAL-T','sha-target',
                      'building','DEF','engagement_proxy','BASE','sha-baseline')
            """
        )
        con.execute(
            """
            INSERT INTO post_metrics(
                post_metric_id,post_observation_id,metric_name,metric_value,
                visibility_scope,metric_sha256
            ) VALUES ('METRIC-T','OBS-T','engagement_proxy',40,
                      'public_proxy','sha-target-metric')
            """
        )
        con.execute(
            """
            UPDATE style_post_observations
            SET observation_state='complete',target_post_metric_id='METRIC-T'
            WHERE post_observation_id='OBS-T'
            """
        )
        con.commit()
        con.close()

        result = module.derive_tier(self.db, "OBS-T", "BASE")
        self.assertEqual(result["performance_tier"], "high")
        self.assertEqual(result["traffic_verdict"], "not_applicable")
        self.assertEqual(result["visibility_scope"], "public_proxy")
        con = module.connect_db(self.db)
        self.addCleanup(con.close)
        receipt = con.execute(
            """
            SELECT performance_tier,account_baseline_multiple,
                   performance_computation_sha256,traffic_verdict
            FROM post_performance_publications
            WHERE post_observation_id='OBS-T'
            """
        ).fetchone()
        self.assertIsNotNone(receipt)
        self.assertEqual(receipt["performance_tier"], "high")
        self.assertAlmostEqual(receipt["account_baseline_multiple"], 40 / 15)
        self.assertEqual(
            receipt["performance_computation_sha256"],
            result["performance_computation_sha256"],
        )
        with self.assertRaisesRegex(
            sqlite3.IntegrityError, "performance_publication_not_recomputable"
        ):
            con.execute(
                """
                INSERT INTO post_performance_publications(
                    post_observation_id,library_account_id,
                    baseline_snapshot_id,baseline_snapshot_sha256,
                    performance_definition_id,definition_sha256,metric_name,
                    target_post_metric_id,target_metric_sha256,
                    target_metric_value,baseline_median_value,
                    account_baseline_multiple,performance_tier,
                    performance_computation_sha256,visibility_scope,
                    traffic_stage,traffic_verdict
                )
                SELECT
                    post_observation_id,library_account_id,
                    baseline_snapshot_id,baseline_snapshot_sha256,
                    performance_definition_id,definition_sha256,metric_name,
                    target_post_metric_id,target_metric_sha256,
                    target_metric_value,baseline_median_value,
                    account_baseline_multiple,'ordinary','made-up-computation',
                    visibility_scope,traffic_stage,traffic_verdict
                FROM post_performance_publications
                WHERE post_observation_id='OBS-T'
                """
            )
        with self.assertRaisesRegex(
            sqlite3.IntegrityError, "immutable_post_performance_publications"
        ):
            con.execute(
                """
                UPDATE post_performance_publications
                SET performance_tier='ordinary'
                WHERE post_observation_id='OBS-T'
                """
            )

    def test_derive_tier_rejects_parallel_observation_of_target_post_in_baseline(self) -> None:
        module = load_style_module()
        module.init_db(self.db)
        con = module.connect_db(self.db)
        included_hash, all_hash = self._seed_publishable_baseline(con)
        con.execute(
            """
            INSERT INTO baseline_snapshot_publications(
                baseline_snapshot_id,library_account_id,
                performance_definition_id,metric_name,
                baseline_snapshot_sha256,included_members_sha256,
                all_members_sha256
            ) VALUES ('BASE','ACC','DEF','engagement_proxy',
                      'sha-baseline',?,?)
            """,
            (included_hash, all_hash),
        )
        con.execute("INSERT INTO run_post_refs VALUES ('RUN-C','LOCAL-C','POST-1')")
        con.execute(
            """
            INSERT INTO style_post_observations(
                post_observation_id,library_post_id,library_account_id,
                run_id,run_post_id,source_csv_sha256,observation_state,
                performance_definition_id,target_metric_name,
                baseline_snapshot_id,baseline_snapshot_sha256
            ) VALUES ('OBS-C','POST-1','ACC','RUN-C','LOCAL-C','sha-c',
                      'building','DEF','engagement_proxy','BASE','sha-baseline')
            """
        )
        con.execute(
            """
            INSERT INTO post_metrics(
                post_metric_id,post_observation_id,metric_name,metric_value,
                visibility_scope,metric_sha256
            ) VALUES ('METRIC-C','OBS-C','engagement_proxy',30,
                      'public_proxy','sha-c-metric')
            """
        )
        con.execute(
            """
            UPDATE style_post_observations
            SET observation_state='complete',target_post_metric_id='METRIC-C'
            WHERE post_observation_id='OBS-C'
            """
        )
        con.commit()
        con.close()
        with self.assertRaisesRegex(
            module.StyleLibraryError, "baseline_target_post_contamination"
        ):
            module.derive_tier(self.db, "OBS-C", "BASE")

    def test_v2_binding_is_exactly_one_primary_per_draft(self) -> None:
        run_cli("init", self.db)
        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)
        seed_style_graph(con)
        insert_binding(con, "BIND-1", "DRAFT-1")
        insert_binding(con, "BIND-2", "DRAFT-2")
        with self.assertRaises(sqlite3.IntegrityError):
            insert_binding(
                con,
                "BIND-SECONDARY",
                "DRAFT-2",
                binding_role="secondary",
            )
        with self.assertRaises(sqlite3.IntegrityError):
            insert_binding(con, "BIND-3", "DRAFT-1", archetype_id="ARCH-B")


class StyleLibraryPromotionPipelineTests(unittest.TestCase):
    """The public CLI can promote real observations without trusting claims."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.db = self.root / "style-library.sqlite3"

    def _write_json(self, name: str, value: object) -> Path:
        path = self.root / name
        path.write_text(
            json.dumps(value, ensure_ascii=False, sort_keys=True),
            encoding="utf-8",
        )
        return path

    def _seed_structured_observations(self) -> None:
        module = load_style_module()
        try:
            from PIL import Image
        except ImportError as exc:  # production path intentionally fails closed too
            self.fail(f"Pillow is required by the style evidence contract: {exc}")
        raw_dir = self.root / "raw"
        raw_dir.mkdir()
        asset_rows: list[tuple[object, ...]] = []
        for suffix, color in (
            ("support-1", (230, 40, 70)),
            ("support-2", (40, 120, 230)),
            ("boundary", (120, 120, 120)),
        ):
            image_path = raw_dir / f"{suffix}.png"
            Image.new("RGB", (8, 10), color).save(image_path, format="PNG")
            caption_path = raw_dir / f"{suffix}-caption.txt"
            caption_path.write_text(f"{suffix} caption\n", encoding="utf-8")
            asset_rows.append(
                (
                    f"ASSET-{suffix.upper()}",
                    "image",
                    f"raw/{suffix}.png",
                    hashlib.sha256(image_path.read_bytes()).hexdigest(),
                    "image/png",
                    8,
                    10,
                )
            )
            asset_rows.append(
                (
                    f"CAPTION-{suffix.upper()}",
                    "caption",
                    f"raw/{suffix}-caption.txt",
                    hashlib.sha256(caption_path.read_bytes()).hexdigest(),
                    "text/plain",
                    None,
                    None,
                )
            )
        con = module.connect_db(self.db)
        try:
            con.executemany(
                "INSERT INTO style_accounts(library_account_id,platform) "
                "VALUES (?,'xiaohongshu')",
                [("ACC-LAW-1",), ("ACC-LAW-2",)],
            )
            con.executemany(
                """
                INSERT INTO style_posts(
                    library_post_id,platform,library_account_id,category,
                    cluster_id,status
                ) VALUES (?,'xiaohongshu',?,'法律科普',?,'active')
                """,
                [
                    ("POST-SUPPORT-1", "ACC-LAW-1", "CLUSTER-TOPIC-1"),
                    ("POST-SUPPORT-2", "ACC-LAW-2", "CLUSTER-TOPIC-2"),
                    ("POST-BOUNDARY", "ACC-LAW-1", "CLUSTER-TOPIC-3"),
                    ("BASEPOST-1-1", "ACC-LAW-1", "BASE-1-1"),
                    ("BASEPOST-1-2", "ACC-LAW-1", "BASE-1-2"),
                    ("BASEPOST-2-1", "ACC-LAW-2", "BASE-2-1"),
                    ("BASEPOST-2-2", "ACC-LAW-2", "BASE-2-2"),
                ],
            )
            con.executemany(
                """
                INSERT INTO style_assets(
                    asset_id,asset_kind,asset_path,asset_sha256,mime_type,
                    width,height,access_status,copyright_notes
                ) VALUES (?,?,?,?,?,?,?,'available',
                          'research observation only; do not redistribute')
                """,
                asset_rows,
            )
            con.executemany(
                "UPDATE style_posts SET caption_asset_id=? "
                "WHERE library_post_id=?",
                [
                    ("CAPTION-SUPPORT-1", "POST-SUPPORT-1"),
                    ("CAPTION-SUPPORT-2", "POST-SUPPORT-2"),
                    ("CAPTION-BOUNDARY", "POST-BOUNDARY"),
                ],
            )
            con.executemany(
                """
                INSERT INTO style_slides(
                    slide_id,library_post_id,slide_index,slide_role,asset_id
                ) VALUES (?,?,0,'cover',?)
                """,
                [
                    ("SLIDE-SUPPORT-1", "POST-SUPPORT-1", "ASSET-SUPPORT-1"),
                    ("SLIDE-SUPPORT-2", "POST-SUPPORT-2", "ASSET-SUPPORT-2"),
                    ("SLIDE-BOUNDARY", "POST-BOUNDARY", "ASSET-BOUNDARY"),
                ],
            )
            con.executemany(
                """
                INSERT INTO visual_observations(
                    visual_observation_id,slide_id,library_post_id,
                    observation_sha256,composition,dominant_material,
                    background_type,layout_structure,text_density,
                    hierarchy_levels,image_text_relationship
                ) VALUES (?,?,?,?,'single_focus','type_only','solid','list',
                          'medium','two','text_leads')
                """,
                [
                    ("VIS-SUPPORT-1", "SLIDE-SUPPORT-1", "POST-SUPPORT-1", "c" * 64),
                    ("VIS-SUPPORT-2", "SLIDE-SUPPORT-2", "POST-SUPPORT-2", "7" * 64),
                    ("VIS-BOUNDARY", "SLIDE-BOUNDARY", "POST-BOUNDARY", "d" * 64),
                ],
            )
            con.executemany(
                """
                INSERT INTO copy_observations(
                    observation_id,library_post_id,slide_id,observation_sha256,
                    text_surface,point_of_view,audience_address,register,
                    sentence_length_pattern,line_break_pattern,
                    punctuation_pattern,emoji_pattern,hook_move,
                    narrative_moves,evidence_move,payoff_move,cta_move,
                    image_caption_division
                ) VALUES (?,?,?,?, 'cover','second_person','direct',
                          'plain_explanatory','short','phrase','light','none',
                          'give_answer','setup','state_limit','framework','save',
                          'image_core_caption_context')
                """,
                [
                    ("COPY-SUPPORT-1", "POST-SUPPORT-1", "SLIDE-SUPPORT-1", "e" * 64),
                    ("COPY-SUPPORT-2", "POST-SUPPORT-2", "SLIDE-SUPPORT-2", "8" * 64),
                    ("COPY-BOUNDARY", "POST-BOUNDARY", "SLIDE-BOUNDARY", "f" * 64),
                ],
            )
            con.executemany(
                """
                INSERT INTO copy_observations(
                    observation_id,library_post_id,slide_id,observation_sha256,
                    text_surface,point_of_view,audience_address,register,
                    sentence_length_pattern,line_break_pattern,
                    punctuation_pattern,emoji_pattern,hook_move,
                    narrative_moves,evidence_move,payoff_move,cta_move,
                    image_caption_division
                ) VALUES (?,?,NULL,?, 'caption','second_person','direct',
                          'plain_explanatory','short','phrase','light','none',
                          'give_answer','setup','state_limit','framework','save',
                          'image_core_caption_context')
                """,
                [
                    ("COPY-POST-SUPPORT-1", "POST-SUPPORT-1", "3" * 64),
                    ("COPY-POST-SUPPORT-2", "POST-SUPPORT-2", "5" * 64),
                    ("COPY-POST-BOUNDARY", "POST-BOUNDARY", "4" * 64),
                ],
            )
            con.execute(
                """
                INSERT INTO performance_definitions(
                    performance_definition_id,definition_version,metric_name,
                    business_objective,primary_job,traffic_stage,
                    metric_selection_reason,comparison_design,min_baseline_n,
                    paid_or_pinned_policy,missing_value_policy,tier_rules_json,
                    as_of,review_by,definition_sha256
                ) VALUES (
                    'DEF-LAW',1,'engagement_proxy','engagement_proxy',
                    'search_answer','read_through','public visible proxy only',
                    'account_baseline',2,'exclude','exclude',
                    '{"high_min_multiple":2.0,"low_max_multiple":0.5}',
                    '2026-07-18','2026-08-18',?
                )
                """,
                ("9" * 64,),
            )
            run_refs: list[tuple[str, str, str]] = []
            for account_index in (1, 2):
                for ordinal in (1, 2):
                    run_refs.append(
                        (
                            f"RUN-LAW-{account_index}",
                            f"LOCAL-BASE-{account_index}-{ordinal}",
                            f"BASEPOST-{account_index}-{ordinal}",
                        )
                    )
            run_refs.extend(
                [
                    ("RUN-LAW-1", "LOCAL-SUPPORT-1", "POST-SUPPORT-1"),
                    ("RUN-LAW-2", "LOCAL-SUPPORT-2", "POST-SUPPORT-2"),
                    ("RUN-LAW-1", "LOCAL-BOUNDARY", "POST-BOUNDARY"),
                ]
            )
            con.executemany(
                "INSERT INTO run_post_refs(run_id,run_post_id,library_post_id) "
                "VALUES (?,?,?)",
                run_refs,
            )
            for account_index in (1, 2):
                account_id = f"ACC-LAW-{account_index}"
                baseline_id = f"BASE-LAW-{account_index}"
                included_rows = [
                    f"0|OBS-BASE-{account_index}-1|METRIC-BASE-{account_index}-1|10.0||{{}}|[]",
                    f"1|OBS-BASE-{account_index}-2|METRIC-BASE-{account_index}-2|20.0||{{}}|[]",
                ]
                all_rows = [
                    f"0|OBS-BASE-{account_index}-1|METRIC-BASE-{account_index}-1|included||10.0||{{}}|[]",
                    f"1|OBS-BASE-{account_index}-2|METRIC-BASE-{account_index}-2|included||20.0||{{}}|[]",
                ]
                included_sha = hashlib.sha256(
                    json.dumps(
                        included_rows,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ).encode()
                ).hexdigest()
                all_sha = hashlib.sha256(
                    json.dumps(
                        all_rows,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ).encode()
                ).hexdigest()
                baseline_sha = hashlib.sha256(
                    baseline_id.encode()
                ).hexdigest()
                con.execute(
                    """
                    INSERT INTO account_baseline_snapshots(
                        baseline_snapshot_id,library_account_id,metric_name,
                        sample_n,median_value,performance_definition_id,
                        included_members_sha256,all_members_sha256,
                        baseline_snapshot_sha256,source_run_id
                    ) VALUES (?,?, 'engagement_proxy',2,15.0,'DEF-LAW',?,?,?,?)
                    """,
                    (
                        baseline_id,
                        account_id,
                        included_sha,
                        all_sha,
                        baseline_sha,
                        f"RUN-LAW-{account_index}",
                    ),
                )
                for ordinal, value in ((1, 10.0), (2, 20.0)):
                    observation_id = f"OBS-BASE-{account_index}-{ordinal}"
                    metric_id = f"METRIC-BASE-{account_index}-{ordinal}"
                    con.execute(
                        """
                        INSERT INTO style_post_observations(
                            post_observation_id,library_post_id,
                            library_account_id,run_id,run_post_id,
                            source_csv_sha256,observation_state,
                            performance_definition_id,target_metric_name
                        ) VALUES (?,?,?,?,?,?,'building','DEF-LAW',
                                  'engagement_proxy')
                        """,
                        (
                            observation_id,
                            f"BASEPOST-{account_index}-{ordinal}",
                            account_id,
                            f"RUN-LAW-{account_index}",
                            f"LOCAL-BASE-{account_index}-{ordinal}",
                            hashlib.sha256(observation_id.encode()).hexdigest(),
                        ),
                    )
                    con.execute(
                        """
                        INSERT INTO post_metrics(
                            post_metric_id,post_observation_id,metric_name,
                            metric_value,visibility_scope,metric_sha256
                        ) VALUES (?,?,'engagement_proxy',?,'public_proxy',?)
                        """,
                        (
                            metric_id,
                            observation_id,
                            value,
                            hashlib.sha256(metric_id.encode()).hexdigest(),
                        ),
                    )
                    con.execute(
                        "UPDATE style_post_observations SET "
                        "observation_state='complete',target_post_metric_id=? "
                        "WHERE post_observation_id=?",
                        (metric_id, observation_id),
                    )
                    con.execute(
                        """
                        INSERT INTO account_baseline_members(
                            baseline_snapshot_id,library_account_id,
                            performance_definition_id,metric_name,
                            member_post_observation_id,member_post_metric_id,
                            inclusion_status,metric_value,member_ordinal
                        ) VALUES (?,?,'DEF-LAW','engagement_proxy',?,?,'included',?,?)
                        """,
                        (
                            baseline_id,
                            account_id,
                            observation_id,
                            metric_id,
                            value,
                            ordinal - 1,
                        ),
                    )
                con.execute(
                    """
                    INSERT INTO baseline_snapshot_publications(
                        baseline_snapshot_id,library_account_id,
                        performance_definition_id,metric_name,
                        baseline_snapshot_sha256,included_members_sha256,
                        all_members_sha256
                    ) VALUES (?,?,'DEF-LAW','engagement_proxy',?,?,?)
                    """,
                    (
                        baseline_id,
                        account_id,
                        baseline_sha,
                        included_sha,
                        all_sha,
                    ),
                )
            for post_id, account_index, local_id, value in (
                ("SUPPORT-1", 1, "LOCAL-SUPPORT-1", 40.0),
                ("SUPPORT-2", 2, "LOCAL-SUPPORT-2", 45.0),
                ("BOUNDARY", 1, "LOCAL-BOUNDARY", 5.0),
            ):
                observation_id = f"OBS-{post_id}"
                metric_id = f"METRIC-{post_id}"
                baseline_id = f"BASE-LAW-{account_index}"
                baseline_sha = hashlib.sha256(baseline_id.encode()).hexdigest()
                con.execute(
                    """
                    INSERT INTO style_post_observations(
                        post_observation_id,library_post_id,library_account_id,
                        run_id,run_post_id,source_csv_sha256,observation_state,
                        performance_definition_id,target_metric_name,
                        baseline_snapshot_id,baseline_snapshot_sha256
                    ) VALUES (?,?,?,?,?,?,'building','DEF-LAW',
                              'engagement_proxy',?,?)
                    """,
                    (
                        observation_id,
                        f"POST-{post_id}",
                        f"ACC-LAW-{account_index}",
                        f"RUN-LAW-{account_index}",
                        local_id,
                        hashlib.sha256(observation_id.encode()).hexdigest(),
                        baseline_id,
                        baseline_sha,
                    ),
                )
                con.execute(
                    """
                    INSERT INTO post_metrics(
                        post_metric_id,post_observation_id,metric_name,
                        metric_value,visibility_scope,metric_sha256
                    ) VALUES (?,?,'engagement_proxy',?,'public_proxy',?)
                    """,
                    (
                        metric_id,
                        observation_id,
                        value,
                        hashlib.sha256(metric_id.encode()).hexdigest(),
                    ),
                )
                con.execute(
                    "UPDATE style_post_observations SET "
                    "observation_state='complete',target_post_metric_id=? "
                    "WHERE post_observation_id=?",
                    (metric_id, observation_id),
                )
            con.commit()
        finally:
            con.close()
        module.derive_tier(self.db, "OBS-SUPPORT-1", "BASE-LAW-1")
        module.derive_tier(self.db, "OBS-SUPPORT-2", "BASE-LAW-2")
        module.derive_tier(self.db, "OBS-BOUNDARY", "BASE-LAW-1")

    @staticmethod
    def _candidate_record() -> dict[str, object]:
        common_payload = {
            "claim_kind": "contrastive_performance_hypothesis",
            "performance_evidence_scope": "public_proxy_association",
            "traffic_stage": "read_through",
            "required_material_codes": ["text_only"],
            "required_constraint_codes": [
                "deterministic_chinese_typesetting",
                "no_generated_evidence",
            ],
            "contraindication_codes": ["generated_person_as_evidence"],
            "prohibited_claims": ["traffic_causality", "guaranteed_viral"],
            "selection_requirement": "required",
            "dependency_rule_ids": [],
        }
        return {
            "archetype_id": "ARCH-LAW-NATIVE",
            "name": "结论先行的原生法律清单",
            "category": "法律科普",
            "carrier": "checklist_steps",
            "primary_job": "search_answer",
            "audience_state": "带着具体问题寻找可执行答案",
            "description": "用原生信息卡给结论、边界和下一步，不模仿原帖。",
            "production_cost": "low",
            "confidence": 0.72,
            "archetype_version": 1,
            "rules": [
                {
                    "rule_id": "RULE-LAW-VISUAL",
                    "rule_type": "visual",
                    "applicability_scope": "法律科普×checklist_steps×search_answer",
                    "payload": {
                        **common_payload,
                        "instruction": "首屏先呈现问题与结论，再以边界分层。",
                    },
                    "evidence": [
                        {
                            "rule_evidence_id": "EVID-LAW-VIS-SUPPORT",
                            "observation_type": "visual",
                            "observation_id": "VIS-SUPPORT-1",
                            "post_observation_id": "OBS-SUPPORT-1",
                            "evidence_role": "support",
                            "limitations": "公开互动代理高表现，不支持流量因果。",
                        },
                        {
                            "rule_evidence_id": "EVID-LAW-VIS-SUPPORT-2",
                            "observation_type": "visual",
                            "observation_id": "VIS-SUPPORT-2",
                            "post_observation_id": "OBS-SUPPORT-2",
                            "evidence_role": "support",
                            "limitations": "第二独立账号与内容簇的高表现样本。",
                        },
                        {
                            "rule_evidence_id": "EVID-LAW-VIS-BOUNDARY",
                            "observation_type": "visual",
                            "observation_id": "VIS-BOUNDARY",
                            "post_observation_id": "OBS-BOUNDARY",
                            "evidence_role": "boundary",
                            "limitations": "同类目边界样本。",
                        },
                    ],
                },
                {
                    "rule_id": "RULE-LAW-COPY",
                    "rule_type": "copy",
                    "applicability_scope": "法律科普×checklist_steps×search_answer",
                    "payload": {
                        **common_payload,
                        "instruction": "短句回答，明确适用边界，不写保证性结论。",
                    },
                    "evidence": [
                        {
                            "rule_evidence_id": "EVID-LAW-COPY-SUPPORT",
                            "observation_type": "copy",
                            "observation_id": "COPY-SUPPORT-1",
                            "post_observation_id": "OBS-SUPPORT-1",
                            "evidence_role": "support",
                            "limitations": "不可复用原句。",
                        },
                        {
                            "rule_evidence_id": "EVID-LAW-COPY-SUPPORT-2",
                            "observation_type": "copy",
                            "observation_id": "COPY-SUPPORT-2",
                            "post_observation_id": "OBS-SUPPORT-2",
                            "evidence_role": "support",
                            "limitations": "第二独立账号与内容簇的高表现样本。",
                        },
                        {
                            "rule_evidence_id": "EVID-LAW-COPY-BOUNDARY",
                            "observation_type": "copy",
                            "observation_id": "COPY-BOUNDARY",
                            "post_observation_id": "OBS-BOUNDARY",
                            "evidence_role": "boundary",
                            "limitations": "只约束语域与节奏。",
                        },
                    ],
                },
            ],
        }

    @staticmethod
    def _archetype_review() -> dict[str, object]:
        return {
            "archetype_id": "ARCH-LAW-NATIVE",
            "archetype_version": 1,
            "category": "法律科普",
            "carrier": "checklist_steps",
            "primary_job": "search_answer",
            "selected_rule_ids": ["RULE-LAW-COPY", "RULE-LAW-VISUAL"],
            "decision": "PASS",
            "target_status": "supported",
            "content_owner_id": "OWNER-1",
            "reviewer_ids": ["REVIEWER-2"],
            "reviewer_independence_status": "independent",
            "reviewed_at": "2026-07-18",
            "limitations": [
                "public engagement proxy association only",
                "not traffic causality or a virality guarantee",
            ],
        }

    def test_cli_candidate_review_publish_query_bind_review_and_publish_e2e(self) -> None:
        run_cli("init", self.db)
        self._seed_structured_observations()
        candidate_path = self._write_json("candidate.json", self._candidate_record())
        review = self._archetype_review()
        review_path = self._write_json("archetype-review.json", review)

        created = run_cli("create-archetype", self.db, "--record", candidate_path)
        self.assertEqual(created["status"], "candidate_created")
        before_cli = subprocess.run(
            [
                sys.executable, str(STYLE_CLI), "query", str(self.db),
                "--category", "法律科普",
                "--carrier", "checklist_steps",
                "--primary-job", "search_answer",
                "--traffic-stage", "read_through",
                "--materials", "text_only",
                "--constraints", "deterministic_chinese_typesetting,no_generated_evidence",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(before_cli.returncode, 2)
        self.assertEqual(json.loads(before_cli.stdout)["status"], "needs_style_research")

        reviewed = run_cli("review-archetype", self.db, "--record", review_path)
        self.assertEqual(reviewed["status"], "review_pass")
        self.assertRegex(reviewed["review_receipt_sha256"], r"^[0-9a-f]{64}$")
        published = run_cli("publish-archetype", self.db, "--record", review_path)
        self.assertEqual(published["status"], "published")
        self.assertEqual(published["published_rule_ids"], review["selected_rule_ids"])
        readiness = run_cli("status", self.db)
        self.assertEqual(readiness["counts"]["qualified_style_rules"], 2)
        self.assertEqual(readiness["release_readiness"]["state"], "ready_to_bind")
        self.assertEqual(
            readiness["traffic_stage_qualified_counts"]["read_through"], 2
        )

        exact = run_cli(
            "query", self.db,
            "--category", "法律科普",
            "--carrier", "checklist_steps",
            "--primary-job", "search_answer",
            "--traffic-stage", "read_through",
            "--materials", "text_only",
            "--constraints", "deterministic_chinese_typesetting,no_generated_evidence",
        )
        self.assertEqual(exact["status"], "ready_to_bind")
        self.assertEqual(exact["eligible_count"], 1)
        self.assertEqual(
            exact["eligible_archetypes"][0]["performance_evidence_scope"],
            "public_proxy_association",
        )
        self.assertEqual(len(exact["eligible_archetypes"][0]["selected_rules"]), 2)

        wrong_category = subprocess.run(
            [
                sys.executable, str(STYLE_CLI), "query", str(self.db),
                "--category", "职场",
                "--carrier", "checklist_steps",
                "--primary-job", "search_answer",
                "--traffic-stage", "read_through",
                "--materials", "text_only",
                "--constraints", "deterministic_chinese_typesetting,no_generated_evidence",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(wrong_category.returncode, 2)
        self.assertEqual(json.loads(wrong_category.stdout)["eligible_count"], 0)

        bound = run_cli(
            "bind", self.db,
            "--draft-id", "DRAFT-LAW-1",
            "--draft-binding-id", "BIND-LAW-1",
            "--archetype-id", "ARCH-LAW-NATIVE",
            "--category", "法律科普",
            "--carrier", "checklist_steps",
            "--primary-job", "search_answer",
            "--business-objective", "engagement_proxy",
            "--traffic-stage", "read_through",
            "--materials", "text_only",
            "--constraints", "deterministic_chinese_typesetting,no_generated_evidence",
        )
        self.assertEqual(bound["status"], "binding_created_pending_review")
        self.assertEqual(
            bound["material_plan"]["performance_evidence_scope"],
            "public_proxy_association",
        )
        self.assertIn(
            bound["material_plan"]["primary_performance_rule_id"],
            bound["selected_rule_ids"],
        )
        self.assertEqual(
            bound["material_plan"]["primary_performance_evidence_scope"],
            bound["material_plan"]["performance_evidence_scope"],
        )
        with self.assertRaisesRegex(
            subprocess.CalledProcessError, "returned non-zero exit status"
        ):
            run_cli(
                "publish-binding", self.db,
                "--draft-binding-id", "BIND-LAW-1",
            )

        binding_review = {
            "draft_binding_id": "BIND-LAW-1",
            "decision": "PASS",
            "expected_pending_binding_sha256": bound["pending_binding_sha256"],
            "content_owner_id": "OWNER-1",
            "reviewer_ids": ["REVIEWER-2"],
            "reviewer_independence_status": "independent",
            "reviewed_at": "2026-07-18",
        }
        binding_review_path = self._write_json(
            "binding-review.json", binding_review
        )
        binding_reviewed = run_cli(
            "review-binding", self.db, "--record", binding_review_path
        )
        self.assertEqual(binding_reviewed["status"], "review_pass")
        receipt = run_cli(
            "publish-binding", self.db,
            "--draft-binding-id", "BIND-LAW-1",
        )
        self.assertEqual(receipt["status"], "published")
        self.assertRegex(receipt["binding_sha256"], r"^[0-9a-f]{64}$")

        con = load_style_module().connect_db(self.db)
        self.addCleanup(con.close)
        self.assertEqual(
            con.execute("SELECT status FROM style_archetypes").fetchone()[0],
            "supported",
        )
        self.assertEqual(
            con.execute("SELECT count(*) FROM archetype_rule_publications").fetchone()[0],
            2,
        )
        self.assertEqual(
            con.execute("SELECT count(*) FROM draft_binding_publications").fetchone()[0],
            1,
        )
        self.assertEqual(
            con.execute(
                "SELECT count(*) FROM draft_binding_review_receipts"
            ).fetchone()[0],
            1,
        )

    def test_candidate_ingest_rejects_missing_typed_observation_atomically(self) -> None:
        module = load_style_module()
        module.init_db(self.db)
        self._seed_structured_observations()
        record = self._candidate_record()
        record["rules"][0]["evidence"][0]["observation_id"] = "VIS-FORGED"
        with self.assertRaisesRegex(
            module.StyleLibraryError, "candidate_evidence_observation_missing"
        ):
            module.create_archetype_candidate(self.db, record)
        con = module.connect_db(self.db)
        self.addCleanup(con.close)
        self.assertEqual(con.execute("SELECT count(*) FROM style_archetypes").fetchone()[0], 0)
        self.assertEqual(con.execute("SELECT count(*) FROM archetype_rules").fetchone()[0], 0)

    def test_candidate_accepts_post_level_caption_copy_with_caption_asset(self) -> None:
        module = load_style_module()
        module.init_db(self.db)
        self._seed_structured_observations()
        record = self._candidate_record()
        copy_rule = record["rules"][1]
        copy_rule["evidence"][0]["observation_id"] = "COPY-POST-SUPPORT-1"
        copy_rule["evidence"][1]["observation_id"] = "COPY-POST-SUPPORT-2"
        copy_rule["evidence"][2]["observation_id"] = "COPY-POST-BOUNDARY"
        created = module.create_archetype_candidate(self.db, record)
        self.assertEqual(created["status"], "candidate_created")
        module.review_archetype(self.db, self._archetype_review())
        published = module.publish_archetype(self.db, self._archetype_review())
        self.assertEqual(published["status"], "published")

    def test_candidate_requires_matching_type_support_and_counterevidence(self) -> None:
        module = load_style_module()
        module.init_db(self.db)
        self._seed_structured_observations()
        record = self._candidate_record()
        for index, observation_id in enumerate(
            ("VIS-SUPPORT-1", "VIS-SUPPORT-2")
        ):
            copy_support = record["rules"][1]["evidence"][index]
            copy_support["observation_type"] = "visual"
            copy_support["observation_id"] = observation_id
        with self.assertRaisesRegex(
            module.StyleLibraryError,
            "candidate_matching_type_contrast_missing",
        ):
            module.create_archetype_candidate(self.db, record)

    def test_candidate_rejects_free_text_applicability_scope_drift(self) -> None:
        module = load_style_module()
        module.init_db(self.db)
        self._seed_structured_observations()
        record = self._candidate_record()
        record["rules"][0]["applicability_scope"] = "所有类目都适用"
        with self.assertRaisesRegex(
            module.StyleLibraryError, "candidate_rule_scope_mismatch"
        ):
            module.create_archetype_candidate(self.db, record)

    def test_review_rejects_self_review_and_first_party_claim_without_rule_receipt(self) -> None:
        module = load_style_module()
        module.init_db(self.db)
        self._seed_structured_observations()
        record = self._candidate_record()
        record["rules"][0]["payload"][
            "performance_evidence_scope"
        ] = "first_party_traffic_validated"
        with self.assertRaisesRegex(
            module.StyleLibraryError, "performance_scope_unsupported_by_schema"
        ):
            module.create_archetype_candidate(self.db, record)

        module.create_archetype_candidate(self.db, self._candidate_record())
        review = self._archetype_review()
        review["reviewer_ids"] = [review["content_owner_id"]]
        with self.assertRaisesRegex(
            module.StyleLibraryError, "reviewer_not_independent"
        ):
            module.publish_archetype(self.db, review)
        con = module.connect_db(self.db)
        self.addCleanup(con.close)
        row = con.execute(
            "SELECT status,snapshot_sha256 FROM style_archetypes"
        ).fetchone()
        self.assertEqual(row[0], "candidate")
        self.assertEqual(con.execute("SELECT count(*) FROM archetype_publications").fetchone()[0], 0)
        self.assertEqual(con.execute("SELECT count(*) FROM archetype_rule_publications").fetchone()[0], 0)

    def test_query_and_binding_fail_closed_on_resource_or_review_hash_mismatch(self) -> None:
        module = load_style_module()
        module.init_db(self.db)
        self._seed_structured_observations()
        module.create_archetype_candidate(self.db, self._candidate_record())
        module.review_archetype(self.db, self._archetype_review())
        module.publish_archetype(self.db, self._archetype_review())

        result = module.query_library(
            self.db,
            category="法律科普",
            carrier="checklist_steps",
            primary_job="search_answer",
            traffic_stage="read_through",
            available_material_codes=["text_only"],
            active_constraint_codes=["deterministic_chinese_typesetting"],
            active_contraindication_codes=[],
        )
        self.assertEqual(result["status"], "needs_style_research")
        self.assertTrue(
            any(
                reason.startswith("constraint_inactive:no_generated_evidence")
                for reason in result["published_rejection_audit"][0]["reason_codes"]
            ),
            result["published_rejection_audit"],
        )

        bound = module.bind_draft(
            self.db,
            draft_id="DRAFT-REVIEW-HASH",
            draft_binding_id="BIND-REVIEW-HASH",
            archetype_id="ARCH-LAW-NATIVE",
            category="法律科普",
            carrier="checklist_steps",
            primary_job="search_answer",
            business_objective="engagement_proxy",
            traffic_stage="read_through",
            available_material_codes=["text_only"],
            active_constraint_codes=[
                "deterministic_chinese_typesetting",
                "no_generated_evidence",
            ],
            active_contraindication_codes=[],
        )
        review = {
            "draft_binding_id": "BIND-REVIEW-HASH",
            "decision": "PASS",
            "expected_pending_binding_sha256": "0" * 64,
            "content_owner_id": "OWNER-1",
            "reviewer_ids": ["REVIEWER-2"],
            "reviewer_independence_status": "independent",
            "reviewed_at": "2026-07-18",
        }
        with self.assertRaisesRegex(
            module.StyleLibraryError, "binding_review_preimage_mismatch"
        ):
            module.review_draft_binding(self.db, review)
        con = module.connect_db(self.db)
        self.addCleanup(con.close)
        self.assertEqual(
            con.execute(
                "SELECT review_status FROM draft_style_bindings "
                "WHERE draft_binding_id='BIND-REVIEW-HASH'"
            ).fetchone()[0],
            "pending",
        )
        self.assertRegex(bound["pending_binding_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(
            bound["material_plan"]["business_objective"], "engagement_proxy"
        )

    def test_published_archetype_review_receipt_is_immutable(self) -> None:
        module = load_style_module()
        module.init_db(self.db)
        self._seed_structured_observations()
        module.create_archetype_candidate(self.db, self._candidate_record())
        module.review_archetype(self.db, self._archetype_review())
        module.publish_archetype(self.db, self._archetype_review())
        con = module.connect_db(self.db)
        with self.assertRaisesRegex(
            sqlite3.IntegrityError, "immutable_archetype_review_receipts"
        ):
            con.execute("DELETE FROM archetype_review_receipts")
        con.close()

        self.assertEqual(
            module.status_db(self.db)["counts"]["qualified_style_rules"], 2
        )

        result = module.query_library(
            self.db,
            category="法律科普",
            carrier="checklist_steps",
            primary_job="search_answer",
            traffic_stage="read_through",
            available_material_codes=["text_only"],
            active_constraint_codes=[
                "deterministic_chinese_typesetting",
                "no_generated_evidence",
            ],
            active_contraindication_codes=[],
        )
        self.assertEqual(result["status"], "ready_to_bind")
        self.assertEqual(result["eligible_count"], 1)

    def test_binding_review_rechecks_archetype_review_receipt(self) -> None:
        module = load_style_module()
        module.init_db(self.db)
        self._seed_structured_observations()
        module.create_archetype_candidate(self.db, self._candidate_record())
        module.review_archetype(self.db, self._archetype_review())
        module.publish_archetype(self.db, self._archetype_review())
        bound = module.bind_draft(
            self.db,
            draft_id="DRAFT-LOST-REVIEW",
            draft_binding_id="BIND-LOST-REVIEW",
            archetype_id="ARCH-LAW-NATIVE",
            category="法律科普",
            carrier="checklist_steps",
            primary_job="search_answer",
            business_objective="engagement_proxy",
            traffic_stage="read_through",
            available_material_codes=["text_only"],
            active_constraint_codes=[
                "deterministic_chinese_typesetting",
                "no_generated_evidence",
            ],
            active_contraindication_codes=[],
        )
        con = module.connect_db(self.db)
        con.execute(
            "UPDATE style_assets SET access_status='blocked' "
            "WHERE asset_id='ASSET-SUPPORT-1'"
        )
        con.commit()
        con.close()
        review = {
            "draft_binding_id": "BIND-LOST-REVIEW",
            "decision": "PASS",
            "expected_pending_binding_sha256": bound["pending_binding_sha256"],
            "content_owner_id": "OWNER-1",
            "reviewer_ids": ["REVIEWER-2"],
            "reviewer_independence_status": "independent",
            "reviewed_at": "2026-07-18",
        }
        with self.assertRaisesRegex(
            module.StyleLibraryError, "qualified_rule_evidence_stale"
        ):
            module.review_draft_binding(self.db, review)

    def test_query_excludes_optional_unavailable_rule_without_losing_usable_pair(self) -> None:
        module = load_style_module()
        module.init_db(self.db)
        self._seed_structured_observations()
        record = self._candidate_record()
        optional = json.loads(json.dumps(record["rules"][0]))
        optional["rule_id"] = "RULE-LAW-OPTIONAL-PACKSHOT"
        optional["payload"]["required_material_codes"] = ["product_packshot"]
        optional["payload"]["selection_requirement"] = "optional"
        for item in optional["evidence"]:
            item["rule_evidence_id"] += "-OPTIONAL"
        record["rules"].append(optional)
        review = self._archetype_review()
        review["selected_rule_ids"].append("RULE-LAW-OPTIONAL-PACKSHOT")
        module.create_archetype_candidate(self.db, record)
        module.review_archetype(self.db, review)
        module.publish_archetype(self.db, review)

        result = module.query_library(
            self.db,
            category="法律科普",
            carrier="checklist_steps",
            primary_job="search_answer",
            traffic_stage="read_through",
            available_material_codes=["text_only"],
            active_constraint_codes=[
                "deterministic_chinese_typesetting",
                "no_generated_evidence",
            ],
            active_contraindication_codes=[],
        )
        self.assertEqual(result["status"], "ready_to_bind")
        self.assertEqual(
            result["eligible_archetypes"][0]["selected_rule_ids"],
            ["RULE-LAW-COPY", "RULE-LAW-VISUAL"],
        )
        self.assertIn(
            "material_unavailable:product_packshot@RULE-LAW-OPTIONAL-PACKSHOT",
            result["eligible_archetypes"][0]["excluded_rule_reasons"],
        )

    def test_query_rechecks_backing_asset_after_publication(self) -> None:
        module = load_style_module()
        module.init_db(self.db)
        self._seed_structured_observations()
        module.create_archetype_candidate(self.db, self._candidate_record())
        module.review_archetype(self.db, self._archetype_review())
        module.publish_archetype(self.db, self._archetype_review())
        con = module.connect_db(self.db)
        con.execute(
            "UPDATE style_assets SET access_status='blocked' "
            "WHERE asset_id='ASSET-SUPPORT-1'"
        )
        con.commit()
        con.close()

        result = module.query_library(
            self.db,
            category="法律科普",
            carrier="checklist_steps",
            primary_job="search_answer",
            traffic_stage="read_through",
            available_material_codes=["text_only"],
            active_constraint_codes=[
                "deterministic_chinese_typesetting",
                "no_generated_evidence",
            ],
            active_contraindication_codes=[],
        )
        self.assertEqual(result["status"], "needs_style_research")
        self.assertTrue(
            any(
                reason.startswith("qualified_bundle_unavailable:")
                for reason in result["published_rejection_audit"][0]["reason_codes"]
            ),
            result["published_rejection_audit"],
        )

    def test_review_receipt_rejects_rule_toctou_mutation(self) -> None:
        module = load_style_module()
        module.init_db(self.db)
        self._seed_structured_observations()
        module.create_archetype_candidate(self.db, self._candidate_record())
        review = self._archetype_review()
        module.review_archetype(self.db, review)
        con = module.connect_db(self.db)
        payload = json.loads(
            con.execute(
                "SELECT rule_payload_json FROM archetype_rules "
                "WHERE rule_id='RULE-LAW-COPY'"
            ).fetchone()[0]
        )
        payload["instruction"] = "复核后被偷偷替换的指令"
        con.execute(
            "UPDATE archetype_rules SET rule_payload_json=? "
            "WHERE rule_id='RULE-LAW-COPY'",
            (json.dumps(payload, ensure_ascii=False, sort_keys=True),),
        )
        con.commit()
        con.close()
        with self.assertRaisesRegex(
            module.StyleLibraryError, "review_receipt_missing"
        ):
            module.publish_archetype(self.db, review)
        con = module.connect_db(self.db)
        try:
            self.assertEqual(
                con.execute(
                    "SELECT count(*) FROM archetype_publications"
                ).fetchone()[0],
                0,
            )
        finally:
            con.close()

    def test_published_archetype_version_is_a_closed_rule_set(self) -> None:
        module = load_style_module()
        module.init_db(self.db)
        self._seed_structured_observations()
        module.create_archetype_candidate(self.db, self._candidate_record())
        module.review_archetype(self.db, self._archetype_review())
        module.publish_archetype(self.db, self._archetype_review())
        con = module.connect_db(self.db)
        self.addCleanup(con.close)
        with self.assertRaisesRegex(
            sqlite3.IntegrityError, "published_archetype_rule_set_frozen"
        ):
            con.execute(
                """
                INSERT INTO archetype_rules(
                    rule_id,archetype_id,archetype_version,rule_type,
                    rule_payload_json,applicability_scope,status
                ) VALUES (
                    'RULE-LATE','ARCH-LAW-NATIVE',1,'copy','{}',
                    '法律科普×checklist_steps×search_answer','active'
                )
                """
            )

    def test_candidate_requires_two_independent_support_clusters(self) -> None:
        module = load_style_module()
        module.init_db(self.db)
        self._seed_structured_observations()
        con = module.connect_db(self.db)
        con.execute(
            "UPDATE style_posts SET cluster_id='CLUSTER-TOPIC-1' "
            "WHERE library_post_id='POST-SUPPORT-2'"
        )
        con.commit()
        con.close()
        with self.assertRaisesRegex(
            module.StyleLibraryError, "public_proxy_independent_cluster_missing"
        ):
            module.create_archetype_candidate(self.db, self._candidate_record())

    def test_candidate_rejects_unspecified_traffic_stage(self) -> None:
        module = load_style_module()
        module.init_db(self.db)
        self._seed_structured_observations()
        record = self._candidate_record()
        record["rules"][0]["payload"]["traffic_stage"] = None
        with self.assertRaisesRegex(
            module.StyleLibraryError, "candidate_rule_payload_invalid"
        ):
            module.create_archetype_candidate(self.db, record)

    def test_query_rejects_truncated_asset_even_if_image_header_survives(self) -> None:
        module = load_style_module()
        module.init_db(self.db)
        self._seed_structured_observations()
        module.create_archetype_candidate(self.db, self._candidate_record())
        module.review_archetype(self.db, self._archetype_review())
        module.publish_archetype(self.db, self._archetype_review())
        image_path = self.root / "raw" / "support-1.png"
        image_path.write_bytes(image_path.read_bytes()[:24])
        result = module.query_library(
            self.db,
            category="法律科普",
            carrier="checklist_steps",
            primary_job="search_answer",
            traffic_stage="read_through",
            available_material_codes=["text_only"],
            active_constraint_codes=[
                "deterministic_chinese_typesetting",
                "no_generated_evidence",
            ],
        )
        self.assertEqual(result["status"], "needs_style_research")
        self.assertIn(
            "qualified_rule_evidence_stale",
            result["published_rejection_audit"][0]["reason_codes"][0],
        )

    def test_old_v2_revision_is_rejected_without_silent_migration(self) -> None:
        module = load_style_module()
        con = sqlite3.connect(self.db)
        con.execute(
            "CREATE TABLE style_schema_metadata("
            "singleton INTEGER PRIMARY KEY,schema_version INTEGER,"
            "schema_revision TEXT)"
        )
        con.execute(
            "INSERT INTO style_schema_metadata VALUES "
            "(1,2,'2.1-feature-links')"
        )
        con.execute("PRAGMA user_version=2")
        con.commit()
        con.close()
        before = self.db.read_bytes()
        with self.assertRaisesRegex(
            module.StyleLibraryError, "schema_v2_revision_mismatch"
        ):
            module.init_db(self.db)
        self.assertEqual(self.db.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
