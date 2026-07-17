from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LIBRARY = ROOT / "redbook-writing" / "assets" / "visual-direction-cards-v1.json"
SCRIPT = ROOT / "redbook-writing" / "scripts" / "select_visual_directions.py"


def receipt(
    asset_id: str,
    *material_codes: str,
    expires_at: str | None = None,
) -> dict[str, object]:
    return {
        "asset_id": asset_id,
        "material_codes": list(material_codes),
        "sha256": hashlib.sha256(asset_id.encode()).hexdigest(),
        "rights_basis": "owned",
        "authorization_ref": None,
        "license_ref": None,
        "transform_history": [],
        "privacy_review": "not_applicable",
        "commercial_disclosure": "not_applicable",
        "expires_at": expires_at,
    }


def binding(job: str, carrier: str) -> dict[str, object]:
    return {
        "binding_id": "DSB-TEST-001",
        "status": "published",
        "primary_job": job,
        "carrier": carrier,
        "snapshot_id": "SNAP-TEST-001",
        "style_rule_ids": ["RULE-TEST-001"],
        "aesthetic_contract": {
            "palette": "from published binding",
            "typography": "from published binding",
            "image_treatment": "from published binding",
            "density": "from published binding",
            "annotation_language": "from published binding",
            "crop_logic": "from published binding",
        },
    }


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
    ) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as temporary_directory:
            args = [
                "python3",
                str(SCRIPT),
                "--job",
                job,
                "--carrier",
                carrier,
                "--mode",
                mode,
                "--json",
            ]
            if assets is not None:
                manifest = Path(temporary_directory) / "assets.json"
                manifest.write_text(
                    json.dumps({"asset_manifest_refs": assets}, ensure_ascii=False),
                    encoding="utf-8",
                )
                args.extend(["--asset-manifest", str(manifest)])
            if style_binding is not None:
                style = Path(temporary_directory) / "style-binding.json"
                style.write_text(
                    json.dumps(style_binding, ensure_ascii=False), encoding="utf-8"
                )
                args.extend(["--style-binding", str(style)])
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
                self.assertTrue(required_proofs.issubset(variables), required_proofs - variables.keys())
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
                "material_codes",
                "sha256",
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
            },
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
