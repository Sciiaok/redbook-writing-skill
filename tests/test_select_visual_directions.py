from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import subprocess
import tempfile
import unittest
from base64 import b64decode
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LIBRARY = ROOT / "redbook-writing" / "assets" / "visual-direction-cards-v1.json"
SCRIPT = ROOT / "redbook-writing" / "scripts" / "select_visual_directions.py"


def receipt(
    asset_id: str,
    *material_codes: str,
    expires_at: str | None = None,
    asset_path: str | None = None,
    media_dimensions: dict[str, int] | None = None,
    test_content: bytes | None = None,
    test_symlink_outside: bool = False,
) -> dict[str, object]:
    content = test_content if test_content is not None else asset_id.encode()
    payload: dict[str, object] = {
        "asset_id": asset_id,
        "asset_path": asset_path or f"assets/{asset_id}.txt",
        "material_codes": list(material_codes),
        "sha256": hashlib.sha256(content).hexdigest(),
        "media_dimensions": media_dimensions,
        "rights_basis": "owned",
        "authorization_ref": None,
        "license_ref": None,
        "transform_history": [],
        "privacy_review": "not_applicable",
        "commercial_disclosure": "not_applicable",
        "expires_at": expires_at,
    }
    if test_content is not None:
        payload["_test_content_hex"] = content.hex()
    if test_symlink_outside:
        payload["_test_symlink_outside"] = True
    return payload


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def canonical_row_sha256(*values: object) -> str:
    normalized = [float(value) if isinstance(value, float) else value for value in values]
    return hashlib.sha256(canonical_json(normalized).encode()).hexdigest()


def binding(
    job: str,
    carrier: str,
    category: str = "test-category",
    *,
    tamper_binding_hash: bool = False,
) -> dict[str, object]:
    return {
        "draft_binding_id": "DSB-TEST-001",
        "category": category,
        "primary_job": job,
        "carrier": carrier,
        "tamper_binding_hash": tamper_binding_hash,
    }


def write_style_library(path: Path, spec: dict[str, object]) -> None:
    category = str(spec["category"])
    job = str(spec["primary_job"])
    carrier = str(spec["carrier"])
    draft_binding_id = str(spec["draft_binding_id"])
    archetype_id = "ARCH-TEST-001"
    archetype_version = 1
    confidence = 0.9
    archetype_values = (
        archetype_id,
        "Test published archetype",
        category,
        carrier,
        job,
        "test audience",
        "test description",
        "medium",
        confidence,
        "supported",
        archetype_version,
        2,
    )
    snapshot_sha256 = canonical_row_sha256(*archetype_values)
    rule_id = "RULE-TEST-001"
    rule_payload = {
        "palette": {"source": "published observation"},
        "typography": {"source": "published observation"},
        "image_treatment": {"source": "published observation"},
        "density": {"source": "published observation"},
        "annotation_language": {"source": "published observation"},
        "crop_logic": {"source": "published observation"},
    }
    rule_payload_json = canonical_json(rule_payload)
    rule_hash = canonical_row_sha256(
        rule_id,
        archetype_id,
        archetype_version,
        "visual",
        rule_payload_json,
        "exact category/job/carrier",
        "active",
    )
    selected_rule_ids = canonical_json([rule_id])
    reference_posts = canonical_json(["POST-REF"])
    counter_posts = canonical_json(["POST-COUNTER"])
    material_plan = canonical_json({"asset_manifest_required": True})
    deviations = canonical_json([])
    anti_patterns = canonical_json(["generic-ai-ppt"])
    draft_id = "DRAFT-TEST-001"
    binding_hash = canonical_row_sha256(
        draft_binding_id,
        draft_id,
        "library",
        archetype_id,
        archetype_version,
        snapshot_sha256,
        None,
        None,
        None,
        None,
        selected_rule_ids,
        reference_posts,
        counter_posts,
        material_plan,
        deviations,
        anti_patterns,
        "PASS",
    )
    if spec.get("tamper_binding_hash"):
        binding_hash = "0" * 64

    con = sqlite3.connect(path)
    try:
        con.executescript(
            """
            PRAGMA user_version = 2;
            CREATE TABLE style_archetypes (
                archetype_id TEXT PRIMARY KEY, name TEXT, category_scope TEXT,
                carrier TEXT, primary_job_scope TEXT, audience_state TEXT,
                description TEXT, production_cost TEXT, confidence REAL,
                status TEXT, current_version INTEGER, snapshot_sha256 TEXT,
                taxonomy_version INTEGER
            );
            CREATE TABLE archetype_publications (
                archetype_id TEXT, archetype_version INTEGER,
                archetype_snapshot_sha256 TEXT, published_at TEXT
            );
            CREATE TABLE archetype_rules (
                rule_id TEXT PRIMARY KEY, archetype_id TEXT,
                archetype_version INTEGER, rule_type TEXT,
                rule_payload_json TEXT, applicability_scope TEXT, status TEXT
            );
            CREATE TABLE archetype_rule_publications (
                rule_id TEXT, archetype_id TEXT, archetype_version INTEGER,
                archetype_snapshot_sha256 TEXT, rule_sha256 TEXT,
                evidence_set_sha256 TEXT, evidence_count INTEGER, published_at TEXT
            );
            CREATE TABLE draft_style_bindings (
                draft_binding_id TEXT PRIMARY KEY, draft_id TEXT,
                binding_source TEXT, archetype_id TEXT, binding_role TEXT,
                archetype_version INTEGER, archetype_snapshot_sha256 TEXT,
                starter_pack_id TEXT, starter_pack_version INTEGER,
                starter_pack_sha256 TEXT, starter_prompt_id TEXT,
                selected_rule_ids TEXT, reference_library_post_ids TEXT,
                counterexample_library_post_ids TEXT, material_plan_json TEXT,
                intentional_deviations_json TEXT, anti_patterns_checked_json TEXT,
                retrieved_at TEXT, review_status TEXT
            );
            CREATE TABLE draft_binding_publications (
                draft_binding_id TEXT, draft_id TEXT, binding_sha256 TEXT,
                published_at TEXT
            );
            """
        )
        con.execute(
            "INSERT INTO style_archetypes VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (*archetype_values[:-1], snapshot_sha256, archetype_values[-1]),
        )
        con.execute(
            "INSERT INTO archetype_publications VALUES (?,?,?,?)",
            (archetype_id, archetype_version, snapshot_sha256, "2026-07-18T00:00:00Z"),
        )
        con.execute(
            "INSERT INTO archetype_rules VALUES (?,?,?,?,?,?,?)",
            (
                rule_id,
                archetype_id,
                archetype_version,
                "visual",
                rule_payload_json,
                "exact category/job/carrier",
                "active",
            ),
        )
        con.execute(
            "INSERT INTO archetype_rule_publications VALUES (?,?,?,?,?,?,?,?)",
            (
                rule_id,
                archetype_id,
                archetype_version,
                snapshot_sha256,
                rule_hash,
                "1" * 64,
                2,
                "2026-07-18T00:00:00Z",
            ),
        )
        con.execute(
            "INSERT INTO draft_style_bindings VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                draft_binding_id,
                draft_id,
                "library",
                archetype_id,
                "primary",
                archetype_version,
                snapshot_sha256,
                None,
                None,
                None,
                None,
                selected_rule_ids,
                reference_posts,
                counter_posts,
                material_plan,
                deviations,
                anti_patterns,
                "2026-07-18T00:00:00Z",
                "PASS",
            ),
        )
        con.execute(
            "INSERT INTO draft_binding_publications VALUES (?,?,?,?)",
            (draft_binding_id, draft_id, binding_hash, "2026-07-18T00:00:00Z"),
        )
        con.commit()
    finally:
        con.close()


class SelectVisualDirectionsTests(unittest.TestCase):
    def run_cli(
        self,
        *,
        job: str,
        carrier: str,
        assets: list[dict[str, object]] | None,
        style_binding: dict[str, object] | None = None,
        mode: str = "production",
        contraindications: tuple[str, ...] = (),
        category: str = "test-category",
    ) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as temporary_directory:
            manifest_directory = Path(temporary_directory) / "run"
            manifest_directory.mkdir()
            args = [
                "python3",
                str(SCRIPT),
                "--job",
                job,
                "--category",
                category,
                "--carrier",
                carrier,
                "--mode",
                mode,
                "--json",
            ]
            if assets is not None:
                serialized_assets = []
                for source in assets:
                    asset = dict(source)
                    content = bytes.fromhex(
                        str(
                            asset.pop(
                                "_test_content_hex",
                                str(asset.get("asset_id", "missing")).encode().hex(),
                            )
                        )
                    )
                    symlink_outside = bool(asset.pop("_test_symlink_outside", False))
                    relative_path = asset.get(
                        "asset_path", f"assets/{asset.get('asset_id', 'missing')}.txt"
                    )
                    local_path = manifest_directory / str(relative_path)
                    local_path.parent.mkdir(parents=True, exist_ok=True)
                    if symlink_outside:
                        outside = Path(temporary_directory) / f"outside-{asset['asset_id']}"
                        outside.write_bytes(content)
                        local_path.symlink_to(outside)
                    else:
                        local_path.write_bytes(content)
                    serialized_assets.append(asset)
                manifest = manifest_directory / "assets.json"
                manifest.write_text(
                    json.dumps(
                        {"asset_manifest_refs": serialized_assets}, ensure_ascii=False
                    ),
                    encoding="utf-8",
                )
                args.extend(["--asset-manifest", str(manifest)])
            if style_binding is not None:
                style = Path(temporary_directory) / "style-library.sqlite"
                write_style_library(style, style_binding)
                args.extend(
                    [
                        "--style-library",
                        str(style),
                        "--draft-binding-id",
                        str(style_binding["draft_binding_id"]),
                    ]
                )
            for code in contraindications:
                args.extend(["--contraindication", code])
            return subprocess.run(
                args,
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

    def test_library_is_candidate_skeleton_with_four_native_carriers(self) -> None:
        payload = json.loads(LIBRARY.read_text(encoding="utf-8"))
        self.assertEqual(payload["schema_version"], "1.1.0")
        self.assertEqual(len(payload["cards"]), 16)
        self.assertTrue(
            {
                "chat_dramatization",
                "process_video",
                "screen_recording",
                "talking_head_or_field_video",
            }.issubset(payload["carrier_taxonomy"])
        )
        for card in payload["cards"]:
            with self.subTest(card=card["card_id"]):
                self.assertEqual(card["performance_evidence_status"], "candidate_only")
                self.assertEqual(
                    card["performance_evidence_scope"], "not_performance_evidence"
                )
                self.assertFalse(card["starter_eligible"])
                self.assertEqual(card["maturity"], "prototype")
                self.assertIn(
                    card["selection_eligibility"],
                    {"requires_published_style_binding", "series_modifier_only"},
                )
                self.assertTrue(card["decision_predicate"]["all"])
                self.assertTrue(card["not_for"])
                self.assertTrue(card["nearest_alternative"])
                self.assertEqual(
                    set(card["carrier_role_plans"]), set(card["suitable"]["carriers"])
                )
                self.assertEqual(
                    set(card["material_count_gates"]),
                    set(card["suitable"]["carriers"]),
                )

    def test_prompt_variable_contract_covers_every_proof_and_asset_manifest(self) -> None:
        payload = json.loads(LIBRARY.read_text(encoding="utf-8"))
        allowed_null_behaviors = {
            "block_selection",
            "omit_clause",
            "render_as_not_applicable",
            "require_human_review",
        }
        for card in payload["cards"]:
            with self.subTest(card=card["card_id"]):
                variables = {item["name"]: item for item in card["prompt_variables"]}
                self.assertIn("asset_manifest_refs", variables)
                for variable in variables.values():
                    self.assertIsInstance(variable["type"], str)
                    self.assertIsInstance(variable["required"], bool)
                    self.assertIn(variable["null_behavior"], allowed_null_behaviors)
                    if variable["required"]:
                        self.assertEqual(variable["null_behavior"], "block_selection")
                required_proofs = {
                    item["required_proof"] for item in card["page_roles"]
                }
                for plan in card["carrier_role_plans"].values():
                    required_proofs.update(
                        role["required_proof"] for role in plan["roles"]
                    )
                self.assertTrue(
                    required_proofs.issubset(variables),
                    required_proofs - variables.keys(),
                )
                for proof in required_proofs:
                    self.assertTrue(variables[proof]["required"], proof)
                placeholders = set(re.findall(r"\{([a-zA-Z0-9_]+)\}", card["prompt_template"]))
                self.assertTrue(placeholders.issubset(variables), placeholders - variables.keys())
                self.assertIn("asset_manifest_refs", card["prompt_template"])

    def test_cards_do_not_encode_unsupported_fixed_ratios_or_word_limits(self) -> None:
        text = LIBRARY.read_text(encoding="utf-8")
        self.assertNotRegex(text, r"\d+\s*%|\d+\s*％")
        self.assertNotRegex(text, r"\d+\s*[—-]\s*\d+\s*字|\d+\s*字(?:内|以下|以上)")

    def test_manifest_contract_requires_rights_and_integrity_receipts(self) -> None:
        payload = json.loads(LIBRARY.read_text(encoding="utf-8"))
        required = set(payload["asset_manifest_contract"]["required_fields"])
        self.assertEqual(
            required,
            {
                "asset_id",
                "asset_path",
                "material_codes",
                "sha256",
                "media_dimensions",
                "rights_basis",
                "authorization_ref",
                "license_ref",
                "transform_history",
                "privacy_review",
                "commercial_disclosure",
                "expires_at",
            },
        )
        self.assertEqual(
            payload["asset_manifest_contract"]["nullable_fields"],
            {
                "authorization_ref": "only_when_rights_basis_does_not_require_it",
                "license_ref": "only_when_rights_basis_is_not_licensed",
                "expires_at": "only_for_non_expiring_rights_or_currentness",
                "media_dimensions": "only_for_non_visual_files",
            },
        )
        style_contract = payload["style_binding_contract"]
        self.assertEqual(
            style_contract["source"], "sqlite_publication_reconciliation_only"
        )
        self.assertIn("category", style_contract["exact_match_fields"])
        self.assertEqual(
            style_contract["standalone_json_policy"],
            "rejected_self_declared_not_publication_evidence",
        )

    def test_exact_job_carrier_material_and_binding_returns_skeleton(self) -> None:
        assets = [
            receipt(
                "screen-1",
                "current_owned_screen_captures",
                "device_or_app_version",
                "redacted_private_data",
            ),
            receipt("screen-2", "current_owned_screen_captures"),
            receipt("screen-3", "current_owned_screen_captures"),
            receipt("path", "verified_path"),
        ]
        result = self.run_cli(
            job="search_answer",
            carrier="screenshot_markup",
            assets=assets,
            style_binding=binding("search_answer", "screenshot_markup"),
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "matched")
        self.assertEqual(payload["query"]["category"], "test-category")
        self.assertTrue(payload["matches"])
        for match in payload["matches"]:
            self.assertEqual(match["query_fit"]["primary_job"], "exact")
            self.assertEqual(match["query_fit"]["carrier"], "exact")
            self.assertEqual(
                match["aesthetic_control"]["source"], "published_style_binding"
            )
            self.assertEqual(
                match["aesthetic_control"]["binding_id"], "DSB-TEST-001"
            )
            self.assertEqual(
                match["aesthetic_control"]["category"], "test-category"
            )
            self.assertRegex(
                match["aesthetic_control"]["binding_sha256"], r"^[0-9a-f]{64}$"
            )
            for field in (
                "palette",
                "typography",
                "image_treatment",
                "density",
                "annotation_language",
                "crop_logic",
            ):
                self.assertEqual(
                    match["aesthetic_control"]["aesthetic_contract"][field][0][
                        "rule_id"
                    ],
                    "RULE-TEST-001",
                )
            self.assertFalse(match["direction_card_controls_aesthetics"])
            self.assertTrue(match["carrier_role_plan"]["roles"])

    def test_missing_materials_returns_no_eligible_card_without_invention(self) -> None:
        result = self.run_cli(
            job="search_answer",
            carrier="screenshot_markup",
            assets=[receipt("screen-1", "current_owned_screen_captures")],
            style_binding=binding("search_answer", "screenshot_markup"),
        )
        self.assertEqual(result.returncode, 2)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "no_eligible_card")
        self.assertEqual(payload["matches"], [])
        self.assertIn("verified_path", payload["prototype_gaps"][0]["missing_materials"])

    def test_active_contraindication_returns_no_eligible_card(self) -> None:
        assets = [
            receipt(
                "screen-1",
                "current_owned_screen_captures",
                "device_or_app_version",
                "redacted_private_data",
                "verified_path",
            ),
            receipt("screen-2", "current_owned_screen_captures"),
        ]
        result = self.run_cli(
            job="search_answer",
            carrier="screenshot_markup",
            assets=assets,
            style_binding=binding("search_answer", "screenshot_markup"),
            contraindications=("private_data_unredacted",),
        )
        self.assertEqual(result.returncode, 2)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "no_eligible_card")
        self.assertIn(
            "private_data_unredacted",
            payload["prototype_gaps"][0]["active_contraindications"],
        )

    def test_candidate_without_published_binding_returns_prototype_gap(self) -> None:
        assets = [
            receipt(
                "screen-1",
                "current_owned_screen_captures",
                "device_or_app_version",
                "redacted_private_data",
                "verified_path",
            ),
            receipt("screen-2", "current_owned_screen_captures"),
        ]
        result = self.run_cli(
            job="search_answer",
            carrier="screenshot_markup",
            assets=assets,
        )
        self.assertEqual(result.returncode, 2)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "prototype_gap")
        self.assertEqual(payload["matches"], [])
        self.assertIn("published_style_binding", payload["missing_requirements"])

    def test_non_exact_style_binding_cannot_supply_aesthetics(self) -> None:
        assets = [
            receipt(
                "screen-1",
                "current_owned_screen_captures",
                "device_or_app_version",
                "redacted_private_data",
                "verified_path",
            ),
            receipt("screen-2", "current_owned_screen_captures"),
        ]
        result = self.run_cli(
            job="search_answer",
            carrier="screenshot_markup",
            assets=assets,
            style_binding=binding("search_answer", "text_card"),
        )
        self.assertEqual(result.returncode, 2)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "prototype_gap")
        self.assertEqual(payload["matches"], [])
        self.assertIn("exact_published_style_binding", payload["missing_requirements"])

    def test_standalone_style_binding_json_is_not_a_supported_cli_input(self) -> None:
        result = subprocess.run(
            [
                "python3",
                str(SCRIPT),
                "--category",
                "test-category",
                "--job",
                "search_answer",
                "--carrier",
                "screenshot_markup",
                "--style-binding",
                "self-declared.json",
                "--json",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("unrecognized arguments: --style-binding", result.stderr)

    def test_category_mismatch_and_tampered_db_receipt_are_rejected(self) -> None:
        assets = [
            receipt(
                "screen-1",
                "current_owned_screen_captures",
                "device_or_app_version",
                "redacted_private_data",
                "verified_path",
            ),
            receipt("screen-2", "current_owned_screen_captures"),
        ]
        result = self.run_cli(
            job="search_answer",
            carrier="screenshot_markup",
            category="test-category",
            assets=assets,
            style_binding=binding(
                "search_answer", "screenshot_markup", category="other-category"
            ),
        )
        self.assertEqual(result.returncode, 2)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "prototype_gap")
        self.assertIn("category", payload["message"])

        result = self.run_cli(
            job="search_answer",
            carrier="screenshot_markup",
            assets=assets,
            style_binding=binding(
                "search_answer", "screenshot_markup", tamper_binding_hash=True
            ),
        )
        self.assertEqual(result.returncode, 2)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "prototype_gap")
        self.assertIn("binding publication hash mismatch", payload["message"])

    def test_explicit_exploration_can_use_candidate_as_prototype_direction(self) -> None:
        assets = [
            receipt(
                "screen-1",
                "current_owned_screen_captures",
                "device_or_app_version",
                "redacted_private_data",
                "verified_path",
            ),
            receipt("screen-2", "current_owned_screen_captures"),
        ]
        result = self.run_cli(
            job="search_answer",
            carrier="screenshot_markup",
            assets=assets,
            mode="exploration",
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "matched_exploration")
        self.assertTrue(payload["matches"])
        self.assertTrue(payload["matches"][0]["sole_direction_allowed"])
        self.assertEqual(payload["matches"][0]["output_ceiling"], "prototype_only")

    def test_invalid_asset_receipt_is_rejected_before_selection(self) -> None:
        invalid = receipt(
            "screen-1",
            "current_owned_screen_captures",
            "device_or_app_version",
            "redacted_private_data",
            "verified_path",
        )
        invalid.pop("privacy_review")
        result = self.run_cli(
            job="search_answer",
            carrier="screenshot_markup",
            assets=[invalid],
            style_binding=binding("search_answer", "screenshot_markup"),
        )
        self.assertEqual(result.returncode, 2)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "invalid_asset_manifest")
        self.assertIn("privacy_review", payload["message"])

    def test_expired_asset_receipt_is_not_available_material(self) -> None:
        assets = [
            receipt(
                "screen-1",
                "current_owned_screen_captures",
                "device_or_app_version",
                "redacted_private_data",
                "verified_path",
                expires_at="2000-01-01",
            )
        ]
        result = self.run_cli(
            job="search_answer",
            carrier="screenshot_markup",
            assets=assets,
            style_binding=binding("search_answer", "screenshot_markup"),
        )
        self.assertEqual(result.returncode, 2)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "invalid_asset_manifest")
        self.assertIn("expired", payload["message"])

    def test_missing_asset_path_and_hash_mismatch_are_rejected(self) -> None:
        missing_path = receipt(
            "screen-1",
            "current_owned_screen_captures",
            "device_or_app_version",
            "redacted_private_data",
            "verified_path",
        )
        missing_path.pop("asset_path")
        result = self.run_cli(
            job="search_answer",
            carrier="screenshot_markup",
            assets=[missing_path, receipt("screen-2", "current_owned_screen_captures")],
            style_binding=binding("search_answer", "screenshot_markup"),
        )
        self.assertEqual(result.returncode, 2)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "invalid_asset_manifest")
        self.assertIn("asset_path", payload["message"])

        wrong_hash = receipt(
            "screen-1",
            "current_owned_screen_captures",
            "device_or_app_version",
            "redacted_private_data",
            "verified_path",
        )
        wrong_hash["sha256"] = "0" * 64
        result = self.run_cli(
            job="search_answer",
            carrier="screenshot_markup",
            assets=[wrong_hash, receipt("screen-2", "current_owned_screen_captures")],
            style_binding=binding("search_answer", "screenshot_markup"),
        )
        self.assertEqual(result.returncode, 2)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "invalid_asset_manifest")
        self.assertIn("sha256 mismatch", payload["message"])

    def test_asset_path_traversal_and_outside_symlink_are_rejected(self) -> None:
        traversal = receipt(
            "screen-1",
            "current_owned_screen_captures",
            "device_or_app_version",
            "redacted_private_data",
            "verified_path",
            asset_path="../outside.txt",
        )
        result = self.run_cli(
            job="search_answer",
            carrier="screenshot_markup",
            assets=[traversal, receipt("screen-2", "current_owned_screen_captures")],
            style_binding=binding("search_answer", "screenshot_markup"),
        )
        self.assertEqual(result.returncode, 2)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "invalid_asset_manifest")
        self.assertIn("path traversal", payload["message"])

        symlink = receipt(
            "screen-1",
            "current_owned_screen_captures",
            "device_or_app_version",
            "redacted_private_data",
            "verified_path",
            asset_path="assets/link.txt",
            test_symlink_outside=True,
        )
        result = self.run_cli(
            job="search_answer",
            carrier="screenshot_markup",
            assets=[symlink, receipt("screen-2", "current_owned_screen_captures")],
            style_binding=binding("search_answer", "screenshot_markup"),
        )
        self.assertEqual(result.returncode, 2)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "invalid_asset_manifest")
        self.assertIn("outside manifest root", payload["message"])

    def test_image_dimensions_are_read_from_file_not_self_declared(self) -> None:
        one_pixel_png = b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8A"
            "AQUBAScY42YAAAAASUVORK5CYII="
        )
        common = (
            "current_owned_screen_captures",
            "device_or_app_version",
            "redacted_private_data",
            "verified_path",
        )
        valid_image = receipt(
            "screen-1",
            *common,
            asset_path="assets/screen-1.png",
            media_dimensions={"width_px": 1, "height_px": 1},
            test_content=one_pixel_png,
        )
        result = self.run_cli(
            job="search_answer",
            carrier="screenshot_markup",
            assets=[valid_image, receipt("screen-2", "current_owned_screen_captures")],
            style_binding=binding("search_answer", "screenshot_markup"),
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

        invalid_image = dict(valid_image)
        invalid_image["media_dimensions"] = {"width_px": 2, "height_px": 1}
        result = self.run_cli(
            job="search_answer",
            carrier="screenshot_markup",
            assets=[invalid_image, receipt("screen-2", "current_owned_screen_captures")],
            style_binding=binding("search_answer", "screenshot_markup"),
        )
        self.assertEqual(result.returncode, 2)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "invalid_asset_manifest")
        self.assertIn("dimensions mismatch", payload["message"])

        disguised_image = receipt(
            "screen-1",
            *common,
            asset_path="assets/disguised.txt",
            test_content=one_pixel_png,
        )
        result = self.run_cli(
            job="search_answer",
            carrier="screenshot_markup",
            assets=[
                disguised_image,
                receipt("screen-2", "current_owned_screen_captures"),
            ],
            style_binding=binding("search_answer", "screenshot_markup"),
        )
        self.assertEqual(result.returncode, 2)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "invalid_asset_manifest")
        self.assertIn("media_dimensions", payload["message"])

    def test_single_image_selection_returns_explicit_merge_rule(self) -> None:
        assets = [
            receipt(
                "worksheet",
                "worksheet_preview_id",
                "verified_check_items",
                "decision_or_action_order",
                "source_and_currentness",
            )
        ]
        result = self.run_cli(
            job="search_answer",
            carrier="single_image_reminder",
            assets=assets,
            style_binding=binding("search_answer", "single_image_reminder"),
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        plan = payload["matches"][0]["carrier_role_plan"]
        self.assertEqual(plan["output_shape"], "single_image")
        self.assertTrue(plan["single_image_merge"]["allowed"])
        self.assertTrue(plan["single_image_merge"]["merge_rule"])

    def test_series_modifier_cannot_be_the_only_production_direction(self) -> None:
        assets = [
            receipt(
                "series-evidence",
                "owned_proxy_concept",
                "new_episode_fact_or_observation",
                "explicit_fiction_or_real_source_label",
            )
        ]
        result = self.run_cli(
            job="relationship_build",
            carrier="single_image_reminder",
            assets=assets,
            style_binding=binding("relationship_build", "single_image_reminder"),
        )
        self.assertEqual(result.returncode, 2)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "prototype_gap")
        self.assertEqual(payload["matches"], [])
        self.assertIn("base_direction_card", payload["missing_requirements"])

    def test_video_and_chat_carriers_have_distinct_native_role_plans(self) -> None:
        payload = json.loads(LIBRARY.read_text(encoding="utf-8"))
        by_carrier = {
            carrier: card
            for card in payload["cards"]
            for carrier in card["suitable"]["carriers"]
            if carrier
            in {
                "chat_dramatization",
                "process_video",
                "screen_recording",
                "talking_head_or_field_video",
            }
        }
        self.assertEqual(len(by_carrier), 4)
        self.assertEqual(
            by_carrier["chat_dramatization"]["carrier_role_plans"][
                "chat_dramatization"
            ]["output_shape"],
            "chat_carousel",
        )
        for carrier in (
            "process_video",
            "screen_recording",
            "talking_head_or_field_video",
        ):
            plan = by_carrier[carrier]["carrier_role_plans"][carrier]
            self.assertEqual(plan["output_shape"], "video")
            self.assertFalse(plan["single_image_merge"]["allowed"])


if __name__ == "__main__":
    unittest.main()
