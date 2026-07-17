from __future__ import annotations

import json
import importlib.util
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STYLE_CLI = ROOT / "redbook-writing" / "scripts" / "style_library.py"

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
        con.execute("PRAGMA foreign_keys = ON")
        con.execute(
            "INSERT INTO style_accounts(library_account_id, platform) VALUES (?, ?)",
            ("ACC-A", "xiaohongshu"),
        )
        con.execute(
            """
            INSERT INTO style_posts(
                library_post_id, platform, library_account_id, status
            ) VALUES (?, ?, ?, ?)
            """,
            ("POST-A", "xiaohongshu", "ACC-A", "active"),
        )
        con.execute(
            """
            INSERT INTO run_post_refs(run_id, run_post_id, library_post_id)
            VALUES (?, ?, ?)
            """,
            ("RUN-A", "POST-001", "POST-A"),
        )
        con.execute(
            """
            INSERT INTO style_archetypes(
                archetype_id, name, status, snapshot_sha256
            ) VALUES (?, ?, ?, ?)
            """,
            ("ARCH-A", "Diary", "candidate", "snapshot-a"),
        )
        con.execute(
            """
            INSERT INTO archetype_rules(
                rule_id, archetype_id, archetype_version, rule_type
            ) VALUES (?, ?, ?, ?)
            """,
            ("RULE-A", "ARCH-A", 1, "visual"),
        )
        con.execute(
            """
            INSERT INTO draft_style_bindings(
                draft_binding_id, draft_id, archetype_id, binding_role,
                archetype_version, archetype_snapshot_sha256
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("BIND-A", "DRAFT-A", "ARCH-A", "primary", 1, "snapshot-a"),
        )

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
                ("EVIDENCE-BAD-TYPE", "RULE-A", "slide", "OBS-1", "support"),
            ),
            (
                """
                INSERT INTO rule_evidence(
                    rule_evidence_id, rule_id, observation_type,
                    observation_id, evidence_role
                ) VALUES (?, ?, ?, ?, ?)
                """,
                ("EVIDENCE-BAD-ROLE", "RULE-A", "visual", "OBS-2", "neutral"),
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

    def test_rule_evidence_and_binding_cardinality_are_enforced(self) -> None:
        run_cli("init", self.db)
        con = sqlite3.connect(self.db)
        self.addCleanup(con.close)
        con.execute("PRAGMA foreign_keys = ON")
        con.execute(
            """
            INSERT INTO style_archetypes(
                archetype_id, name, status, snapshot_sha256
            ) VALUES ('ARCH-A', 'Diary', 'candidate', 'snapshot-a')
            """
        )
        con.executemany(
            """
            INSERT INTO archetype_rules(
                rule_id, archetype_id, archetype_version, rule_type
            ) VALUES (?, 'ARCH-A', 1, 'visual')
            """,
            [("RULE-A",), ("RULE-B",)],
        )
        con.execute(
            """
            INSERT INTO rule_evidence(
                rule_evidence_id, rule_id, observation_type,
                observation_id, evidence_role
            ) VALUES ('E-A', 'RULE-A', 'visual', 'OBS-1', 'support')
            """
        )
        with self.assertRaises(sqlite3.IntegrityError):
            con.execute(
                """
                INSERT INTO rule_evidence(
                    rule_evidence_id, rule_id, observation_type,
                    observation_id, evidence_role
                ) VALUES ('E-DUP', 'RULE-A', 'visual', 'OBS-1', 'support')
                """
            )
        with self.assertRaises(sqlite3.IntegrityError):
            con.execute(
                """
                INSERT INTO rule_evidence(
                    rule_evidence_id, rule_id, observation_type,
                    observation_id, evidence_role
                ) VALUES ('E-CONFLICT', 'RULE-A', 'visual', 'OBS-1', 'counterexample')
                """
            )
        con.execute(
            """
            INSERT INTO rule_evidence(
                rule_evidence_id, rule_id, observation_type,
                observation_id, evidence_role
            ) VALUES ('E-B', 'RULE-B', 'visual', 'OBS-1', 'counterexample')
            """
        )

        binding = (
            """
            INSERT INTO draft_style_bindings(
                draft_binding_id, draft_id, archetype_id, binding_role,
                archetype_version, archetype_snapshot_sha256
            ) VALUES (?, ?, 'ARCH-A', ?, 1, 'snapshot-a')
            """
        )
        con.execute(binding, ("BIND-PRIMARY-A", "DRAFT-A", "primary"))
        with self.assertRaises(sqlite3.IntegrityError):
            con.execute(binding, ("BIND-PRIMARY-B", "DRAFT-A", "primary"))
        con.execute(binding, ("BIND-SECONDARY-A", "DRAFT-A", "secondary"))
        with self.assertRaises(sqlite3.IntegrityError):
            con.execute(binding, ("BIND-SECONDARY-B", "DRAFT-A", "secondary"))

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

    def test_taxonomy_v1_is_exact_and_loadable(self) -> None:
        module = load_style_module()
        self.assertEqual(module.load_taxonomy(), EXPECTED_TAXONOMY)

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
