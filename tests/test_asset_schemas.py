from __future__ import annotations

import csv
import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "redbook-writing"
VALIDATOR = SKILL / "scripts" / "validate_run.py"


def load_validator_module():
    spec = importlib.util.spec_from_file_location("redbook_validate_run", VALIDATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load validator module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class AssetSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = load_validator_module()

    def test_every_csv_schema_has_a_matching_asset(self) -> None:
        for filename, expected in self.validator.SCHEMAS.items():
            asset = SKILL / "assets" / filename.replace(".csv", "-template.csv")
            self.assertTrue(asset.exists(), f"missing template for {filename}")
            with asset.open("r", encoding="utf-8-sig", newline="") as handle:
                actual = next(csv.reader(handle))
            self.assertEqual(actual, expected, f"header drift in {asset.name}")

    def test_skill_relative_links_resolve(self) -> None:
        skill_text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        import re

        links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", skill_text)
        local_links = [link for link in links if "://" not in link and not link.startswith("#")]
        self.assertTrue(local_links, "SKILL.md should link to progressive-disclosure resources")
        for link in local_links:
            self.assertTrue((SKILL / link).exists(), f"broken local link: {link}")

    def test_openai_default_prompt_mentions_skill(self) -> None:
        text = (SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn("$redbook-writing", text)

    def test_draft_lifecycle_has_no_universal_day_schedule(self) -> None:
        text = (SKILL / "references" / "draft-quality.md").read_text(encoding="utf-8")
        self.assertNotRegex(text, r"\|\s*D\d")
        self.assertIn("可解释事件量", text)

    def test_draft_template_matches_validator_contract(self) -> None:
        import re

        text = (SKILL / "assets" / "draft-template.md").read_text(encoding="utf-8")
        meta = self.validator.parse_frontmatter(text)
        self.assertTrue(self.validator.DRAFT_META.issubset(meta))
        headings = {
            match.group(1).strip()
            for match in re.finditer(r"^##\s+(.+?)\s*$", text, flags=re.MULTILINE)
        }
        self.assertTrue(self.validator.DRAFT_HEADINGS.issubset(headings))
        cta = self.validator.parse_contract_block(
            self.validator.markdown_section(text, "CTA 与披露")
        )
        self.assertTrue(
            {
                "cta_type",
                "cta_copy",
                "commercial_relationship",
                "disclosure_text",
                "disclosure_location",
                "eligibility_ids",
                "platform",
                "account_scope",
                "surfaces",
            }.issubset(cta)
        )


if __name__ == "__main__":
    unittest.main()
