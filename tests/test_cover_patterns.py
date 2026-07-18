from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "redbook-writing" / "assets" / "cover-patterns-v1.json"
VISUAL_DIRECTIONS = ROOT / "redbook-writing" / "assets" / "visual-direction-cards-v1.json"


class CoverPatternAssetTests(unittest.TestCase):
    def load_asset(self) -> dict:
        return json.loads(ASSET.read_text(encoding="utf-8"))

    def test_asset_has_cross_category_machine_contract(self) -> None:
        payload = self.load_asset()
        self.assertEqual(payload["schema_version"], "1.0.0")
        self.assertEqual(payload["claim_ceiling"], "task_fit")
        self.assertEqual(payload["output_state_ceiling"], "prototype_only")
        self.assertGreaterEqual(len(payload["patterns"]), 13)
        ids = [pattern["pattern_id"] for pattern in payload["patterns"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_text_card_is_prioritized_only_for_text_first_jobs(self) -> None:
        payload = self.load_asset()
        text_card = next(p for p in payload["patterns"] if p["pattern_id"] == "CP01")
        self.assertEqual(text_card["family"], "text_dominant_native_card")
        self.assertTrue(text_card["priority_policy"]["default_when"])
        self.assertIn("real_scene_is_primary_evidence", text_card["contraindications"])
        self.assertEqual(text_card["claim_ceiling"], "task_fit")
        self.assertTrue(text_card["evidence_refs"])

    def test_all_patterns_have_positive_and_counterexample_contracts(self) -> None:
        payload = self.load_asset()
        required = {
            "pattern_id", "name", "family", "jobs", "carriers",
            "priority_policy", "required_materials_any", "contraindications",
            "design_contract", "counterexample", "evidence_refs", "claim_ceiling",
        }
        for pattern in payload["patterns"]:
            self.assertFalse(required - set(pattern), pattern["pattern_id"])
            self.assertTrue(pattern["jobs"])
            self.assertTrue(pattern["carriers"])
            self.assertTrue(pattern["design_contract"]["first_screen_job"])
            self.assertTrue(pattern["counterexample"])
            self.assertEqual(pattern["claim_ceiling"], "task_fit")

    def test_local_high_and_low_text_cards_do_not_become_performance_rules(self) -> None:
        payload = self.load_asset()
        raw = json.dumps(payload, ensure_ascii=False)
        self.assertIn("LOCAL-COVER-001", raw)
        self.assertIn("LOCAL-COVER-004", raw)
        self.assertNotIn("performance_rule", raw)
        self.assertNotIn("guaranteed", raw)

    def test_cover_carriers_are_compatible_with_visual_direction_taxonomy(self) -> None:
        payload = self.load_asset()
        visual = json.loads(VISUAL_DIRECTIONS.read_text(encoding="utf-8"))
        allowed = set(visual["carrier_taxonomy"])
        used = {carrier for pattern in payload["patterns"] for carrier in pattern["carriers"]}
        self.assertFalse(used - allowed, f"cover-only carrier aliases drifted: {sorted(used - allowed)}")

    def test_every_existing_visual_carrier_has_a_cover_route(self) -> None:
        payload = self.load_asset()
        visual = json.loads(VISUAL_DIRECTIONS.read_text(encoding="utf-8"))
        expected = set(visual["carrier_taxonomy"])
        used = {carrier for pattern in payload["patterns"] for carrier in pattern["carriers"]}
        self.assertEqual(used, expected)

    def test_cover_materials_are_compatible_with_visual_direction_taxonomy(self) -> None:
        payload = self.load_asset()
        visual = json.loads(VISUAL_DIRECTIONS.read_text(encoding="utf-8"))

        allowed: set[str] = set()

        def collect_material_codes(value: object) -> None:
            if isinstance(value, dict):
                code = value.get("material_code")
                if isinstance(code, str):
                    allowed.add(code)
                for child in value.values():
                    collect_material_codes(child)
            elif isinstance(value, list):
                for child in value:
                    collect_material_codes(child)

        collect_material_codes(visual)
        used = {
            material
            for pattern in payload["patterns"]
            for option in pattern["required_materials_any"]
            for material in option
        }
        self.assertFalse(used - allowed, f"cover-only material aliases drifted: {sorted(used - allowed)}")


if __name__ == "__main__":
    unittest.main()
