from __future__ import annotations

import json
import subprocess
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
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "matched")
        self.assertGreaterEqual(len(payload["matches"]), 2)
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
