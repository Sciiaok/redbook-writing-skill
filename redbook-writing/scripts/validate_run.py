#!/usr/bin/env python3
"""Validate a redbook-writing research/content run with no third-party deps."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Iterable


SCHEMAS: dict[str, list[str]] = {
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
        "confidence",
        "owner",
        "status",
        "source_asset_sha256",
        "consent_ids",
    ],
    "sku-registry.csv": [
        "eligibility_id",
        "sku_id",
        "sku_name",
        "platform",
        "account_scope",
        "surface",
        "source_asset_id",
        "status",
        "evidence_ids",
        "platform_ticket",
        "verified_at",
        "expires_at",
        "material_limits",
        "qualification_requirements",
        "notes",
        "source_asset_sha256",
        "qualification_claim_id",
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
        "status",
        "evidence_ids",
        "platform_ticket",
        "verified_at",
        "expires_at",
        "permission_or_consent_requirements",
        "prohibited_uses",
        "notes",
        "source_asset_sha256",
        "qualification_claim_id",
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

COMMON_FILES = {
    "run.yaml",
    "research.md",
    "query-log.csv",
    "source-log.csv",
    "claim-ledger.csv",
}
MODE_FILES = {
    "mechanism": set(),
    "discovery": {"accounts.csv", "posts.csv", "topics.csv"},
    "refresh": {"accounts.csv", "posts.csv", "topics.csv"},
    "draft": {"topics.csv"},
}

ID_FIELDS = {
    "query-log.csv": "query_id",
    "source-log.csv": "source_id",
    "claim-ledger.csv": "claim_id",
    "accounts.csv": "account_id",
    "posts.csv": "post_id",
    "topics.csv": "topic_id",
    "acquisition-channels.csv": "channel_id",
    "sku-registry.csv": "eligibility_id",
    "offer-registry.csv": "eligibility_id",
    "authorization-log.csv": "authorization_id",
}

REQUIRED_ROW_FIELDS = {
    "query-log.csv": {"query_id", "platform", "query", "search_surface", "run_at"},
    "source-log.csv": {
        "source_id",
        "source_layer",
        "source_type",
        "title",
        "collected_at",
        "url",
        "access_status",
        "evidence_grade",
    },
    "claim-ledger.csv": {
        "claim_id",
        "category",
        "claim_text",
        "source_ids",
        "evidence_grade",
        "claim_status",
        "scope",
        "confidence_reason",
        "skill_action",
        "last_verified_at",
        "verification_class",
    },
    "accounts.csv": {
        "account_id",
        "account_name",
        "profile_url",
        "head_type",
        "window_start",
        "window_end",
        "recent_sample_n",
        "collected_at",
        "confidence",
        "status",
    },
    "posts.csv": {
        "post_id",
        "title",
        "url",
        "account_id",
        "collected_at",
        "queries_matched",
        "format",
        "evidence_level",
        "confidence",
        "status",
    },
    "topics.csv": {
        "topic_id",
        "topic",
        "primary_job",
        "target_audience",
        "specific_scenario",
        "core_promise_or_tension",
        "evidence_ids",
        "lifecycle",
        "format",
        "measurement_plan",
        "status",
        "last_seen_at",
    },
    "acquisition-channels.csv": {
        "channel_id",
        "direction",
        "platform",
        "account_scope",
        "audience_state",
        "channel_role",
        "native_format",
        "source_asset_id",
        "public_identity",
        "surfaces",
        "permitted_cta",
        "primary_metric",
        "metric_availability",
        "data_source",
        "event_definition",
        "attribution_method",
        "attribution_level",
        "decision_rule",
        "compliance_scope",
        "owner",
        "status",
    },
    "sku-registry.csv": {
        "eligibility_id",
        "sku_id",
        "sku_name",
        "platform",
        "account_scope",
        "surface",
        "status",
        "evidence_ids",
    },
    "offer-registry.csv": {
        "eligibility_id",
        "offer_id",
        "offer_name",
        "offer_type",
        "platform",
        "account_scope",
        "surface",
        "status",
        "evidence_ids",
    },
    "authorization-log.csv": {
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
        "withdrawal_process",
        "evidence_locator",
        "verified_by",
        "verified_at",
        "status",
        "authorized_output_sha256",
    },
}

APPROVED_ELIGIBILITY = {"approved", "confirmed"}
BLOCKED_CHANNEL_STATES = {"blocked", "draft"}
BLOCKED_CHANNEL_PREFIXES = ("blocked_", "draft_", "needs_")
FORBIDDEN_CHANNEL_STATUS_TOKENS = {
    "active",
    "allowed",
    "approved",
    "enabled",
    "launch",
    "live",
    "publishable",
    "ready",
}
CLAIM_STATUSES = {
    "confirmed",
    "supported_experience",
    "hypothesis",
    "contradicted",
    "unknown",
}
VERIFICATION_CLASSES = {
    "current_runtime",
    "experience",
    "historical_research",
    "hypothesis",
    "mechanism_evidence",
}
EVIDENCE_GRADES = {"A", "B", "C", "D"}
EVIDENCE_GRADE_RANK = {"A": 0, "B": 1, "C": 2, "D": 3}
SOURCE_LAYERS = {
    "official",
    "engineering",
    "academic",
    "industry",
    "creator_experience",
    "rumor",
}
ACCESS_STATUSES = {"full", "partial", "snippet_only", "blocked", "dead_link"}
SOURCE_LAYER_MIN_GRADE_RANK = {
    "official": 0,
    "engineering": 0,
    "academic": 0,
    "industry": 1,
    "creator_experience": 2,
    "rumor": 3,
}
ACCESS_MIN_GRADE_RANK = {
    "full": 0,
    "partial": 0,
    "snippet_only": 2,
    "blocked": 3,
    "dead_link": 2,
}
CONFIRMED_SOURCE_LAYERS = {"official", "engineering", "academic"}
RUNTIME_CLAIM_CATEGORIES = {
    "advertising_law",
    "compliance",
    "competition_law",
    "current_rule",
    "current_rules",
    "governance",
    "platform_capability",
    "policy",
    "privacy",
    "sensitive_commercial",
    "sku_eligibility",
    "sku_compliance",
    "offer_eligibility",
}
RUNTIME_CATEGORY_MARKERS = {
    "compliance",
    "current",
    "governance",
    "law",
    "policy",
    "privacy",
    "rule",
    "rules",
    "合规",
    "政策",
    "更新",
    "法律",
    "治理",
    "规则",
    "隐私",
}
EVIDENCE_LEVELS = {"observed", "calculated", "inferred", "hypothesis"}
CONFIDENCES = {"high", "medium", "low"}
TOPIC_STATUSES = {"experimental", "active", "deprecated"}
RUN_STATUSES = {"in_progress", "complete", "blocked"}
HEAD_TYPES = {"scale", "recent_performance", "audience_precision", "commercial_adjacent"}
ACCOUNT_STATUSES = {"candidate", "focus", "excluded", "stale"}
COMMERCIAL_DISTANCES = {"far", "adjacent", "near", "direct"}
POST_STATUSES = {"active", "excluded", "stale"}
DIRECT_DEMAND_SOURCE_TOKENS = {
    "interview",
    "survey",
    "transcript",
    "customer_research",
    "user_material",
    "backend_screenshot",
}
CONTENT_SAMPLE_TOKENS = {"post", "note", "comment"}
ACCOUNT_SAMPLE_TOKENS = {"account", "creator_profile", "note", "post", "profile"}
PRIMARY_JOBS = {
    "recommendation_reach",
    "search_capture",
    "relationship_building",
    "commercial_conversion",
}
LIFECYCLES = {"hot", "periodic", "evergreen_search"}
DIRECTIONS = {
    "external_to_xhs",
    "xhs_to_native_conversion",
    "xhs_to_approved_external",
    "owned_retention",
}
XHS_PLATFORM_NAMES = {"xiaohongshu", "redbook", "小红书"}
NON_SPECIFIC_SCOPES = {
    "*",
    "all",
    "all_accounts",
    "all_platforms",
    "all_surfaces",
    "any",
    "any_account",
    "any_platform",
    "any_surface",
    "multi_account",
    "multi_platform",
    "multi_surface",
    "none",
    "tbd",
    "unassigned",
    "unknown",
    "待定",
    "任意平台",
    "全部平台",
    "全平台",
    "全账户",
    "全账号",
    "全表面",
    "全触点",
    "所有平台",
    "所有账户",
    "所有账号",
    "所有表面",
    "所有触点",
}

DRAFT_HEADINGS = {
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
DRAFT_META = {
    "draft_id",
    "topic_id",
    "platform",
    "account_scope",
    "primary_job",
    "lifecycle",
    "truth_label",
    "truth_disclosure_text",
    "truth_disclosure_location",
    "authorization_ids",
    "source_material_ids",
    "commercial_relationship",
    "disclosure_text",
    "disclosure_location",
    "answer_location",
    "cta_type",
    "eligibility_ids",
    "surfaces",
    "status",
}
DRAFT_NONEMPTY_META = DRAFT_META - {"eligibility_ids", "surfaces"}
TRUTH_LABELS = {
    "first_person_documented",
    "authorized_anonymized",
    "authorized_adaptation",
    "composite_cases",
    "fictional_scenario",
    "factual_explainer",
}
COMMERCIAL_RELATIONSHIPS = {
    "none",
    "owned_product",
    "sponsored",
    "gifted",
    "affiliate",
    "commissioned_creator",
    "other_disclosed",
}
COMMERCIAL_DISCLOSURE_PATTERNS = {
    "owned_product": (r"自有", r"自营", r"本店", r"品牌方", r"我方产品"),
    "sponsored": (r"广告", r"品牌合作", r"商业合作", r"赞助"),
    "gifted": (r"赠品", r"获赠", r"品牌赠送", r"免费提供"),
    "affiliate": (r"佣金", r"返佣", r"联盟", r"推广分成"),
    "commissioned_creator": (
        r"受委托",
        r"委托创作",
        r"有偿创作",
        r"付费创作",
        r"品牌合作",
    ),
    "other_disclosed": (r"商业关系", r"利益关系", r"合作关系", r"有偿", r"付费"),
}
COMMERCIAL_DISCLOSURE_CONFLICT_PATTERNS = {
    "owned_product": (r"(?:不是|并非|没有|无|不存在|不属于|非).{0,6}(?:自有|自营|品牌方)",),
    "sponsored": (r"(?:不是|并非|没有|无|不存在|不属于|非).{0,6}(?:广告|品牌合作|商业合作|赞助)",),
    "gifted": (r"(?:不是|并非|没有|无|不存在|不属于|非).{0,6}(?:赠品|获赠|赠送|免费提供)",),
    "affiliate": (r"(?:不是|并非|没有|无|不存在|不属于|非).{0,6}(?:佣金|返佣|联盟|推广分成)",),
    "commissioned_creator": (r"(?:不是|并非|没有|无|不存在|不属于|非).{0,6}(?:受委托|委托创作|有偿创作|付费创作|品牌合作)",),
    "other_disclosed": (r"(?:不是|并非|没有|无|不存在|不属于|非).{0,6}(?:商业关系|利益关系|合作关系|有偿|付费)",),
}
NONCOMMERCIAL_CTA_TYPES = {"none", "save", "follow", "comment_question", "read_series"}
COMMERCIAL_CTA_TYPES = {"product_component", "leadgen", "approved_external", "paid_offer"}
CTA_TYPES = NONCOMMERCIAL_CTA_TYPES | COMMERCIAL_CTA_TYPES
DRAFT_STATUSES = {"needs_review", "ready", "blocked"}
CTA_REQUIRED_REGISTRY_KINDS = {
    "product_component": {"sku", "offer"},
    "leadgen": {"offer"},
    "approved_external": {"offer"},
    "paid_offer": {"offer"},
}
PRODUCT_OFFER_TYPES = {"commerce", "product", "product_sale", "retail", "trial"}
AUTHORIZATION_MATERIAL_TYPES = {
    "case_record",
    "chat_record",
    "first_party",
    "interview",
    "other",
    "submission",
}
AUTHORIZATION_PERMISSION_SCOPES = {
    "adaptation",
    "anonymized_publish",
    "composite",
    "cross_platform_attribution",
    "verbatim",
}
AUTHORIZATION_COMMERCIAL_USE = {"approved", "prohibited"}
AUTHORIZATION_STATUSES = {"approved", "expired", "pending", "withdrawn"}
AUTH_REQUIRED_TRUTH_LABELS = {
    "authorized_anonymized": ("anonymized_publish", 1),
    "authorized_adaptation": ("adaptation", 1),
    "composite_cases": ("composite", 2),
}
APPROVAL_SOURCE_TYPES = {
    "approval_record",
    "platform_approval_record",
    "platform_ticket",
    "work_order",
}
TRUTH_DISCLOSURE_PATTERNS = {
    "first_person_documented": (
        r"(?:本人(?:亲历|真实记录|记录)|我的亲历记录)",
    ),
    "authorized_anonymized": (
        r"(?:经|已获).{0,6}授权.{0,12}(?:匿名|脱敏)",
    ),
    "authorized_adaptation": (
        r"(?:经|已获).{0,6}授权.{0,12}改编",
    ),
    "composite_cases": (
        r"(?:多案例|多个.{0,6}案例|多份.{0,6}材料).{0,16}(?:合成|综合改编)",
        r"(?:合成|综合改编).{0,16}(?:多案例|多个.{0,6}案例|多份.{0,6}材料)",
    ),
    "fictional_scenario": (
        r"本(?:文|内容|故事|对话|情境)?为(?:明确)?虚构",
        r"虚构情境(?:演绎|练习)",
        r"情境演绎.{0,12}(?:明确虚构|非真人经历)",
    ),
    "factual_explainer": (
        r"(?:事实说明|事实科普|资料说明|基于可核验资料的说明)",
    ),
}
TRUTH_DISCLOSURE_CONFLICT_PATTERNS = {
    "first_person_documented": (r"(?:不是|并非|不属于|非)本人", r"虚构", r"情境演绎"),
    "authorized_anonymized": (r"(?:未经|未获|没有|无|并非|不是)授权",),
    "authorized_adaptation": (r"(?:未经|未获|没有|无|并非|不是)授权",),
    "composite_cases": (r"(?:不是|并非|不属于|非)合成", r"(?:单一|一个)真人"),
    "fictional_scenario": (
        r"(?:不是|并非|不属于|非)虚构",
        r"真人真事",
        r"真人真实投稿",
        r"真实投稿",
        r"真实发生",
        r"亲身经历",
    ),
    "factual_explainer": (
        r"(?:不是|并非|不属于|非)事实",
        r"虚构",
        r"(?:未经|未)核实",
    ),
}
VISIBLE_DISCLOSURE_LOCATIONS = {"首屏", "第一页", "首段", "开头", "标题下"}
VISIBLE_COMMERCIAL_DISCLOSURE_LOCATIONS = {
    "首屏",
    "第一页",
    "首段",
    "开头",
    "标题下",
    "CTA前",
    "正文CTA前",
}


@dataclass(frozen=True)
class Issue:
    severity: str
    code: str
    location: str
    message: str


def split_ids(value: str | None) -> list[str]:
    if not value:
        return []
    return [item for item in re.split(r"[;|\s]+", value.strip()) if item]


def parse_iso(value: str) -> date | None:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def parse_dateish(value: str) -> date | None:
    if not value:
        return None
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(normalized).date()
    except ValueError:
        return parse_iso(normalized)


def parse_partial_iso(value: str) -> date | None:
    if re.fullmatch(r"\d{4}", value):
        return date(int(value), 1, 1)
    if re.fullmatch(r"\d{4}-\d{2}", value):
        try:
            return date(int(value[:4]), int(value[5:7]), 1)
        except ValueError:
            return None
    return parse_iso(value)


def parse_top_level_yaml(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        if not raw or raw[0].isspace() or raw.lstrip().startswith("#"):
            continue
        match = re.match(r"^([A-Za-z][A-Za-z0-9_-]*):\s*(.*?)\s*$", raw)
        if not match:
            continue
        value = match.group(2).strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[match.group(1)] = value
    return values


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}
    values: dict[str, str] = {}
    for raw in text[4:end].splitlines():
        match = re.match(r"^([A-Za-z][A-Za-z0-9_-]*):\s*(.*?)\s*$", raw)
        if match:
            value = match.group(2).strip().strip("\"'")
            values[match.group(1)] = value
    return values


def markdown_section(text: str, heading: str) -> str:
    match = re.search(
        rf"^##\s+{re.escape(heading)}\s*$\n(.*?)(?=^##\s+|\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    return match.group(1).strip() if match else ""


def visible_markdown(text: str) -> str:
    """Remove common non-rendered/hidden HTML before validating visible contracts."""
    cleaned = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    cleaned = re.sub(
        r"<(?:script|style|template|noscript|details)\b[^>]*>.*?</(?:script|style|template|noscript|details)\s*>",
        "",
        cleaned,
        flags=re.IGNORECASE | re.DOTALL,
    )
    hidden_block = re.compile(
        r"<(?P<tag>[a-z][a-z0-9:-]*)\b"
        r"(?=[^>]*(?:\bhidden\b|aria-hidden\s*=\s*['\"]?true|"
        r"class\s*=\s*['\"][^'\"]*(?:hidden|sr-only|visually-hidden)|"
        r"style\s*=\s*['\"][^'\"]*(?:display\s*:\s*none|visibility\s*:\s*hidden)))"
        r"[^>]*>.*?</(?P=tag)\s*>",
        flags=re.IGNORECASE | re.DOTALL,
    )
    previous = None
    while previous != cleaned:
        previous = cleaned
        cleaned = hidden_block.sub("", cleaned)
    cleaned = re.sub(r"!\[[^\]]*\]\([^\n)]*\)", "", cleaned)
    cleaned = re.sub(r"!\[[^\]]*\]\[[^\]]*\]", "", cleaned)
    cleaned = re.sub(
        r"(?m)^\s*\[[^\]]+\]:\s*\S+.*$",
        "",
        cleaned,
    )
    cleaned = re.sub(r"\[([^\]]+)\]\([^\n)]*\)", r"\1", cleaned)
    cleaned = re.sub(r"\[([^\]]+)\]\[[^\]]*\]", r"\1", cleaned)
    cleaned = re.sub(r"</?[a-z][^>]*>", "", cleaned, flags=re.IGNORECASE)
    return cleaned


def parse_contract_block(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in text.splitlines():
        match = re.match(r"^([a-z][a-z0-9_]*):\s*(.*?)\s*$", raw.strip())
        if match:
            values[match.group(1)] = match.group(2).strip().strip("\"'")
    return values


def normalize_none(value: str | None) -> str:
    normalized = (value or "").strip().lower()
    return "none" if normalized in {"", "none"} else normalized


def exact_tokens(value: str | None) -> set[str]:
    """Return normalized identifier-like tokens without substring matching."""
    return {
        token
        for token in re.split(r"[^a-z0-9]+", (value or "").strip().lower())
        if token
    }


def normalized_descriptor(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", "_", (value or "").strip().lower()).strip("_")


def source_descriptors(row: dict[str, str]) -> set[str]:
    return {
        descriptor
        for descriptor in (
            normalized_descriptor(row.get("source_type")),
            normalized_descriptor(row.get("evidence_form")),
        )
        if descriptor
    }


def claim_requires_runtime_verification(category: str | None) -> bool:
    raw = (category or "").strip().lower()
    normalized = normalized_descriptor(raw)
    if normalized in RUNTIME_CLAIM_CATEGORIES:
        return True
    english_tokens = set(normalized.split("_"))
    if english_tokens & {marker for marker in RUNTIME_CATEGORY_MARKERS if marker.isascii()}:
        return True
    return any(marker in raw for marker in RUNTIME_CATEGORY_MARKERS if not marker.isascii())


def claim_text_requires_runtime_verification(claim_text: str | None) -> bool:
    text = (claim_text or "").strip().lower()
    platform_markers = (
        "平台",
        "小红书",
        "redbook",
        "抖音",
        "douyin",
        "知乎",
        "b站",
        "微信",
    )
    capability_markers = (
        "入口",
        "能力",
        "功能",
        "组件",
        "外跳",
        "私信",
        "信息流",
        "资格",
        "准入",
        "禁入",
        "可用",
        "支持",
        "允许",
        "开放",
    )
    currency_markers = (
        "当前",
        "现行",
        "目前",
        "现已",
        "已开放",
        "已上线",
        "截至",
        "仍可",
        "不再",
        "官方页面",
        "官方规则",
        "后台",
    )
    return (
        any(marker in text for marker in platform_markers)
        and any(marker in text for marker in capability_markers)
        and any(marker in text for marker in currency_markers)
    )


def scope_is_specific(value: str | None) -> bool:
    raw = (value or "").strip()
    normalized = raw.lower().replace("-", "_").replace(" ", "_")
    if normalized in NON_SPECIFIC_SCOPES or normalized.startswith(("all_", "any_", "multi_")):
        return False
    if any(separator in raw for separator in (";", "|", ",", "，", "、", "/", "+", "&", "＆")):
        return False
    return bool(raw)


def claim_scope_is_specific(value: str | None) -> bool:
    raw = (value or "").strip()
    normalized = re.sub(r"[\s_-]+", "", raw.lower())
    if not raw:
        return False
    banned = {
        "all",
        "allplatforms",
        "anyplatform",
        "multiplatform",
        "全平台",
        "全部平台",
        "所有平台",
        "全站",
        "通用",
        "小红书",
        "xiaohongshu",
        "redbook",
    }
    broad_markers = (
        "allsurface",
        "allaccount",
        "anysurface",
        "anyaccount",
        "全部入口",
        "所有入口",
        "全入口",
        "全部表面",
        "所有表面",
        "全账号",
        "全账户",
        "所有账号",
        "所有账户",
    )
    return normalized not in banned and not any(marker in normalized for marker in broad_markers)


def platform_is_xhs(value: str | None) -> bool:
    return (value or "").strip().lower() in XHS_PLATFORM_NAMES


def platforms_equivalent(left: str | None, right: str | None) -> bool:
    if platform_is_xhs(left) and platform_is_xhs(right):
        return True
    return (left or "").strip().lower() == (right or "").strip().lower()


def parse_scope_contract(value: str | None) -> dict[str, str]:
    result: dict[str, str] = {}
    for part in (value or "").split("|"):
        if "=" not in part:
            continue
        key, raw = part.split("=", 1)
        key = key.strip()
        if key:
            result[key] = raw.strip()
    return result


def valid_sha256(value: str | None) -> bool:
    return bool(re.fullmatch(r"[a-fA-F0-9]{64}", (value or "").strip()))


def channel_status_class(value: str | None) -> str | None:
    """Return active/blocked only for machine-readable, non-contradictory statuses."""
    status = (value or "").strip().lower()
    if status == "active":
        return "active"
    if status in BLOCKED_CHANNEL_STATES:
        return "blocked"
    if not status.startswith(BLOCKED_CHANNEL_PREFIXES):
        return None
    tokens = exact_tokens(status)
    if tokens & FORBIDDEN_CHANNEL_STATUS_TOKENS:
        return None
    return "blocked"


class RunValidator:
    def __init__(self, run_dir: Path, strict: bool = False) -> None:
        self.run_dir = run_dir
        self.strict = strict
        self.issues: list[Issue] = []
        self.rows: dict[str, list[dict[str, str]]] = {}
        self.run: dict[str, str] = {}

    def add(self, severity: str, code: str, location: str, message: str) -> None:
        self.issues.append(Issue(severity, code, location, message))

    def error(self, code: str, location: str, message: str) -> None:
        self.add("error", code, location, message)

    def warn(self, code: str, location: str, message: str) -> None:
        self.add("warning", code, location, message)

    def validate(self) -> list[Issue]:
        if not self.run_dir.is_dir():
            self.error("missing_run_dir", str(self.run_dir), "run directory does not exist")
            return self.issues
        self._load_run()
        self._check_required_files()
        self._load_csvs()
        self._check_completion()
        self._check_rows()
        self._check_dates()
        self._check_references()
        self._check_sources()
        self._check_claims()
        self._check_accounts_and_posts()
        self._check_topics()
        self._check_registry_rows()
        self._check_authorizations()
        self._check_channels()
        self._check_drafts()
        return sorted(
            self.issues,
            key=lambda item: (item.severity != "error", item.code, item.location, item.message),
        )

    def _load_run(self) -> None:
        path = self.run_dir / "run.yaml"
        if not path.exists():
            return
        try:
            self.run = parse_top_level_yaml(path)
        except UnicodeDecodeError as exc:
            self.error("invalid_encoding", "run.yaml", str(exc))
            return
        required = {
            "run_id",
            "mode",
            "status",
            "created_at",
            "category",
            "target_audience",
            "primary_goal",
            "commercial_goal",
            "window_start",
            "window_end",
            "assumptions",
            "limitations",
        }
        for key in sorted(required - self.run.keys()):
            self.error("missing_run_field", "run.yaml", f"missing top-level field: {key}")
        for key in sorted((required - {"assumptions", "limitations"}) & self.run.keys()):
            if not self.run.get(key, "").strip():
                self.error(
                    "missing_run_value",
                    "run.yaml",
                    f"top-level field cannot be blank: {key}",
                )
        mode = self.run.get("mode", "")
        if mode and mode not in MODE_FILES:
            self.error("invalid_mode", "run.yaml", f"unsupported mode: {mode}")
        status = self.run.get("status", "")
        if status and status not in RUN_STATUSES:
            self.error("invalid_status", "run.yaml", f"unsupported status: {status}")
        for field in ("created_at", "window_start", "window_end"):
            value = self.run.get(field, "")
            if value and parse_iso(value) is None:
                self.error("invalid_date", "run.yaml", f"{field} must be YYYY-MM-DD")
        window_start = parse_iso(self.run.get("window_start", ""))
        window_end = parse_iso(self.run.get("window_end", ""))
        created = parse_iso(self.run.get("created_at", ""))
        if window_start and window_end and window_start > window_end:
            self.error("invalid_date_order", "run.yaml", "window_start cannot be after window_end")
        if created and window_end and window_end > created:
            self.error("future_date", "run.yaml", "window_end cannot be after created_at")

    def _check_required_files(self) -> None:
        mode = self.run.get("mode", "")
        required = COMMON_FILES | MODE_FILES.get(mode, set())
        for name in sorted(required):
            if not (self.run_dir / name).exists():
                self.error("missing_file", name, f"required for mode {mode or 'unknown'}")
        if mode == "draft":
            drafts = self.run_dir / "drafts"
            if not drafts.is_dir():
                self.error("missing_file", "drafts/", "draft mode requires a drafts directory")
            elif not any(drafts.glob("*.md")):
                self.error("missing_file", "drafts/", "draft mode requires at least one Markdown draft")

    def _check_completion(self) -> None:
        if self.run.get("status") != "complete":
            return
        mode = self.run.get("mode", "")
        required_nonempty = {"query-log.csv", "source-log.csv", "claim-ledger.csv"}
        required_nonempty |= MODE_FILES.get(mode, set())
        for name in sorted(required_nonempty):
            if name in self.rows and not self.rows[name]:
                self.error(
                    "incomplete_run",
                    name,
                    f"completed {mode} run cannot use an empty required dataset",
                )
        research = self.run_dir / "research.md"
        if research.exists():
            content = re.sub(r"[#>*_`\-\s]", "", research.read_text(encoding="utf-8-sig"))
            if not content:
                self.error(
                    "incomplete_run",
                    "research.md",
                    "completed run requires substantive research content",
                )

    def _load_csvs(self) -> None:
        for name, schema in SCHEMAS.items():
            path = self.run_dir / name
            if not path.exists():
                continue
            try:
                with path.open("r", encoding="utf-8-sig", newline="") as handle:
                    reader = csv.DictReader(handle)
                    headers = reader.fieldnames or []
                    missing = [field for field in schema if field not in headers]
                    if missing:
                        self.error(
                            "schema_mismatch",
                            name,
                            "missing columns: " + ", ".join(missing),
                        )
                    loaded: list[dict[str, str]] = []
                    for raw in reader:
                        if None in raw:
                            self.error("malformed_csv", name, "row has more values than headers")
                            continue
                        loaded.append({key: (value or "").strip() for key, value in raw.items()})
                    self.rows[name] = loaded
            except (OSError, UnicodeDecodeError, csv.Error) as exc:
                self.error("unreadable_csv", name, str(exc))

    def _check_rows(self) -> None:
        for name, rows in self.rows.items():
            id_field = ID_FIELDS[name]
            seen_ids: dict[str, int] = {}
            for index, row in enumerate(rows, start=2):
                location = f"{name}:{index}"
                for field in sorted(REQUIRED_ROW_FIELDS[name]):
                    if not row.get(field, ""):
                        self.error("missing_value", location, f"{field} is required")
                row_id = row.get(id_field, "")
                if row_id:
                    if row_id in seen_ids:
                        self.error(
                            "duplicate_id",
                            location,
                            f"{row_id} duplicates row {seen_ids[row_id]}",
                        )
                    else:
                        seen_ids[row_id] = index

            for url_field in ("url", "profile_url"):
                seen_urls: dict[str, int] = {}
                for index, row in enumerate(rows, start=2):
                    value = row.get(url_field, "")
                    if not value:
                        continue
                    if not re.match(r"^https?://", value):
                        self.error("invalid_url", f"{name}:{index}", f"invalid {url_field}: {value}")
                    normalized = value.rstrip("/")
                    if normalized in seen_urls:
                        self.error(
                            "duplicate_url",
                            f"{name}:{index}",
                            f"{value} duplicates row {seen_urls[normalized]}",
                        )
                    else:
                        seen_urls[normalized] = index

    def _check_dates(self) -> None:
        run_date = parse_iso(self.run.get("created_at", ""))
        for index, row in enumerate(self.rows.get("query-log.csv", []), start=2):
            location = f"query-log.csv:{index}"
            observed = parse_dateish(row.get("run_at", ""))
            if observed is None:
                self.error("invalid_date", location, "run_at must be an ISO date or timestamp")
            elif run_date and observed > run_date:
                self.error("future_date", location, "run_at cannot be after the run date")

        for index, row in enumerate(self.rows.get("source-log.csv", []), start=2):
            location = f"source-log.csv:{index}"
            collected = parse_iso(row.get("collected_at", ""))
            published_raw = row.get("published_at", "")
            published = parse_partial_iso(published_raw) if published_raw else None
            if collected is None:
                self.error("invalid_date", location, "collected_at must be YYYY-MM-DD")
            elif run_date and collected > run_date:
                self.error("future_date", location, "collected_at cannot be after the run date")
            if published_raw and published is None:
                self.error(
                    "invalid_date",
                    location,
                    "published_at must be YYYY, YYYY-MM, YYYY-MM-DD, or blank",
                )
            if published and collected and published > collected:
                self.error("invalid_date_order", location, "published_at cannot be after collected_at")

        for index, row in enumerate(self.rows.get("accounts.csv", []), start=2):
            location = f"accounts.csv:{index}"
            start = parse_iso(row.get("window_start", ""))
            end = parse_iso(row.get("window_end", ""))
            collected = parse_iso(row.get("collected_at", ""))
            if start is None or end is None or collected is None:
                self.error(
                    "invalid_date",
                    location,
                    "window_start, window_end, and collected_at must be YYYY-MM-DD",
                )
            if start and end and start > end:
                self.error("invalid_date_order", location, "window_start cannot be after window_end")
            if end and collected and end > collected:
                self.error(
                    "invalid_date_order",
                    location,
                    "window_end cannot be after collected_at",
                )
            if end and run_date and end > run_date:
                self.error("future_date", location, "window_end cannot be after the run date")
            if collected and run_date and collected > run_date:
                self.error("future_date", location, "collected_at cannot be after the run date")

        for index, row in enumerate(self.rows.get("posts.csv", []), start=2):
            location = f"posts.csv:{index}"
            collected = parse_iso(row.get("collected_at", ""))
            published = parse_iso(row.get("published_at", "")) if row.get("published_at") else None
            if collected is None:
                self.error("invalid_date", location, "collected_at must be YYYY-MM-DD")
            elif run_date and collected > run_date:
                self.error("future_date", location, "collected_at cannot be after the run date")
            if published and collected and published > collected:
                self.error("invalid_date_order", location, "published_at cannot be after collected_at")

        for index, row in enumerate(self.rows.get("topics.csv", []), start=2):
            location = f"topics.csv:{index}"
            last_seen = parse_iso(row.get("last_seen_at", ""))
            if last_seen is None:
                self.error("invalid_date", location, "last_seen_at must be YYYY-MM-DD")
            elif run_date and last_seen > run_date:
                self.error("future_date", location, "last_seen_at cannot be after the run date")

        for index, row in enumerate(self.rows.get("authorization-log.csv", []), start=2):
            location = f"authorization-log.csv:{index}"
            granted = parse_iso(row.get("granted_at", ""))
            verified = parse_iso(row.get("verified_at", ""))
            expires_raw = row.get("expires_at", "")
            expires = parse_iso(expires_raw) if expires_raw else None
            if granted is None or verified is None or (expires_raw and expires is None):
                self.error(
                    "invalid_authorization_date",
                    location,
                    "granted_at/verified_at and optional expires_at must be YYYY-MM-DD",
                )
            if granted and verified and granted > verified:
                self.error(
                    "invalid_date_order",
                    location,
                    "granted_at cannot be after verified_at",
                )
            if granted and expires and expires < granted:
                self.error(
                    "invalid_date_order",
                    location,
                    "expires_at cannot be before granted_at",
                )
            if run_date and verified and verified > run_date:
                self.error("future_date", location, "verified_at cannot be after the run date")

    def _id_set(self, filename: str) -> set[str]:
        field = ID_FIELDS[filename]
        return {row.get(field, "") for row in self.rows.get(filename, []) if row.get(field, "")}

    def _check_id_refs(
        self,
        filename: str,
        field: str,
        known: set[str],
        *,
        required: bool = False,
    ) -> None:
        for index, row in enumerate(self.rows.get(filename, []), start=2):
            refs = split_ids(row.get(field))
            if required and not refs:
                self.error("missing_reference", f"{filename}:{index}", f"{field} is empty")
            for ref in refs:
                if ref not in known:
                    self.error(
                        "dangling_reference",
                        f"{filename}:{index}",
                        f"{field} references unknown id {ref}",
                    )

    def _check_references(self) -> None:
        query_ids = self._id_set("query-log.csv")
        source_ids = self._id_set("source-log.csv")
        account_ids = self._id_set("accounts.csv")
        post_ids = self._id_set("posts.csv")
        claim_ids = self._id_set("claim-ledger.csv")
        authorization_ids = self._id_set("authorization-log.csv")

        self._check_id_refs("source-log.csv", "query_id", query_ids)
        self._check_id_refs("query-log.csv", "selected_source_ids", source_ids)
        if "accounts.csv" in self.rows:
            self._check_id_refs("query-log.csv", "selected_account_ids", account_ids)
            self._check_id_refs("accounts.csv", "source_ids", source_ids, required=True)
        if "posts.csv" in self.rows:
            self._check_id_refs("query-log.csv", "selected_post_ids", post_ids)
            self._check_id_refs("posts.csv", "account_id", account_ids, required=True)
            self._check_id_refs("posts.csv", "queries_matched", query_ids, required=True)
        self._check_id_refs("claim-ledger.csv", "source_ids", source_ids, required=True)
        self._check_id_refs("claim-ledger.csv", "counter_source_ids", source_ids)
        registry_evidence = source_ids | claim_ids
        self._check_id_refs(
            "sku-registry.csv",
            "evidence_ids",
            registry_evidence,
            required=True,
        )
        self._check_id_refs(
            "offer-registry.csv",
            "evidence_ids",
            registry_evidence,
            required=True,
        )
        for filename in ("sku-registry.csv", "offer-registry.csv"):
            self._check_id_refs(filename, "platform_ticket", source_ids)
            self._check_id_refs(filename, "qualification_claim_id", claim_ids)
        self._check_id_refs("acquisition-channels.csv", "consent_ids", authorization_ids)
        evidence_ids = source_ids | account_ids | post_ids | claim_ids
        self._check_id_refs("topics.csv", "evidence_ids", evidence_ids, required=True)

    def _check_sources(self) -> None:
        for index, row in enumerate(self.rows.get("source-log.csv", []), start=2):
            location = f"source-log.csv:{index}"
            layer = row.get("source_layer", "")
            access = row.get("access_status", "")
            grade = row.get("evidence_grade", "")
            if layer not in SOURCE_LAYERS:
                self.error("invalid_enum", location, f"unknown source_layer: {layer}")
            if access not in ACCESS_STATUSES:
                self.error("invalid_enum", location, f"unknown access_status: {access}")
            if grade not in EVIDENCE_GRADES:
                self.error("invalid_enum", location, f"unknown evidence_grade: {grade}")
            if (
                grade in EVIDENCE_GRADES
                and layer in SOURCE_LAYER_MIN_GRADE_RANK
                and access in ACCESS_MIN_GRADE_RANK
            ):
                minimum_rank = max(
                    SOURCE_LAYER_MIN_GRADE_RANK[layer],
                    ACCESS_MIN_GRADE_RANK[access],
                )
                if EVIDENCE_GRADE_RANK[grade] < minimum_rank:
                    minimum_grade = next(
                        item for item, rank in EVIDENCE_GRADE_RANK.items() if rank == minimum_rank
                    )
                    self.error(
                        "source_grade_conflict",
                        location,
                        f"{layer}/{access} source cannot exceed grade {minimum_grade}",
                    )

    def _check_claims(self) -> None:
        run_date = parse_iso(self.run.get("created_at", ""))
        sources = {
            row.get("source_id", ""): row
            for row in self.rows.get("source-log.csv", [])
            if row.get("source_id", "")
        }
        for index, row in enumerate(self.rows.get("claim-ledger.csv", []), start=2):
            location = f"claim-ledger.csv:{index}"
            grade = row.get("evidence_grade", "")
            status = row.get("claim_status", "")
            verification_class = row.get("verification_class", "")
            runtime_claim = verification_class == "current_runtime"
            if verification_class not in VERIFICATION_CLASSES:
                self.error(
                    "invalid_enum",
                    location,
                    f"invalid verification_class: {verification_class}",
                )
            if (
                (
                    claim_requires_runtime_verification(row.get("category"))
                    or claim_text_requires_runtime_verification(row.get("claim_text"))
                )
                and verification_class
                and verification_class != "current_runtime"
            ):
                self.error(
                    "verification_class_conflict",
                    location,
                    "category appears runtime-sensitive; explicitly classify it current_runtime or rename it as a bounded historical claim",
                )
            if verification_class == "hypothesis" and status not in {"hypothesis", "unknown"}:
                self.error(
                    "verification_class_conflict",
                    location,
                    "verification_class=hypothesis requires claim_status hypothesis or unknown",
                )
            if grade not in EVIDENCE_GRADES:
                self.error("invalid_enum", location, f"unknown evidence_grade: {grade}")
            if status not in CLAIM_STATUSES:
                self.error("invalid_enum", location, f"unknown claim_status: {status}")
            if status == "confirmed" and grade in {"C", "D"}:
                self.error(
                    "grade_status_conflict",
                    location,
                    f"grade {grade} cannot support confirmed status",
                )
            if grade == "D" and status == "supported_experience":
                self.error(
                    "grade_status_conflict",
                    location,
                    "grade D cannot be promoted to supported_experience",
                )
            supporting_sources = [
                sources[source_id]
                for source_id in split_ids(row.get("source_ids"))
                if source_id in sources
            ]
            eligible_confirmed_layers = (
                {"official"} if runtime_claim else CONFIRMED_SOURCE_LAYERS
            )
            if status == "confirmed" and not any(
                source.get("source_layer") in eligible_confirmed_layers
                and source.get("access_status") in {"full", "partial"}
                and source.get("evidence_grade") in {"A", "B"}
                and (
                    not runtime_claim
                    or (run_date and parse_iso(source.get("collected_at", "")) == run_date)
                )
                for source in supporting_sources
            ):
                self.error(
                    "confirmed_source_conflict",
                    location,
                    "confirmed current claims require a same-run official A/B source; other confirmed claims require accessible official, engineering, or academic A/B evidence",
                )
            supporting_grades = [
                source.get("evidence_grade", "")
                for source in supporting_sources
                if source.get("evidence_grade", "") in EVIDENCE_GRADES
            ]
            if grade in EVIDENCE_GRADES and supporting_grades:
                best_source_grade = min(
                    supporting_grades,
                    key=lambda item: EVIDENCE_GRADE_RANK[item],
                )
                if EVIDENCE_GRADE_RANK[grade] < EVIDENCE_GRADE_RANK[best_source_grade]:
                    self.error(
                        "grade_source_conflict",
                        location,
                        f"claim grade {grade} exceeds best supporting source grade {best_source_grade}",
                    )
            verified = parse_iso(row.get("last_verified_at", ""))
            if not claim_scope_is_specific(row.get("scope")):
                self.error(
                    "invalid_claim_scope",
                    location,
                    "claim scope must identify a concrete module, entry point, time, or content/commercial surface",
                )
            if verified is None:
                self.error("invalid_date", location, "last_verified_at must be YYYY-MM-DD")
            elif run_date and verified > run_date:
                self.error(
                    "future_date",
                    location,
                    "last_verified_at cannot be after the run date",
                )
            elif (
                run_date
                and runtime_claim
                and verified != run_date
            ):
                self.error(
                    "not_verified_this_run",
                    location,
                    "current rules and platform capabilities must be verified in this run",
                )
            if runtime_claim and run_date and not any(
                parse_iso(source.get("collected_at", "")) == run_date
                and source.get("access_status") in {"full", "partial"}
                for source in supporting_sources
            ):
                self.error(
                    "current_source_not_refreshed",
                    location,
                    "runtime rule/law/policy claim needs at least one accessible supporting source collected in this run",
                )

    def _check_accounts_and_posts(self) -> None:
        sources = {
            row.get("source_id", ""): row
            for row in self.rows.get("source-log.csv", [])
            if row.get("source_id", "")
        }
        for index, row in enumerate(self.rows.get("accounts.csv", []), start=2):
            location = f"accounts.csv:{index}"
            if row.get("confidence") not in CONFIDENCES:
                self.error("invalid_enum", location, "confidence must be high, medium, or low")
            head_types = set(split_ids(row.get("head_type")))
            if not head_types or not head_types.issubset(HEAD_TYPES):
                self.error("invalid_enum", location, f"invalid head_type: {row.get('head_type')}")
            if row.get("commercial_distance") not in COMMERCIAL_DISTANCES:
                self.error(
                    "invalid_enum",
                    location,
                    f"invalid commercial_distance: {row.get('commercial_distance')}",
                )
            if row.get("status") not in ACCOUNT_STATUSES:
                self.error("invalid_enum", location, f"invalid account status: {row.get('status')}")
            if row.get("status") in {"candidate", "focus"} and not any(
                source_id in sources
                and self._source_supports_account_sample(sources[source_id], row)
                for source_id in split_ids(row.get("source_ids"))
            ):
                self.error(
                    "account_source_mismatch",
                    location,
                    "candidate/focus account needs an accessible account/profile source whose URL matches profile_url",
                )
            sample = row.get("recent_sample_n", "")
            if sample and (not sample.isdigit() or int(sample) < 0):
                self.error("invalid_number", location, "recent_sample_n must be a non-negative integer")
            sample_n = int(sample) if sample.isdigit() else None
            if sample_n == 0 and (
                row.get("status") == "focus" or row.get("confidence") == "high"
            ):
                self.error(
                    "account_sample_conflict",
                    location,
                    "focus or high-confidence account cannot have a zero recent sample",
                )
            if "scale" in head_types and not re.search(
                r"\d", row.get("follower_count", "")
            ):
                self.error(
                    "missing_scale_metric",
                    location,
                    "scale head_type requires an observed follower_count containing a visible numeric value; otherwise remove scale",
                )
            numeric: dict[str, float] = {}
            for field in (
                "recent_median_visible_engagement",
                "recent_max_visible_engagement",
                "outlier_multiple",
            ):
                raw = row.get(field, "")
                if not raw:
                    continue
                try:
                    value = float(raw.replace(",", ""))
                except ValueError:
                    self.error("invalid_number", location, f"{field} must be numeric or blank")
                    continue
                if not math.isfinite(value) or value < 0:
                    self.error(
                        "invalid_number",
                        location,
                        f"{field} must be a finite non-negative number",
                    )
                    continue
                numeric[field] = value
            median = numeric.get("recent_median_visible_engagement")
            maximum = numeric.get("recent_max_visible_engagement")
            multiple = numeric.get("outlier_multiple")
            if median is not None and maximum is not None and maximum < median:
                self.error(
                    "invalid_baseline_order",
                    location,
                    "recent_max_visible_engagement cannot be below the recent median",
                )
            if median == 0 and multiple is not None:
                self.error(
                    "outlier_mismatch",
                    location,
                    "outlier_multiple must be blank when the median is zero",
                )
            elif median and maximum is not None and multiple is not None:
                expected = maximum / median
                if abs(multiple - expected) > max(0.01, expected * 0.01):
                    self.error(
                        "outlier_mismatch",
                        location,
                        f"outlier_multiple {multiple:g} does not match max/median {expected:g}",
                    )

            if (
                "recent_performance" in head_types
                and row.get("status") in {"candidate", "focus"}
                and (
                    sample_n is None
                    or sample_n <= 0
                    or not all(
                        field in numeric
                        for field in (
                            "recent_median_visible_engagement",
                            "recent_max_visible_engagement",
                            "outlier_multiple",
                        )
                    )
                )
            ):
                self.error(
                    "missing_performance_baseline",
                    location,
                    "recent_performance candidate/focus requires a positive recent sample plus numeric median, max, and outlier_multiple; otherwise remove that head_type",
                )

        note_ids: dict[str, int] = {}
        for index, row in enumerate(self.rows.get("posts.csv", []), start=2):
            location = f"posts.csv:{index}"
            if row.get("evidence_level") not in EVIDENCE_LEVELS:
                self.error("invalid_enum", location, f"invalid evidence_level: {row.get('evidence_level')}")
            if row.get("confidence") not in CONFIDENCES:
                self.error("invalid_enum", location, "confidence must be high, medium, or low")
            note_id = row.get("note_id", "")
            if note_id:
                if note_id in note_ids:
                    self.error(
                        "duplicate_note_id",
                        location,
                        f"{note_id} duplicates row {note_ids[note_id]}",
                    )
                else:
                    note_ids[note_id] = index
            published = row.get("published_at", "")
            date_confidence = row.get("date_confidence", "")
            if published and parse_iso(published) is None:
                self.error("invalid_date", location, "published_at must be YYYY-MM-DD or blank")
            if date_confidence not in {"high", "medium", "low", "unknown"}:
                self.error("invalid_enum", location, f"invalid date_confidence: {date_confidence}")
            if row.get("status") not in POST_STATUSES:
                self.error("invalid_enum", location, f"invalid post status: {row.get('status')}")
            multiple = row.get("account_baseline_multiple", "").strip()
            if multiple:
                try:
                    value = float(multiple.replace(",", ""))
                    if not math.isfinite(value) or value < 0:
                        raise ValueError
                except ValueError:
                    self.error(
                        "invalid_number",
                        location,
                        "account_baseline_multiple must be a non-negative number or blank",
                    )

    def _source_is_demand_sample(self, row: dict[str, str]) -> bool:
        if row.get("access_status") not in {"full", "partial"}:
            return False
        if row.get("evidence_grade") == "D":
            return False
        descriptors = source_descriptors(row)
        if descriptors & DIRECT_DEMAND_SOURCE_TOKENS:
            return True
        return row.get("source_layer") in {"creator_experience", "industry"} and bool(
            descriptors & CONTENT_SAMPLE_TOKENS
        )

    def _source_supports_account_sample(
        self,
        row: dict[str, str],
        account: dict[str, str],
    ) -> bool:
        descriptors = source_descriptors(row)
        source_url = row.get("url", "").rstrip("/")
        profile_url = account.get("profile_url", "").rstrip("/")
        return (
            row.get("access_status") in {"full", "partial"}
            and row.get("evidence_grade") != "D"
            and (
                bool(descriptors & ACCOUNT_SAMPLE_TOKENS)
                or any(
                    descriptor.endswith(("_account", "_note", "_post", "_profile"))
                    for descriptor in descriptors
                )
            )
            and bool(source_url and profile_url and source_url == profile_url)
        )

    def _post_is_usable_sample(self, row: dict[str, str]) -> bool:
        return (
            row.get("status") == "active"
            and row.get("evidence_level") in {"observed", "calculated"}
        )

    def _post_has_performance_metric(self, row: dict[str, str]) -> bool:
        visible = row.get("visible_engagement", "").strip().lower()
        if (
            visible in {"", "none", "n/a", "na", "unknown", "不可得", "未显示"}
            or not re.search(r"\d", visible)
        ):
            return False
        try:
            multiple = float(row.get("account_baseline_multiple", "").replace(",", ""))
        except ValueError:
            return False
        return math.isfinite(multiple) and multiple >= 0

    def _post_is_current_sample(
        self,
        post: dict[str, str],
        accounts: dict[str, dict[str, str]],
        sources: dict[str, dict[str, str]],
    ) -> bool:
        if not self._post_is_usable_sample(post):
            return False
        published = parse_iso(post.get("published_at", ""))
        window_start = parse_iso(self.run.get("window_start", ""))
        window_end = parse_iso(self.run.get("window_end", ""))
        if published is None or post.get("date_confidence") not in {"high", "medium"}:
            return False
        if window_start and published < window_start:
            return False
        if window_end and published > window_end:
            return False
        account = accounts.get(post.get("account_id", ""))
        return bool(
            account
            and account.get("status") in {"candidate", "focus"}
            and any(
                source_id in sources
                and self._source_supports_account_sample(sources[source_id], account)
                for source_id in split_ids(account.get("source_ids"))
            )
        )

    def _check_topics(self) -> None:
        posts = {row.get("post_id", ""): row for row in self.rows.get("posts.csv", [])}
        accounts = {
            row.get("account_id", ""): row
            for row in self.rows.get("accounts.csv", [])
            if row.get("account_id", "")
        }
        sources = {
            row.get("source_id", ""): row
            for row in self.rows.get("source-log.csv", [])
            if row.get("source_id", "")
        }
        known_counter_ids = (
            set(posts)
            | set(accounts)
            | set(sources)
            | self._id_set("claim-ledger.csv")
        )
        for index, row in enumerate(self.rows.get("topics.csv", []), start=2):
            location = f"topics.csv:{index}"
            if row.get("primary_job") not in PRIMARY_JOBS:
                self.error("invalid_enum", location, f"invalid primary_job: {row.get('primary_job')}")
            if row.get("lifecycle") not in LIFECYCLES:
                self.error("invalid_enum", location, f"invalid lifecycle: {row.get('lifecycle')}")
            if row.get("status") not in TOPIC_STATUSES:
                self.error("invalid_enum", location, f"invalid topic status: {row.get('status')}")
            evidence_refs = split_ids(row.get("evidence_ids"))
            usable_posts = [
                posts[ref]
                for ref in evidence_refs
                if ref in posts and self._post_is_usable_sample(posts[ref])
            ]
            demand_sources = [
                sources[ref]
                for ref in evidence_refs
                if ref in sources and self._source_is_demand_sample(sources[ref])
            ]
            if row.get("status") == "experimental" and not (usable_posts or demand_sources):
                self.error(
                    "insufficient_topic_sample",
                    location,
                    "experimental topic needs a traceable demand or content sample",
                )
            if row.get("status") != "active":
                continue
            missing_metric_ids = [
                post.get("post_id", "")
                for post in usable_posts
                if not self._post_has_performance_metric(post)
            ]
            if missing_metric_ids:
                self.error(
                    "missing_post_metric",
                    location,
                    "active topic performance samples need visible_engagement and numeric account_baseline_multiple; mark the topic experimental if the sample is non-performance evidence: "
                    + ";".join(missing_metric_ids),
                )
            counterexamples = row.get("counterexamples", "").strip().lower()
            referenced_counter_ids = {
                counter_id
                for counter_id in known_counter_ids
                if re.search(
                    rf"(?<![A-Za-z0-9_-]){re.escape(counter_id)}(?![A-Za-z0-9_-])",
                    row.get("counterexamples", ""),
                )
            }
            if counterexamples in {"", "none", "n/a", "na", "暂无", "无"}:
                self.error(
                    "missing_counterexample",
                    location,
                    "active topic requires at least one traceable counterexample and bounded interpretation",
                )
            elif not referenced_counter_ids:
                self.error(
                    "invalid_counterexample_reference",
                    location,
                    "active topic counterexamples must cite an existing source/account/post/claim ID",
                )
            elif referenced_counter_ids & set(evidence_refs):
                self.error(
                    "counterexample_evidence_overlap",
                    location,
                    "the same source/account/post/claim ID cannot be both supporting evidence and a counterexample",
                )
            referenced_posts = [
                post
                for post in usable_posts
                if self._post_has_performance_metric(post)
                and self._post_is_current_sample(post, accounts, sources)
            ]
            independent_accounts = {
                post.get("account_id", "") for post in referenced_posts if post.get("account_id", "")
            }
            if len(referenced_posts) < 2 or len(independent_accounts) < 2:
                self.error(
                    "insufficient_independent_samples",
                    location,
                    "active topic needs at least two referenced posts from two accounts; use experimental otherwise",
                )

    def _registry(self) -> dict[str, dict[str, str]]:
        registry: dict[str, dict[str, str]] = {}
        for filename in ("sku-registry.csv", "offer-registry.csv"):
            for index, row in enumerate(self.rows.get(filename, []), start=2):
                eligibility_id = row.get("eligibility_id", "")
                if eligibility_id in registry:
                    self.error(
                        "duplicate_id",
                        f"{filename}:{index}",
                        f"eligibility_id {eligibility_id} already exists in another registry",
                    )
                registry[eligibility_id] = row
        return registry

    def _eligibility_has_valid_provenance(self, item: dict[str, str]) -> bool:
        run_date = parse_iso(self.run.get("created_at", ""))
        sources = {
            row.get("source_id", ""): row
            for row in self.rows.get("source-log.csv", [])
            if row.get("source_id", "")
        }
        claims = {
            row.get("claim_id", ""): row
            for row in self.rows.get("claim-ledger.csv", [])
            if row.get("claim_id", "")
        }
        ticket_id = item.get("platform_ticket", "").strip()
        ticket = sources.get(ticket_id)
        qualification_id = item.get("qualification_claim_id", "").strip()
        qualification = claims.get(qualification_id)
        evidence_ids = set(split_ids(item.get("evidence_ids")))
        if ticket is None or qualification is None:
            return False
        if not {ticket_id, qualification_id}.issubset(evidence_ids):
            return False
        if not (
            ticket.get("source_layer") == "official"
            and ticket.get("access_status") in {"full", "partial"}
            and ticket.get("evidence_grade") in {"A", "B"}
            and source_descriptors(ticket) & APPROVAL_SOURCE_TYPES
            and platforms_equivalent(ticket.get("platform"), item.get("platform"))
            and run_date
            and parse_iso(ticket.get("collected_at", "")) == run_date
        ):
            return False
        expected_category = "sku_eligibility" if "sku_id" in item else "offer_eligibility"
        if not (
            qualification.get("category") == expected_category
            and qualification.get("claim_status") == "confirmed"
            and qualification.get("evidence_grade") in {"A", "B"}
            and ticket_id in split_ids(qualification.get("source_ids"))
            and run_date
            and parse_iso(qualification.get("last_verified_at", "")) == run_date
        ):
            return False
        scope = parse_scope_contract(qualification.get("scope"))
        expected_scope = {
            "platform": item.get("platform", ""),
            "account_scope": item.get("account_scope", ""),
            "surface": item.get("surface", ""),
            "source_asset_id": item.get("source_asset_id", ""),
            "source_asset_sha256": item.get("source_asset_sha256", ""),
        }
        if "sku_id" in item:
            expected_scope["sku_id"] = item.get("sku_id", "")
        else:
            expected_scope["offer_id"] = item.get("offer_id", "")
            expected_scope["offer_type"] = item.get("offer_type", "")
        return all(
            platforms_equivalent(scope.get(key), value)
            if key == "platform"
            else scope.get(key) == value
            for key, value in expected_scope.items()
        )

    def _eligibility_is_current(self, item: dict[str, str]) -> bool:
        if item.get("status", "") not in APPROVED_ELIGIBILITY:
            return False
        run_date = parse_iso(self.run.get("created_at", ""))
        verified = parse_iso(item.get("verified_at", ""))
        if verified is None or (run_date and verified > run_date):
            return False
        if not scope_is_specific(item.get("account_scope")):
            return False
        if not scope_is_specific(item.get("platform")):
            return False
        if not scope_is_specific(item.get("surface")):
            return False
        if not scope_is_specific(item.get("source_asset_id")):
            return False
        if not valid_sha256(item.get("source_asset_sha256")):
            return False
        if not item.get("platform_ticket", "").strip():
            return False
        if not self._eligibility_has_valid_provenance(item):
            return False
        expires_raw = item.get("expires_at", "")
        if expires_raw:
            expires = parse_iso(expires_raw)
            if expires is None or (run_date and expires < run_date):
                return False
        elif run_date and verified != run_date:
            return False
        return True

    def _check_registry_rows(self) -> None:
        run_date = parse_iso(self.run.get("created_at", ""))
        for filename in ("sku-registry.csv", "offer-registry.csv"):
            for index, row in enumerate(self.rows.get(filename, []), start=2):
                if row.get("status", "") not in APPROVED_ELIGIBILITY:
                    continue
                location = f"{filename}:{index}"
                if not all(
                    scope_is_specific(row.get(field))
                    for field in ("platform", "account_scope", "surface", "source_asset_id")
                ):
                    self.error(
                        "unscoped_eligibility",
                        location,
                        "approved/confirmed eligibility requires one specific platform, account_scope, surface, and source_asset_id",
                    )
                if not row.get("platform_ticket", "").strip():
                    self.error(
                        "missing_approval_record",
                        location,
                        "approved/confirmed eligibility requires a platform ticket or exact approval record",
                    )
                if not valid_sha256(row.get("source_asset_sha256")):
                    self.error(
                        "invalid_source_asset_hash",
                        location,
                        "approved/confirmed eligibility requires a 64-character SHA-256 of the approved creative",
                    )
                if not self._eligibility_has_valid_provenance(row):
                    self.error(
                        "invalid_qualification_evidence",
                        location,
                        "approved/confirmed eligibility needs a same-run official approval-record source and matching sku/offer eligibility claim bound to the exact tuple and creative hash",
                    )
                verified = parse_iso(row.get("verified_at", ""))
                if verified is None:
                    self.error(
                        "invalid_eligibility_date",
                        location,
                        "approved/confirmed eligibility requires verified_at",
                    )
                elif run_date and verified > run_date:
                    self.error(
                        "future_date",
                        location,
                        "verified_at cannot be after the run date",
                    )
                expires_raw = row.get("expires_at", "")
                if expires_raw:
                    expires = parse_iso(expires_raw)
                    if expires is None:
                        self.error(
                            "invalid_eligibility_date",
                            location,
                            "expires_at must be YYYY-MM-DD or blank",
                        )
                    elif run_date and expires < run_date:
                        self.error(
                            "expired_eligibility",
                            location,
                            f"eligibility expired on {expires_raw}",
                        )
                elif verified and run_date and verified != run_date:
                    self.error(
                        "stale_eligibility",
                        location,
                        "eligibility without expires_at must be reverified in this run",
                    )

    def _authorization_is_current(self, row: dict[str, str]) -> bool:
        if row.get("status", "") != "approved":
            return False
        run_date = parse_iso(self.run.get("created_at", ""))
        verified = parse_iso(row.get("verified_at", ""))
        granted = parse_iso(row.get("granted_at", ""))
        if verified is None or granted is None or (run_date and verified > run_date):
            return False
        expires_raw = row.get("expires_at", "")
        if expires_raw:
            expires = parse_iso(expires_raw)
            return bool(expires and (not run_date or expires >= run_date))
        return bool(not run_date or verified == run_date)

    def _check_authorizations(self) -> None:
        run_date = parse_iso(self.run.get("created_at", ""))
        for index, row in enumerate(self.rows.get("authorization-log.csv", []), start=2):
            location = f"authorization-log.csv:{index}"
            if row.get("material_type", "") not in AUTHORIZATION_MATERIAL_TYPES:
                self.error(
                    "invalid_enum",
                    location,
                    f"invalid material_type: {row.get('material_type')}",
                )
            permissions = set(split_ids(row.get("permission_scope")))
            if not permissions or not permissions.issubset(AUTHORIZATION_PERMISSION_SCOPES):
                self.error(
                    "invalid_enum",
                    location,
                    f"invalid permission_scope: {row.get('permission_scope')}",
                )
            if row.get("commercial_use", "") not in AUTHORIZATION_COMMERCIAL_USE:
                self.error(
                    "invalid_enum",
                    location,
                    f"invalid commercial_use: {row.get('commercial_use')}",
                )
            if row.get("status", "") not in AUTHORIZATION_STATUSES:
                self.error(
                    "invalid_enum",
                    location,
                    f"invalid authorization status: {row.get('status')}",
                )
            if not scope_is_specific(row.get("subject_scope")):
                self.error(
                    "unscoped_authorization",
                    location,
                    "subject_scope must identify one documented subject or controlled case set",
                )
            if row.get("status") == "approved" and not all(
                scope_is_specific(row.get(field))
                for field in ("source_asset_id", "material_id")
            ):
                self.error(
                    "unscoped_authorization",
                    location,
                    "approved authorization must bind one source_asset_id and one material_id",
                )
            if row.get("status") == "approved" and not valid_sha256(
                row.get("material_sha256")
            ):
                self.error(
                    "invalid_authorization_hash",
                    location,
                    "approved authorization requires the SHA-256 fingerprint of the consented source material",
                )
            if row.get("status") == "approved" and not valid_sha256(
                row.get("authorized_output_sha256")
            ):
                self.error(
                    "invalid_authorization_hash",
                    location,
                    "approved authorization requires the SHA-256 of the reviewed output or consent-linked channel asset",
                )
            if row.get("status") == "approved" and not self._authorization_is_current(row):
                expires = parse_iso(row.get("expires_at", "")) if row.get("expires_at") else None
                if expires and run_date and expires < run_date:
                    code = "expired_authorization"
                else:
                    code = "stale_authorization"
                self.error(
                    code,
                    location,
                    "approved authorization must be current; without expires_at it must be reverified in this run",
                )

    def _check_draft_authorization(
        self,
        path: Path,
        meta: dict[str, str],
        authorizations: dict[str, dict[str, str]],
    ) -> None:
        truth_label = meta.get("truth_label", "")
        raw_ids = normalize_none(meta.get("authorization_ids"))
        refs = [] if raw_ids == "none" else split_ids(meta.get("authorization_ids"))
        raw_material_ids = normalize_none(meta.get("source_material_ids"))
        material_ids = (
            [] if raw_material_ids == "none" else split_ids(meta.get("source_material_ids"))
        )
        actual_output_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        if truth_label in {"factual_explainer", "fictional_scenario"}:
            if refs or material_ids:
                self.error(
                    "truth_authorization_conflict",
                    path.name,
                    f"{truth_label} must use authorization_ids=none and source_material_ids=none; choose an authorized truth label for case material",
                )
            return
        if truth_label == "first_person_documented" and refs == ["self_only"]:
            if not material_ids or not all(scope_is_specific(item) for item in material_ids):
                self.error(
                    "authorization_material_mismatch",
                    path.name,
                    "first_person_documented requires specific source_material_ids even for self_only",
                )
            return
        requirement = AUTH_REQUIRED_TRUTH_LABELS.get(truth_label)
        if truth_label == "first_person_documented" and not refs:
            self.error(
                "authorization_required",
                path.name,
                "first_person_documented requires authorization_ids=self_only or current records for other people",
            )
            return
        if requirement and len(set(refs)) < requirement[1]:
            self.error(
                "authorization_required",
                path.name,
                f"{truth_label} requires at least {requirement[1]} current authorization record(s)",
            )
        if not refs:
            return
        required_permissions = {requirement[0]} if requirement else set()
        if truth_label == "first_person_documented":
            required_permissions = {"anonymized_publish", "verbatim"}
        authorized_material_ids: set[str] = set()
        authorized_material_hashes: set[str] = set()
        authorized_subject_scopes: set[str] = set()
        for ref in refs:
            if ref == "self_only":
                self.error(
                    "authorization_required",
                    path.name,
                    f"self_only is not valid for {truth_label}",
                )
                continue
            row = authorizations.get(ref)
            if row is None:
                self.error(
                    "authorization_required",
                    path.name,
                    f"unknown authorization_id {ref}",
                )
                continue
            if not self._authorization_is_current(row):
                self.error(
                    "authorization_required",
                    path.name,
                    f"authorization {ref} is not current and approved",
                )
            if row.get("source_asset_id", "") != meta.get("draft_id", ""):
                self.error(
                    "authorization_asset_mismatch",
                    path.name,
                    f"authorization {ref} is not scoped to draft_id {meta.get('draft_id', '')}",
                )
            if row.get("authorized_output_sha256", "") != actual_output_hash:
                self.error(
                    "authorization_output_mismatch",
                    path.name,
                    f"draft bytes no longer match the reviewed output authorized by {ref}",
                )
            if row.get("material_id", ""):
                authorized_material_ids.add(row.get("material_id", ""))
            if valid_sha256(row.get("material_sha256")):
                authorized_material_hashes.add(row.get("material_sha256", "").lower())
            if row.get("subject_scope", ""):
                authorized_subject_scopes.add(row.get("subject_scope", ""))
            permissions = set(split_ids(row.get("permission_scope")))
            if required_permissions and not required_permissions & permissions:
                self.error(
                    "authorization_scope_mismatch",
                    path.name,
                    f"authorization {ref} lacks one of the required publication permissions: {', '.join(sorted(required_permissions))}",
                )
            if (
                meta.get("commercial_relationship") not in {"", "none"}
                and row.get("commercial_use") != "approved"
            ):
                self.error(
                    "authorization_scope_mismatch",
                    path.name,
                    f"authorization {ref} prohibits commercial use",
                )
        if truth_label == "composite_cases" and (
            len(authorized_material_ids) < 2
            or len(authorized_material_hashes) < 2
            or len(authorized_subject_scopes) < 2
        ):
            self.error(
                "insufficient_distinct_cases",
                path.name,
                "composite_cases requires at least two distinct subject_scope, material_id, and material_sha256 values; renamed or duplicate consent rows for one case do not count",
            )
        if set(material_ids) != authorized_material_ids:
            self.error(
                "authorization_material_mismatch",
                path.name,
                "source_material_ids must exactly match the material_id values in referenced authorizations",
            )

    def _check_channels(self) -> None:
        channels = self.rows.get("acquisition-channels.csv")
        if channels is None:
            return
        if "sku-registry.csv" not in self.rows or "offer-registry.csv" not in self.rows:
            self.error(
                "missing_file",
                "acquisition-channels.csv",
                "channels require both sku-registry.csv and offer-registry.csv",
            )
        registry = self._registry()
        known_evidence = self._id_set("source-log.csv") | self._id_set("claim-ledger.csv")
        for index, row in enumerate(channels, start=2):
            location = f"acquisition-channels.csv:{index}"
            direction = row.get("direction", "")
            if direction not in DIRECTIONS:
                self.error("invalid_enum", location, f"invalid direction: {direction}")
            channel_platform = row.get("platform", "")
            if direction in {"xhs_to_native_conversion", "xhs_to_approved_external"} and not platform_is_xhs(
                channel_platform
            ):
                self.error(
                    "direction_platform_mismatch",
                    location,
                    f"{direction} requires platform=xiaohongshu/小红书",
                )
            if direction == "external_to_xhs" and platform_is_xhs(channel_platform):
                self.error(
                    "direction_platform_mismatch",
                    location,
                    "external_to_xhs requires one specific non-Xiaohongshu source platform",
                )
            refs = split_ids(row.get("eligibility_ids"))
            surfaces = set(split_ids(row.get("surfaces")))
            cta = row.get("permitted_cta", "").strip().lower()
            has_cta = cta not in {"", "none", "no_cta"}
            if has_cta and not refs:
                self.error("missing_reference", location, "CTA requires eligibility_ids")
            if has_cta and not split_ids(row.get("evidence_ids")):
                self.error("missing_reference", location, "CTA requires current evidence_ids")
            for evidence_id in split_ids(row.get("evidence_ids")):
                if evidence_id not in known_evidence:
                    self.error(
                        "dangling_reference",
                        location,
                        f"evidence_ids references unknown id {evidence_id}",
                    )
            referenced_rows: list[dict[str, str]] = []
            for ref in refs:
                item = registry.get(ref)
                if item is None:
                    self.error("dangling_reference", location, f"unknown eligibility_id {ref}")
                    continue
                referenced_rows.append(item)
            registry_surfaces = {item.get("surface", "") for item in referenced_rows}
            if referenced_rows and surfaces != registry_surfaces:
                self.error(
                    "surface_mismatch",
                    location,
                    f"channel surfaces {sorted(surfaces)} do not match registry {sorted(registry_surfaces)}",
                )
            wrong_platform = [
                item.get("eligibility_id", "")
                for item in referenced_rows
                if item.get("platform", "") != channel_platform
            ]
            if wrong_platform:
                self.error(
                    "platform_mismatch",
                    location,
                    "channel platform does not match eligibility: " + ", ".join(wrong_platform),
                )
            channel_account = row.get("account_scope", "")
            wrong_account = [
                item.get("eligibility_id", "")
                for item in referenced_rows
                if item.get("account_scope", "") != channel_account
            ]
            if wrong_account:
                self.error(
                    "account_scope_mismatch",
                    location,
                    "channel account_scope does not match eligibility: " + ", ".join(wrong_account),
                )
            unapproved = [
                item for item in referenced_rows if not self._eligibility_is_current(item)
            ]
            wrong_asset = [
                item.get("eligibility_id", "")
                for item in referenced_rows
                if item.get("status", "") in APPROVED_ELIGIBILITY
                and (
                    item.get("source_asset_id", "") != row.get("source_asset_id", "")
                    or item.get("source_asset_sha256", "")
                    != row.get("source_asset_sha256", "")
                )
            ]
            if wrong_asset:
                self.error(
                    "source_asset_mismatch",
                    location,
                    "channel source_asset_id does not match approval record: "
                    + ", ".join(wrong_asset),
                )
            status = row.get("status", "")
            status_class = channel_status_class(status)
            if status_class is None:
                self.error(
                    "invalid_channel_status",
                    location,
                    "status must be active or an unambiguous blocked/draft/needs_* state",
                )
            is_blocked = status_class == "blocked"
            if status_class == "active" and not all(
                scope_is_specific(value)
                for value in (channel_platform, channel_account, *surfaces)
            ):
                self.error(
                    "unscoped_channel",
                    location,
                    "active channel requires one specific platform, account_scope, and surface",
                )
            if status_class == "active" and not valid_sha256(
                row.get("source_asset_sha256")
            ):
                self.error(
                    "invalid_source_asset_hash",
                    location,
                    "active channel requires the SHA-256 of the exact source asset",
                )
            if has_cta and unapproved and not is_blocked:
                ids = [item.get("eligibility_id", "") for item in unapproved]
                self.error(
                    "eligibility_not_approved",
                    location,
                    "active CTA references unapproved eligibility: " + ", ".join(ids),
                )
            if direction == "external_to_xhs" and row.get("attribution_level") not in {
                "directional",
                "user_level_with_consent",
            }:
                self.error(
                    "invalid_attribution",
                    location,
                    "external_to_xhs is directional unless a consented user-level link exists",
                )
            if row.get("attribution_level") == "user_level_with_consent":
                authorization_rows = {
                    item.get("authorization_id", ""): item
                    for item in self.rows.get("authorization-log.csv", [])
                    if item.get("authorization_id", "")
                }
                consent_ids = split_ids(row.get("consent_ids"))
                valid_consents = [
                    authorization_rows[consent_id]
                    for consent_id in consent_ids
                    if consent_id in authorization_rows
                    and self._authorization_is_current(authorization_rows[consent_id])
                    and "cross_platform_attribution"
                    in split_ids(authorization_rows[consent_id].get("permission_scope"))
                    and authorization_rows[consent_id].get("commercial_use") == "approved"
                    and authorization_rows[consent_id].get("source_asset_id")
                    == row.get("source_asset_id")
                    and authorization_rows[consent_id].get("authorized_output_sha256")
                    == row.get("source_asset_sha256")
                ]
                if len(valid_consents) != len(consent_ids) or not consent_ids:
                    self.error(
                        "missing_consent_evidence",
                        location,
                        "user-level attribution requires current explicit consent records bound to this source asset",
                    )
            if direction == "xhs_to_approved_external" and not is_blocked:
                present_kinds = {
                    "sku" if "sku_id" in item else "offer" for item in referenced_rows
                }
                product_offer_present = any(
                    item.get("offer_type", "") in PRODUCT_OFFER_TYPES
                    for item in referenced_rows
                    if "offer_id" in item
                )
                landing_asset = row.get("landing_asset", "").strip()
                landing_is_specific = bool(
                    re.fullmatch(r"https?://\S+", landing_asset)
                    or scope_is_specific(landing_asset)
                )
                external_jump_invalid = (
                    "approved_external_destination" not in surfaces
                    or not refs
                    or bool(unapproved)
                    or "offer" not in present_kinds
                    or (product_offer_present and "sku" not in present_kinds)
                    or bool(wrong_platform)
                    or bool(wrong_account)
                    or bool(wrong_asset)
                    or not landing_is_specific
                )
                if external_jump_invalid:
                    self.error(
                        "external_jump_not_approved",
                        location,
                        "active external jump requires a specific destination plus current matching offer eligibility; product offers also require SKU eligibility, all bound to the exact platform, account, surface, asset ID, and hash",
                    )

    def _check_draft_eligibility(
        self,
        path: Path,
        meta: dict[str, str],
        registry: dict[str, dict[str, str]],
    ) -> None:
        cta_type = meta.get("cta_type", "")
        if cta_type not in COMMERCIAL_CTA_TYPES:
            return
        refs = split_ids(meta.get("eligibility_ids"))
        surfaces = set(split_ids(meta.get("surfaces")))
        if not refs:
            self.error("draft_eligibility", path.name, "commercial draft CTA needs eligibility_ids")
            return
        referenced_rows: list[dict[str, str]] = []
        actual_asset_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        for ref in refs:
            item = registry.get(ref)
            if item is None:
                self.error("draft_eligibility", path.name, f"unknown eligibility_id {ref}")
                continue
            referenced_rows.append(item)
            if not self._eligibility_is_current(item):
                self.error("draft_eligibility", path.name, f"eligibility {ref} is not current and approved")
            if item.get("surface") not in surfaces:
                self.error(
                    "surface_mismatch",
                    path.name,
                    f"draft surfaces do not include registry surface {item.get('surface')}",
                )
            if item.get("platform", "") != meta.get("platform", ""):
                self.error(
                    "platform_mismatch",
                    path.name,
                    f"draft platform does not match eligibility {ref}",
                )
            if item.get("account_scope", "") != meta.get("account_scope", ""):
                self.error(
                    "account_scope_mismatch",
                    path.name,
                    f"draft account_scope does not match eligibility {ref}",
                )
            if item.get("source_asset_id", "") != meta.get("draft_id", ""):
                self.error(
                    "source_asset_mismatch",
                    path.name,
                    f"draft_id does not match approved source_asset_id for {ref}",
                )
            if item.get("source_asset_sha256", "") != actual_asset_hash:
                self.error(
                    "source_asset_mismatch",
                    path.name,
                    f"draft content hash does not match approved source_asset_sha256 for {ref}",
                )
        registry_surfaces = {item.get("surface", "") for item in referenced_rows}
        present_kinds = {
            "sku" if "sku_id" in item else "offer" for item in referenced_rows
        }
        required_kinds = set(CTA_REQUIRED_REGISTRY_KINDS.get(cta_type, set()))
        if any(
            item.get("offer_type", "") in PRODUCT_OFFER_TYPES
            for item in referenced_rows
            if "offer_id" in item
        ):
            required_kinds.add("sku")
        missing_kinds = sorted(required_kinds - present_kinds)
        if missing_kinds:
            self.error(
                "eligibility_kind_mismatch",
                path.name,
                f"{cta_type} requires registry kind(s): {', '.join(missing_kinds)}",
            )
        if referenced_rows and surfaces != registry_surfaces:
            self.error(
                "surface_mismatch",
                path.name,
                f"draft surfaces {sorted(surfaces)} do not exactly match registry {sorted(registry_surfaces)}",
            )

    def _check_drafts(self) -> None:
        drafts = self.run_dir / "drafts"
        if not drafts.is_dir():
            return
        topics = {
            row.get("topic_id", ""): row
            for row in self.rows.get("topics.csv", [])
            if row.get("topic_id", "")
        }
        authorizations = {
            row.get("authorization_id", ""): row
            for row in self.rows.get("authorization-log.csv", [])
            if row.get("authorization_id", "")
        }
        registry = self._registry()
        for path in sorted(drafts.glob("*.md")):
            try:
                text = path.read_text(encoding="utf-8-sig")
            except (OSError, UnicodeDecodeError) as exc:
                self.error("unreadable_draft", path.name, str(exc))
                continue
            meta = parse_frontmatter(text)
            rendered_text = visible_markdown(text)
            missing_meta = sorted(DRAFT_META - meta.keys())
            if missing_meta:
                self.error(
                    "draft_contract",
                    path.name,
                    "missing frontmatter: " + ", ".join(missing_meta),
                )
            if self.run.get("status") == "complete":
                for field in sorted(DRAFT_NONEMPTY_META):
                    if not meta.get(field, "").strip():
                        self.error(
                            "empty_draft_field",
                            path.name,
                            f"completed draft requires a non-empty {field}",
                        )
            truth_label = meta.get("truth_label", "")
            disclosure_text = meta.get("truth_disclosure_text", "").strip()
            disclosure_location = meta.get("truth_disclosure_location", "").strip()
            frontmatter_end = (
                rendered_text.find("\n---", 4) if rendered_text.startswith("---\n") else -1
            )
            visible_body = (
                rendered_text[frontmatter_end + 4 :]
                if frontmatter_end >= 0
                else rendered_text
            )
            first_screen = visible_body[:800]
            disclosure_patterns = TRUTH_DISCLOSURE_PATTERNS.get(truth_label, ())
            disclosure_conflicts = TRUTH_DISCLOSURE_CONFLICT_PATTERNS.get(
                truth_label, ()
            )
            marker_ok = bool(disclosure_patterns) and any(
                re.search(pattern, disclosure_text) for pattern in disclosure_patterns
            )
            conflict_found = any(
                re.search(pattern, disclosure_text) for pattern in disclosure_conflicts
            )
            if truth_label in TRUTH_LABELS and conflict_found:
                self.error(
                    "truth_disclosure_conflict",
                    path.name,
                    "truth disclosure contradicts the selected truth_label",
                )
            if truth_label in TRUTH_LABELS and not (
                marker_ok
                and not conflict_found
                and disclosure_location in VISIBLE_DISCLOSURE_LOCATIONS
                and disclosure_text
                and disclosure_text in first_screen
            ):
                self.error(
                    "truth_disclosure_missing",
                    path.name,
                    "truth label must be rendered with an accurate disclosure in the first screen/paragraph, not only stored in metadata",
                )
            heading_list = [
                match.group(1).strip()
                for match in re.finditer(
                    r"^##\s+(.+?)\s*$", rendered_text, flags=re.MULTILINE
                )
            ]
            headings = set(heading_list)
            duplicate_headings = sorted(
                heading for heading, count in Counter(heading_list).items() if count > 1
            )
            if duplicate_headings:
                self.error(
                    "duplicate_draft_section",
                    path.name,
                    "duplicate sections are forbidden: " + ", ".join(duplicate_headings),
                )
            missing_headings = sorted(DRAFT_HEADINGS - headings)
            if missing_headings:
                self.error(
                    "draft_contract",
                    path.name,
                    "missing sections: " + ", ".join(missing_headings),
                )
            if self.run.get("status") == "complete":
                for heading in sorted(DRAFT_HEADINGS & headings):
                    body = markdown_section(rendered_text, heading)
                    if not re.sub(r"[#>*_`\-\s]", "", body):
                        self.error(
                            "empty_draft_section",
                            path.name,
                            f"completed draft section has no substantive content: {heading}",
                        )
            cta_contract: dict[str, str] = {}
            if "CTA 与披露" in headings:
                cta_contract = parse_contract_block(
                    markdown_section(rendered_text, "CTA 与披露")
                )
                required_contract = {
                    "cta_type",
                    "cta_copy",
                    "commercial_relationship",
                    "disclosure_text",
                    "disclosure_location",
                    "eligibility_ids",
                    "platform",
                    "account_scope",
                    "surfaces",
                }
                missing_contract = sorted(required_contract - cta_contract.keys())
                if missing_contract:
                    self.error(
                        "cta_contract_mismatch",
                        path.name,
                        "CTA 与披露 missing keys: " + ", ".join(missing_contract),
                    )
                empty_contract = sorted(
                    key for key in required_contract if key in cta_contract and not cta_contract[key]
                )
                if empty_contract:
                    self.error(
                        "cta_contract_mismatch",
                        path.name,
                        "CTA 与披露 has empty values: " + ", ".join(empty_contract),
                    )
                for field in (
                    "cta_type",
                    "commercial_relationship",
                    "disclosure_text",
                    "disclosure_location",
                    "eligibility_ids",
                    "platform",
                    "account_scope",
                    "surfaces",
                ):
                    if field in cta_contract and normalize_none(cta_contract[field]) != normalize_none(
                        meta.get(field)
                    ):
                        self.error(
                            "cta_contract_mismatch",
                            path.name,
                            f"CTA 与披露 {field} does not match frontmatter",
                        )
                contract_cta = normalize_none(cta_contract.get("cta_type"))
                contract_copy = normalize_none(cta_contract.get("cta_copy"))
                if (contract_cta == "none") != (contract_copy == "none"):
                    self.error(
                        "cta_contract_mismatch",
                        path.name,
                        "cta_copy must be none exactly when cta_type is none",
                    )
            topic_id = meta.get("topic_id", "")
            if topic_id and topic_id not in topics:
                self.error("dangling_reference", path.name, f"unknown topic_id {topic_id}")
            elif topic_id:
                topic = topics[topic_id]
                mismatches = [
                    field
                    for field in ("primary_job", "lifecycle")
                    if meta.get(field, "") != topic.get(field, "")
                ]
                if mismatches:
                    self.error(
                        "draft_topic_mismatch",
                        path.name,
                        "draft and topic disagree on: " + ", ".join(mismatches),
                    )
            primary_job = meta.get("primary_job", "")
            if primary_job and primary_job not in PRIMARY_JOBS:
                self.error("invalid_enum", path.name, f"invalid primary_job: {primary_job}")
            lifecycle = meta.get("lifecycle", "")
            if lifecycle and lifecycle not in LIFECYCLES:
                self.error("invalid_enum", path.name, f"invalid lifecycle: {lifecycle}")
            if truth_label and truth_label not in TRUTH_LABELS:
                self.error(
                    "invalid_truth_label",
                    path.name,
                    f"invalid truth_label: {truth_label}",
                )
            relationship = meta.get("commercial_relationship", "")
            if relationship and relationship not in COMMERCIAL_RELATIONSHIPS:
                self.error(
                    "invalid_enum",
                    path.name,
                    f"invalid commercial_relationship: {relationship}",
                )
            if relationship and relationship != "none":
                commercial_disclosure = meta.get("disclosure_text", "").strip()
                commercial_location = meta.get("disclosure_location", "").strip()
                published_copy = markdown_section(rendered_text, "成稿")
                disclosure_patterns = COMMERCIAL_DISCLOSURE_PATTERNS.get(
                    relationship, ()
                )
                commercial_marker_ok = bool(disclosure_patterns) and any(
                    re.search(pattern, commercial_disclosure)
                    for pattern in disclosure_patterns
                )
                commercial_conflict = any(
                    re.search(pattern, commercial_disclosure)
                    for pattern in COMMERCIAL_DISCLOSURE_CONFLICT_PATTERNS.get(
                        relationship, ()
                    )
                )
                if commercial_conflict:
                    self.error(
                        "commercial_disclosure_conflict",
                        path.name,
                        "commercial disclosure contradicts the declared commercial_relationship",
                    )
                location_ok = False
                if commercial_location in VISIBLE_DISCLOSURE_LOCATIONS:
                    location_ok = commercial_disclosure in published_copy[:800]
                elif commercial_location in {"CTA前", "正文CTA前"}:
                    cta_copy = cta_contract.get("cta_copy", "").strip()
                    location_ok = (
                        normalize_none(cta_copy) != "none"
                        and commercial_disclosure in published_copy
                        and cta_copy in published_copy
                        and published_copy.index(commercial_disclosure)
                        < published_copy.index(cta_copy)
                    )
                if (
                    commercial_disclosure.lower() in {"", "none"}
                    or not commercial_marker_ok
                    or commercial_conflict
                    or commercial_location not in VISIBLE_COMMERCIAL_DISCLOSURE_LOCATIONS
                    or commercial_disclosure not in published_copy
                    or not location_ok
                ):
                    self.error(
                        "missing_commercial_disclosure",
                        path.name,
                        "commercial relationship requires exact disclosure_text in the visible 成稿 section and a controlled disclosure_location",
                    )
            cta_type = meta.get("cta_type", "")
            if cta_type and cta_type not in CTA_TYPES:
                self.error("invalid_enum", path.name, f"invalid cta_type: {cta_type}")
            if cta_type in COMMERCIAL_CTA_TYPES and relationship in {"", "none"}:
                self.error(
                    "commercial_cta_without_relationship",
                    path.name,
                    "commercial CTA requires the real commercial relationship and disclosure",
                )
            if cta_type in COMMERCIAL_CTA_TYPES and primary_job != "commercial_conversion":
                self.error(
                    "commercial_cta_job_mismatch",
                    path.name,
                    "commercial CTA requires primary_job=commercial_conversion",
                )
            draft_status = meta.get("status", "")
            if draft_status and draft_status not in DRAFT_STATUSES:
                self.error("invalid_enum", path.name, f"invalid draft status: {draft_status}")
            if self.run.get("status") == "complete":
                if draft_status != "ready":
                    self.error(
                        "review_not_passed",
                        path.name,
                        "completed draft run requires draft status ready",
                    )
                for heading in ("合规审校", "创意审校"):
                    review = parse_contract_block(markdown_section(rendered_text, heading))
                    if review.get("review_status") != "PASS":
                        self.error(
                            "review_not_passed",
                            path.name,
                            f"{heading} requires review_status: PASS",
                        )
            self._check_draft_authorization(path, meta, authorizations)
            self._check_draft_eligibility(path, meta, registry)


def format_text(issues: Iterable[Issue], strict: bool, status: str = "unknown") -> tuple[str, int]:
    issues = list(issues)
    errors = [issue for issue in issues if issue.severity == "error"]
    warnings = [issue for issue in issues if issue.severity == "warning"]
    lines = ["redbook-writing run validator"]
    for issue in issues:
        lines.append(
            f"[{issue.severity.upper()}] {issue.code} {issue.location}: {issue.message}"
        )
    failed = bool(errors or (strict and warnings))
    verdict = "INVALID" if failed else f"VALID_{status.upper()}"
    lines.append(f"{verdict}: {len(errors)} error(s), {len(warnings)} warning(s)")
    return "\n".join(lines) + "\n", 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate a redbook-writing run directory and its evidence/CTA contracts."
    )
    parser.add_argument("run_dir", type=Path, help="Path to research/xiaohongshu/<run>")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings (for example stale current rules) as failures.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args(argv)

    validator = RunValidator(args.run_dir.expanduser().resolve(), strict=args.strict)
    issues = validator.validate()
    run_status = validator.run.get("status", "unknown")
    text_output, exit_code = format_text(issues, args.strict, run_status)
    if args.json:
        payload = {
            "valid": exit_code == 0,
            "strict": args.strict,
            "status": run_status,
            "complete": run_status == "complete" and exit_code == 0,
            "run_dir": str(validator.run_dir),
            "errors": sum(issue.severity == "error" for issue in issues),
            "warnings": sum(issue.severity == "warning" for issue in issues),
            "issues": [asdict(issue) for issue in issues],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        sys.stdout.write(text_output)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
