from __future__ import annotations

import importlib.util
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

EXPECTED_TABLES = {
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
    "style_archetypes",
    "archetype_rules",
    "rule_evidence",
    "draft_style_bindings",
    "draft_assets",
    "draft_outcomes",
    "ingest_receipts",
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
            source_csv_sha256, baseline_snapshot_id, performance_tier
        ) VALUES (
            'POST-OBS-A', 'POST-A', 'RUN-A', 'POST-001',
            'sha-source-csv', 'BASELINE-A', 'high'
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
        INSERT INTO visual_observations(visual_observation_id, slide_id)
        VALUES ('VISUAL-A', 'SLIDE-A')
        """
    )
    con.execute(
        """
        INSERT INTO copy_observations(observation_id, library_post_id, slide_id)
        VALUES ('COPY-A', 'POST-A', 'SLIDE-A')
        """
    )
    con.executemany(
        """
        INSERT INTO style_archetypes(
            archetype_id, name, status, current_version, snapshot_sha256
        ) VALUES (?, ?, ?, ?, ?)
        """,
        [
            ("ARCH-A", "Diary", "supported", 2, "snapshot-a-v2"),
            ("ARCH-B", "Checklist", "reusable", 1, "snapshot-b-v1"),
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
            f"snapshot-{archetype_id}-{archetype_version}",
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

    def test_init_creates_v1_schema_without_blob_columns(self) -> None:
        result = run_cli("init", self.db)
        self.assertEqual(result["schema_version"], 1)
        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)
        self.assertEqual(con.execute("PRAGMA user_version").fetchone()[0], 1)
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

    def test_schema_contains_complete_v1_table_set_and_is_idempotent(self) -> None:
        first = run_cli("init", self.db)
        second = run_cli("init", self.db)
        self.assertEqual(first["schema_version"], 1)
        self.assertEqual(second["schema_version"], 1)

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
        con.execute("PRAGMA user_version = 2")
        con.commit()
        con.close()

        module = load_style_module()
        with self.assertRaisesRegex(
            module.StyleLibraryError, "schema_version_unsupported"
        ):
            module.init_db(self.db)

        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)
        self.assertEqual(con.execute("PRAGMA user_version").fetchone()[0], 2)
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

    def test_each_draft_allows_at_most_one_secondary_binding(self) -> None:
        run_cli("init", self.db)
        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)
        seed_style_graph(con)
        insert_binding(con, "BIND-PRIMARY", "DRAFT-A")
        insert_binding(
            con,
            "BIND-SECONDARY-A",
            "DRAFT-A",
            archetype_id="ARCH-B",
            binding_role="secondary",
            selected_rule_ids='["RULE-OTHER"]',
        )
        with self.assertRaises(sqlite3.IntegrityError):
            insert_binding(
                con,
                "BIND-SECONDARY-B",
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

    def test_primary_binding_cannot_be_deleted_before_secondary(self) -> None:
        run_cli("init", self.db)
        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)
        seed_style_graph(con)
        insert_binding(con, "BIND-PRIMARY", "DRAFT-A")
        insert_binding(
            con,
            "BIND-SECONDARY",
            "DRAFT-A",
            archetype_id="ARCH-B",
            binding_role="secondary",
            selected_rule_ids='["RULE-OTHER"]',
        )
        with self.assertRaises(sqlite3.IntegrityError):
            con.execute(
                "DELETE FROM draft_style_bindings WHERE draft_binding_id='BIND-PRIMARY'"
            )
        con.execute(
            "DELETE FROM draft_style_bindings WHERE draft_binding_id='BIND-SECONDARY'"
        )
        con.execute(
            "DELETE FROM draft_style_bindings WHERE draft_binding_id='BIND-PRIMARY'"
        )
        self.assertEqual(
            con.execute(
                "SELECT count(*) FROM draft_style_bindings WHERE draft_id='DRAFT-A'"
            ).fetchone()[0],
            0,
        )

    def test_primary_binding_cannot_move_away_from_its_secondary(self) -> None:
        run_cli("init", self.db)
        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)
        seed_style_graph(con)
        insert_binding(con, "BIND-PRIMARY", "DRAFT-A")
        insert_binding(
            con,
            "BIND-SECONDARY",
            "DRAFT-A",
            archetype_id="ARCH-B",
            binding_role="secondary",
            selected_rule_ids='["RULE-OTHER"]',
        )
        with self.assertRaises(sqlite3.IntegrityError):
            con.execute(
                """
                UPDATE draft_style_bindings SET draft_id='DRAFT-B'
                WHERE draft_binding_id='BIND-PRIMARY'
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
        insert_binding(con, "BIND-A", "DRAFT-A")
        con.execute(
            """
            INSERT INTO draft_assets(
                draft_asset_id, draft_binding_id, asset_id,
                slide_index, style_rule_ids
            ) VALUES (
                'DRAFT-ASSET-A', 'BIND-A', 'ASSET-DRAFT-1', 0,
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
                'STARTER-WARM', 1, 'starter-sha', 'PROMPT-COVER',
                '[]', NULL, NULL, NULL
            )
            """
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
        con.execute(
            """
            INSERT INTO draft_style_bindings(
                draft_binding_id, draft_id, binding_role, binding_source,
                starter_pack_id, starter_pack_version,
                starter_pack_sha256, starter_prompt_id,
                selected_rule_ids
            ) VALUES (
                'BIND-STARTER', 'DRAFT-STARTER', 'primary', 'starter_pack',
                'STARTER-WARM', 1, 'starter-sha', 'PROMPT-COVER', '[]'
            )
            """
        )
        con.executemany(
            """
            INSERT INTO draft_assets(
                draft_asset_id, draft_binding_id, asset_id,
                slide_index, style_rule_ids
            ) VALUES (?, ?, ?, 0, ?)
            """,
            [
                (
                    "DRAFT-ASSET-LIBRARY",
                    "BIND-LIBRARY",
                    "ASSET-DRAFT-1",
                    '["RULE-A"]',
                ),
                (
                    "DRAFT-ASSET-STARTER",
                    "BIND-STARTER",
                    "ASSET-DRAFT-2",
                    "[]",
                ),
            ],
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
            (
                "starter-to-library",
                """
                UPDATE draft_style_bindings
                SET binding_source = 'library',
                    archetype_id = 'ARCH-A',
                    archetype_version = 1,
                    archetype_snapshot_sha256 = 'snapshot-a-v1',
                    selected_rule_ids = '["RULE-A"]',
                    starter_pack_id = NULL,
                    starter_pack_version = NULL,
                    starter_pack_sha256 = NULL,
                    starter_prompt_id = NULL
                WHERE draft_binding_id = 'BIND-STARTER'
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
            ) VALUES (?, ?, 'ASSET-DRAFT-1', 0, '["RULE-A"]')
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
                'DRAFT-ASSET-1', 'BIND-A', 'ASSET-DRAFT-1', 0,
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
                    'DRAFT-ASSET-CONFLICT', 'BIND-A', 'ASSET-DRAFT-2', 0,
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
                'DRAFT-ASSET-2', 'BIND-A', 'ASSET-DRAFT-2', 0,
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
        for index, rule_ids in enumerate(invalid_rule_ids):
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
                0, '["RULE-A"]', 1
            )
            """
        )

    def test_starter_pack_draft_asset_cannot_claim_library_rule_ids(self) -> None:
        run_cli("init", self.db)
        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)
        seed_style_graph(con)
        con.execute(
            """
            INSERT INTO draft_style_bindings(
                draft_binding_id, draft_id, binding_role, binding_source,
                starter_pack_id, starter_pack_version,
                starter_pack_sha256, starter_prompt_id,
                selected_rule_ids
            ) VALUES (
                'BIND-STARTER', 'DRAFT-STARTER', 'primary', 'starter_pack',
                'STARTER-WARM', 1, 'starter-sha', 'PROMPT-COVER', '[]'
            )
            """
        )
        with self.assertRaises(sqlite3.IntegrityError):
            con.execute(
                """
                INSERT INTO draft_assets(
                    draft_asset_id, draft_binding_id, asset_id,
                    slide_index, style_rule_ids
                ) VALUES (
                    'DRAFT-ASSET-STARTER', 'BIND-STARTER', 'ASSET-DRAFT-1',
                    0, '["RULE-A"]'
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
                0, '["RULE-A"]', 0
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
                    0, '["RULE-A"]', 'DRAFT-ASSET-BASE', 1
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
                    1, '["RULE-A"]', 'DRAFT-ASSET-BASE', 1
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

    def test_database_taxonomy_version_is_exactly_v1(self) -> None:
        run_cli("init", self.db)
        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)
        seed_style_graph(con)
        updates = [
            "UPDATE style_slides SET taxonomy_version=2 WHERE slide_id='SLIDE-A'",
            """
            UPDATE visual_observations SET taxonomy_version=2
            WHERE visual_observation_id='VISUAL-A'
            """,
            """
            UPDATE copy_observations SET taxonomy_version=2
            WHERE observation_id='COPY-A'
            """,
            """
            UPDATE style_archetypes SET taxonomy_version=2
            WHERE archetype_id='ARCH-A'
            """,
        ]
        for statement in updates:
            with self.subTest(statement=statement):
                with self.assertRaises(sqlite3.IntegrityError):
                    con.execute(statement)

    def test_taxonomy_v1_is_exact_and_loadable(self) -> None:
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


if __name__ == "__main__":
    unittest.main()
