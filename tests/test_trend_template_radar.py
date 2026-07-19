from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "redbook-writing"
VALIDATOR = SKILL / "scripts" / "validate_run.py"

SAMPLE_HEADER = [
    "template_sample_id",
    "template_id",
    "family_id",
    "post_id",
    "note_id",
    "url",
    "account_id",
    "query_ids",
    "parent_query_id",
    "query_round",
    "search_surface",
    "sort_or_filter",
    "rank_observed",
    "published_at",
    "date_confidence",
    "collected_at",
    "carrier",
    "primary_job",
    "template_type",
    "remix_relation",
    "creative_family_id",
    "lineage_cluster_id",
    "supply_origin",
    "hook_observation",
    "shot_grammar_observation",
    "edit_grammar_observation",
    "participation_signal",
    "visible_engagement",
    "account_baseline_multiple",
    "performance_tier",
    "evidence_role",
    "duplicate_of",
    "category_scope",
    "comment_evidence_ids",
    "source_ids",
    "access_status",
    "source_snapshot_sha256",
    "capture_status",
    "limitations",
]

CARD_FIELDS = {
    "record_type",
    "schema_version",
    "candidate_record_id",
    "run_id",
    "candidate_version",
    "supersedes_candidate_record_id",
    "template_id",
    "family_id",
    "canonical_name",
    "aliases",
    "template_types",
    "discovery_queries",
    "discovery_lanes",
    "source_sample_ids",
    "support_sample_ids",
    "counterexample_sample_ids",
    "boundary_sample_ids",
    "independent_account_count",
    "category_scopes",
    "carrier_scopes",
    "primary_job_scopes",
    "traffic_stage_scopes",
    "supply_origin",
    "supply_origin_evidence_ids",
    "first_seen_at",
    "last_seen_at",
    "sample_window",
    "window_comparisons",
    "hook_grammar",
    "shot_grammar",
    "edit_grammar",
    "participation_loop",
    "slot_map",
    "required_material_codes",
    "optional_material_codes",
    "contraindications",
    "rights_status",
    "safety_status",
    "authorized_asset_ids",
    "source_asset_hashes",
    "replication_status",
    "lifecycle_phase",
    "lifecycle_reason",
    "confidence",
    "evidence_level",
    "performance_evidence_scope",
    "decision",
    "adaptation_notes",
    "last_refreshed_at",
    "limitations",
    "record_sha256",
}


def load_validator_module():
    spec = importlib.util.spec_from_file_location("trend_validator", VALIDATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load validator module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def record_hash(row: dict[str, object]) -> str:
    payload = dict(row)
    payload.pop("record_sha256", None)
    return hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def sample(
    sample_id: str,
    role: str,
    account_id: str,
    lineage: str,
    remix_relation: str,
    *,
    published_at: str = "2026-07-10",
) -> dict[str, str]:
    row = {field: "value" for field in SAMPLE_HEADER}
    row.update(
        {
            "template_sample_id": sample_id,
            "template_id": "TT-001",
            "family_id": "TTF-001",
            "post_id": f"POST-{sample_id}",
            "note_id": f"note-{sample_id}",
            "url": f"https://example.com/{sample_id}",
            "account_id": account_id,
            "query_ids": "Q-001",
            "parent_query_id": "Q-ROOT",
            "query_round": "2",
            "search_surface": "notes",
            "sort_or_filter": "latest",
            "rank_observed": "1",
            "published_at": published_at,
            "date_confidence": "high",
            "collected_at": "2026-07-19",
            "carrier": "short_video",
            "primary_job": "feed_stop",
            "template_type": "challenge",
            "remix_relation": remix_relation,
            "creative_family_id": f"CF-{lineage}",
            "lineage_cluster_id": lineage,
            "supply_origin": "spontaneous",
            "hook_observation": "限制规则",
            "shot_grammar_observation": "动作—失败—完成",
            "edit_grammar_observation": "动作节点切镜",
            "participation_signal": "匿名交作业语义",
            "visible_engagement": "页面显示值",
            "account_baseline_multiple": "",
            "performance_tier": "unknown",
            "evidence_role": role,
            "duplicate_of": "",
            "category_scope": "泛知识",
            "comment_evidence_ids": "none",
            "source_ids": "SRC-001",
            "access_status": "full",
            "source_snapshot_sha256": "a" * 64,
            "capture_status": "complete",
            "limitations": "none",
        }
    )
    return row


def candidate(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "record_type": "trend_template_candidate",
        "schema_version": 1,
        "candidate_record_id": "TTC-001-V1",
        "run_id": "RUN-20260719-001",
        "candidate_version": 1,
        "supersedes_candidate_record_id": None,
        "template_id": "TT-001",
        "family_id": "TTF-001",
        "canonical_name": "规则挑战",
        "aliases": ["挑战别名"],
        "template_types": ["challenge"],
        "discovery_queries": [
            {"query_id": "Q-001", "parent_query_id": "Q-ROOT", "round": 2, "source": "title_phrase"}
        ],
        "discovery_lanes": ["named_trend", "unnamed_structure_cluster"],
        "source_sample_ids": ["TTS-001"],
        "support_sample_ids": ["TTS-002", "TTS-003"],
        "counterexample_sample_ids": ["TTS-004"],
        "boundary_sample_ids": ["TTS-005"],
        "independent_account_count": 2,
        "category_scopes": ["泛知识"],
        "carrier_scopes": ["short_video"],
        "primary_job_scopes": ["feed_stop"],
        "traffic_stage_scopes": ["feed_stop"],
        "supply_origin": "spontaneous",
        "supply_origin_evidence_ids": ["SRC-001"],
        "first_seen_at": "2026-07-01",
        "last_seen_at": "2026-07-18",
        "sample_window": {"start": "2026-06-20", "end": "2026-07-19", "timezone": "Asia/Shanghai", "end_inclusive": True},
        "window_comparisons": [
            {
                "start": "2026-06-20",
                "end": "2026-07-04",
                "support_sample_ids": ["TTS-002"],
                "independent_derivatives": 1,
            },
            {
                "start": "2026-07-05",
                "end": "2026-07-19",
                "support_sample_ids": ["TTS-003"],
                "independent_derivatives": 1,
            },
        ],
        "hook_grammar": "给出限制规则",
        "shot_grammar": "动作—失败—完成",
        "edit_grammar": "动作节点切镜",
        "participation_loop": "按同一规则交作业",
        "slot_map": {"fixed": ["限制规则"], "replaceable": ["人物", "场景"], "new_semantic_contribution": "把规则迁移到目标用户真实场景"},
        "required_material_codes": ["real_scene"],
        "optional_material_codes": [],
        "contraindications": [],
        "rights_status": "grammar_only",
        "safety_status": "passed",
        "authorized_asset_ids": [],
        "source_asset_hashes": [],
        "replication_status": "replicated",
        "lifecycle_phase": "rising",
        "lifecycle_reason": "两个可比窗口中独立复刻仍在出现",
        "confidence": "medium",
        "evidence_level": "inferred",
        "performance_evidence_scope": "public_proxy_association",
        "decision": "adapt",
        "adaptation_notes": "只复用语法",
        "last_refreshed_at": "2026-07-19",
        "limitations": ["没有一方曝光"],
        "record_sha256": "",
    }
    row.update(overrides)
    row["record_sha256"] = record_hash(row)
    return row


class TrendTemplateRadarTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = load_validator_module()

    def test_skill_routes_live_template_requests_to_the_radar(self) -> None:
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("trend-template-radar.md", text)
        self.assertIn("近期爆火模板", text)
        self.assertIn("二创链", text)
        self.assertIn("低表现对照", text)

    def test_radar_specifies_discovery_validation_lifecycle_and_reuse(self) -> None:
        text = (SKILL / "references" / "trend-template-radar.md").read_text(
            encoding="utf-8"
        )
        for required in (
            "发现词树",
            "模板家族",
            "精确短语追链",
            "评论参与证据",
            "同模板高低对照",
            "query_candidate",
            "observed",
            "replicated",
            "rising",
            "mature",
            "fatigued",
            "evergreen_carrier",
            "拍",
            "改后拍",
            "观察",
            "不追",
            "public_proxy ≠ traffic",
            "单篇高赞",
            "生成时调用",
        ):
            self.assertIn(required, text)

    def test_template_sample_asset_has_exact_header(self) -> None:
        path = SKILL / "assets" / "trend-template-samples-template.csv"
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            self.assertEqual(next(csv.reader(handle)), SAMPLE_HEADER)

    def test_template_card_asset_is_parseable_and_fail_closed(self) -> None:
        path = SKILL / "assets" / "trend-template-candidates-template.jsonl"
        rows = [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(set(row), CARD_FIELDS)
        self.assertEqual(row["record_type"], "trend_template_candidate")
        self.assertEqual(row["candidate_record_id"], "TTC-PLACEHOLDER-V1")
        self.assertEqual(row["candidate_version"], 1)
        self.assertIsNone(row["supersedes_candidate_record_id"])
        self.assertEqual(row["replication_status"], "query_candidate")
        self.assertEqual(row["lifecycle_phase"], "unknown")
        self.assertEqual(row["performance_evidence_scope"], "not_performance_evidence")
        self.assertEqual(row["decision"], "observe")
        self.assertEqual(row["source_sample_ids"], [])
        self.assertEqual(row["support_sample_ids"], [])
        self.assertEqual(row["counterexample_sample_ids"], [])
        self.assertEqual(row["record_sha256"], record_hash(row))

    def trend_issues(self, row: dict[str, object]) -> list[object]:
        validator = self.validator.RunValidator(Path("."))
        samples = [
            sample("TTS-001", "seed", "ACC-001", "L-001", "direct_remake"),
            sample(
                "TTS-002",
                "support",
                "ACC-002",
                "L-002",
                "slot_substitution",
                published_at="2026-06-25",
            ),
            sample("TTS-003", "support", "ACC-003", "L-003", "category_transfer"),
            sample("TTS-004", "counterexample", "ACC-004", "L-004", "direct_remake"),
            sample("TTS-005", "boundary", "ACC-005", "L-005", "unrelated_same_phrase"),
        ]
        validator.run = {
            "run_id": "RUN-20260719-001",
            "created_at": "2026-07-19",
            "window_start": "2026-06-20",
            "window_end": "2026-07-19",
            "trend_template_requirement": "research",
        }
        validator.rows = {
            "trend-template-samples.csv": samples,
            "query-log.csv": [{"query_id": "Q-001"}, {"query_id": "Q-ROOT"}],
            "source-log.csv": [{"source_id": "SRC-001"}],
            "posts.csv": [
                {
                    "post_id": item["post_id"],
                    "note_id": item["note_id"],
                    "url": item["url"],
                    "account_id": item["account_id"],
                    "published_at": item["published_at"],
                }
                for item in samples
            ],
            "accounts.csv": [{"account_id": item["account_id"]} for item in samples],
        }
        validator.trend_candidates = [row]
        validator._check_trend_templates()
        return validator.issues

    def test_valid_replicated_current_candidate_passes_trend_gate(self) -> None:
        self.assertEqual(self.trend_issues(candidate()), [])

    def test_single_observation_cannot_adapt_or_shoot(self) -> None:
        row = candidate(
            replication_status="observed",
            lifecycle_phase="unknown",
            support_sample_ids=[],
            independent_account_count=0,
            decision="adapt",
        )
        codes = {issue.code for issue in self.trend_issues(row)}
        self.assertIn("trend_decision_not_eligible", codes)

    def test_fake_independent_count_and_missing_rights_fail_closed(self) -> None:
        row = candidate(independent_account_count=9, rights_status="unknown")
        codes = {issue.code for issue in self.trend_issues(row)}
        self.assertIn("trend_independence_mismatch", codes)
        self.assertIn("trend_rights_gate", codes)

    def test_rising_requires_comparable_windows(self) -> None:
        row = candidate(window_comparisons=[])
        codes = {issue.code for issue in self.trend_issues(row)}
        self.assertIn("trend_lifecycle_evidence", codes)

    def test_empty_window_shells_and_mature_without_windows_fail_closed(self) -> None:
        rising_codes = {
            issue.code for issue in self.trend_issues(candidate(window_comparisons=[{}, {}]))
        }
        mature_codes = {
            issue.code
            for issue in self.trend_issues(
                candidate(lifecycle_phase="mature", window_comparisons=[])
            )
        }
        self.assertIn("trend_lifecycle_evidence", rising_codes)
        self.assertIn("trend_lifecycle_evidence", mature_codes)

    def test_one_post_cannot_masquerade_as_independent_roles(self) -> None:
        validator = self.validator.RunValidator(Path("."))
        samples = [
            sample("TTS-001", "seed", "ACC-001", "L-001", "direct_remake"),
            sample("TTS-002", "support", "ACC-002", "L-002", "slot_substitution"),
            sample("TTS-003", "support", "ACC-003", "L-003", "category_transfer"),
            sample("TTS-004", "counterexample", "ACC-004", "L-004", "direct_remake"),
            sample("TTS-005", "boundary", "ACC-005", "L-005", "unrelated_same_phrase"),
        ]
        for item in samples:
            item.update(
                {
                    "post_id": "POST-SINGLE",
                    "note_id": "note-single",
                    "url": "https://example.com/single?tracking=" + item["template_sample_id"],
                }
            )
        validator.run = {
            "run_id": "RUN-20260719-001",
            "created_at": "2026-07-19",
            "window_start": "2026-06-20",
            "window_end": "2026-07-19",
            "trend_template_requirement": "research",
        }
        validator.rows = {
            "trend-template-samples.csv": samples,
            "query-log.csv": [{"query_id": "Q-001"}, {"query_id": "Q-ROOT"}],
            "source-log.csv": [{"source_id": "SRC-001"}],
            "posts.csv": [
                {
                    "post_id": "POST-SINGLE",
                    "note_id": "note-single",
                    "url": "https://example.com/single",
                    "account_id": "ACC-001",
                    "published_at": "2026-07-10",
                }
            ],
            "accounts.csv": [
                {"account_id": item["account_id"]} for item in samples
            ],
        }
        validator.trend_candidates = [candidate()]
        validator._check_trend_templates()
        codes = {issue.code for issue in validator.issues}
        self.assertIn("trend_sample_post_mismatch", codes)
        self.assertIn("trend_post_role_overlap", codes)

    def test_v2_requires_explicit_trend_declaration_and_draft_section(self) -> None:
        validator = self.validator.RunValidator(Path("."))
        validator.run = {
            "run_contract_version": "2",
            "mode": "draft",
            "business_objective": "traffic_first",
            "objective_primary_job": "feed_stop",
            "performance_visibility_scope": "public_proxy",
            "style_requirement": "both",
            "style_library_path": "../_style_library/style-library.sqlite",
            "style_taxonomy_version": "2",
        }
        validator._check_v2_run_contract()
        self.assertTrue(
            any(
                issue.code == "missing_v2_run_field"
                and "trend_template_requirement" in issue.message
                for issue in validator.issues
            )
        )

        validator.issues = []
        validator.run["trend_template_requirement"] = "none"
        validator._check_trend_template_contract(Path("draft.md"), "", {}, set())
        self.assertTrue(
            any(issue.code == "trend_template_contract_missing" for issue in validator.issues)
        )

    def test_fake_authorized_assets_fail_closed(self) -> None:
        row = candidate(
            rights_status="authorized_assets",
            authorized_asset_ids=["MATERIAL-NOT-FOUND"],
            source_asset_hashes=["b" * 64],
        )
        codes = {issue.code for issue in self.trend_issues(row)}
        self.assertIn("trend_rights_gate", codes)

    def test_validator_requires_both_trend_files_when_run_declares_radar(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            validator = self.validator.RunValidator(Path(tmp))
            validator.run = {
                "mode": "refresh",
                "trend_template_requirement": "research",
            }
            validator._check_required_files()
        missing = {issue.location for issue in validator.issues if issue.code == "missing_file"}
        self.assertIn("trend-template-samples.csv", missing)
        self.assertIn("trend-template-candidates.jsonl", missing)

    def test_draft_trend_binding_matches_latest_candidate_and_materials(self) -> None:
        validator = self.validator.RunValidator(Path("."))
        validator.run = {
            "trend_template_requirement": "draft",
            "created_at": "2026-07-19",
        }
        validator.rows = {"posts.csv": [{"post_id": "POST-TTS-001"}]}
        validator.trend_candidates = [candidate()]
        rendered = """## 趋势模板绑定
template_contract_status: bound_candidate
candidate_record_id: TTC-001-V1
template_id: TT-001
family_id: TTF-001
candidate_version: 1
replication_status: replicated
lifecycle_phase: rising
last_refreshed_at: 2026-07-19
decision: adapt
source_sample_ids: TTS-001
support_sample_ids: TTS-002;TTS-003
counterexample_sample_ids: TTS-004
fixed_slots: 限制规则
replaced_slots: 人物
new_semantic_contribution: 迁移到目标用户真实场景并增加新的限制解释
material_evidence_map: {"real_scene":["POST-TTS-001"]}
failure_condition: 当前窗口不再出现独立复刻时停止
"""
        meta = {
            "style_query_category": "泛知识",
            "style_query_carrier": "short_video",
            "primary_job": "feed_stop",
            "traffic_stage": "feed_stop",
        }
        validator._check_trend_template_contract(
            Path("draft.md"), rendered, meta, {"趋势模板绑定"}
        )
        self.assertEqual(validator.issues, [])

    def test_draft_rejects_unknown_material_evidence_id(self) -> None:
        validator = self.validator.RunValidator(Path("."))
        validator.run = {
            "trend_template_requirement": "draft",
            "created_at": "2026-07-19",
        }
        validator.rows = {"posts.csv": [{"post_id": "POST-TTS-001"}]}
        validator.trend_candidates = [candidate()]
        rendered = """## 趋势模板绑定
template_contract_status: bound_candidate
candidate_record_id: TTC-001-V1
template_id: TT-001
family_id: TTF-001
candidate_version: 1
replication_status: replicated
lifecycle_phase: rising
last_refreshed_at: 2026-07-19
decision: adapt
source_sample_ids: TTS-001
support_sample_ids: TTS-002;TTS-003
counterexample_sample_ids: TTS-004
fixed_slots: 限制规则
replaced_slots: 人物
new_semantic_contribution: 迁移到目标用户真实场景并增加新的限制解释
material_evidence_map: {"real_scene":["ASSET-NOT-FOUND"]}
failure_condition: 当前窗口不再出现独立复刻时停止
"""
        meta = {
            "style_query_category": "泛知识",
            "style_query_carrier": "short_video",
            "primary_job": "feed_stop",
            "traffic_stage": "feed_stop",
        }
        validator._check_trend_template_contract(
            Path("draft.md"), rendered, meta, {"趋势模板绑定"}
        )
        self.assertTrue(
            any(issue.code == "trend_material_gate" for issue in validator.issues)
        )


if __name__ == "__main__":
    unittest.main()
