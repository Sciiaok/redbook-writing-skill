from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "redbook-writing" / "scripts" / "select_cover_pattern.py"


class CoverPatternSelectorTests(unittest.TestCase):
    def run_selector(self, *args: str) -> tuple[subprocess.CompletedProcess[str], dict]:
        result = subprocess.run(
            ["python3", str(SCRIPT), *args, "--json"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        payload = json.loads(result.stdout)
        return result, payload

    def test_text_first_without_visual_evidence_prefers_text_card(self) -> None:
        result, payload = self.run_selector(
            "--job", "feed_stop",
            "--carrier", "text_card",
            "--materials", "truthful_serious_premise",
            "--visual-evidence-role", "none",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(payload["status"], "matched")
        self.assertEqual(payload["selected_pattern"]["pattern_id"], "CP01")
        self.assertEqual(payload["claim_ceiling"], "task_fit")

    def test_real_scene_evidence_routes_away_from_text_card(self) -> None:
        result, payload = self.run_selector(
            "--job", "decision_support",
            "--carrier", "comparison_warning",
            "--materials", "owned_or_authorized_before_after",
            "--visual-evidence-role", "primary",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(payload["selected_pattern"]["pattern_id"], "CP05")

    def test_missing_materials_fail_closed(self) -> None:
        result, payload = self.run_selector(
            "--job", "decision_support",
            "--carrier", "comparison_warning",
            "--materials", "truthful_serious_premise",
            "--visual-evidence-role", "primary",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(payload["status"], "needs_materials")
        self.assertIn("owned_or_authorized_before_after", payload["missing_materials"])

    def test_explicit_text_card_is_rejected_when_primary_visual_proof_exists(self) -> None:
        result, payload = self.run_selector(
            "--job", "decision_support",
            "--carrier", "comparison_warning",
            "--materials", "owned_or_authorized_before_after",
            "--visual-evidence-role", "primary",
            "--pattern-id", "CP01",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(payload["status"], "contraindicated")


if __name__ == "__main__":
    unittest.main()
