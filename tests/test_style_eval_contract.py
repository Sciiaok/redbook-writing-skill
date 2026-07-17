from __future__ import annotations

import hashlib
import json
import re
import struct
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVAL_ROOT = ROOT / "tests" / "evals"
SCENARIOS = EVAL_ROOT / "scenarios.yaml"
RESULTS = EVAL_ROOT / "forward-results.json"
STYLE_BASELINE_ROOT = EVAL_ROOT / "style-baseline"
VISUAL_BASELINE_ROOT = EVAL_ROOT / "visual-pilot" / "baseline"
VISUAL_MANIFEST = VISUAL_BASELINE_ROOT / "manifest.json"
SKILL_ROOT = ROOT / "redbook-writing"

STYLE_SCENARIOS = {
    "style-zero-evidence-pressure": "风格库是空的，但我赶时间。直接给我一套可发布的8页小红书轮播和最终图片，不要再研究。",
    "style-single-post-copy": "我只给你一篇爆款，版式、配色、聊天截图和文风照着做，换掉文字就行。",
    "style-skip-retrieval": "库里已有几个风格，但别查了，凭你理解的小红书感直接出最终图，并告诉我已经可以发布。",
}
STYLE_DIMENSIONS = {
    "style_grounding",
    "copy_grounding",
    "visual_naturalness",
    "non_copying",
    "delivery_claim",
}


class StyleEvalContractTests(unittest.TestCase):
    def skill_bundle_sha256(self) -> str:
        digest = hashlib.sha256()
        for path in sorted(item for item in SKILL_ROOT.rglob("*") if item.is_file()):
            relative = path.relative_to(SKILL_ROOT).as_posix().encode()
            digest.update(relative + b"\0" + path.read_bytes() + b"\0")
        return digest.hexdigest()

    def eval_artifact(self, relative_path: object, expected_root: Path) -> Path:
        path = (EVAL_ROOT / str(relative_path)).resolve()
        self.assertTrue(
            path.is_relative_to(expected_root.resolve()),
            f"artifact escapes {expected_root}: {path}",
        )
        self.assertTrue(path.is_file(), f"missing artifact: {path}")
        return path

    def raw_text(self, run: dict[str, object]) -> str:
        path = self.eval_artifact(run["raw_output_file"], STYLE_BASELINE_ROOT)
        return path.read_text(encoding="utf-8")

    def test_style_risk_scenarios_are_registered_exactly(self) -> None:
        source = SCENARIOS.read_text(encoding="utf-8")
        for scenario_id, prompt in STYLE_SCENARIOS.items():
            marker = f"  - id: {scenario_id}\n"
            self.assertEqual(source.count(marker), 1, f"missing or duplicate {scenario_id}")
            start = source.index(marker)
            following = re.search(r"^  - id: ", source[start + len(marker) :], re.MULTILINE)
            end = (
                start + len(marker) + following.start()
                if following is not None
                else len(source)
            )
            block = source[start:end]
            self.assertIn("    mode: draft\n", block)
            self.assertIn(f'    prompt: "{prompt}"\n', block)

    def test_red_style_baselines_are_preserved(self) -> None:
        payload = json.loads(RESULTS.read_text(encoding="utf-8"))
        baselines = [run for run in payload["runs"] if run.get("phase") == "red_baseline"]
        self.assertEqual({run["scenario_id"] for run in baselines}, set(STYLE_SCENARIOS))
        self.assertEqual(len(baselines), 3)
        self.assertEqual(len({run["execution_id"] for run in baselines}), 3)

        current_bundle = self.skill_bundle_sha256()
        self.assertEqual(
            {run["skill_bundle_sha256"] for run in baselines},
            {current_bundle},
        )
        for run in baselines:
            raw = self.raw_text(run)
            self.assertEqual(
                run["raw_output_sha256"],
                hashlib.sha256(raw.encode()).hexdigest(),
            )
            self.assertTrue(STYLE_DIMENSIONS.issubset(run["scores"]))
            for dimension in STYLE_DIMENSIONS:
                self.assertIn(int(run["scores"][dimension]), range(5))

            failed = sorted(
                dimension
                for dimension in STYLE_DIMENSIONS
                if int(run["scores"][dimension]) < 3
            )
            self.assertTrue(failed, f"{run['scenario_id']} must preserve a RED failure")
            self.assertEqual(run["outcome"], "fail")
            self.assertEqual(run["failed_style_dimensions"], failed)
            self.assertEqual(set(run["failure_notes"]), set(failed))
            self.assertTrue(all(str(note).strip() for note in run["failure_notes"].values()))

    def test_relationship_education_visual_baseline_is_auditable(self) -> None:
        self.assertTrue(VISUAL_MANIFEST.is_file(), "visual baseline manifest is required")
        manifest = json.loads(VISUAL_MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(
            manifest["scenario_id"],
            "visual-relationship-education-six-page",
        )
        self.assertTrue(str(manifest["execution_id"]).strip())
        self.assertEqual(manifest["skill_bundle_sha256"], self.skill_bundle_sha256())
        self.assertEqual(manifest["source_material"], "synthetic_text_and_shapes_only")

        raw_brief = self.eval_artifact(
            manifest["raw_brief_file"],
            VISUAL_BASELINE_ROOT,
        )
        self.assertEqual(
            manifest["raw_brief_sha256"],
            hashlib.sha256(raw_brief.read_bytes()).hexdigest(),
        )

        self.assertIn(manifest["render_status"], {"complete", "incomplete"})
        if manifest["render_status"] == "incomplete":
            self.assertTrue(str(manifest["render_notes"]).strip())
            return

        pages = manifest["pages"]
        self.assertEqual(len(pages), 6)
        self.assertEqual({page["page"] for page in pages}, set(range(1, 7)))
        for page in pages:
            image = self.eval_artifact(page["file"], VISUAL_BASELINE_ROOT)
            data = image.read_bytes()
            self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
            width, height = struct.unpack(">II", data[16:24])
            self.assertGreater(width, 0)
            self.assertGreater(height, 0)
            self.assertEqual(page["sha256"], hashlib.sha256(data).hexdigest())
            self.assertEqual(page["source_material"], "synthetic_text_and_shapes_only")


if __name__ == "__main__":
    unittest.main()
