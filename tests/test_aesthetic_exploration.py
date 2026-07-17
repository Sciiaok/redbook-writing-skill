from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "redbook-writing" / "scripts" / "select_aesthetic_exploration.py"
ASSET = ROOT / "redbook-writing" / "assets" / "aesthetic-exploration-prompts-v1.json"


class AestheticExplorationTests(unittest.TestCase):
    def run_selector(self, *args: str) -> tuple[subprocess.CompletedProcess[str], dict]:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        return result, json.loads(result.stdout)

    def ap03_args(self) -> list[str]:
        return [
            "--category-code", "lived_experience_opinion",
            "--primary-job", "relationship_build",
            "--carrier", "real_photo_diary",
            "--direction-card-id", "VDC12",
            "--materials", "owned_or_authorized_lived_scene,real_problem_or_desire,actionable_method_or_decision",
            "--constraints", "no_generated_evidence,experience_provenance_recorded,commercial_disclosure_complete",
            "--rights-provenance-status", "passed",
            "--prompt-id", "AP03",
        ]

    def test_exact_scope_can_emit_only_prototype_exploration(self) -> None:
        result, payload = self.run_selector(*self.ap03_args())
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(payload["status"], "matched_exploration")
        self.assertEqual(payload["output_state"], "prototype_only")
        self.assertEqual(payload["performance_evidence_scope"], "not_performance_evidence")
        self.assertEqual(payload["cell_id"], "AP03-LIVED-RELATIONSHIP-DIARY")
        self.assertTrue(payload["source_snapshot_hashes"])
        self.assertTrue(payload["counterexample_refs"])

    def test_scope_arrays_cannot_cross_product_into_a_fake_match(self) -> None:
        result, payload = self.run_selector(
            "--category-code", "software_tutorial",
            "--primary-job", "decision_support",
            "--carrier", "comparison_warning",
            "--direction-card-id", "VDC04",
            "--rights-provenance-status", "passed",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(payload["status"], "no_exact_scope_cell")

    def test_research_lead_cannot_render_a_prototype(self) -> None:
        result, payload = self.run_selector(
            "--category-code", "beauty_texture",
            "--primary-job", "decision_support",
            "--carrier", "photo_annotation",
            "--direction-card-id", "VDC04",
            "--rights-provenance-status", "passed",
            "--prompt-id", "AP02",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(payload["status"], "research_lead_only")
        self.assertEqual(payload["output_state"], "brief_only")

    def test_published_binding_disables_candidate_overlay(self) -> None:
        result, payload = self.run_selector(
            *self.ap03_args(), "--published-binding-status", "published"
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(payload["status"], "binding_controls_aesthetics")

    def test_two_holistic_rejections_require_real_reset(self) -> None:
        result, payload = self.run_selector(
            *self.ap03_args(),
            "--holistic-rejections", "2",
            "--reset-changes", "prompt_module",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(payload["status"], "reset_required_after_two_rejections")

    def test_prompt_tampering_fails_closed(self) -> None:
        payload = json.loads(ASSET.read_text(encoding="utf-8"))
        payload["prompts"][0]["prompt_template"] += " tampered"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "asset.json"
            path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            result, output = self.run_selector(*self.ap03_args(), "--asset", str(path))
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(output["status"], "stale_or_tampered_evidence")
        self.assertIn("prompt hash mismatch", output["reason"])


if __name__ == "__main__":
    unittest.main()
