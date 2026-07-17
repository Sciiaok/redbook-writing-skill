from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "redbook-writing" / "scripts" / "select_traffic_mechanisms.py"


class SelectTrafficMechanismsTests(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(SCRIPT), *args, "--json"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_exact_job_stage_and_carrier_returns_actionable_cards(self) -> None:
        result = self.run_cli(
            "--stage",
            "save_share",
            "--job",
            "decision_support",
            "--carrier",
            "comparison_warning",
            "--materials",
            (
                "comparison_candidates,uniform_protocol,proof_inventory,"
                "first_party_metrics,comment_semantics"
            ),
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "matched")
        self.assertEqual(len(payload["matches"]), 3)
        self.assertEqual(
            {match["selection_slot"] for match in payload["matches"]},
            {"content", "carrier_or_truth", "learning_or_governance"},
        )
        self.assertEqual(
            sum(match["mechanism_kind"] == "content" for match in payload["matches"]),
            1,
        )
        for match in payload["matches"]:
            self.assertIn("decision_support", match["primary_jobs"])
            self.assertIn(
                "comparison_warning",
                match["carrier_task_fit"]["preferred"]
                + match["carrier_task_fit"]["compatible"],
            )
            self.assertTrue(match["actions"]["title"])
            self.assertTrue(match["failure_conditions"])
            self.assertTrue(match["source_refs"])
            self.assertIn("activation", match)
            self.assertIn("priority", match)

    def test_library_cards_have_machine_contract_and_atomic_references(self) -> None:
        library = json.loads(
            (ROOT / "redbook-writing" / "assets" / "traffic-mechanisms-v1.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(len(library["mechanisms"]), 17)
        allowed_kinds = {
            "content",
            "carrier_router",
            "truth_gate",
            "feedback",
            "measurement",
            "governance",
        }
        required_fields = {
            "mechanism_kind",
            "required_material_codes",
            "forbidden_material_codes",
            "requires",
            "conflicts_with",
            "activation",
            "priority",
        }
        for card in library["mechanisms"]:
            self.assertTrue(required_fields.issubset(card), card["mechanism_id"])
            self.assertIn(card["mechanism_kind"], allowed_kinds)
            self.assertIsInstance(card["priority"], int)
            self.assertTrue(card["source_refs"])
            for ref in card["source_refs"]:
                self.assertNotRegex(ref["ref"].split(":", 1)[-1], r"/")
                self.assertTrue(ref["evidence_layer"])
                self.assertTrue(ref["scope"])
                self.assertTrue(ref["limitation"])

    def test_missing_materials_returns_explicit_gaps_not_generic_cards(self) -> None:
        result = self.run_cli(
            "--stage",
            "save_share",
            "--job",
            "decision_support",
            "--carrier",
            "comparison_warning",
        )
        self.assertEqual(result.returncode, 2)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "needs_materials")
        self.assertEqual(payload["matches"], [])
        self.assertIn("comparison_candidates", payload["missing_material_codes"])

    def test_forbidden_material_blocks_matching_card(self) -> None:
        result = self.run_cli(
            "--stage",
            "feed_stop",
            "--job",
            "feed_stop",
            "--carrier",
            "real_photo_diary",
            "--materials",
            (
                "promise,real_proof,source_ledger,version_log,rights_clearance,"
                "fabricated_evidence"
            ),
        )
        self.assertEqual(result.returncode, 2)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "needs_materials")
        self.assertIn("fabricated_evidence", payload["forbidden_material_codes"])

    def test_entry_and_fulfillment_are_not_selected_as_two_content_cards(self) -> None:
        result = self.run_cli(
            "--stage",
            "feed_stop",
            "--job",
            "feed_stop",
            "--carrier",
            "real_photo_diary",
            "--materials",
            (
                "promise,real_proof,proof_inventory,source_ledger,version_log,"
                "rights_clearance"
            ),
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        selected = {item["mechanism_id"]: item for item in payload["matches"]}
        self.assertEqual(selected["TM01"]["selection_slot"], "content")
        self.assertEqual(selected["TM02"]["mechanism_kind"], "truth_gate")
        self.assertEqual(selected["TM02"]["selection_slot"], "carrier_or_truth")
        self.assertEqual(
            sum(item["selection_slot"] == "content" for item in payload["matches"]),
            1,
        )

    def test_governance_cards_do_not_fan_out_without_required_materials(self) -> None:
        result = self.run_cli(
            "--stage",
            "read_through",
            "--job",
            "explain",
            "--carrier",
            "screenshot_markup",
            "--materials",
            "promise,real_proof,proof_inventory,source_ledger,version_log,rights_clearance",
            "--limit",
            "10",
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        governance = [
            item
            for item in payload["matches"]
            if item["mechanism_kind"] in {"feedback", "measurement", "governance"}
        ]
        self.assertEqual(len(governance), 1)

    def test_conflicts_with_replaces_the_lower_slot_candidate(self) -> None:
        library_path = (
            ROOT / "redbook-writing" / "assets" / "traffic-mechanisms-v1.json"
        )
        library = json.loads(library_path.read_text(encoding="utf-8"))
        cards = {item["mechanism_id"]: item for item in library["mechanisms"]}
        cards["TM01"]["conflicts_with"] = ["TM02"]
        cards["TM02"]["conflicts_with"] = ["TM01"]
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_library = Path(temporary_directory) / "library.json"
            temporary_library.write_text(
                json.dumps(library, ensure_ascii=False), encoding="utf-8"
            )
            result = self.run_cli(
                "--stage",
                "feed_stop",
                "--job",
                "feed_stop",
                "--carrier",
                "real_photo_diary",
                "--materials",
                (
                    "promise,real_proof,proof_inventory,source_ledger,version_log,"
                    "rights_clearance"
                ),
                "--library",
                str(temporary_library),
            )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        selected = {item["mechanism_id"] for item in payload["matches"]}
        self.assertIn("TM01", selected)
        self.assertIn("TM08", selected)
        self.assertNotIn("TM02", selected)

    def test_requires_replaces_generic_measurement_with_required_governance(self) -> None:
        result = self.run_cli(
            "--stage",
            "read_through",
            "--job",
            "explain",
            "--carrier",
            "text_card",
            "--materials",
            (
                "problem_evidence,category_facts,ai_draft,human_review,"
                "first_party_metrics,comment_semantics,source_ledger,version_log,"
                "rights_clearance"
            ),
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        selected = {item["mechanism_id"] for item in payload["matches"]}
        self.assertEqual(selected, {"TM12", "TM16", "TM17"})

    def test_chat_carrier_requires_truth_material(self) -> None:
        common = (
            "--stage",
            "read_through",
            "--job",
            "relationship_build",
            "--carrier",
            "chat_dramatization",
            "--materials",
            (
                "promise,real_proof,authorized_experience,actionable_method,"
                "source_ledger,version_log,rights_clearance"
            ),
        )
        blocked = self.run_cli(*common)
        self.assertEqual(blocked.returncode, 2)
        blocked_payload = json.loads(blocked.stdout)
        self.assertEqual(blocked_payload["status"], "needs_materials")
        self.assertIn(
            "authorized_chat_original_or_fiction_disclosure",
            blocked_payload["missing_material_codes"],
        )

        allowed = self.run_cli(
            *common,
            "--material",
            "fiction_disclosure",
        )
        self.assertEqual(allowed.returncode, 0, allowed.stdout + allowed.stderr)
        payload = json.loads(allowed.stdout)
        self.assertEqual(payload["query"]["carrier"], "chat_dramatization")

    def test_video_carriers_are_supported(self) -> None:
        carrier_materials = {
            "process_video": "real_process_video,rights_clearance",
            "screen_recording": "current_interface_capture,privacy_redaction",
            "talking_head_or_field_video": (
                "real_person_authorized,spoken_claim_sources,rights_clearance"
            ),
        }
        for carrier, truth_materials in carrier_materials.items():
            with self.subTest(carrier=carrier):
                result = self.run_cli(
                    "--stage",
                    "read_through",
                    "--job",
                    "explain",
                    "--carrier",
                    carrier,
                    "--materials",
                    (
                        "promise,real_proof,proof_inventory,source_ledger,version_log,"
                        "rights_clearance,"
                        + truth_materials
                    ),
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                payload = json.loads(result.stdout)
                self.assertTrue(
                    any(item["mechanism_id"] == "TM08" for item in payload["matches"])
                )

    def test_ox06_is_title_subrecipe_and_tm10_tension_is_optional(self) -> None:
        library = json.loads(
            (ROOT / "redbook-writing" / "assets" / "traffic-mechanisms-v1.json").read_text(
                encoding="utf-8"
            )
        )
        cards = {card["mechanism_id"]: card for card in library["mechanisms"]}
        self.assertIn("official-xhs-merchant-course:OX06", cards["TM01"]["subrecipe_refs"])
        self.assertIn("可选", cards["TM10"]["one_line_formula"])
        self.assertNotIn("张力", cards["TM10"]["required_material_codes"])

    def test_official_course_7d_is_historical_example_not_default(self) -> None:
        base = ROOT / "docs" / "research" / "2026-07-18-official-xhs-merchant-course-notes"
        payload = json.loads(base.with_suffix(".json").read_text(encoding="utf-8"))
        ox09 = next(item for item in payload["mechanisms"] if item["id"] == "OX09")
        self.assertEqual(
            ox09["historical_course_examples"][0]["status"],
            "historical_course_example",
        )
        self.assertIsNone(ox09["default_observation_window"])
        markdown = base.with_suffix(".md").read_text(encoding="utf-8")
        self.assertIn("Skill 不设置 7 天默认窗口", markdown)
        self.assertNotIn("default 7d", markdown)

    def test_unknown_carrier_is_rejected(self) -> None:
        result = self.run_cli(
            "--stage",
            "feed_stop",
            "--job",
            "feed_stop",
            "--carrier",
            "carrier_that_does_not_exist",
        )
        self.assertEqual(result.returncode, 2)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "invalid_query")
        self.assertEqual(payload["matches"], [])

    def test_invalid_enum_is_rejected(self) -> None:
        result = self.run_cli("--stage", "viral_magic", "--job", "feed_stop")
        self.assertNotEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "invalid_query")


if __name__ == "__main__":
    unittest.main()
