from __future__ import annotations

import csv
import hashlib
import re
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = REPO_ROOT / "redbook-writing" / "scripts" / "validate_run.py"


HEADERS = {
    "query-log.csv": [
        "query_id",
        "platform",
        "query",
        "search_surface",
        "sort_or_filter",
        "run_at",
        "result_count",
        "selected_source_ids",
        "selected_account_ids",
        "selected_post_ids",
        "new_valid_accounts",
        "new_content_patterns",
        "notes",
    ],
    "source-log.csv": [
        "source_id",
        "source_layer",
        "platform",
        "source_type",
        "title",
        "author_org",
        "published_at",
        "collected_at",
        "url",
        "query_id",
        "access_status",
        "evidence_form",
        "evidence_grade",
        "notes_file",
    ],
    "claim-ledger.csv": [
        "claim_id",
        "category",
        "claim_text",
        "source_ids",
        "counter_source_ids",
        "evidence_grade",
        "claim_status",
        "scope",
        "confidence_reason",
        "skill_action",
        "last_verified_at",
        "verification_class",
    ],
    "accounts.csv": [
        "account_id",
        "account_name",
        "profile_url",
        "head_type",
        "follower_count",
        "window_start",
        "window_end",
        "recent_sample_n",
        "recent_median_visible_engagement",
        "recent_max_visible_engagement",
        "outlier_multiple",
        "audience_evidence",
        "commercial_distance",
        "collected_at",
        "source_ids",
        "confidence",
        "status",
    ],
    "posts.csv": [
        "post_id",
        "note_id",
        "title",
        "url",
        "account_id",
        "published_at",
        "date_confidence",
        "collected_at",
        "queries_matched",
        "search_surface",
        "sort_or_filter",
        "rank_observed",
        "format",
        "visible_engagement",
        "engagement_breakdown_available",
        "account_baseline_multiple",
        "hook",
        "page_or_scene_structure",
        "need_signal",
        "cover_mechanism",
        "evidence_level",
        "confidence",
        "duplicate_of",
        "cluster_id",
        "status",
        "performance_tier",
        "style_capture_status",
        "style_library_post_id",
        "style_observation_ids",
        "style_skip_reason",
    ],
    "topics.csv": [
        "topic_id",
        "topic",
        "primary_job",
        "entry_surface",
        "target_audience",
        "specific_scenario",
        "core_promise_or_tension",
        "evidence_ids",
        "counterexamples",
        "lifecycle",
        "format",
        "format_reason",
        "commercial_distance",
        "rule_scopes",
        "measurement_plan",
        "hypothesis_id",
        "priority",
        "status",
        "last_seen_at",
    ],
    "acquisition-channels.csv": [
        "channel_id",
        "direction",
        "platform",
        "account_scope",
        "audience_state",
        "channel_role",
        "native_format",
        "source_asset_id",
        "source_asset_sha256",
        "public_identity",
        "eligibility_ids",
        "surfaces",
        "permitted_cta",
        "prohibited_cta",
        "landing_asset",
        "primary_metric",
        "metric_availability",
        "data_source",
        "event_definition",
        "diagnostic_metrics",
        "attribution_method",
        "attribution_level",
        "baseline_window",
        "test_window",
        "minimum_events",
        "decision_rule",
        "compliance_scope",
        "evidence_ids",
        "consent_ids",
        "confidence",
        "owner",
        "status",
    ],
    "sku-registry.csv": [
        "eligibility_id",
        "sku_id",
        "sku_name",
        "platform",
        "account_scope",
        "surface",
        "source_asset_id",
        "source_asset_sha256",
        "status",
        "evidence_ids",
        "platform_ticket",
        "qualification_claim_id",
        "verified_at",
        "expires_at",
        "material_limits",
        "qualification_requirements",
        "notes",
    ],
    "offer-registry.csv": [
        "eligibility_id",
        "offer_id",
        "offer_name",
        "offer_type",
        "platform",
        "account_scope",
        "surface",
        "source_asset_id",
        "source_asset_sha256",
        "status",
        "evidence_ids",
        "platform_ticket",
        "qualification_claim_id",
        "verified_at",
        "expires_at",
        "permission_or_consent_requirements",
        "prohibited_uses",
        "notes",
    ],
    "authorization-log.csv": [
        "authorization_id",
        "subject_scope",
        "source_asset_id",
        "material_id",
        "material_sha256",
        "material_type",
        "permission_scope",
        "commercial_use",
        "anonymization_requirements",
        "granted_at",
        "expires_at",
        "withdrawal_process",
        "evidence_locator",
        "verified_by",
        "verified_at",
        "status",
        "authorized_output_sha256",
    ],
}


V2_POST_STYLE_COLUMNS = {
    "performance_tier",
    "style_capture_status",
    "style_library_post_id",
    "style_observation_ids",
    "style_skip_reason",
}


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=HEADERS[path.name])
        writer.writeheader()
        writer.writerows(rows)


def base_source(source_id: str = "OFF-001") -> dict[str, str]:
    return {
        "source_id": source_id,
        "source_layer": "official",
        "platform": "小红书",
        "source_type": "official_rule",
        "title": "当前规则",
        "author_org": "小红书",
        "published_at": "2026-07-01",
        "collected_at": "2026-07-16",
        "url": f"https://example.com/{source_id}",
        "query_id": "Q-001",
        "access_status": "full",
        "evidence_form": "official_page",
        "evidence_grade": "A",
        "notes_file": "research.md",
    }


def base_claim(**overrides: str) -> dict[str, str]:
    row = {
        "claim_id": "CLM-001",
        "category": "current_rule",
        "claim_text": "规则仅支持有限作用域。",
        "source_ids": "OFF-001",
        "counter_source_ids": "",
        "evidence_grade": "A",
        "claim_status": "confirmed",
        "scope": "organic_content",
        "confidence_reason": "官方当前页面直接说明",
        "skill_action": "按作用域使用",
        "last_verified_at": "2026-07-16",
        "verification_class": "current_runtime",
    }
    row.update(overrides)
    return row


def base_account(account_id: str, **overrides: str) -> dict[str, str]:
    suffix = account_id.lower()
    row = {
        "account_id": account_id,
        "account_name": f"账号{suffix}",
        "profile_url": f"https://example.com/account/{suffix}",
        "head_type": "recent_performance",
        "follower_count": "1000",
        "window_start": "2026-06-16",
        "window_end": "2026-07-16",
        "recent_sample_n": "10",
        "recent_median_visible_engagement": "20",
        "recent_max_visible_engagement": "200",
        "outlier_multiple": "10",
        "audience_evidence": "简介、内容和评论问题",
        "commercial_distance": "far",
        "collected_at": "2026-07-16",
        "source_ids": "OFF-001",
        "confidence": "medium",
        "status": "focus",
    }
    row.update(overrides)
    return row


def base_post(post_id: str, account_id: str, **overrides: str) -> dict[str, str]:
    suffix = post_id.lower()
    row = {
        "post_id": post_id,
        "note_id": f"note-{suffix}",
        "title": f"样本{suffix}",
        "url": f"https://example.com/post/{suffix}",
        "account_id": account_id,
        "published_at": "2026-07-10",
        "date_confidence": "high",
        "collected_at": "2026-07-16",
        "queries_matched": "Q-001",
        "search_surface": "notes",
        "sort_or_filter": "latest",
        "rank_observed": "1",
        "format": "carousel",
        "visible_engagement": "200",
        "engagement_breakdown_available": "false",
        "account_baseline_multiple": "10",
        "hook": "具体处境",
        "page_or_scene_structure": "1:问题;2:证据",
        "need_signal": "读者求方法",
        "cover_mechanism": "具体问题",
        "evidence_level": "observed",
        "confidence": "high",
        "duplicate_of": "",
        "cluster_id": "C-1",
        "status": "active",
    }
    row.update(overrides)
    return row


def base_topic(**overrides: str) -> dict[str, str]:
    row = {key: "" for key in HEADERS["topics.csv"]}
    row.update(
        {
            "topic_id": "TOPIC-001",
            "topic": "有真实需求样本的测试选题",
            "primary_job": "relationship_building",
            "entry_surface": "search",
            "target_audience": "成年用户",
            "specific_scenario": "具体关系场景",
            "core_promise_or_tension": "提供边界判断",
            "evidence_ids": "USER-001",
            "counterexamples": "USER-002：只支持相邻场景，不外推",
            "lifecycle": "evergreen_search",
            "format": "carousel",
            "format_reason": "便于逐步说明",
            "commercial_distance": "adjacent",
            "rule_scopes": "organic_content",
            "measurement_plan": "以搜索进入后的有效阅读为主指标，事件不足时 inconclusive",
            "hypothesis_id": "H-001",
            "priority": "P1",
            "status": "experimental",
            "last_seen_at": "2026-07-16",
        }
    )
    row.update(overrides)
    return row


def base_sku(**overrides: str) -> dict[str, str]:
    row = {key: "" for key in HEADERS["sku-registry.csv"]}
    row.update(
        {
            "eligibility_id": "SKU-XHS-SHOP",
            "sku_id": "SKU-001",
            "sku_name": "具体商品",
            "platform": "xiaohongshu",
            "account_scope": "acct-xhs-001",
            "surface": "shop",
            "source_asset_id": "DRAFT-001",
            "source_asset_sha256": "a" * 64,
            "status": "confirmed",
            "evidence_ids": "TICKET-001;QUAL-001",
            "platform_ticket": "TICKET-001",
            "qualification_claim_id": "QUAL-001",
            "verified_at": "2026-07-16",
            "expires_at": "2026-08-16",
            "material_limits": "只允许工单审核的素材",
            "qualification_requirements": "主体、账户、商品、素材与组件均匹配",
        }
    )
    row.update(overrides)
    return row


def base_channel(**overrides: str) -> dict[str, str]:
    row = {key: "x" for key in HEADERS["acquisition-channels.csv"]}
    row.update(
        {
            "channel_id": "CH-001",
            "direction": "xhs_to_native_conversion",
            "platform": "xiaohongshu",
            "account_scope": "acct-xhs-001",
            "source_asset_id": "DRAFT-001",
            "source_asset_sha256": "a" * 64,
            "eligibility_ids": "SKU-XHS-SHOP",
            "surfaces": "shop",
            "permitted_cta": "使用已审核站内商品组件",
            "attribution_level": "platform_native",
            "evidence_ids": "OFF-001",
            "consent_ids": "",
            "status": "active",
        }
    )
    row.update(overrides)
    return row


def write_complete_draft(path: Path, **overrides: str) -> None:
    meta = {
        "draft_id": "DRAFT-001",
        "topic_id": "TOPIC-001",
        "platform": "xiaohongshu",
        "account_scope": "none",
        "primary_job": "relationship_building",
        "lifecycle": "evergreen_search",
        "truth_label": "factual_explainer",
        "truth_disclosure_text": "事实说明",
        "truth_disclosure_location": "首屏",
        "authorization_ids": "none",
        "source_material_ids": "none",
        "commercial_relationship": "none",
        "disclosure_text": "none",
        "disclosure_location": "none",
        "answer_location": "正文第2段",
        "cta_type": "none",
        "eligibility_ids": "none",
        "surfaces": "none",
        "status": "ready",
    }
    meta.update(overrides)
    sections: list[str] = []
    for heading in sorted(
        {
            "证据与目标用户",
            "标题版本",
            "封面版本",
            "成稿",
            "关键词与话题",
            "事实与证明",
            "CTA 与披露",
            "合规审校",
            "创意审校",
            "观测计划",
        }
    ):
        if heading == "CTA 与披露":
            cta_copy = "none" if meta["cta_type"] == "none" else "使用已审核站内商品组件"
            body = "\n".join(
                [
                    f"cta_type: {meta['cta_type']}",
                    f"cta_copy: {cta_copy}",
                    f"commercial_relationship: {meta['commercial_relationship']}",
                    f"disclosure_text: {meta['disclosure_text']}",
                    f"disclosure_location: {meta['disclosure_location']}",
                    f"eligibility_ids: {meta['eligibility_ids']}",
                    f"platform: {meta['platform']}",
                    f"account_scope: {meta['account_scope']}",
                    f"surfaces: {meta['surfaces']}",
                ]
            )
        elif heading in {"合规审校", "创意审校"}:
            body = "review_status: PASS\nfindings: none"
        elif heading == "成稿" and meta["commercial_relationship"] != "none":
            body_lines = [
                meta["disclosure_text"],
                f"已完成且可审计的{heading}内容。",
            ]
            if meta["cta_type"] != "none":
                body_lines.append("使用已审核站内商品组件")
            body = "\n".join(body_lines)
        else:
            body = f"已完成且可审计的{heading}内容。"
        sections.append(f"## {heading}\n{body}")
    frontmatter = "\n".join(f'{key}: "{value}"' for key, value in meta.items())
    path.write_text(
        f"---\n{frontmatter}\n---\n\n> {meta['truth_disclosure_text']}\n\n"
        + "\n\n".join(sections)
        + "\n",
        encoding="utf-8",
    )


def v2_style_meta(**overrides: str) -> dict[str, str]:
    meta = {
        "style_contract_version": "2",
        "business_objective": "traffic_first",
        "style_requirement": "both",
        "style_query_carrier": "text_card",
        "style_query_primary_job": "feed_stop",
        "style_binding_source": "none",
        "style_binding_status": "needs_style_research",
        "performance_rule_claim_kind": "series_constant",
        "style_feature_contrast": "invariant",
        "performance_evidence_scope": "not_performance_evidence",
        "performance_visibility_scope": "public_proxy",
        "traffic_primary_metric": "engagement_proxy",
        "traffic_verdict": "not_applicable",
        "traffic_stage": "feed_stop",
        "visual_delivery_requirement": "brief",
        "visual_delivery_status": "brief_only",
    }
    meta.update(overrides)
    return meta


def asset_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def approval_source(source_id: str = "TICKET-001") -> dict[str, str]:
    row = base_source(source_id)
    row.update(
        {
            "source_type": "platform_approval_record",
            "title": "精确素材审批记录",
            "evidence_form": "platform_ticket",
        }
    )
    return row


def qualification_claim(asset_hash: str, **overrides: str) -> dict[str, str]:
    row = base_claim(
        claim_id="QUAL-001",
        category="sku_eligibility",
        claim_text="该精确素材资格已获批。",
        source_ids="TICKET-001",
        scope=(
            "sku_id=SKU-001|platform=xiaohongshu|account_scope=acct-xhs-001|surface=shop|"
            f"source_asset_id=DRAFT-001|source_asset_sha256={asset_hash}"
        ),
    )
    row.update(overrides)
    return row


def base_offer(**overrides: str) -> dict[str, str]:
    row = {key: "" for key in HEADERS["offer-registry.csv"]}
    row.update(
        {
            "eligibility_id": "OFFER-XHS-SHOP",
            "offer_id": "OFFER-RETAIL-001",
            "offer_name": "标准零售交易",
            "offer_type": "product_sale",
            "platform": "xiaohongshu",
            "account_scope": "acct-xhs-001",
            "surface": "shop",
            "source_asset_id": "DRAFT-001",
            "source_asset_sha256": "a" * 64,
            "status": "confirmed",
            "evidence_ids": "TICKET-OFFER-001;QUAL-OFFER-001",
            "platform_ticket": "TICKET-OFFER-001",
            "qualification_claim_id": "QUAL-OFFER-001",
            "verified_at": "2026-07-16",
            "expires_at": "2026-08-16",
            "permission_or_consent_requirements": "购买行为自愿且披露经营关系",
            "prohibited_uses": "暗号、陌生私信、未审核外跳",
        }
    )
    row.update(overrides)
    return row


def offer_qualification_claim(asset_hash: str, **overrides: str) -> dict[str, str]:
    row = base_claim(
        claim_id="QUAL-OFFER-001",
        category="offer_eligibility",
        claim_text="该精确零售offer与素材资格已获批。",
        source_ids="TICKET-OFFER-001",
        scope=(
            "offer_id=OFFER-RETAIL-001|offer_type=product_sale|platform=xiaohongshu|"
            "account_scope=acct-xhs-001|surface=shop|source_asset_id=DRAFT-001|"
            f"source_asset_sha256={asset_hash}"
        ),
    )
    row.update(overrides)
    return row


class RunFixture:
    def __init__(self, mode: str = "mechanism") -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name)
        (self.path / "run.yaml").write_text(
            textwrap.dedent(
                f"""\
                run_id: TEST-001
                mode: {mode}
                status: in_progress
                created_at: 2026-07-16
                category: 测试类目
                target_audience: 成年用户
                primary_goal: research
                commercial_goal: none
                window_start: 2026-06-16
                window_end: 2026-07-16
                assumptions: []
                limitations: []
                """
            ),
            encoding="utf-8",
        )
        (self.path / "research.md").write_text("# 研究结论\n\n保留范围和局限。\n", encoding="utf-8")
        write_csv(
            self.path / "query-log.csv",
            [
                {
                    "query_id": "Q-001",
                    "platform": "web",
                    "query": "当前规则",
                    "search_surface": "search",
                    "sort_or_filter": "default",
                    "run_at": "2026-07-16",
                    "result_count": "1",
                    "selected_source_ids": "OFF-001",
                    "selected_account_ids": "",
                    "selected_post_ids": "",
                    "new_valid_accounts": "0",
                    "new_content_patterns": "0",
                    "notes": "",
                }
            ],
        )
        write_csv(self.path / "source-log.csv", [base_source()])
        write_csv(self.path / "claim-ledger.csv", [base_claim()])

    def close(self) -> None:
        self._tmp.cleanup()

    def set_run_field(self, field: str, value: str) -> None:
        path = self.path / "run.yaml"
        lines = path.read_text(encoding="utf-8").splitlines()
        replaced = False
        updated: list[str] = []
        for line in lines:
            if line.startswith(f"{field}:"):
                updated.append(f"{field}: {value}")
                replaced = True
            else:
                updated.append(line)
        if not replaced:
            updated.append(f"{field}: {value}")
        path.write_text("\n".join(updated) + "\n", encoding="utf-8")


class ValidateRunTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = RunFixture()

    def tearDown(self) -> None:
        self.fixture.close()

    def run_validator(self, *extra: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(VALIDATOR), str(self.fixture.path), *extra],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_valid_mechanism_run_passes(self) -> None:
        result = self.run_validator()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("VALID", result.stdout)

    def test_valid_verdict_exposes_run_status(self) -> None:
        in_progress = self.run_validator()
        self.assertIn("VALID_IN_PROGRESS", in_progress.stdout)
        self.fixture.set_run_field("status", "complete")
        complete = self.run_validator()
        self.assertEqual(complete.returncode, 0, complete.stdout + complete.stderr)
        self.assertIn("VALID_COMPLETE", complete.stdout)
        self.fixture.set_run_field("status", "blocked")
        blocked = self.run_validator()
        self.assertEqual(blocked.returncode, 0, blocked.stdout + blocked.stderr)
        self.assertIn("VALID_BLOCKED", blocked.stdout)

    def test_duplicate_source_id_is_rejected(self) -> None:
        write_csv(self.fixture.path / "source-log.csv", [base_source(), base_source()])
        result = self.run_validator()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("duplicate_id", result.stdout)

    def test_dangling_claim_source_is_rejected(self) -> None:
        write_csv(
            self.fixture.path / "claim-ledger.csv",
            [base_claim(source_ids="OFF-MISSING")],
        )
        result = self.run_validator()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("dangling_reference", result.stdout)

    def test_d_grade_claim_cannot_be_confirmed(self) -> None:
        write_csv(
            self.fixture.path / "claim-ledger.csv",
            [base_claim(evidence_grade="D", claim_status="confirmed")],
        )
        result = self.run_validator()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("grade_status_conflict", result.stdout)

    def test_claim_grade_cannot_exceed_best_supporting_source(self) -> None:
        weak_source = base_source()
        weak_source["source_layer"] = "rumor"
        weak_source["evidence_grade"] = "D"
        write_csv(self.fixture.path / "source-log.csv", [weak_source])
        write_csv(
            self.fixture.path / "claim-ledger.csv",
            [base_claim(evidence_grade="A", claim_status="confirmed")],
        )
        result = self.run_validator()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("grade_source_conflict", result.stdout)

    def test_invalid_source_enums_are_rejected(self) -> None:
        for field, value in (
            ("evidence_grade", "Z"),
            ("source_layer", "social_media_oracle"),
            ("access_status", "probably_full"),
        ):
            with self.subTest(field=field):
                source = base_source()
                source[field] = value
                write_csv(self.fixture.path / "source-log.csv", [source])
                result = self.run_validator()
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("invalid_enum", result.stdout)

    def test_source_grade_is_capped_by_layer_and_access(self) -> None:
        source = base_source()
        source["source_layer"] = "rumor"
        source["access_status"] = "blocked"
        source["evidence_grade"] = "A"
        write_csv(self.fixture.path / "source-log.csv", [source])
        result = self.run_validator()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("source_grade_conflict", result.stdout)

    def test_confirmed_claim_requires_eligible_primary_source(self) -> None:
        source = base_source()
        source["source_layer"] = "industry"
        source["evidence_grade"] = "B"
        write_csv(self.fixture.path / "source-log.csv", [source])
        write_csv(
            self.fixture.path / "claim-ledger.csv",
            [base_claim(evidence_grade="B", claim_status="confirmed")],
        )
        result = self.run_validator()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("confirmed_source_conflict", result.stdout)

    def test_current_rule_must_be_verified_in_this_run(self) -> None:
        write_csv(
            self.fixture.path / "claim-ledger.csv",
            [base_claim(last_verified_at="2026-07-15")],
        )
        result = self.run_validator()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not_verified_this_run", result.stdout)

    def test_future_claim_verification_date_is_rejected(self) -> None:
        write_csv(
            self.fixture.path / "claim-ledger.csv",
            [base_claim(last_verified_at="2026-07-17")],
        )
        result = self.run_validator()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("future_date", result.stdout)

    def test_run_query_and_source_dates_cannot_be_reversed_or_future(self) -> None:
        self.fixture.set_run_field("window_start", "2026-07-20")
        self.fixture.set_run_field("window_end", "2026-07-16")
        query = {key: "" for key in HEADERS["query-log.csv"]}
        query.update(
            {
                "query_id": "Q-001",
                "platform": "web",
                "query": "当前规则",
                "search_surface": "search",
                "run_at": "2026-07-18T12:00:00+08:00",
                "selected_source_ids": "OFF-001",
            }
        )
        write_csv(self.fixture.path / "query-log.csv", [query])
        source = base_source()
        source["collected_at"] = "2026-07-17"
        write_csv(self.fixture.path / "source-log.csv", [source])
        result = self.run_validator()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid_date_order", result.stdout)
        self.assertIn("future_date", result.stdout)

    def test_account_window_and_collection_dates_are_validated(self) -> None:
        self.fixture.close()
        self.fixture = RunFixture(mode="discovery")
        write_csv(
            self.fixture.path / "accounts.csv",
            [
                base_account(
                    "ACC-001",
                    window_start="2026-07-20",
                    window_end="2026-07-10",
                    collected_at="2026-07-17",
                )
            ],
        )
        write_csv(self.fixture.path / "posts.csv", [])
        write_csv(self.fixture.path / "topics.csv", [])
        result = self.run_validator()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid_date_order", result.stdout)
        self.assertIn("future_date", result.stdout)

    def test_discovery_requires_accounts_posts_and_topics(self) -> None:
        (self.fixture.path / "run.yaml").write_text(
            (self.fixture.path / "run.yaml").read_text(encoding="utf-8").replace(
                "mode: mechanism", "mode: discovery"
            ),
            encoding="utf-8",
        )
        result = self.run_validator()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing_file", result.stdout)

    def test_complete_discovery_rejects_empty_required_datasets(self) -> None:
        self.fixture.close()
        self.fixture = RunFixture(mode="discovery")
        self.fixture.set_run_field("status", "complete")
        for name in ("accounts.csv", "posts.csv", "topics.csv"):
            write_csv(self.fixture.path / name, [])
        result = self.run_validator("--strict")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("incomplete_run", result.stdout)

    def test_recent_performance_completion_requires_baselines_and_post_metrics(self) -> None:
        self.fixture.close()
        self.fixture = RunFixture(mode="discovery")
        self.fixture.set_run_field("status", "complete")
        profiles: list[dict[str, str]] = []
        for source_id, account_id in (("PROFILE-001", "ACC-001"), ("PROFILE-002", "ACC-002")):
            profile = base_source(source_id)
            profile.update(
                {
                    "source_layer": "creator_experience",
                    "source_type": "creator_profile",
                    "evidence_form": "profile",
                    "evidence_grade": "C",
                    "url": f"https://example.com/account/{account_id.lower()}",
                }
            )
            profiles.append(profile)
        counter = base_source("COUNTER-001")
        counter.update(
            {
                "source_layer": "creator_experience",
                "source_type": "interview",
                "evidence_form": "interview",
                "evidence_grade": "C",
            }
        )
        write_csv(self.fixture.path / "source-log.csv", [base_source(), *profiles, counter])
        write_csv(
            self.fixture.path / "accounts.csv",
            [
                base_account(
                    "ACC-001",
                    source_ids="PROFILE-001",
                    recent_median_visible_engagement="",
                    recent_max_visible_engagement="",
                    outlier_multiple="",
                ),
                base_account(
                    "ACC-002",
                    source_ids="PROFILE-002",
                    recent_median_visible_engagement="",
                    recent_max_visible_engagement="",
                    outlier_multiple="",
                ),
            ],
        )
        write_csv(
            self.fixture.path / "posts.csv",
            [
                base_post(
                    "POST-001",
                    "ACC-001",
                    visible_engagement="not-a-metric",
                    account_baseline_multiple="10",
                ),
                base_post(
                    "POST-002",
                    "ACC-002",
                    visible_engagement="",
                    account_baseline_multiple="",
                ),
            ],
        )
        write_csv(
            self.fixture.path / "topics.csv",
            [
                base_topic(
                    status="active",
                    evidence_ids="POST-001;POST-002",
                    counterexamples="COUNTER-001：没有表现指标，不能认定为高表现样本",
                )
            ],
        )
        result = self.run_validator("--strict")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing_performance_baseline", result.stdout)
        self.assertIn("missing_post_metric", result.stdout)
        self.assertIn("POST-001", result.stdout)

    def test_scale_head_type_requires_follower_count(self) -> None:
        self.fixture.close()
        self.fixture = RunFixture(mode="discovery")
        profile = base_source("PROFILE-001")
        profile.update(
            {
                "source_layer": "creator_experience",
                "source_type": "creator_profile",
                "evidence_form": "profile",
                "evidence_grade": "C",
                "url": "https://example.com/account/acc-001",
            }
        )
        write_csv(self.fixture.path / "source-log.csv", [base_source(), profile])
        write_csv(
            self.fixture.path / "accounts.csv",
            [
                base_account(
                    "ACC-001",
                    source_ids="PROFILE-001",
                    head_type="scale",
                    follower_count="not-visible",
                )
            ],
        )
        write_csv(self.fixture.path / "posts.csv", [])
        write_csv(self.fixture.path / "topics.csv", [])
        result = self.run_validator()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing_scale_metric", result.stdout)

    def test_unknown_run_status_is_rejected(self) -> None:
        self.fixture.set_run_field("status", "looks_done")
        result = self.run_validator()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid_status", result.stdout)

    def test_required_run_fields_cannot_be_blank(self) -> None:
        self.fixture.set_run_field("status", "complete")
        for field in (
            "run_id",
            "created_at",
            "category",
            "target_audience",
            "primary_goal",
            "commercial_goal",
            "window_start",
            "window_end",
        ):
            self.fixture.set_run_field(field, "")
        result = self.run_validator("--strict")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing_run_value", result.stdout)

    def test_active_topic_requires_two_independent_account_samples(self) -> None:
        self.fixture.close()
        self.fixture = RunFixture(mode="discovery")
        write_csv(
            self.fixture.path / "accounts.csv",
            [
                {
                    "account_id": "ACC-001",
                    "account_name": "账号一",
                    "profile_url": "https://example.com/account/1",
                    "head_type": "recent_performance",
                    "follower_count": "1000",
                    "window_start": "2026-06-16",
                    "window_end": "2026-07-16",
                    "recent_sample_n": "10",
                    "recent_median_visible_engagement": "20",
                    "recent_max_visible_engagement": "200",
                    "outlier_multiple": "10",
                    "audience_evidence": "标题与评论问题",
                    "commercial_distance": "far",
                    "collected_at": "2026-07-16",
                    "source_ids": "OFF-001",
                    "confidence": "medium",
                    "status": "focus",
                }
            ],
        )
        post = {
            "post_id": "POST-001",
            "note_id": "note-1",
            "title": "样本",
            "url": "https://example.com/post/1",
            "account_id": "ACC-001",
            "published_at": "2026-07-10",
            "date_confidence": "high",
            "collected_at": "2026-07-16",
            "queries_matched": "Q-001",
            "search_surface": "notes",
            "sort_or_filter": "latest",
            "rank_observed": "1",
            "format": "carousel",
            "visible_engagement": "200",
            "engagement_breakdown_available": "false",
            "account_baseline_multiple": "10",
            "hook": "具体处境",
            "page_or_scene_structure": "1:问题;2:证据",
            "need_signal": "读者求方法",
            "cover_mechanism": "具体问题",
            "evidence_level": "observed",
            "confidence": "high",
            "duplicate_of": "",
            "cluster_id": "C-1",
            "status": "active",
        }
        write_csv(self.fixture.path / "posts.csv", [post])
        write_csv(
            self.fixture.path / "topics.csv",
            [
                {
                    "topic_id": "TOPIC-001",
                    "topic": "一个选题",
                    "primary_job": "search_capture",
                    "entry_surface": "search",
                    "target_audience": "成年用户",
                    "specific_scenario": "具体场景",
                    "core_promise_or_tension": "给出判断",
                    "evidence_ids": "POST-001",
                    "counterexamples": "",
                    "lifecycle": "evergreen_search",
                    "format": "carousel",
                    "format_reason": "便于回看",
                    "commercial_distance": "far",
                    "rule_scopes": "organic_content",
                    "measurement_plan": "搜索曝光→点击→收藏",
                    "hypothesis_id": "H-001",
                    "priority": "P1",
                    "status": "active",
                    "last_seen_at": "2026-07-16",
                }
            ],
        )
        result = self.run_validator()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("insufficient_independent_samples", result.stdout)

    def test_experimental_topic_requires_demand_or_content_sample(self) -> None:
        self.fixture.close()
        self.fixture = RunFixture(mode="discovery")
        official_post = base_source()
        official_post["source_type"] = "official_post"
        official_post["evidence_form"] = "post"
        write_csv(self.fixture.path / "source-log.csv", [official_post])
        write_csv(self.fixture.path / "accounts.csv", [])
        write_csv(self.fixture.path / "posts.csv", [])
        topic = {key: "" for key in HEADERS["topics.csv"]}
        topic.update(
            {
                "topic_id": "TOPIC-001",
                "topic": "只有规则来源的选题",
                "primary_job": "search_capture",
                "target_audience": "成年用户",
                "specific_scenario": "具体场景",
                "core_promise_or_tension": "提供判断",
                "evidence_ids": "OFF-001",
                "lifecycle": "evergreen_search",
                "format": "carousel",
                "measurement_plan": "按本账号基线判断",
                "status": "experimental",
                "last_seen_at": "2026-07-16",
            }
        )
        write_csv(self.fixture.path / "topics.csv", [topic])
        result = self.run_validator()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("insufficient_topic_sample", result.stdout)

    def test_active_topic_rejects_excluded_hypothetical_undated_posts(self) -> None:
        self.fixture.close()
        self.fixture = RunFixture(mode="discovery")
        accounts = [
            base_account(
                "ACC-001",
                recent_sample_n="0",
                source_ids="",
                confidence="high",
                status="excluded",
            ),
            base_account(
                "ACC-002",
                recent_sample_n="0",
                source_ids="",
                confidence="high",
                status="excluded",
            ),
        ]
        write_csv(self.fixture.path / "accounts.csv", accounts)
        posts = [
            base_post(
                "POST-001",
                "ACC-001",
                published_at="",
                date_confidence="unknown",
                evidence_level="hypothesis",
                status="excluded",
            ),
            base_post(
                "POST-002",
                "ACC-002",
                published_at="",
                date_confidence="unknown",
                evidence_level="hypothesis",
                status="excluded",
            ),
        ]
        write_csv(self.fixture.path / "posts.csv", posts)
        topic = {key: "" for key in HEADERS["topics.csv"]}
        topic.update(
            {
                "topic_id": "TOPIC-001",
                "topic": "由失效样本拼出的选题",
                "primary_job": "recommendation_reach",
                "target_audience": "成年用户",
                "specific_scenario": "具体场景",
                "core_promise_or_tension": "解释问题",
                "evidence_ids": "POST-001;POST-002",
                "lifecycle": "hot",
                "format": "carousel",
                "measurement_plan": "按本账号基线判断",
                "status": "active",
                "last_seen_at": "2026-07-16",
            }
        )
        write_csv(self.fixture.path / "topics.csv", [topic])
        result = self.run_validator()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing_reference", result.stdout)
        self.assertIn("account_sample_conflict", result.stdout)
        self.assertIn("insufficient_independent_samples", result.stdout)

    def test_account_outlier_multiple_must_match_visible_values(self) -> None:
        self.fixture.close()
        self.fixture = RunFixture(mode="discovery")
        write_csv(
            self.fixture.path / "accounts.csv",
            [base_account("ACC-001", outlier_multiple="8")],
        )
        write_csv(self.fixture.path / "posts.csv", [])
        write_csv(self.fixture.path / "topics.csv", [])
        result = self.run_validator()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("outlier_mismatch", result.stdout)

    def test_account_recent_max_cannot_be_below_median(self) -> None:
        self.fixture.close()
        self.fixture = RunFixture(mode="discovery")
        profile = base_source("PROFILE-001")
        profile.update(
            {
                "source_layer": "creator_experience",
                "source_type": "creator_profile",
                "evidence_form": "profile",
                "evidence_grade": "C",
                "url": "https://example.com/account/acc-001",
            }
        )
        write_csv(self.fixture.path / "source-log.csv", [base_source(), profile])
        write_csv(
            self.fixture.path / "accounts.csv",
            [
                base_account(
                    "ACC-001",
                    source_ids="PROFILE-001",
                    recent_median_visible_engagement="100",
                    recent_max_visible_engagement="50",
                    outlier_multiple="0.5",
                )
            ],
        )
        write_csv(self.fixture.path / "posts.csv", [])
        write_csv(self.fixture.path / "topics.csv", [])
        result = self.run_validator()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid_baseline_order", result.stdout)

    def test_non_finite_performance_numbers_are_rejected(self) -> None:
        self.fixture.close()
        self.fixture = RunFixture(mode="discovery")
        profile = base_source("PROFILE-001")
        profile.update(
            {
                "source_layer": "creator_experience",
                "source_type": "creator_profile",
                "evidence_form": "profile",
                "evidence_grade": "C",
                "url": "https://example.com/account/acc-001",
            }
        )
        write_csv(self.fixture.path / "source-log.csv", [base_source(), profile])
        write_csv(
            self.fixture.path / "accounts.csv",
            [
                base_account(
                    "ACC-001",
                    source_ids="PROFILE-001",
                    recent_median_visible_engagement="nan",
                    recent_max_visible_engagement="inf",
                    outlier_multiple="nan",
                )
            ],
        )
        write_csv(
            self.fixture.path / "posts.csv",
            [base_post("POST-001", "ACC-001", account_baseline_multiple="inf")],
        )
        write_csv(self.fixture.path / "topics.csv", [])
        result = self.run_validator("--strict")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("accounts.csv:2", result.stdout)
        self.assertIn("posts.csv:2", result.stdout)
        self.assertIn("invalid_number", result.stdout)

    def test_unconfirmed_eligibility_blocks_active_commercial_channel(self) -> None:
        write_csv(
            self.fixture.path / "sku-registry.csv",
            [
                {
                    "eligibility_id": "SKU-XHS-SHOP",
                    "sku_id": "SKU-001",
                    "sku_name": "具体商品",
                    "platform": "xiaohongshu",
                    "account_scope": "acct-xhs-001",
                    "surface": "shop",
                    "status": "needs_platform_confirmation",
                    "evidence_ids": "OFF-001",
                    "platform_ticket": "",
                    "verified_at": "",
                    "expires_at": "",
                    "material_limits": "",
                    "qualification_requirements": "",
                    "notes": "",
                }
            ],
        )
        write_csv(self.fixture.path / "offer-registry.csv", [])
        channel = {key: "" for key in HEADERS["acquisition-channels.csv"]}
        channel.update(
            {
                "channel_id": "CH-001",
                "direction": "xhs_to_native_conversion",
                "platform": "xiaohongshu",
                "account_scope": "acct-xhs-001",
                "audience_state": "有购买意图",
                "channel_role": "conversion",
                "native_format": "carousel",
                "source_asset_id": "SERIES-001",
                "public_identity": "品牌身份公开",
                "eligibility_ids": "SKU-XHS-SHOP",
                "surfaces": "shop",
                "permitted_cta": "使用站内商品组件",
                "prohibited_cta": "站外暗号",
                "landing_asset": "shop",
                "primary_metric": "approved_component_click",
                "metric_availability": "available",
                "data_source": "platform_backend",
                "event_definition": "经审组件有效点击",
                "diagnostic_metrics": "refund;complaint",
                "attribution_method": "platform_native",
                "attribution_level": "platform_native",
                "baseline_window": "volume_based",
                "test_window": "volume_based",
                "minimum_events": "30",
                "decision_rule": "达到30个事件后比较",
                "compliance_scope": "shop",
                "evidence_ids": "OFF-001",
                "confidence": "medium",
                "owner": "owner",
                "status": "active",
            }
        )
        write_csv(self.fixture.path / "acquisition-channels.csv", [channel])
        result = self.run_validator()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("eligibility_not_approved", result.stdout)

    def test_registry_evidence_must_resolve(self) -> None:
        write_csv(
            self.fixture.path / "sku-registry.csv",
            [
                {
                    "eligibility_id": "SKU-XHS-SHOP",
                    "sku_id": "SKU-001",
                    "sku_name": "具体商品",
                    "platform": "xiaohongshu",
                    "account_scope": "acct-xhs-001",
                    "surface": "shop",
                    "status": "needs_platform_confirmation",
                    "evidence_ids": "OFF-MISSING",
                    "platform_ticket": "",
                    "verified_at": "",
                    "expires_at": "",
                    "material_limits": "",
                    "qualification_requirements": "",
                    "notes": "",
                }
            ],
        )
        result = self.run_validator()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("dangling_reference", result.stdout)

    def test_channel_surface_must_match_registry_surface(self) -> None:
        write_csv(
            self.fixture.path / "sku-registry.csv",
            [
                {
                    "eligibility_id": "SKU-XHS-SHOP",
                    "sku_id": "SKU-001",
                    "sku_name": "具体商品",
                    "platform": "xiaohongshu",
                    "surface": "shop",
                    "status": "confirmed",
                    "evidence_ids": "OFF-001",
                    "platform_ticket": "TICKET-1",
                    "verified_at": "2026-07-16",
                    "expires_at": "2026-08-16",
                    "material_limits": "按工单",
                    "qualification_requirements": "按工单",
                    "notes": "",
                }
            ],
        )
        write_csv(self.fixture.path / "offer-registry.csv", [])
        channel = {key: "x" for key in HEADERS["acquisition-channels.csv"]}
        channel.update(
            {
                "channel_id": "CH-001",
                "direction": "xhs_to_native_conversion",
                "platform": "xiaohongshu",
                "account_scope": "acct-xhs-001",
                "eligibility_ids": "SKU-XHS-SHOP",
                "surfaces": "ads",
                "permitted_cta": "使用站内广告",
                "attribution_level": "platform_native",
                "status": "active",
            }
        )
        write_csv(self.fixture.path / "acquisition-channels.csv", [channel])
        result = self.run_validator()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("surface_mismatch", result.stdout)

    def test_channel_rejects_cross_platform_and_expired_eligibility(self) -> None:
        write_csv(
            self.fixture.path / "sku-registry.csv",
            [
                {
                    "eligibility_id": "SKU-OTHER-SHOP",
                    "sku_id": "SKU-001",
                    "sku_name": "具体商品",
                    "platform": "douyin",
                    "account_scope": "acct-other-001",
                    "surface": "shop",
                    "status": "confirmed",
                    "evidence_ids": "OFF-001",
                    "platform_ticket": "TICKET-OLD",
                    "verified_at": "2020-01-01",
                    "expires_at": "2020-02-01",
                    "material_limits": "按旧工单",
                    "qualification_requirements": "按旧工单",
                    "notes": "",
                }
            ],
        )
        write_csv(self.fixture.path / "offer-registry.csv", [])
        channel = {key: "x" for key in HEADERS["acquisition-channels.csv"]}
        channel.update(
            {
                "channel_id": "CH-001",
                "direction": "xhs_to_native_conversion",
                "platform": "xiaohongshu",
                "account_scope": "acct-xhs-001",
                "eligibility_ids": "SKU-OTHER-SHOP",
                "surfaces": "shop",
                "permitted_cta": "使用站内商品组件",
                "attribution_level": "platform_native",
                "evidence_ids": "OFF-001",
                "status": "active",
            }
        )
        write_csv(self.fixture.path / "acquisition-channels.csv", [channel])
        result = self.run_validator()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("platform_mismatch", result.stdout)
        self.assertIn("account_scope_mismatch", result.stdout)
        self.assertIn("expired_eligibility", result.stdout)

    def test_approved_eligibility_cannot_be_unscoped_or_stale(self) -> None:
        write_csv(
            self.fixture.path / "sku-registry.csv",
            [
                {
                    "eligibility_id": "SKU-XHS-SHOP",
                    "sku_id": "SKU-001",
                    "sku_name": "具体商品",
                    "platform": "xiaohongshu",
                    "account_scope": "unassigned",
                    "surface": "shop",
                    "status": "confirmed",
                    "evidence_ids": "OFF-001",
                    "platform_ticket": "",
                    "verified_at": "2020-01-01",
                    "expires_at": "",
                    "material_limits": "按当前规则",
                    "qualification_requirements": "待绑定账号",
                    "notes": "",
                }
            ],
        )
        result = self.run_validator()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unscoped_eligibility", result.stdout)
        self.assertIn("stale_eligibility", result.stdout)

    def test_xhs_direction_requires_xhs_and_specific_scopes(self) -> None:
        def write_case(platform: str, account_scope: str, surface: str) -> None:
            write_csv(
                self.fixture.path / "sku-registry.csv",
                [
                    {
                        "eligibility_id": "SKU-SCOPE",
                        "sku_id": "SKU-001",
                        "sku_name": "具体商品",
                        "platform": platform,
                        "account_scope": account_scope,
                        "surface": surface,
                        "status": "confirmed",
                        "evidence_ids": "OFF-001",
                        "platform_ticket": "TICKET-1",
                        "verified_at": "2026-07-16",
                        "expires_at": "2026-08-16",
                        "material_limits": "按工单",
                        "qualification_requirements": "按工单",
                        "notes": "",
                    }
                ],
            )
            write_csv(self.fixture.path / "offer-registry.csv", [])
            channel = {key: "x" for key in HEADERS["acquisition-channels.csv"]}
            channel.update(
                {
                    "channel_id": "CH-001",
                    "direction": "xhs_to_native_conversion",
                    "platform": platform,
                    "account_scope": account_scope,
                    "eligibility_ids": "SKU-SCOPE",
                    "surfaces": surface,
                    "permitted_cta": "使用站内商品组件",
                    "attribution_level": "platform_native",
                    "evidence_ids": "OFF-001",
                    "status": "active",
                }
            )
            write_csv(self.fixture.path / "acquisition-channels.csv", [channel])

        write_case("douyin", "acct-dy-001", "shop")
        wrong_platform = self.run_validator()
        self.assertNotEqual(wrong_platform.returncode, 0)
        self.assertIn("direction_platform_mismatch", wrong_platform.stdout)

        write_case("all_platforms", "all_accounts", "all_surfaces")
        generic_scope = self.run_validator()
        self.assertNotEqual(generic_scope.returncode, 0)
        self.assertIn("unscoped_eligibility", generic_scope.stdout)

    def test_draft_mode_requires_complete_draft_contract(self) -> None:
        self.fixture.close()
        self.fixture = RunFixture(mode="draft")
        write_csv(self.fixture.path / "topics.csv", [])
        drafts = self.fixture.path / "drafts"
        drafts.mkdir()
        (drafts / "bad.md").write_text(
            "---\ndraft_id: D-001\ntopic_id: T-001\n---\n\n## 成稿\n只有正文。\n",
            encoding="utf-8",
        )
        result = self.run_validator()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("draft_contract", result.stdout)

    def test_draft_frontmatter_requires_eligibility_and_surface_keys(self) -> None:
        self.fixture.close()
        self.fixture = RunFixture(mode="draft")
        topic = {key: "" for key in HEADERS["topics.csv"]}
        topic.update(
            {
                "topic_id": "TOPIC-001",
                "topic": "有证据的测试选题",
                "primary_job": "search_capture",
                "target_audience": "成年用户",
                "specific_scenario": "具体场景",
                "core_promise_or_tension": "提供判断方法",
                "evidence_ids": "OFF-001",
                "lifecycle": "evergreen_search",
                "format": "carousel",
                "measurement_plan": "按本账号基线判断",
                "status": "experimental",
                "last_seen_at": "2026-07-16",
            }
        )
        write_csv(self.fixture.path / "topics.csv", [topic])
        drafts = self.fixture.path / "drafts"
        drafts.mkdir()
        headings = "\n\n".join(
            f"## {heading}\n内容" for heading in sorted(
                {
                    "证据与目标用户",
                    "标题版本",
                    "封面版本",
                    "成稿",
                    "关键词与话题",
                    "事实与证明",
                    "合规审校",
                    "创意审校",
                    "观测计划",
                }
            )
        )
        (drafts / "missing-keys.md").write_text(
            textwrap.dedent(
                """\
                ---
                draft_id: DRAFT-001
                topic_id: TOPIC-001
                platform: xiaohongshu
                primary_job: search_capture
                lifecycle: evergreen_search
                truth_label: 事实科普
                answer_location: 正文
                cta_type: none
                status: needs_review
                ---

                """
            )
            + headings
            + "\n",
            encoding="utf-8",
        )
        result = self.run_validator()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("eligibility_ids", result.stdout)
        self.assertIn("surfaces", result.stdout)

    def test_complete_draft_rejects_empty_metadata_and_sections(self) -> None:
        self.fixture.close()
        self.fixture = RunFixture(mode="draft")
        self.fixture.set_run_field("status", "complete")
        topic = {key: "" for key in HEADERS["topics.csv"]}
        topic.update(
            {
                "topic_id": "TOPIC-001",
                "topic": "测试选题",
                "primary_job": "search_capture",
                "target_audience": "成年用户",
                "specific_scenario": "具体场景",
                "core_promise_or_tension": "提供判断",
                "evidence_ids": "OFF-001",
                "lifecycle": "evergreen_search",
                "format": "carousel",
                "measurement_plan": "按基线判断",
                "status": "experimental",
                "last_seen_at": "2026-07-16",
            }
        )
        write_csv(self.fixture.path / "topics.csv", [topic])
        drafts = self.fixture.path / "drafts"
        drafts.mkdir()
        metadata = "\n".join(f"{key}: \"\"" for key in sorted(
            {
                "draft_id",
                "topic_id",
                "platform",
                "primary_job",
                "lifecycle",
                "truth_label",
                "answer_location",
                "cta_type",
                "eligibility_ids",
                "surfaces",
                "status",
            }
        ))
        headings = "\n\n".join(
            f"## {heading}\n" for heading in sorted(
                {
                    "证据与目标用户",
                    "标题版本",
                    "封面版本",
                    "成稿",
                    "关键词与话题",
                    "事实与证明",
                    "合规审校",
                    "创意审校",
                    "观测计划",
                }
            )
        )
        (drafts / "empty.md").write_text(
            f"---\n{metadata}\n---\n\n{headings}\n",
            encoding="utf-8",
        )
        result = self.run_validator("--strict")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("empty_draft_field", result.stdout)
        self.assertIn("empty_draft_section", result.stdout)

    def test_draft_rejects_cross_platform_and_account_eligibility(self) -> None:
        self.fixture.close()
        self.fixture = RunFixture(mode="draft")
        topic = {key: "" for key in HEADERS["topics.csv"]}
        topic.update(
            {
                "topic_id": "TOPIC-001",
                "topic": "测试选题",
                "primary_job": "commercial_conversion",
                "target_audience": "成年用户",
                "specific_scenario": "具体选择场景",
                "core_promise_or_tension": "给出适用边界",
                "evidence_ids": "OFF-001",
                "lifecycle": "evergreen_search",
                "format": "carousel",
                "measurement_plan": "使用平台原生指标",
                "status": "experimental",
                "last_seen_at": "2026-07-16",
            }
        )
        write_csv(self.fixture.path / "topics.csv", [topic])
        write_csv(
            self.fixture.path / "sku-registry.csv",
            [
                {
                    "eligibility_id": "SKU-OTHER-SHOP",
                    "sku_id": "SKU-001",
                    "sku_name": "具体商品",
                    "platform": "douyin",
                    "account_scope": "acct-other-001",
                    "surface": "shop",
                    "status": "confirmed",
                    "evidence_ids": "OFF-001",
                    "platform_ticket": "TICKET-OLD",
                    "verified_at": "2020-01-01",
                    "expires_at": "2020-02-01",
                    "material_limits": "按旧工单",
                    "qualification_requirements": "按旧工单",
                    "notes": "",
                }
            ],
        )
        write_csv(self.fixture.path / "offer-registry.csv", [])
        drafts = self.fixture.path / "drafts"
        drafts.mkdir()
        headings = "\n\n".join(
            f"## {heading}\n内容" for heading in sorted(
                {
                    "证据与目标用户",
                    "标题版本",
                    "封面版本",
                    "成稿",
                    "关键词与话题",
                    "事实与证明",
                    "合规审校",
                    "创意审校",
                    "观测计划",
                }
            )
        )
        (drafts / "cross-platform.md").write_text(
            textwrap.dedent(
                """\
                ---
                draft_id: DRAFT-001
                topic_id: TOPIC-001
                platform: xiaohongshu
                account_scope: acct-xhs-001
                primary_job: commercial_conversion
                lifecycle: evergreen_search
                truth_label: 事实科普
                answer_location: 正文
                cta_type: product_component
                eligibility_ids: SKU-OTHER-SHOP
                surfaces: shop
                status: needs_review
                ---

                """
            )
            + headings
            + "\n",
            encoding="utf-8",
        )
        result = self.run_validator()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("platform_mismatch", result.stdout)
        self.assertIn("account_scope_mismatch", result.stdout)

    def test_truth_label_and_commercial_disclosure_are_separate_contracts(self) -> None:
        self.fixture.close()
        self.fixture = RunFixture(mode="draft")
        user_source = base_source("USER-001")
        user_source.update(
            {
                "source_layer": "creator_experience",
                "source_type": "interview",
                "title": "经同意的用户访谈",
                "evidence_form": "interview",
                "evidence_grade": "C",
            }
        )
        write_csv(self.fixture.path / "source-log.csv", [base_source(), user_source])
        topic = {key: "" for key in HEADERS["topics.csv"]}
        topic.update(
            {
                "topic_id": "TOPIC-001",
                "topic": "有需求样本的选题",
                "primary_job": "relationship_building",
                "target_audience": "成年用户",
                "specific_scenario": "具体场景",
                "core_promise_or_tension": "提供边界判断",
                "evidence_ids": "USER-001",
                "lifecycle": "evergreen_search",
                "format": "carousel",
                "measurement_plan": "按本账号基线判断",
                "status": "experimental",
                "last_seen_at": "2026-07-16",
            }
        )
        write_csv(self.fixture.path / "topics.csv", [topic])
        drafts = self.fixture.path / "drafts"
        drafts.mkdir()
        headings = "\n\n".join(
            f"## {heading}\n内容" for heading in sorted(
                {
                    "证据与目标用户",
                    "标题版本",
                    "封面版本",
                    "成稿",
                    "关键词与话题",
                    "事实与证明",
                    "CTA 与披露",
                    "合规审校",
                    "创意审校",
                    "观测计划",
                }
            )
        )
        (drafts / "bad-truth.md").write_text(
            textwrap.dedent(
                """\
                ---
                draft_id: DRAFT-001
                topic_id: TOPIC-001
                platform: xiaohongshu
                account_scope: none
                primary_job: relationship_building
                lifecycle: evergreen_search
                truth_label: 品牌合作/广告
                commercial_relationship: sponsored
                disclosure_text: ""
                disclosure_location: ""
                answer_location: 正文
                cta_type: none
                eligibility_ids: ""
                surfaces: ""
                status: needs_review
                ---

                """
            )
            + headings
            + "\n",
            encoding="utf-8",
        )
        result = self.run_validator()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid_truth_label", result.stdout)
        self.assertIn("missing_commercial_disclosure", result.stdout)

    def test_complete_noncommercial_draft_contract_passes(self) -> None:
        self.fixture.close()
        self.fixture = RunFixture(mode="draft")
        self.fixture.set_run_field("status", "complete")
        user_source = base_source("USER-001")
        user_source.update(
            {
                "source_layer": "creator_experience",
                "source_type": "interview",
                "title": "经同意的用户访谈",
                "evidence_form": "interview",
                "evidence_grade": "C",
            }
        )
        write_csv(self.fixture.path / "source-log.csv", [base_source(), user_source])
        topic = {key: "" for key in HEADERS["topics.csv"]}
        topic.update(
            {
                "topic_id": "TOPIC-001",
                "topic": "有需求样本的选题",
                "primary_job": "relationship_building",
                "target_audience": "成年用户",
                "specific_scenario": "具体场景",
                "core_promise_or_tension": "提供边界判断",
                "evidence_ids": "USER-001",
                "lifecycle": "evergreen_search",
                "format": "carousel",
                "measurement_plan": "按本账号基线判断",
                "status": "experimental",
                "last_seen_at": "2026-07-16",
            }
        )
        write_csv(self.fixture.path / "topics.csv", [topic])
        drafts = self.fixture.path / "drafts"
        drafts.mkdir()
        section_names = {
            "证据与目标用户",
            "标题版本",
            "封面版本",
            "成稿",
            "关键词与话题",
            "事实与证明",
            "CTA 与披露",
            "合规审校",
            "创意审校",
            "观测计划",
        }
        sections: list[str] = []
        for heading in sorted(section_names):
            if heading == "CTA 与披露":
                body = textwrap.dedent(
                    """\
                    cta_type: none
                    cta_copy: none
                    commercial_relationship: none
                    disclosure_text: none
                    disclosure_location: none
                    eligibility_ids: none
                    platform: xiaohongshu
                    account_scope: none
                    surfaces: none
                    """
                ).strip()
            elif heading in {"合规审校", "创意审校"}:
                body = "review_status: PASS\nfindings: none"
            else:
                body = f"已完成的{heading}内容。"
            sections.append(f"## {heading}\n{body}")
        headings = "\n\n".join(sections)
        draft_path = drafts / "valid.md"
        draft_path.write_text(
            textwrap.dedent(
                """\
                ---
                draft_id: DRAFT-001
                topic_id: TOPIC-001
                platform: xiaohongshu
                account_scope: none
                primary_job: relationship_building
                lifecycle: evergreen_search
                truth_label: factual_explainer
                truth_disclosure_text: 事实说明
                truth_disclosure_location: 首屏
                authorization_ids: none
                source_material_ids: none
                commercial_relationship: none
                disclosure_text: none
                disclosure_location: none
                answer_location: 正文
                cta_type: none
                eligibility_ids: ""
                surfaces: ""
                status: ready
                ---

                """
            )
            + "> 事实说明\n\n"
            + headings
            + "\n",
            encoding="utf-8",
        )
        result = self.run_validator("--strict")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        draft_path.write_text(
            draft_path.read_text(encoding="utf-8").replace(
                "cta_type: none\ncta_copy:",
                "cta_type: product_component\ncta_copy:",
            ),
            encoding="utf-8",
        )
        mismatch = self.run_validator("--strict")
        self.assertNotEqual(mismatch.returncode, 0)
        self.assertIn("cta_contract_mismatch", mismatch.stdout)
        draft_path.write_text(
            draft_path.read_text(encoding="utf-8")
            .replace("cta_type: product_component\ncta_copy:", "cta_type: none\ncta_copy:")
            .replace(
                "## 合规审校\nreview_status: PASS",
                "## 合规审校\nreview_status: PARTIAL",
            ),
            encoding="utf-8",
        )
        review_failure = self.run_validator("--strict")
        self.assertNotEqual(review_failure.returncode, 0)
        self.assertIn("review_not_passed", review_failure.stdout)
        draft_path.write_text(
            draft_path.read_text(encoding="utf-8")
            .replace(
                "## 合规审校\nreview_status: PARTIAL",
                "## 合规审校\nreview_status: PASS",
            )
            .replace("cta_copy: none", "cta_copy:"),
            encoding="utf-8",
        )
        empty_cta = self.run_validator("--strict")
        self.assertNotEqual(empty_cta.returncode, 0)
        self.assertIn("cta_contract_mismatch", empty_cta.stdout)

    def test_current_claim_requires_exact_scope_official_refresh_and_category_variants(self) -> None:
        stale_academic = base_source()
        stale_academic.update(
            {
                "source_layer": "academic",
                "source_type": "paper",
                "author_org": "研究机构",
                "collected_at": "2026-07-15",
                "evidence_form": "paper",
            }
        )
        write_csv(self.fixture.path / "source-log.csv", [stale_academic])
        write_csv(
            self.fixture.path / "claim-ledger.csv",
            [base_claim(category="current_rules", scope="全平台")],
        )
        result = self.run_validator("--strict")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid_claim_scope", result.stdout)
        self.assertIn("current_source_not_refreshed", result.stdout)
        self.assertIn("confirmed_source_conflict", result.stdout)

    def test_account_window_cannot_extend_beyond_collection_or_run(self) -> None:
        self.fixture.close()
        self.fixture = RunFixture(mode="discovery")
        write_csv(
            self.fixture.path / "accounts.csv",
            [
                base_account(
                    "ACC-001",
                    window_start="2026-07-01",
                    window_end="2030-01-01",
                    collected_at="2026-07-16",
                )
            ],
        )
        write_csv(self.fixture.path / "posts.csv", [])
        write_csv(self.fixture.path / "topics.csv", [])
        result = self.run_validator("--strict")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid_date_order", result.stdout)
        self.assertIn("future_date", result.stdout)

    def test_postmortem_substring_is_not_a_demand_sample(self) -> None:
        self.fixture.close()
        self.fixture = RunFixture(mode="discovery")
        source = base_source()
        source.update(
            {
                "source_layer": "industry",
                "source_type": "postmortem_report",
                "evidence_form": "report",
                "evidence_grade": "B",
            }
        )
        write_csv(self.fixture.path / "source-log.csv", [source])
        write_csv(self.fixture.path / "accounts.csv", [])
        write_csv(self.fixture.path / "posts.csv", [])
        write_csv(
            self.fixture.path / "topics.csv",
            [base_topic(evidence_ids="OFF-001", status="experimental")],
        )
        result = self.run_validator("--strict")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("insufficient_topic_sample", result.stdout)

    def test_active_topic_requires_profile_or_post_evidence_and_counterexample(self) -> None:
        self.fixture.close()
        self.fixture = RunFixture(mode="discovery")
        write_csv(
            self.fixture.path / "accounts.csv",
            [base_account("ACC-001"), base_account("ACC-002")],
        )
        write_csv(
            self.fixture.path / "posts.csv",
            [base_post("POST-001", "ACC-001"), base_post("POST-002", "ACC-002")],
        )
        write_csv(
            self.fixture.path / "topics.csv",
            [
                base_topic(
                    evidence_ids="POST-001;POST-002",
                    counterexamples="",
                    status="active",
                )
            ],
        )
        result = self.run_validator("--strict")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing_counterexample", result.stdout)
        self.assertIn("insufficient_independent_samples", result.stdout)

    def test_ambiguous_blocked_channel_status_cannot_bypass_eligibility(self) -> None:
        write_csv(
            self.fixture.path / "sku-registry.csv",
            [
                base_sku(
                    status="needs_platform_confirmation",
                    platform_ticket="",
                    verified_at="",
                    expires_at="",
                )
            ],
        )
        write_csv(self.fixture.path / "offer-registry.csv", [])
        write_csv(
            self.fixture.path / "acquisition-channels.csv",
            [base_channel(status="blocked_but_publishable")],
        )
        result = self.run_validator("--strict")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid_channel_status", result.stdout)
        self.assertIn("eligibility_not_approved", result.stdout)

    def test_approved_registry_requires_ticket_and_exact_source_asset_binding(self) -> None:
        write_csv(
            self.fixture.path / "sku-registry.csv",
            [base_sku(source_asset_id="ASSET-OTHER", platform_ticket="")],
        )
        write_csv(self.fixture.path / "offer-registry.csv", [])
        write_csv(
            self.fixture.path / "acquisition-channels.csv",
            [base_channel(source_asset_id="ASSET-CHANNEL")],
        )
        result = self.run_validator("--strict")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing_approval_record", result.stdout)
        self.assertIn("source_asset_mismatch", result.stdout)

    def test_commercial_cta_cannot_claim_no_commercial_relationship(self) -> None:
        self.fixture.close()
        self.fixture = RunFixture(mode="draft")
        self.fixture.set_run_field("status", "complete")
        user = base_source("USER-001")
        user.update(
            {
                "source_layer": "creator_experience",
                "source_type": "interview",
                "evidence_form": "interview",
                "evidence_grade": "C",
            }
        )
        write_csv(self.fixture.path / "source-log.csv", [base_source(), user])
        write_csv(
            self.fixture.path / "topics.csv",
            [base_topic(primary_job="commercial_conversion")],
        )
        write_csv(self.fixture.path / "sku-registry.csv", [base_sku()])
        write_csv(self.fixture.path / "offer-registry.csv", [])
        drafts = self.fixture.path / "drafts"
        drafts.mkdir()
        write_complete_draft(
            drafts / "commercial.md",
            account_scope="acct-xhs-001",
            primary_job="commercial_conversion",
            cta_type="product_component",
            eligibility_ids="SKU-XHS-SHOP",
            surfaces="shop",
            commercial_relationship="none",
            disclosure_text="none",
            disclosure_location="none",
        )
        result = self.run_validator("--strict")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("commercial_cta_without_relationship", result.stdout)

    def test_duplicate_review_section_cannot_hide_a_later_failure(self) -> None:
        self.fixture.close()
        self.fixture = RunFixture(mode="draft")
        self.fixture.set_run_field("status", "complete")
        user = base_source("USER-001")
        user.update(
            {
                "source_layer": "creator_experience",
                "source_type": "interview",
                "evidence_form": "interview",
                "evidence_grade": "C",
            }
        )
        write_csv(self.fixture.path / "source-log.csv", [base_source(), user])
        write_csv(self.fixture.path / "topics.csv", [base_topic()])
        drafts = self.fixture.path / "drafts"
        drafts.mkdir()
        draft = drafts / "duplicate.md"
        write_complete_draft(draft)
        draft.write_text(
            draft.read_text(encoding="utf-8")
            + "\n## 合规审校\nreview_status: FAIL\nfindings: later failure\n",
            encoding="utf-8",
        )
        result = self.run_validator("--strict")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("duplicate_draft_section", result.stdout)

    def test_draft_contract_must_match_topic_job_and_lifecycle(self) -> None:
        self.fixture.close()
        self.fixture = RunFixture(mode="draft")
        self.fixture.set_run_field("status", "complete")
        user = base_source("USER-001")
        user.update(
            {
                "source_layer": "creator_experience",
                "source_type": "interview",
                "evidence_form": "interview",
                "evidence_grade": "C",
            }
        )
        write_csv(self.fixture.path / "source-log.csv", [base_source(), user])
        write_csv(
            self.fixture.path / "topics.csv",
            [base_topic(primary_job="search_capture", lifecycle="hot")],
        )
        drafts = self.fixture.path / "drafts"
        drafts.mkdir()
        write_complete_draft(
            drafts / "mismatch.md",
            primary_job="relationship_building",
            lifecycle="evergreen_search",
        )
        result = self.run_validator("--strict")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("draft_topic_mismatch", result.stdout)

    def test_authorized_truth_label_requires_current_permission_record(self) -> None:
        self.fixture.close()
        self.fixture = RunFixture(mode="draft")
        self.fixture.set_run_field("status", "complete")
        user = base_source("USER-001")
        user.update(
            {
                "source_layer": "creator_experience",
                "source_type": "interview",
                "evidence_form": "interview",
                "evidence_grade": "C",
            }
        )
        write_csv(self.fixture.path / "source-log.csv", [base_source(), user])
        write_csv(self.fixture.path / "topics.csv", [base_topic()])
        drafts = self.fixture.path / "drafts"
        drafts.mkdir()
        write_complete_draft(
            drafts / "unauthorized.md",
            truth_label="authorized_anonymized",
            authorization_ids="none",
        )
        result = self.run_validator("--strict")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("authorization_required", result.stdout)

    def test_other_person_first_person_material_requires_publish_permission(self) -> None:
        self.fixture.close()
        self.fixture = RunFixture(mode="draft")
        self.fixture.set_run_field("status", "complete")
        user = base_source("USER-001")
        user.update(
            {
                "source_layer": "creator_experience",
                "source_type": "interview",
                "evidence_form": "interview",
                "evidence_grade": "C",
            }
        )
        write_csv(self.fixture.path / "source-log.csv", [base_source(), user])
        write_csv(self.fixture.path / "topics.csv", [base_topic()])
        drafts = self.fixture.path / "drafts"
        drafts.mkdir()
        draft = drafts / "first-person-without-publish-permission.md"
        write_complete_draft(
            draft,
            truth_label="first_person_documented",
            truth_disclosure_text="本人亲历记录，涉及他人材料已授权",
            authorization_ids="AUTH-001",
            source_material_ids="CASE-001",
        )
        write_csv(
            self.fixture.path / "authorization-log.csv",
            [
                {
                    "authorization_id": "AUTH-001",
                    "subject_scope": "adult-subject-001",
                    "source_asset_id": "DRAFT-001",
                    "material_id": "CASE-001",
                    "material_sha256": "b" * 64,
                    "material_type": "chat_record",
                    "permission_scope": "cross_platform_attribution",
                    "commercial_use": "prohibited",
                    "anonymization_requirements": "移除可识别细节",
                    "granted_at": "2026-07-10",
                    "expires_at": "",
                    "withdrawal_process": "撤回后停止使用",
                    "evidence_locator": "private://consent/AUTH-001",
                    "verified_by": "editor-001",
                    "verified_at": "2026-07-16",
                    "status": "approved",
                    "authorized_output_sha256": asset_sha256(draft),
                }
            ],
        )
        result = self.run_validator("--strict")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("authorization_scope_mismatch", result.stdout)

    def test_first_person_disclosure_must_identify_the_author_as_subject(self) -> None:
        self.fixture.close()
        self.fixture = RunFixture(mode="draft")
        self.fixture.set_run_field("status", "complete")
        user = base_source("USER-001")
        user.update(
            {
                "source_layer": "creator_experience",
                "source_type": "interview",
                "evidence_form": "interview",
                "evidence_grade": "C",
            }
        )
        write_csv(self.fixture.path / "source-log.csv", [base_source(), user])
        write_csv(self.fixture.path / "topics.csv", [base_topic()])
        drafts = self.fixture.path / "drafts"
        drafts.mkdir()
        write_complete_draft(
            drafts / "ambiguous-first-person.md",
            truth_label="first_person_documented",
            truth_disclosure_text="真实记录",
            authorization_ids="self_only",
            source_material_ids="SELF-MATERIAL-001",
        )
        result = self.run_validator("--strict")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("truth_disclosure_missing", result.stdout)

    def test_composite_cases_require_distinct_source_materials(self) -> None:
        self.fixture.close()
        self.fixture = RunFixture(mode="draft")
        self.fixture.set_run_field("status", "complete")
        user = base_source("USER-001")
        user.update(
            {
                "source_layer": "creator_experience",
                "source_type": "interview",
                "evidence_form": "interview",
                "evidence_grade": "C",
            }
        )
        write_csv(self.fixture.path / "source-log.csv", [base_source(), user])
        write_csv(self.fixture.path / "topics.csv", [base_topic()])
        drafts = self.fixture.path / "drafts"
        drafts.mkdir()
        draft = drafts / "duplicate-case.md"
        write_complete_draft(
            draft,
            truth_label="composite_cases",
            truth_disclosure_text="由多个经授权案例合成",
            authorization_ids="AUTH-001;AUTH-002",
            source_material_ids="CASE-001",
        )
        output_hash = asset_sha256(draft)
        authorization_rows: list[dict[str, str]] = []
        for authorization_id in ("AUTH-001", "AUTH-002"):
            authorization_rows.append(
                {
                    "authorization_id": authorization_id,
                    "subject_scope": "controlled-case-set-001",
                    "source_asset_id": "DRAFT-001",
                    "material_id": "CASE-001",
                    "material_sha256": "b" * 64,
                    "material_type": "interview",
                    "permission_scope": "composite",
                    "commercial_use": "prohibited",
                    "anonymization_requirements": "移除所有可识别细节",
                    "granted_at": "2026-07-10",
                    "expires_at": "",
                    "withdrawal_process": "撤回后停止使用",
                    "evidence_locator": f"private://consent/{authorization_id}",
                    "verified_by": "editor-001",
                    "verified_at": "2026-07-16",
                    "status": "approved",
                    "authorized_output_sha256": output_hash,
                }
            )
        write_csv(
            self.fixture.path / "authorization-log.csv",
            authorization_rows,
        )
        result = self.run_validator("--strict")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("insufficient_distinct_cases", result.stdout)

    def test_composite_cases_reject_renamed_duplicate_material_hashes(self) -> None:
        self.fixture.close()
        self.fixture = RunFixture(mode="draft")
        self.fixture.set_run_field("status", "complete")
        user = base_source("USER-001")
        user.update(
            {
                "source_layer": "creator_experience",
                "source_type": "interview",
                "evidence_form": "interview",
                "evidence_grade": "C",
            }
        )
        write_csv(self.fixture.path / "source-log.csv", [base_source(), user])
        write_csv(self.fixture.path / "topics.csv", [base_topic()])
        drafts = self.fixture.path / "drafts"
        drafts.mkdir()
        draft = drafts / "renamed-duplicate-case.md"
        write_complete_draft(
            draft,
            truth_label="composite_cases",
            truth_disclosure_text="由多个经授权案例合成",
            authorization_ids="AUTH-001;AUTH-002",
            source_material_ids="CASE-001;CASE-002",
        )
        output_hash = asset_sha256(draft)
        rows: list[dict[str, str]] = []
        for index, authorization_id in enumerate(("AUTH-001", "AUTH-002"), start=1):
            rows.append(
                {
                    "authorization_id": authorization_id,
                    "subject_scope": f"adult-subject-{index:03d}",
                    "source_asset_id": "DRAFT-001",
                    "material_id": f"CASE-{index:03d}",
                    "material_sha256": "b" * 64,
                    "material_type": "interview",
                    "permission_scope": "composite",
                    "commercial_use": "prohibited",
                    "anonymization_requirements": "移除所有可识别细节",
                    "granted_at": "2026-07-10",
                    "expires_at": "",
                    "withdrawal_process": "撤回后停止使用",
                    "evidence_locator": f"private://consent/{authorization_id}",
                    "verified_by": "editor-001",
                    "verified_at": "2026-07-16",
                    "status": "approved",
                    "authorized_output_sha256": output_hash,
                }
            )
        write_csv(self.fixture.path / "authorization-log.csv", rows)
        result = self.run_validator("--strict")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("insufficient_distinct_cases", result.stdout)

    def test_two_distinct_authorized_cases_allow_composite(self) -> None:
        self.fixture.close()
        self.fixture = RunFixture(mode="draft")
        self.fixture.set_run_field("status", "complete")
        user = base_source("USER-001")
        user.update(
            {
                "source_layer": "creator_experience",
                "source_type": "interview",
                "evidence_form": "interview",
                "evidence_grade": "C",
            }
        )
        write_csv(self.fixture.path / "source-log.csv", [base_source(), user])
        write_csv(self.fixture.path / "topics.csv", [base_topic()])
        drafts = self.fixture.path / "drafts"
        drafts.mkdir()
        draft = drafts / "distinct-composite.md"
        write_complete_draft(
            draft,
            truth_label="composite_cases",
            truth_disclosure_text="由多个经授权案例合成",
            authorization_ids="AUTH-001;AUTH-002",
            source_material_ids="CASE-001;CASE-002",
        )
        output_hash = asset_sha256(draft)
        rows: list[dict[str, str]] = []
        for index, authorization_id in enumerate(("AUTH-001", "AUTH-002"), start=1):
            rows.append(
                {
                    "authorization_id": authorization_id,
                    "subject_scope": f"adult-subject-{index:03d}",
                    "source_asset_id": "DRAFT-001",
                    "material_id": f"CASE-{index:03d}",
                    "material_sha256": ("a" if index == 1 else "b") * 64,
                    "material_type": "interview",
                    "permission_scope": "composite",
                    "commercial_use": "prohibited",
                    "anonymization_requirements": "移除所有可识别细节",
                    "granted_at": "2026-07-10",
                    "expires_at": "",
                    "withdrawal_process": "撤回后停止使用",
                    "evidence_locator": f"private://consent/{authorization_id}",
                    "verified_by": "editor-001",
                    "verified_at": "2026-07-16",
                    "status": "approved",
                    "authorized_output_sha256": output_hash,
                }
            )
        write_csv(self.fixture.path / "authorization-log.csv", rows)
        result = self.run_validator("--strict")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_current_authorization_record_allows_anonymized_draft(self) -> None:
        self.fixture.close()
        self.fixture = RunFixture(mode="draft")
        self.fixture.set_run_field("status", "complete")
        user = base_source("USER-001")
        user.update(
            {
                "source_layer": "creator_experience",
                "source_type": "interview",
                "evidence_form": "interview",
                "evidence_grade": "C",
            }
        )
        write_csv(self.fixture.path / "source-log.csv", [base_source(), user])
        write_csv(self.fixture.path / "topics.csv", [base_topic()])
        write_csv(
            self.fixture.path / "authorization-log.csv",
            [
                {
                    "authorization_id": "AUTH-001",
                    "subject_scope": "adult-subject-001",
                    "source_asset_id": "DRAFT-001",
                    "material_id": "CASE-001",
                    "material_sha256": "b" * 64,
                    "material_type": "interview",
                    "permission_scope": "anonymized_publish",
                    "commercial_use": "prohibited",
                    "anonymization_requirements": "移除身份、位置、单位和可交叉识别细节",
                    "granted_at": "2026-07-10",
                    "expires_at": "",
                    "withdrawal_process": "收到撤回后停止发布并删除关联稿",
                    "evidence_locator": "private://consent/AUTH-001",
                    "verified_by": "editor-001",
                    "verified_at": "2026-07-16",
                    "status": "approved",
                    "authorized_output_sha256": "",
                }
            ],
        )
        drafts = self.fixture.path / "drafts"
        drafts.mkdir()
        draft = drafts / "authorized.md"
        write_complete_draft(
            draft,
            truth_label="authorized_anonymized",
            truth_disclosure_text="经授权匿名整理",
            authorization_ids="AUTH-001",
            source_material_ids="CASE-001",
        )
        authorization_path = self.fixture.path / "authorization-log.csv"
        with authorization_path.open("r", encoding="utf-8", newline="") as handle:
            authorization_rows = list(csv.DictReader(handle))
        authorization_rows[0]["authorized_output_sha256"] = asset_sha256(draft)
        write_csv(authorization_path, authorization_rows)
        result = self.run_validator("--strict")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_exact_approved_commercial_contract_passes(self) -> None:
        self.fixture.close()
        self.fixture = RunFixture(mode="draft")
        self.fixture.set_run_field("status", "complete")
        user = base_source("USER-001")
        user.update(
            {
                "source_layer": "creator_experience",
                "source_type": "interview",
                "evidence_form": "interview",
                "evidence_grade": "C",
            }
        )
        write_csv(
            self.fixture.path / "source-log.csv",
            [base_source(), user, approval_source(), approval_source("TICKET-OFFER-001")],
        )
        write_csv(
            self.fixture.path / "topics.csv",
            [base_topic(primary_job="commercial_conversion")],
        )
        drafts = self.fixture.path / "drafts"
        drafts.mkdir()
        draft = drafts / "approved.md"
        write_complete_draft(
            draft,
            account_scope="acct-xhs-001",
            primary_job="commercial_conversion",
            commercial_relationship="owned_product",
            disclosure_text="自有产品，利益关系已披露",
            disclosure_location="正文CTA前",
            cta_type="product_component",
            eligibility_ids="SKU-XHS-SHOP;OFFER-XHS-SHOP",
            surfaces="shop",
        )
        approved_hash = asset_sha256(draft)
        write_csv(
            self.fixture.path / "claim-ledger.csv",
            [
                base_claim(),
                qualification_claim(approved_hash),
                offer_qualification_claim(approved_hash),
            ],
        )
        write_csv(
            self.fixture.path / "sku-registry.csv",
            [base_sku(source_asset_sha256=approved_hash)],
        )
        write_csv(
            self.fixture.path / "offer-registry.csv",
            [base_offer(source_asset_sha256=approved_hash)],
        )
        result = self.run_validator("--strict")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_registry_cannot_self_confirm_with_rumor_and_arbitrary_ticket(self) -> None:
        rumor = base_source("RUM-001")
        rumor.update(
            {
                "source_layer": "rumor",
                "source_type": "forum_post",
                "evidence_form": "post",
                "evidence_grade": "D",
            }
        )
        write_csv(self.fixture.path / "source-log.csv", [base_source(), rumor])
        write_csv(
            self.fixture.path / "sku-registry.csv",
            [
                base_sku(
                    evidence_ids="RUM-001",
                    platform_ticket="anything",
                    qualification_claim_id="",
                    source_asset_sha256="not-a-hash",
                )
            ],
        )
        result = self.run_validator("--strict")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid_qualification_evidence", result.stdout)
        self.assertIn("invalid_source_asset_hash", result.stdout)

    def test_qualification_claim_cannot_release_a_different_sku(self) -> None:
        write_csv(
            self.fixture.path / "source-log.csv",
            [base_source(), approval_source()],
        )
        write_csv(
            self.fixture.path / "claim-ledger.csv",
            [base_claim(), qualification_claim("a" * 64)],
        )
        write_csv(
            self.fixture.path / "sku-registry.csv",
            [base_sku(sku_id="SKU-SWAPPED")],
        )
        result = self.run_validator("--strict")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid_qualification_evidence", result.stdout)

    def test_product_component_requires_both_sku_and_offer_eligibility(self) -> None:
        self.fixture.close()
        self.fixture = RunFixture(mode="draft")
        self.fixture.set_run_field("status", "complete")
        user = base_source("USER-001")
        user.update(
            {
                "source_layer": "creator_experience",
                "source_type": "interview",
                "evidence_form": "interview",
                "evidence_grade": "C",
            }
        )
        write_csv(self.fixture.path / "source-log.csv", [base_source(), user])
        write_csv(
            self.fixture.path / "topics.csv",
            [base_topic(primary_job="commercial_conversion")],
        )
        write_csv(
            self.fixture.path / "sku-registry.csv",
            [base_sku(status="needs_platform_confirmation")],
        )
        write_csv(self.fixture.path / "offer-registry.csv", [])
        drafts = self.fixture.path / "drafts"
        drafts.mkdir()
        write_complete_draft(
            drafts / "sku-only.md",
            account_scope="acct-xhs-001",
            primary_job="commercial_conversion",
            commercial_relationship="owned_product",
            disclosure_text="自有产品",
            disclosure_location="CTA前",
            cta_type="product_component",
            eligibility_ids="SKU-XHS-SHOP",
            surfaces="shop",
        )
        result = self.run_validator("--strict")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("eligibility_kind_mismatch", result.stdout)
        write_csv(self.fixture.path / "sku-registry.csv", [])
        write_csv(
            self.fixture.path / "offer-registry.csv",
            [base_offer(status="needs_platform_confirmation")],
        )
        write_complete_draft(
            drafts / "sku-only.md",
            account_scope="acct-xhs-001",
            primary_job="commercial_conversion",
            commercial_relationship="owned_product",
            disclosure_text="自有产品",
            disclosure_location="CTA前",
            cta_type="product_component",
            eligibility_ids="OFFER-XHS-SHOP",
            surfaces="shop",
        )
        offer_only = self.run_validator("--strict")
        self.assertNotEqual(offer_only.returncode, 0)
        self.assertIn("eligibility_kind_mismatch", offer_only.stdout)

    def test_fictional_truth_label_must_be_visible_in_first_screen(self) -> None:
        self.fixture.close()
        self.fixture = RunFixture(mode="draft")
        self.fixture.set_run_field("status", "complete")
        user = base_source("USER-001")
        user.update(
            {
                "source_layer": "creator_experience",
                "source_type": "interview",
                "evidence_form": "interview",
                "evidence_grade": "C",
            }
        )
        write_csv(self.fixture.path / "source-log.csv", [base_source(), user])
        write_csv(self.fixture.path / "topics.csv", [base_topic()])
        drafts = self.fixture.path / "drafts"
        drafts.mkdir()
        draft = drafts / "fiction.md"
        write_complete_draft(
            draft,
            truth_label="fictional_scenario",
            truth_disclosure_text="普通说明",
            truth_disclosure_location="正文末尾",
        )
        result = self.run_validator("--strict")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("truth_disclosure_missing", result.stdout)

    def test_fictional_disclosure_rejects_negated_or_real_story_claim(self) -> None:
        self.fixture.close()
        self.fixture = RunFixture(mode="draft")
        self.fixture.set_run_field("status", "complete")
        user = base_source("USER-001")
        user.update(
            {
                "source_layer": "creator_experience",
                "source_type": "interview",
                "evidence_form": "interview",
                "evidence_grade": "C",
            }
        )
        write_csv(self.fixture.path / "source-log.csv", [base_source(), user])
        write_csv(self.fixture.path / "topics.csv", [base_topic()])
        drafts = self.fixture.path / "drafts"
        drafts.mkdir()
        write_complete_draft(
            drafts / "negated-fiction.md",
            truth_label="fictional_scenario",
            truth_disclosure_text="这不是虚构或情境演绎，而是真人真实投稿",
            truth_disclosure_location="首屏",
        )
        result = self.run_validator("--strict")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("truth_disclosure_conflict", result.stdout)

    def test_truth_disclosure_inside_html_comment_is_not_visible(self) -> None:
        self.fixture.close()
        self.fixture = RunFixture(mode="draft")
        self.fixture.set_run_field("status", "complete")
        user = base_source("USER-001")
        user.update(
            {
                "source_layer": "creator_experience",
                "source_type": "interview",
                "evidence_form": "interview",
                "evidence_grade": "C",
            }
        )
        write_csv(self.fixture.path / "source-log.csv", [base_source(), user])
        write_csv(self.fixture.path / "topics.csv", [base_topic()])
        drafts = self.fixture.path / "drafts"
        drafts.mkdir()
        draft = drafts / "comment-hidden-fiction.md"
        disclosure = "本内容为明确虚构"
        write_complete_draft(
            draft,
            truth_label="fictional_scenario",
            truth_disclosure_text=disclosure,
            truth_disclosure_location="首屏",
        )
        draft.write_text(
            draft.read_text(encoding="utf-8").replace(
                f"> {disclosure}", f"<!-- {disclosure} -->"
            ),
            encoding="utf-8",
        )
        result = self.run_validator("--strict")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("truth_disclosure_missing", result.stdout)

    def test_truth_disclosure_in_image_alt_or_collapsed_details_is_not_visible(self) -> None:
        self.fixture.close()
        self.fixture = RunFixture(mode="draft")
        self.fixture.set_run_field("status", "complete")
        user = base_source("USER-001")
        user.update(
            {
                "source_layer": "creator_experience",
                "source_type": "interview",
                "evidence_form": "interview",
                "evidence_grade": "C",
            }
        )
        write_csv(self.fixture.path / "source-log.csv", [base_source(), user])
        write_csv(self.fixture.path / "topics.csv", [base_topic()])
        drafts = self.fixture.path / "drafts"
        drafts.mkdir()
        draft = drafts / "alt-hidden-fiction.md"
        disclosure = "本内容为明确虚构"
        write_complete_draft(
            draft,
            truth_label="fictional_scenario",
            truth_disclosure_text=disclosure,
            truth_disclosure_location="首屏",
        )
        draft.write_text(
            draft.read_text(encoding="utf-8").replace(
                f"> {disclosure}", f"![{disclosure}](cover.png)"
            ),
            encoding="utf-8",
        )
        result = self.run_validator("--strict")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("truth_disclosure_missing", result.stdout)
        write_complete_draft(
            draft,
            truth_label="fictional_scenario",
            truth_disclosure_text=disclosure,
            truth_disclosure_location="首屏",
        )
        draft.write_text(
            draft.read_text(encoding="utf-8").replace(
                f"> {disclosure}",
                f"<details><summary>展开</summary>{disclosure}</details>",
            ),
            encoding="utf-8",
        )
        collapsed = self.run_validator("--strict")
        self.assertNotEqual(collapsed.returncode, 0)
        self.assertIn("truth_disclosure_missing", collapsed.stdout)

    def test_commercial_disclosure_hidden_in_html_comment_is_rejected(self) -> None:
        self.fixture.close()
        self.fixture = RunFixture(mode="draft")
        self.fixture.set_run_field("status", "complete")
        user = base_source("USER-001")
        user.update(
            {
                "source_layer": "creator_experience",
                "source_type": "interview",
                "evidence_form": "interview",
                "evidence_grade": "C",
            }
        )
        write_csv(self.fixture.path / "source-log.csv", [base_source(), user])
        write_csv(self.fixture.path / "topics.csv", [base_topic()])
        drafts = self.fixture.path / "drafts"
        drafts.mkdir()
        draft = drafts / "hidden-commercial-disclosure.md"
        write_complete_draft(
            draft,
            commercial_relationship="sponsored",
            disclosure_text="品牌合作广告",
            disclosure_location="CTA前",
            cta_type="save",
        )
        text_value = draft.read_text(encoding="utf-8")
        text_value = text_value.replace(
            "品牌合作广告\n已完成且可审计的成稿内容。",
            "已完成且可审计的成稿内容。",
        )
        text_value = re.sub(
            r"(## CTA 与披露\n.*?)(?=\n\n## |\Z)",
            lambda match: f"<!--\n{match.group(1)}\n-->",
            text_value,
            flags=re.DOTALL,
        )
        draft.write_text(text_value, encoding="utf-8")
        result = self.run_validator("--strict")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing_commercial_disclosure", result.stdout)

    def test_commercial_disclosure_location_must_match_visible_position(self) -> None:
        self.fixture.close()
        self.fixture = RunFixture(mode="draft")
        self.fixture.set_run_field("status", "complete")
        user = base_source("USER-001")
        user.update(
            {
                "source_layer": "creator_experience",
                "source_type": "interview",
                "evidence_form": "interview",
                "evidence_grade": "C",
            }
        )
        write_csv(self.fixture.path / "source-log.csv", [base_source(), user])
        write_csv(self.fixture.path / "topics.csv", [base_topic()])
        drafts = self.fixture.path / "drafts"
        drafts.mkdir()
        draft = drafts / "late-first-screen-disclosure.md"
        write_complete_draft(
            draft,
            commercial_relationship="sponsored",
            disclosure_text="品牌合作广告",
            disclosure_location="首屏",
            cta_type="save",
        )
        text_value = draft.read_text(encoding="utf-8")
        first_visible = text_value.find("品牌合作广告", text_value.find("## 成稿"))
        self.assertGreaterEqual(first_visible, 0)
        text_value = (
            text_value[:first_visible]
            + ("正文" * 500)
            + "\n品牌合作广告"
            + text_value[first_visible + len("品牌合作广告") :]
        )
        draft.write_text(text_value, encoding="utf-8")
        result = self.run_validator("--strict")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing_commercial_disclosure", result.stdout)

    def test_sponsored_disclosure_cannot_deny_advertising_or_cooperation(self) -> None:
        self.fixture.close()
        self.fixture = RunFixture(mode="draft")
        self.fixture.set_run_field("status", "complete")
        user = base_source("USER-001")
        user.update(
            {
                "source_layer": "creator_experience",
                "source_type": "interview",
                "evidence_form": "interview",
                "evidence_grade": "C",
            }
        )
        write_csv(self.fixture.path / "source-log.csv", [base_source(), user])
        write_csv(self.fixture.path / "topics.csv", [base_topic()])
        drafts = self.fixture.path / "drafts"
        drafts.mkdir()
        write_complete_draft(
            drafts / "denied-sponsorship.md",
            commercial_relationship="sponsored",
            disclosure_text="这不是广告，也没有品牌合作",
            disclosure_location="首屏",
            cta_type="save",
        )
        result = self.run_validator("--strict")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("commercial_disclosure_conflict", result.stdout)

    def test_authorization_must_bind_exact_draft_and_source_material(self) -> None:
        self.fixture.close()
        self.fixture = RunFixture(mode="draft")
        self.fixture.set_run_field("status", "complete")
        user = base_source("USER-001")
        user.update(
            {
                "source_layer": "creator_experience",
                "source_type": "interview",
                "evidence_form": "interview",
                "evidence_grade": "C",
            }
        )
        write_csv(self.fixture.path / "source-log.csv", [base_source(), user])
        write_csv(self.fixture.path / "topics.csv", [base_topic()])
        write_csv(
            self.fixture.path / "authorization-log.csv",
            [
                {
                    "authorization_id": "AUTH-001",
                    "subject_scope": "adult-subject-001",
                    "source_asset_id": "DRAFT-OTHER",
                    "material_id": "CASE-001",
                    "material_sha256": "b" * 64,
                    "material_type": "interview",
                    "permission_scope": "anonymized_publish",
                    "commercial_use": "prohibited",
                    "anonymization_requirements": "移除可识别细节",
                    "granted_at": "2026-07-10",
                    "expires_at": "",
                    "withdrawal_process": "撤回后停止使用",
                    "evidence_locator": "private://consent/AUTH-001",
                    "verified_by": "editor-001",
                    "verified_at": "2026-07-16",
                    "status": "approved",
                    "authorized_output_sha256": "a" * 64,
                }
            ],
        )
        drafts = self.fixture.path / "drafts"
        drafts.mkdir()
        write_complete_draft(
            drafts / "wrong-material.md",
            truth_label="authorized_anonymized",
            truth_disclosure_text="经授权匿名整理",
            authorization_ids="AUTH-001",
            source_material_ids="CASE-999",
        )
        result = self.run_validator("--strict")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("authorization_asset_mismatch", result.stdout)
        self.assertIn("authorization_material_mismatch", result.stdout)

    def test_authorized_output_hash_prevents_post_consent_edit(self) -> None:
        self.fixture.close()
        self.fixture = RunFixture(mode="draft")
        self.fixture.set_run_field("status", "complete")
        user = base_source("USER-001")
        user.update(
            {
                "source_layer": "creator_experience",
                "source_type": "interview",
                "evidence_form": "interview",
                "evidence_grade": "C",
            }
        )
        write_csv(self.fixture.path / "source-log.csv", [base_source(), user])
        write_csv(self.fixture.path / "topics.csv", [base_topic()])
        drafts = self.fixture.path / "drafts"
        drafts.mkdir()
        draft = drafts / "authorized-edited.md"
        write_complete_draft(
            draft,
            truth_label="authorized_anonymized",
            truth_disclosure_text="经授权匿名整理",
            authorization_ids="AUTH-001",
            source_material_ids="CASE-001",
        )
        authorized_hash = asset_sha256(draft)
        write_csv(
            self.fixture.path / "authorization-log.csv",
            [
                {
                    "authorization_id": "AUTH-001",
                    "subject_scope": "adult-subject-001",
                    "source_asset_id": "DRAFT-001",
                    "material_id": "CASE-001",
                    "material_sha256": "b" * 64,
                    "material_type": "interview",
                    "permission_scope": "anonymized_publish",
                    "commercial_use": "prohibited",
                    "anonymization_requirements": "移除可识别细节",
                    "granted_at": "2026-07-10",
                    "expires_at": "",
                    "withdrawal_process": "撤回后停止使用",
                    "evidence_locator": "private://consent/AUTH-001",
                    "verified_by": "editor-001",
                    "verified_at": "2026-07-16",
                    "status": "approved",
                    "authorized_output_sha256": authorized_hash,
                }
            ],
        )
        draft.write_text(
            draft.read_text(encoding="utf-8").replace("已完成且可审计的成稿内容。", "未经再次授权的新情节。"),
            encoding="utf-8",
        )
        result = self.run_validator("--strict")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("authorization_output_mismatch", result.stdout)

    def test_runtime_category_variants_and_broad_scopes_are_rejected(self) -> None:
        source = base_source()
        source.update(
            {
                "source_layer": "academic",
                "source_type": "paper",
                "evidence_form": "paper",
                "collected_at": "2026-07-15",
            }
        )
        write_csv(self.fixture.path / "source-log.csv", [source])
        cases = (
            ("current_rule_v2", "小红书"),
            ("platform_rules_xhs", "all surfaces"),
            ("政策更新", "小红书全部入口"),
            ("privacy_update", "全账号"),
        )
        for category, scope in cases:
            with self.subTest(category=category, scope=scope):
                write_csv(
                    self.fixture.path / "claim-ledger.csv",
                    [
                        base_claim(
                            category=category,
                            scope=scope,
                            last_verified_at="2026-07-15",
                        )
                    ],
                )
                result = self.run_validator("--strict")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("invalid_claim_scope", result.stdout)
                self.assertIn("not_verified_this_run", result.stdout)

    def test_explicit_verification_class_controls_free_text_runtime_claims(self) -> None:
        source = base_source()
        source.update(
            {
                "source_layer": "academic",
                "source_type": "paper",
                "evidence_form": "paper",
                "collected_at": "2026-07-15",
            }
        )
        write_csv(self.fixture.path / "source-log.csv", [source])
        write_csv(
            self.fixture.path / "claim-ledger.csv",
            [
                base_claim(
                    category="平台要求",
                    scope="具体账号的商品组件入口",
                    verification_class="current_runtime",
                    last_verified_at="2026-07-15",
                )
            ],
        )
        result = self.run_validator("--strict")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not_verified_this_run", result.stdout)
        self.assertIn("confirmed_source_conflict", result.stdout)
        write_csv(
            self.fixture.path / "claim-ledger.csv",
            [base_claim(verification_class="")],
        )
        missing = self.run_validator("--strict")
        self.assertNotEqual(missing.returncode, 0)
        self.assertIn("verification_class", missing.stdout)

    def test_affirmative_current_platform_capability_cannot_use_experience_class(self) -> None:
        for claim_text in (
            "不能证明旧版不可用；小红书当前官方页面支持外跳组件。",
            "小红书现已开放官方外跳组件。",
        ):
            with self.subTest(claim_text=claim_text):
                write_csv(
                    self.fixture.path / "claim-ledger.csv",
                    [
                        base_claim(
                            category="audience_acquisition",
                            claim_text=claim_text,
                            scope="聚光帮助页的外跳组件入口",
                            verification_class="experience",
                        )
                    ],
                )
                result = self.run_validator("--strict")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("verification_class_conflict", result.stdout)

    def test_active_topic_rejects_reused_profile_source_and_fake_counterexample_id(self) -> None:
        self.fixture.close()
        self.fixture = RunFixture(mode="discovery")
        profile = base_source("PROFILE-001")
        profile.update(
            {
                "source_layer": "creator_experience",
                "source_type": "creator_profile",
                "evidence_form": "profile",
                "evidence_grade": "C",
                "url": "https://example.com/account/acc-001",
            }
        )
        write_csv(self.fixture.path / "source-log.csv", [base_source(), profile])
        write_csv(
            self.fixture.path / "accounts.csv",
            [
                base_account("ACC-001", source_ids="PROFILE-001"),
                base_account("ACC-002", source_ids="PROFILE-001"),
            ],
        )
        write_csv(
            self.fixture.path / "posts.csv",
            [base_post("POST-001", "ACC-001"), base_post("POST-002", "ACC-002")],
        )
        write_csv(
            self.fixture.path / "topics.csv",
            [
                base_topic(
                    status="active",
                    evidence_ids="POST-001;POST-002",
                    counterexamples="NOT-A-REAL-ID: invented",
                )
            ],
        )
        result = self.run_validator("--strict")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("account_source_mismatch", result.stdout)
        self.assertIn("invalid_counterexample_reference", result.stdout)
        self.assertIn("insufficient_independent_samples", result.stdout)

    def test_cross_platform_channel_rejects_multi_platform_and_unproven_user_link(self) -> None:
        channel = base_channel(
            direction="external_to_xhs",
            platform="知乎/抖音",
            account_scope="acct-external-001",
            permitted_cta="none",
            eligibility_ids="",
            surfaces="public_content",
            evidence_ids="OFF-001",
            attribution_level="user_level_with_consent",
            consent_ids="",
            status="active",
        )
        write_csv(self.fixture.path / "sku-registry.csv", [])
        write_csv(self.fixture.path / "offer-registry.csv", [])
        write_csv(self.fixture.path / "acquisition-channels.csv", [channel])
        result = self.run_validator("--strict")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unscoped_channel", result.stdout)
        self.assertIn("missing_consent_evidence", result.stdout)

    def test_active_external_jump_cannot_bypass_eligibility_with_no_cta(self) -> None:
        write_csv(self.fixture.path / "sku-registry.csv", [])
        write_csv(self.fixture.path / "offer-registry.csv", [])
        write_csv(
            self.fixture.path / "acquisition-channels.csv",
            [
                base_channel(
                    direction="xhs_to_approved_external",
                    platform="xiaohongshu",
                    account_scope="acct-xhs-001",
                    permitted_cta="none",
                    eligibility_ids="",
                    surfaces="approved_external_destination",
                    landing_asset="https://merchant.example/approved-destination",
                    status="active",
                )
            ],
        )
        result = self.run_validator("--strict")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("external_jump_not_approved", result.stdout)

    def test_active_external_jump_with_exact_offer_and_sku_approvals_passes(self) -> None:
        asset_hash = "a" * 64
        surface = "approved_external_destination"
        write_csv(
            self.fixture.path / "source-log.csv",
            [base_source(), approval_source(), approval_source("TICKET-OFFER-001")],
        )
        write_csv(
            self.fixture.path / "claim-ledger.csv",
            [
                base_claim(),
                qualification_claim(
                    asset_hash,
                    scope=(
                        "sku_id=SKU-001|platform=xiaohongshu|account_scope=acct-xhs-001|"
                        f"surface={surface}|source_asset_id=DRAFT-001|"
                        f"source_asset_sha256={asset_hash}"
                    ),
                ),
                offer_qualification_claim(
                    asset_hash,
                    scope=(
                        "offer_id=OFFER-RETAIL-001|offer_type=product_sale|"
                        "platform=xiaohongshu|account_scope=acct-xhs-001|"
                        f"surface={surface}|source_asset_id=DRAFT-001|"
                        f"source_asset_sha256={asset_hash}"
                    ),
                ),
            ],
        )
        write_csv(
            self.fixture.path / "sku-registry.csv",
            [base_sku(surface=surface, source_asset_sha256=asset_hash)],
        )
        write_csv(
            self.fixture.path / "offer-registry.csv",
            [base_offer(surface=surface, source_asset_sha256=asset_hash)],
        )
        write_csv(
            self.fixture.path / "acquisition-channels.csv",
            [
                base_channel(
                    direction="xhs_to_approved_external",
                    surfaces=surface,
                    eligibility_ids="SKU-XHS-SHOP;OFFER-XHS-SHOP",
                    permitted_cta="none",
                    landing_asset="https://merchant.example/approved-destination",
                    status="active",
                )
            ],
        )
        result = self.run_validator("--strict")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_active_topic_with_bound_profiles_and_real_counterexample_passes(self) -> None:
        self.fixture.close()
        self.fixture = RunFixture(mode="discovery")
        profile_rows: list[dict[str, str]] = []
        for source_id, account_id in (("PROFILE-001", "ACC-001"), ("PROFILE-002", "ACC-002")):
            profile = base_source(source_id)
            profile.update(
                {
                    "source_layer": "creator_experience",
                    "source_type": "creator_profile",
                    "evidence_form": "profile",
                    "evidence_grade": "C",
                    "url": f"https://example.com/account/{account_id.lower()}",
                }
            )
            profile_rows.append(profile)
        counter = base_source("COUNTER-001")
        counter.update(
            {
                "source_layer": "creator_experience",
                "source_type": "interview",
                "evidence_form": "interview",
                "evidence_grade": "C",
            }
        )
        write_csv(
            self.fixture.path / "source-log.csv",
            [base_source(), *profile_rows, counter],
        )
        write_csv(
            self.fixture.path / "accounts.csv",
            [
                base_account("ACC-001", source_ids="PROFILE-001"),
                base_account("ACC-002", source_ids="PROFILE-002"),
            ],
        )
        write_csv(
            self.fixture.path / "posts.csv",
            [base_post("POST-001", "ACC-001"), base_post("POST-002", "ACC-002")],
        )
        write_csv(
            self.fixture.path / "topics.csv",
            [
                base_topic(
                    status="active",
                    evidence_ids="POST-001;POST-002",
                    counterexamples="COUNTER-001：只支持相邻场景，不外推",
                )
            ],
        )
        result = self.run_validator("--strict")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_active_topic_counterexample_cannot_reuse_supporting_evidence(self) -> None:
        self.fixture.close()
        self.fixture = RunFixture(mode="discovery")
        profiles: list[dict[str, str]] = []
        for source_id, account_id in (("PROFILE-001", "ACC-001"), ("PROFILE-002", "ACC-002")):
            profile = base_source(source_id)
            profile.update(
                {
                    "source_layer": "creator_experience",
                    "source_type": "creator_profile",
                    "evidence_form": "profile",
                    "evidence_grade": "C",
                    "url": f"https://example.com/account/{account_id.lower()}",
                }
            )
            profiles.append(profile)
        write_csv(self.fixture.path / "source-log.csv", [base_source(), *profiles])
        write_csv(
            self.fixture.path / "accounts.csv",
            [
                base_account("ACC-001", source_ids="PROFILE-001"),
                base_account("ACC-002", source_ids="PROFILE-002"),
            ],
        )
        write_csv(
            self.fixture.path / "posts.csv",
            [base_post("POST-001", "ACC-001"), base_post("POST-002", "ACC-002")],
        )
        write_csv(
            self.fixture.path / "topics.csv",
            [
                base_topic(
                    status="active",
                    evidence_ids="POST-001;POST-002",
                    counterexamples="POST-001：同一正样本也被写成反例",
                )
            ],
        )
        result = self.run_validator("--strict")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("counterexample_evidence_overlap", result.stdout)

    def test_user_level_attribution_with_bound_current_consent_passes(self) -> None:
        write_csv(
            self.fixture.path / "authorization-log.csv",
            [
                {
                    "authorization_id": "AUTH-CONSENT-001",
                    "subject_scope": "consented-cohort-001",
                    "source_asset_id": "DRAFT-001",
                    "material_id": "LINKING-PROTOCOL-001",
                    "material_sha256": "b" * 64,
                    "material_type": "other",
                    "permission_scope": "cross_platform_attribution",
                    "commercial_use": "approved",
                    "anonymization_requirements": "仅使用最小化的经同意链接标识",
                    "granted_at": "2026-07-10",
                    "expires_at": "",
                    "withdrawal_process": "撤回后删除链接标识并停止归因",
                    "evidence_locator": "private://consent/AUTH-CONSENT-001",
                    "verified_by": "privacy-owner-001",
                    "verified_at": "2026-07-16",
                    "status": "approved",
                    "authorized_output_sha256": "a" * 64,
                }
            ],
        )
        write_csv(self.fixture.path / "sku-registry.csv", [])
        write_csv(self.fixture.path / "offer-registry.csv", [])
        write_csv(
            self.fixture.path / "acquisition-channels.csv",
            [
                base_channel(
                    direction="external_to_xhs",
                    platform="知乎",
                    account_scope="acct-zhihu-001",
                    permitted_cta="none",
                    eligibility_ids="",
                    surfaces="public_content",
                    attribution_level="user_level_with_consent",
                    consent_ids="AUTH-CONSENT-001",
                )
            ],
        )
        result = self.run_validator("--strict")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class StyleContractFastPathTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = RunFixture(mode="draft")
        demand_source = base_source("USER-001")
        demand_source.update(
            {
                "source_layer": "creator_experience",
                "source_type": "user_material",
                "title": "用户需求材料",
                "author_org": "用户授权材料",
                "evidence_form": "user_material",
                "evidence_grade": "C",
            }
        )
        write_csv(
            self.fixture.path / "source-log.csv",
            [base_source(), demand_source],
        )
        for field, value in {
            "run_contract_version": "2",
            "business_objective": "traffic_first",
            "objective_primary_job": "feed_stop",
            "performance_visibility_scope": "public_proxy",
            "style_requirement": "both",
            "style_library_path": "../_style_library/style-library.sqlite",
            "style_taxonomy_version": "2",
        }.items():
            self.fixture.set_run_field(field, value)
        write_csv(
            self.fixture.path / "topics.csv",
            [base_topic(primary_job="feed_stop")],
        )
        drafts = self.fixture.path / "drafts"
        drafts.mkdir()
        self.draft = drafts / "v2.md"

    def tearDown(self) -> None:
        self.fixture.close()

    def run_validator(self, *extra: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(VALIDATOR), str(self.fixture.path), *extra],
            capture_output=True,
            text=True,
            check=False,
        )

    def write_v2_draft(self, **overrides: str) -> None:
        meta = v2_style_meta(**overrides)
        primary_job = meta.pop("primary_job", meta["style_query_primary_job"])
        write_complete_draft(
            self.draft,
            primary_job=primary_job,
            status=meta.pop("status", "needs_review"),
            **meta,
        )

    def test_needs_style_research_is_a_valid_nonready_v2_stop(self) -> None:
        self.write_v2_draft()
        result = self.run_validator()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_v2_rejects_uncontrolled_objective_job_and_carrier(self) -> None:
        self.fixture.set_run_field("business_objective", "go_viral")
        self.write_v2_draft(
            business_objective="go_viral",
            style_query_primary_job="recommendation_reach",
            style_query_carrier="viral_ppt",
            traffic_stage="viral_loop",
            primary_job="recommendation_reach",
        )
        result = self.run_validator()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid_v2_style_enum", result.stdout)

    def test_ready_style_draft_cannot_stop_at_needs_style_research(self) -> None:
        self.write_v2_draft(status="ready")
        result = self.run_validator()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("style_not_grounded", result.stdout)

    def test_starter_binding_is_unavailable_while_release_gate_is_incomplete(self) -> None:
        self.write_v2_draft(style_binding_status="starter_applied")
        result = self.run_validator()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("starter_gate_incomplete", result.stdout)

    def test_public_proxy_can_only_report_not_applicable_traffic_verdict(self) -> None:
        self.write_v2_draft(traffic_verdict="win")
        result = self.run_validator()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("public_proxy_traffic_verdict", result.stdout)

    def test_traffic_win_requires_first_party_impressions_or_reach(self) -> None:
        self.fixture.set_run_field("performance_visibility_scope", "first_party_analytics")
        self.write_v2_draft(
            performance_visibility_scope="first_party_analytics",
            traffic_primary_metric="feed_ctr",
            traffic_verdict="win",
        )
        result = self.run_validator()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("traffic_primary_metric", result.stdout)

    def test_invariant_high_low_feature_cannot_be_performance_rule(self) -> None:
        self.write_v2_draft(
            performance_rule_claim_kind="contrastive_performance_hypothesis",
            style_feature_contrast="invariant",
            performance_evidence_scope="public_proxy_association",
        )
        result = self.run_validator()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("shared_feature_not_performance", result.stdout)

    def test_series_constant_and_task_fit_must_remain_nonperformance(self) -> None:
        for claim_kind in ("series_constant", "task_fit"):
            with self.subTest(claim_kind=claim_kind):
                self.write_v2_draft(
                    performance_rule_claim_kind=claim_kind,
                    style_feature_contrast="not_applicable",
                    performance_evidence_scope="first_party_traffic_validated",
                )
                result = self.run_validator()
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("nonperformance_rule_scope", result.stdout)

    def test_rendered_request_cannot_be_delivered_as_brief_only(self) -> None:
        self.write_v2_draft(
            visual_delivery_requirement="rendered",
            visual_delivery_status="brief_only",
        )
        result = self.run_validator()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("rendered_delivery_missing", result.stdout)

    def test_adult_product_cta_requires_current_production_gate_receipt(self) -> None:
        write_csv(
            self.fixture.path / "topics.csv",
            [base_topic(primary_job="conversion")],
        )
        self.write_v2_draft(
            primary_job="conversion",
            style_query_primary_job="conversion",
            cta_type="product_component",
            commercial_relationship="owned_product",
            disclosure_text="本店自营产品",
            disclosure_location="CTA前",
            cta_product_scope="adult_product",
            production_gate_status="unknown",
            production_gate_receipt_ids="none",
        )
        result = self.run_validator()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("sensitive_commercial_gate", result.stdout)

    def test_relationship_education_is_not_product_eligibility(self) -> None:
        write_csv(
            self.fixture.path / "topics.csv",
            [base_topic(primary_job="conversion")],
        )
        self.write_v2_draft(
            primary_job="conversion",
            style_query_primary_job="conversion",
            cta_type="product_component",
            commercial_relationship="owned_product",
            disclosure_text="本店自营产品",
            disclosure_location="CTA前",
            cta_product_scope="relationship_education_only",
        )
        result = self.run_validator()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("relationship_education_not_product_eligibility", result.stdout)


if __name__ == "__main__":
    unittest.main()
