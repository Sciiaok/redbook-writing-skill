from __future__ import annotations

import csv
import importlib.util
import re
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "redbook-writing"
VALIDATOR = SKILL / "scripts" / "validate_run.py"

STYLE_SAMPLES_HEADER = [
    "style_sample_id",
    "post_id",
    "query_ids",
    "performance_tier",
    "carrier",
    "primary_job_scope",
    "slide_count_visible",
    "visible_slide_indexes",
    "slide_count_captured",
    "captured_slide_indexes",
    "visual_observation_ids",
    "copy_observation_ids",
    "archetype_ids",
    "evidence_role",
    "capture_status",
    "limitations",
]

VISUAL_PROTOTYPES_HEADER = [
    "prototype_asset_id",
    "draft_id",
    "visual_brief_id",
    "concept_id",
    "attention_path",
    "prototype_prompt_sha256",
    "asset_path",
    "asset_sha256",
    "width",
    "height",
    "render_method",
    "binding_rule_bundle_sha256",
    "style_rule_refs",
    "starter_prompt_id",
    "starter_prompt_sha256",
    "feed_preview_path",
    "feed_preview_sha256",
    "feed_review_status",
    "full_review_status",
    "selection_status",
    "selection_reason",
    "revision_of",
    "notes",
]

DRAFT_ASSETS_HEADER = [
    "draft_asset_id",
    "draft_id",
    "draft_binding_id",
    "slide_index",
    "asset_path",
    "asset_sha256",
    "width",
    "height",
    "render_method",
    "binding_rule_bundle_sha256",
    "style_rule_refs",
    "starter_prompt_sha256",
    "review_status",
    "revision_of",
    "notes",
]


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

    def test_openai_metadata_promises_reviewable_style_work_not_traffic(self) -> None:
        text = (SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn("逐页风格", text)
        self.assertIn("视觉 Brief", text)
        self.assertNotRegex(text, r"爆款|保证流量|流量增长")

    def test_draft_lifecycle_has_no_universal_day_schedule(self) -> None:
        text = (SKILL / "references" / "draft-quality.md").read_text(encoding="utf-8")
        self.assertNotRegex(text, r"\|\s*D\d")
        self.assertIn("可解释事件量", text)

    def test_draft_template_matches_validator_contract(self) -> None:
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

    def test_v2_references_freeze_primary_job_and_evidence_boundaries(self) -> None:
        research = (SKILL / "references" / "research-method.md").read_text(
            encoding="utf-8"
        )
        draft = (SKILL / "references" / "draft-quality.md").read_text(
            encoding="utf-8"
        )
        schemas = (SKILL / "references" / "schemas.md").read_text(encoding="utf-8")

        v2_primary_jobs = {
            "feed_stop",
            "search_answer",
            "explain",
            "trust_build",
            "decision_support",
            "relationship_build",
            "conversion",
            "authority_statement",
        }
        for job in v2_primary_jobs:
            self.assertIn(job, draft)
            self.assertIn(job, schemas)

        for legacy_job in {
            "recommendation_reach",
            "search_capture",
            "relationship_building",
            "commercial_conversion",
        }:
            self.assertIn(legacy_job, schemas)
        self.assertIn("legacy v1", schemas)

        for anchor in {
            "style-samples.csv",
            "style-records.jsonl",
            "visible_slide_indexes",
            "captured_slide_indexes",
            "claim_kind",
            "performance_evidence_scope",
            "public_proxy ≠ traffic",
        }:
            self.assertIn(anchor, research + schemas)

        for scope in {
            "not_performance_evidence",
            "public_proxy_association",
            "first_party_traffic_validated",
        }:
            self.assertIn(scope, schemas)

    def test_default_positioning_is_cross_category_traffic_funnel(self) -> None:
        research = (SKILL / "references" / "research-method.md").read_text(
            encoding="utf-8"
        )
        draft = (SKILL / "references" / "draft-quality.md").read_text(
            encoding="utf-8"
        )
        schemas = (SKILL / "references" / "schemas.md").read_text(encoding="utf-8")
        metadata = (SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8")

        for text in (research, draft, schemas):
            self.assertIn("跨类目", text)
            self.assertIn("候选流量密码库", text)
        for stage in {
            "feed_stop",
            "read_through",
            "save_share",
            "comment_cocreation",
            "profile_follow",
        }:
            self.assertIn(stage, draft)
            self.assertIn(stage, schemas)
        self.assertIn("任意类目", metadata)
        self.assertIn("成人模块仅在", draft)

    def test_draft_reference_stops_on_missing_style_and_requires_visual_loop(self) -> None:
        text = (SKILL / "references" / "draft-quality.md").read_text(
            encoding="utf-8"
        )
        self.assertRegex(
            text,
            r"(?s)needs_style_research.{0,500}停止 ready 生产",
        )
        self.assertRegex(
            text,
            r"(?s)candidate_only.{0,300}task-fit.{0,300}(?:反例|anti-pattern)",
        )
        self.assertIn("qualified_cells=0", text)
        self.assertRegex(text, r"qualified_cells=0.{0,200}starter_applied")
        for anchor in {
            "visual-briefs.jsonl",
            "visual-prototypes.csv",
            "prototype_count >= 2",
            "feed_preview",
            "full_size",
            "adult_sensitive_commercial_gate",
            "production-gate-receipts.jsonl",
            "deferred/incomplete",
        }:
            self.assertIn(anchor, text)
        self.assertNotRegex(text, r"3\s*人盲评已完成|12\s*帖(?:实验)?已完成")

    def test_private_style_library_is_ignored(self) -> None:
        lines = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        self.assertIn("**/_style_library/", lines)

    def test_v2_style_templates_exist_without_fabricated_rows(self) -> None:
        csv_contracts = {
            "style-samples-template.csv": STYLE_SAMPLES_HEADER,
            "visual-prototypes-template.csv": VISUAL_PROTOTYPES_HEADER,
            "draft-assets-template.csv": DRAFT_ASSETS_HEADER,
        }
        for filename, expected in csv_contracts.items():
            path = SKILL / "assets" / filename
            self.assertTrue(path.exists(), f"missing v2 style template: {filename}")
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.reader(handle))
            self.assertEqual(rows, [expected], f"template must be header-only: {filename}")

        for filename in {
            "style-records-template.jsonl",
            "visual-briefs-template.jsonl",
            "visual-feedback-template.jsonl",
        }:
            path = SKILL / "assets" / filename
            self.assertTrue(path.exists(), f"missing v2 style template: {filename}")
            self.assertEqual(
                path.read_text(encoding="utf-8").strip(),
                "",
                f"template must not fabricate evidence: {filename}",
            )


if __name__ == "__main__":
    unittest.main()
