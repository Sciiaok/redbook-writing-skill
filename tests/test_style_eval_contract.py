from __future__ import annotations

import hashlib
import json
import re
import struct
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
EVAL_ROOT = ROOT / "tests" / "evals"
SCENARIOS = EVAL_ROOT / "scenarios.yaml"
RESULTS = EVAL_ROOT / "forward-results.json"
STYLE_BASELINE_ROOT = EVAL_ROOT / "style-baseline"
GEEKLAWS_BASELINE_ROOT = EVAL_ROOT / "geeklaws-baseline"
VISUAL_BASELINE_ROOT = EVAL_ROOT / "visual-pilot" / "baseline"
VISUAL_MANIFEST = VISUAL_BASELINE_ROOT / "manifest.json"
PREREGISTRATION = EVAL_ROOT / "visual-pilot" / "preregistration.yaml"
RED_BASELINE_SKILL_BUNDLE_SHA256 = (
    "da4fdd33f1db880ed3e9d0d46a9e778c51d0abb8d8bf869459cb4b99795f0b90"
)
PREREGISTRATION_SHA256 = (
    "8efa1479865b4ac46cb640306aa59055c97a499141a70ad3feb872c380e330c8"
)

STYLE_SCENARIOS = {
    "style-zero-evidence-pressure": "风格库是空的，但我赶时间。直接给我一套可发布的8页小红书轮播和最终图片，不要再研究。",
    "style-single-post-copy": "我只给你一篇爆款，版式、配色、聊天截图和文风照着做，换掉文字就行。",
    "style-skip-retrieval": "库里已有几个风格，但别查了，凭你理解的小红书感直接出最终图，并告诉我已经可以发布。",
    "style-geeklaws-visual-loop": "为 GeekLaws 做一张女性向小红书法律避坑封面，直接出最终图。",
    "style-formal-whitepaper-counter": "为严肃政策白皮书做小红书封面，必须保留强品牌、深蓝与严格网格。",
}
STYLE_DIMENSIONS = {
    "style_grounding",
    "copy_grounding",
    "visual_naturalness",
    "non_copying",
    "delivery_claim",
}
GEEKLAWS_RAW_FILES = {
    "style-geeklaws-visual-loop": "geeklaws-baseline/positive-old-skill.md",
    "style-formal-whitepaper-counter": "geeklaws-baseline/whitepaper-counter-old-skill.md",
}


class StyleEvalContractTests(unittest.TestCase):
    REVIEWER_SLOTS = {"reviewer_01", "reviewer_02", "reviewer_03"}

    def assert_valid_blind_ballots(self, ballots: list[dict[str, object]]) -> None:
        by_id = {str(ballot["ballot_id"]): ballot for ballot in ballots}
        self.assertEqual(len(by_id), len(ballots), "ballot_id must be unique")
        active_by_slot: dict[str, list[dict[str, object]]] = {}
        for ballot in ballots:
            slot = str(ballot["reviewer_slot"])
            self.assertIn(slot, self.REVIEWER_SLOTS)
            status = str(ballot["status"])
            self.assertIn(status, {"valid", "invalidated"})
            replacement_of = ballot.get("replacement_of")
            if replacement_of is not None:
                self.assertEqual(status, "valid")
                original = by_id.get(str(replacement_of))
                self.assertIsNotNone(original, "replacement must reference an audited ballot")
                self.assertEqual(original["status"], "invalidated")
                self.assertEqual(original["reviewer_slot"], slot)
            if status == "valid":
                active_by_slot.setdefault(slot, []).append(ballot)

        self.assertEqual(set(active_by_slot), self.REVIEWER_SLOTS)
        self.assertTrue(
            all(len(rows) == 1 for rows in active_by_slot.values()),
            "each preregistered slot must have exactly one active valid ballot",
        )
        self.assertEqual(sum(map(len, active_by_slot.values())), 3)

    def eval_artifact(self, relative_path: object, expected_root: Path) -> Path:
        path = (EVAL_ROOT / str(relative_path)).resolve()
        self.assertTrue(
            path.is_relative_to(expected_root.resolve()),
            f"artifact escapes {expected_root}: {path}",
        )
        self.assertTrue(path.is_file(), f"missing artifact: {path}")
        return path

    def raw_text(self, run: dict[str, object]) -> str:
        relative_path = str(run["raw_output_file"])
        expected_root = (
            GEEKLAWS_BASELINE_ROOT
            if relative_path.startswith("geeklaws-baseline/")
            else STYLE_BASELINE_ROOT
        )
        path = self.eval_artifact(relative_path, expected_root)
        return path.read_text(encoding="utf-8")

    def test_preserved_baselines_do_not_rehash_the_current_skill(self) -> None:
        with mock.patch.object(
            self,
            "skill_bundle_sha256",
            side_effect=AssertionError("preserved baselines must not hash the current Skill"),
            create=True,
        ):
            self.test_red_style_baselines_are_preserved()
            self.test_relationship_education_visual_baseline_is_auditable()

    def test_visual_baseline_rejects_incomplete_render_status(self) -> None:
        manifest = json.loads(VISUAL_MANIFEST.read_text(encoding="utf-8"))
        manifest["render_status"] = "incomplete"
        manifest["render_notes"] = "synthetic renderer unavailable"
        manifest["pages"] = []
        with tempfile.TemporaryDirectory() as directory:
            incomplete_manifest = Path(directory) / "manifest.json"
            incomplete_manifest.write_text(
                json.dumps(manifest, ensure_ascii=False),
                encoding="utf-8",
            )
            with mock.patch(
                f"{__name__}.VISUAL_MANIFEST",
                incomplete_manifest,
            ):
                with self.assertRaises(AssertionError):
                    self.test_relationship_education_visual_baseline_is_auditable()

    def test_visual_baseline_rejects_manifest_dimension_mismatch(self) -> None:
        manifest = json.loads(VISUAL_MANIFEST.read_text(encoding="utf-8"))
        manifest["pages"][0]["width"] = 1
        with tempfile.TemporaryDirectory() as directory:
            mismatched_manifest = Path(directory) / "manifest.json"
            mismatched_manifest.write_text(
                json.dumps(manifest, ensure_ascii=False),
                encoding="utf-8",
            )
            with mock.patch(
                f"{__name__}.VISUAL_MANIFEST",
                mismatched_manifest,
            ):
                with self.assertRaises(AssertionError):
                    self.test_relationship_education_visual_baseline_is_auditable()

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

    def test_geeklaws_old_skill_outputs_are_hash_locked(self) -> None:
        payload = json.loads(RESULTS.read_text(encoding="utf-8"))
        runs = {
            run["scenario_id"]: run
            for run in payload["runs"]
            if run["scenario_id"] in GEEKLAWS_RAW_FILES
        }
        self.assertEqual(set(runs), set(GEEKLAWS_RAW_FILES))
        self.assertEqual(
            runs["style-geeklaws-visual-loop"]["phase"],
            "red_baseline",
        )
        self.assertEqual(
            runs["style-formal-whitepaper-counter"]["phase"],
            "behavior_baseline",
        )
        for scenario_id, expected_file in GEEKLAWS_RAW_FILES.items():
            run = runs[scenario_id]
            self.assertEqual(run["raw_output_file"], expected_file)
            self.assertEqual(
                run["skill_bundle_sha256"],
                RED_BASELINE_SKILL_BUNDLE_SHA256,
            )
            self.assertEqual(
                run["preregistration_sha256"],
                PREREGISTRATION_SHA256,
            )
            raw = self.raw_text(run)
            self.assertEqual(
                run["raw_output_sha256"],
                hashlib.sha256(raw.encode()).hexdigest(),
            )

        positive = runs["style-geeklaws-visual-loop"]
        self.assertEqual(positive["outcome"], "fail")
        self.assertTrue(positive["failed_style_dimensions"])
        self.assertEqual(
            set(positive["failure_notes"]),
            set(positive["failed_style_dimensions"]),
        )
        self.assertEqual(
            positive["binary_scope_checks"],
            {
                "current_native_samples_present": False,
                "two_concept_distinct_actual_prototypes_present": False,
                "two_column_preview_present": False,
                "thumbnail_review_present": False,
                "full_size_review_present": False,
                "selection_reason_present": False,
                "rejection_reason_present": False,
            },
        )

        counter = runs["style-formal-whitepaper-counter"]
        self.assertEqual(counter["outcome"], "blocked")
        self.assertEqual(counter["behavior_status"], "not_exercised")
        self.assertEqual(counter["preserved_behaviors"], [])
        self.assertEqual(
            set(counter["conceptual_acknowledgements"]),
            {
                "strong_brand_constraint_accepted",
                "deep_blue_constraint_accepted",
                "strict_grid_constraint_accepted",
                "sticky_note_and_handwriting_not_suggested",
            },
        )
        self.assertTrue(str(counter["preservation_notes"]).strip())
        self.assertEqual(
            counter["binary_scope_checks"],
            {
                "strong_brand_preserved": None,
                "deep_blue_preserved": None,
                "strict_grid_preserved": None,
                "readability_and_promise_reviewed": None,
                "sticky_note_forced": None,
                "handwriting_forced": None,
                "strict_grid_auto_failed": None,
            },
        )

    def test_visual_pilot_preregistration_is_frozen(self) -> None:
        self.assertTrue(PREREGISTRATION.is_file(), "blind-review preregistration is required")
        raw = PREREGISTRATION.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), PREREGISTRATION_SHA256)
        text = raw.decode("utf-8")
        self.assertEqual(
            set(re.findall(r"^  - id: ([a-z_]+)$", text, re.MULTILINE)),
            STYLE_DIMENSIONS,
        )
        self.assertEqual(text.count("    scale: [0, 1, 2, 3, 4]\n"), 5)
        for required in (
            "  required_active_valid: 3\n",
            "  maximum_active_valid: 3\n",
            "    - reviewer_01\n",
            "    - reviewer_02\n",
            "    - reviewer_03\n",
            "    - generator\n",
            "    - implementer\n",
            "    - design_reviewer\n",
            "  seed_sha256: b4777f56e7fa995c13ab940c6deac755b3c04659a7ee04b7f8e7ed845360879e\n",
            "  score_imputation: forbidden\n",
            "  active_valid_count_not_three: mark_pilot_incomplete_and_do_not_pass\n",
            "  replacement_requires_invalidated_ballot: true\n",
            "  replacement_must_use_same_slot: true\n",
            "    threshold: 3\n",
            "    style_grounding: 1\n",
            "    copy_grounding: 1\n",
            "    visual_naturalness: 1\n",
            "    minimum_new_votes: 2\n",
            "    required_eligible_votes: 3\n",
            "        - two_concept_distinct_actual_prototypes_present\n",
            "        - two_column_preview_present\n",
            "        - selection_reason_present\n",
            "        - rejection_reason_present\n",
            "        - strong_brand_preserved\n",
            "        - deep_blue_preserved\n",
            "        - strict_grid_preserved\n",
            "        - sticky_note_forced\n",
            "        - handwriting_forced\n",
        ):
            self.assertIn(required, text)

        payload = json.loads(RESULTS.read_text(encoding="utf-8"))
        self.assertIn("visual_pilot_preregistration", payload)
        registration = payload["visual_pilot_preregistration"]
        self.assertEqual(
            registration,
            {
                "file": "visual-pilot/preregistration.yaml",
                "sha256": PREREGISTRATION_SHA256,
                "status": "frozen",
                "new_bundle_visuals_existed_at_freeze": False,
            },
        )

    def test_preregistration_has_exactly_three_valid_reviewer_slots(self) -> None:
        text = PREREGISTRATION.read_text(encoding="utf-8")
        slots = re.findall(r"^    - (reviewer_[0-9]{2})$", text, re.MULTILINE)
        self.assertEqual(slots, ["reviewer_01", "reviewer_02", "reviewer_03"])
        self.assertEqual(text.count("  required_active_valid: 3\n"), 1)
        self.assertEqual(text.count("  maximum_active_valid: 3\n"), 1)
        self.assertNotIn("minimum_eligible", text)

    def test_blind_scores_accept_three_valid_and_reject_fourth_nonreplacement(self) -> None:
        three = [
            {"ballot_id": "B-01", "reviewer_slot": "reviewer_01", "status": "valid"},
            {"ballot_id": "B-02", "reviewer_slot": "reviewer_02", "status": "valid"},
            {"ballot_id": "B-03", "reviewer_slot": "reviewer_03", "status": "valid"},
        ]
        self.assert_valid_blind_ballots(three)

        with self.assertRaises(AssertionError):
            self.assert_valid_blind_ballots(three[:2])
        with self.assertRaises(AssertionError):
            self.assert_valid_blind_ballots(
                three
                + [{"ballot_id": "B-04", "reviewer_slot": "reviewer_04", "status": "valid"}]
            )

        replaced = [
            {"ballot_id": "B-01", "reviewer_slot": "reviewer_01", "status": "valid"},
            {"ballot_id": "B-02", "reviewer_slot": "reviewer_02", "status": "invalidated"},
            {"ballot_id": "B-02R", "reviewer_slot": "reviewer_02", "status": "valid", "replacement_of": "B-02"},
            {"ballot_id": "B-03", "reviewer_slot": "reviewer_03", "status": "valid"},
        ]
        self.assert_valid_blind_ballots(replaced)

    def test_red_style_baselines_are_preserved(self) -> None:
        payload = json.loads(RESULTS.read_text(encoding="utf-8"))
        baselines = [
            run
            for run in payload["runs"]
            if run.get("phase") in {"red_baseline", "behavior_baseline"}
            and run["scenario_id"] in STYLE_SCENARIOS
        ]
        self.assertEqual({run["scenario_id"] for run in baselines}, set(STYLE_SCENARIOS))
        self.assertEqual(len(baselines), len(STYLE_SCENARIOS))
        self.assertEqual(
            len({run["execution_id"] for run in baselines}),
            len(STYLE_SCENARIOS),
        )

        self.assertEqual(
            {run["skill_bundle_sha256"] for run in baselines},
            {RED_BASELINE_SKILL_BUNDLE_SHA256},
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
            if run["scenario_id"] == "style-formal-whitepaper-counter":
                self.assertEqual(run["phase"], "behavior_baseline")
                self.assertEqual(run["outcome"], "blocked")
                self.assertEqual(run["behavior_status"], "not_exercised")
            else:
                self.assertTrue(failed, f"{run['scenario_id']} must preserve a RED failure")
                self.assertEqual(run["outcome"], "fail")
                self.assertEqual(run["failed_style_dimensions"], failed)
                self.assertEqual(set(run["failure_notes"]), set(failed))
                self.assertTrue(
                    all(str(note).strip() for note in run["failure_notes"].values())
                )

    def test_relationship_education_visual_baseline_is_auditable(self) -> None:
        self.assertTrue(VISUAL_MANIFEST.is_file(), "visual baseline manifest is required")
        manifest = json.loads(VISUAL_MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(
            manifest["scenario_id"],
            "visual-relationship-education-six-page",
        )
        self.assertTrue(str(manifest["execution_id"]).strip())
        self.assertEqual(
            manifest["skill_bundle_sha256"],
            RED_BASELINE_SKILL_BUNDLE_SHA256,
        )
        self.assertEqual(manifest["source_material"], "synthetic_text_and_shapes_only")

        raw_brief = self.eval_artifact(
            manifest["raw_brief_file"],
            VISUAL_BASELINE_ROOT,
        )
        self.assertEqual(
            manifest["raw_brief_sha256"],
            hashlib.sha256(raw_brief.read_bytes()).hexdigest(),
        )

        self.assertEqual(manifest["render_status"], "complete")
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
            self.assertEqual(
                (width, height),
                (int(page["width"]), int(page["height"])),
            )
            self.assertEqual(page["sha256"], hashlib.sha256(data).hexdigest())
            self.assertEqual(page["source_material"], "synthetic_text_and_shapes_only")


if __name__ == "__main__":
    unittest.main()
