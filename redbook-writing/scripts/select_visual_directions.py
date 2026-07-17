#!/usr/bin/env python3
"""Select evidence/attention skeletons without inventing materials or aesthetics."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any


DEFAULT_LIBRARY = (
    Path(__file__).resolve().parents[1]
    / "assets"
    / "visual-direction-cards-v1.json"
)


class ContractError(ValueError):
    """Raised when a packaged or run-supplied contract is malformed."""


def emit(payload: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    print(f"status: {payload['status']}")
    if payload.get("message"):
        print(payload["message"])
    for gap in payload.get("prototype_gaps", []):
        print(f"\n[{gap['card_id']}] {gap['name']}")
        if gap.get("missing_materials"):
            print("missing_materials: " + ", ".join(gap["missing_materials"]))
        if gap.get("active_contraindications"):
            print(
                "active_contraindications: "
                + ", ".join(gap["active_contraindications"])
            )
    for match in payload.get("matches", []):
        print(f"\n[{match['card_id']}] {match['name']}")
        print("attention: " + " → ".join(match["attention_path"]["sequence"]))
        print("carrier_plan: " + match["carrier_role_plan"]["output_shape"])
        print("aesthetics: " + match["aesthetic_control"]["source"])


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"{label} cannot be read as JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ContractError(f"{label} must be a JSON object")
    return payload


def load_library(path: Path) -> dict[str, Any]:
    payload = load_json(path, "visual direction library")
    if payload.get("schema_version") != "1.1.0":
        raise ContractError("unsupported visual direction library schema")
    cards = payload.get("cards")
    if not isinstance(cards, list) or not cards:
        raise ContractError("visual direction library cards must be non-empty")

    required_top = {
        "carrier_taxonomy",
        "primary_job_taxonomy",
        "asset_manifest_contract",
        "style_binding_contract",
    }
    if required_top - set(payload):
        raise ContractError("visual direction library missing machine contracts")

    card_ids = {card.get("card_id") for card in cards if isinstance(card, dict)}
    if None in card_ids or len(card_ids) != len(cards):
        raise ContractError("card_id values must be present and unique")

    carriers = set(payload["carrier_taxonomy"])
    jobs = set(payload["primary_job_taxonomy"])
    allowed_eligibility = set(payload["selection_eligibility_taxonomy"])
    null_behaviors = {
        "block_selection",
        "omit_clause",
        "render_as_not_applicable",
        "require_human_review",
    }
    required_fields = {
        "maturity",
        "selection_eligibility",
        "decision_predicate",
        "not_for",
        "nearest_alternative",
        "carrier_role_plans",
        "material_count_gates",
        "prompt_variables",
        "prompt_template",
    }
    for card in cards:
        card_id = card.get("card_id", "unknown")
        missing = required_fields - set(card)
        if missing:
            raise ContractError(f"{card_id} missing fields: {', '.join(sorted(missing))}")
        if card.get("performance_evidence_status") != "candidate_only":
            raise ContractError(f"{card_id} is not candidate_only")
        if card.get("performance_evidence_scope") != "not_performance_evidence":
            raise ContractError(f"{card_id} overstates performance evidence")
        if card.get("starter_eligible") is not False:
            raise ContractError(f"{card_id} cannot be starter eligible")
        if card.get("maturity") != "prototype":
            raise ContractError(f"{card_id} has unsupported maturity")
        if card.get("selection_eligibility") not in allowed_eligibility:
            raise ContractError(f"{card_id} has invalid selection_eligibility")
        if card.get("aesthetic_authority") != "published_style_binding_only":
            raise ContractError(f"{card_id} lets candidate guidance control aesthetics")

        suitable = card.get("suitable", {})
        card_carriers = set(suitable.get("carriers", []))
        card_jobs = set(suitable.get("primary_jobs", []))
        if not card_carriers or card_carriers - carriers:
            raise ContractError(f"{card_id} has unknown or empty carrier fit")
        if not card_jobs or card_jobs - jobs:
            raise ContractError(f"{card_id} has unknown or empty primary_job fit")
        if set(card["carrier_role_plans"]) != card_carriers:
            raise ContractError(f"{card_id} carrier role plan drift")
        if set(card["material_count_gates"]) != card_carriers:
            raise ContractError(f"{card_id} material count gate drift")

        variables: dict[str, dict[str, Any]] = {}
        for variable in card["prompt_variables"]:
            if not isinstance(variable, dict):
                raise ContractError(f"{card_id} has untyped prompt variable")
            if not {"name", "type", "required", "null_behavior"}.issubset(variable):
                raise ContractError(f"{card_id} has incomplete prompt variable")
            if variable["name"] in variables:
                raise ContractError(f"{card_id} has duplicate prompt variable")
            if variable["null_behavior"] not in null_behaviors:
                raise ContractError(f"{card_id} has invalid null behavior")
            if variable["required"] and variable["null_behavior"] != "block_selection":
                raise ContractError(f"{card_id} required variable does not fail closed")
            variables[variable["name"]] = variable
        if "asset_manifest_refs" not in variables:
            raise ContractError(f"{card_id} does not require asset_manifest_refs")

        proof_names = {
            role["required_proof"] for role in card.get("page_roles", [])
        }
        for plan in card["carrier_role_plans"].values():
            roles = plan.get("roles")
            if not isinstance(roles, list) or not roles:
                raise ContractError(f"{card_id} has empty carrier roles")
            merge = plan.get("single_image_merge", {})
            if plan.get("output_shape") == "single_image":
                if merge.get("allowed") is not True or not merge.get("merge_rule"):
                    raise ContractError(f"{card_id} lacks single-image merge rule")
            elif merge.get("allowed") is not False:
                raise ContractError(f"{card_id} wrongly permits single-image merge")
            proof_names.update(role["required_proof"] for role in roles)
        for proof_name in proof_names:
            variable = variables.get(proof_name)
            if not variable or not variable["required"]:
                raise ContractError(f"{card_id} proof {proof_name} is not required")

        placeholders = set(re.findall(r"\{([A-Za-z0-9_]+)\}", card["prompt_template"]))
        undeclared = placeholders - set(variables)
        if undeclared:
            raise ContractError(
                f"{card_id} prompt placeholders undeclared: {', '.join(sorted(undeclared))}"
            )
        if "asset_manifest_refs" not in placeholders:
            raise ContractError(f"{card_id} prompt does not bind asset manifest")
        for carrier, gates in card["material_count_gates"].items():
            if not isinstance(gates, list) or not gates:
                raise ContractError(f"{card_id}/{carrier} has no material count gates")
            for gate in gates:
                if (
                    not isinstance(gate.get("min_distinct_asset_refs"), int)
                    or gate["min_distinct_asset_refs"] < 1
                    or not gate.get("material_code")
                ):
                    raise ContractError(f"{card_id}/{carrier} has invalid count gate")
        for alternative in card["nearest_alternative"]:
            if alternative.get("card_id") not in card_ids or not alternative.get("when"):
                raise ContractError(f"{card_id} has invalid nearest alternative")

    raw = json.dumps(payload, ensure_ascii=False)
    if re.search(r"\d+\s*%|\d+\s*％", raw):
        raise ContractError("candidate library contains unsupported fixed ratios")
    if re.search(r"\d+\s*[—-]\s*\d+\s*字|\d+\s*字(?:内|以下|以上)", raw):
        raise ContractError("candidate library contains unsupported word limits")
    return payload


def validate_asset_manifest(
    payload: dict[str, Any], contract: dict[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, set[str]]]:
    assets = payload.get(contract["container_field"])
    if not isinstance(assets, list) or not assets:
        raise ContractError("asset_manifest_refs must be a non-empty array")
    required_fields = set(contract["required_fields"])
    allowed_rights = set(contract["rights_basis_allowed"])
    allowed_privacy = set(contract["privacy_review_allowed"])
    allowed_commercial = set(contract["commercial_disclosure_allowed"])
    ids: set[str] = set()
    material_assets: dict[str, set[str]] = defaultdict(set)

    for index, asset in enumerate(assets):
        if not isinstance(asset, dict):
            raise ContractError(f"asset_manifest_refs[{index}] must be an object")
        missing = required_fields - set(asset)
        if missing:
            raise ContractError(
                f"asset_manifest_refs[{index}] missing " + ", ".join(sorted(missing))
            )
        asset_id = asset.get("asset_id")
        if not isinstance(asset_id, str) or not asset_id.strip() or asset_id in ids:
            raise ContractError(f"asset_manifest_refs[{index}] has invalid/duplicate asset_id")
        ids.add(asset_id)
        codes = asset.get("material_codes")
        if (
            not isinstance(codes, list)
            or not codes
            or any(not isinstance(code, str) or not code.strip() for code in codes)
        ):
            raise ContractError(f"asset {asset_id} has invalid material_codes")
        if not isinstance(asset.get("sha256"), str) or not re.fullmatch(
            r"[0-9a-f]{64}", asset["sha256"]
        ):
            raise ContractError(f"asset {asset_id} has invalid sha256")
        rights = asset.get("rights_basis")
        if rights not in allowed_rights:
            raise ContractError(f"asset {asset_id} has invalid rights_basis")
        if rights == "written_permission" and not asset.get("authorization_ref"):
            raise ContractError(f"asset {asset_id} requires authorization_ref")
        if rights == "licensed" and not asset.get("license_ref"):
            raise ContractError(f"asset {asset_id} requires license_ref")
        for nullable_field in ("authorization_ref", "license_ref"):
            value = asset.get(nullable_field)
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise ContractError(f"asset {asset_id} has invalid {nullable_field}")
        if not isinstance(asset.get("transform_history"), list):
            raise ContractError(f"asset {asset_id} has invalid transform_history")
        if asset.get("privacy_review") not in allowed_privacy:
            raise ContractError(f"asset {asset_id} has invalid privacy_review")
        if asset.get("commercial_disclosure") not in allowed_commercial:
            raise ContractError(f"asset {asset_id} has invalid commercial_disclosure")
        expires_at = asset.get("expires_at")
        if expires_at is not None:
            if not isinstance(expires_at, str):
                raise ContractError(f"asset {asset_id} has invalid expires_at")
            try:
                expiry = date.fromisoformat(expires_at[:10])
            except ValueError as exc:
                raise ContractError(f"asset {asset_id} has invalid expires_at") from exc
            if expiry < date.today():
                raise ContractError(f"asset {asset_id} receipt is expired")
        for code in codes:
            material_assets[code].add(asset_id)
    return assets, material_assets


def validate_style_binding(
    payload: dict[str, Any], contract: dict[str, Any], job: str, carrier: str
) -> dict[str, Any]:
    required = set(contract["required_fields"])
    missing = required - set(payload)
    if missing:
        raise ContractError("style binding missing " + ", ".join(sorted(missing)))
    if payload.get("status") != contract["status_required"]:
        raise ContractError("style binding is not published")
    if payload.get("primary_job") != job or payload.get("carrier") != carrier:
        raise ContractError("style binding does not exactly match primary_job/carrier")
    if not isinstance(payload.get("style_rule_ids"), list) or not payload["style_rule_ids"]:
        raise ContractError("style binding has no published style_rule_ids")
    aesthetic = payload.get("aesthetic_contract")
    if not isinstance(aesthetic, dict):
        raise ContractError("style binding aesthetic_contract must be an object")
    missing_aesthetic = set(contract["aesthetic_fields_required"]) - set(aesthetic)
    if missing_aesthetic:
        raise ContractError(
            "style binding missing aesthetic fields: "
            + ", ".join(sorted(missing_aesthetic))
        )
    return payload


def card_gap(
    card: dict[str, Any], carrier: str, material_assets: dict[str, set[str]],
    active_contraindications: set[str]
) -> dict[str, Any]:
    required = set(card["suitable"]["required_materials"])
    available = {code for code, asset_ids in material_assets.items() if asset_ids}
    missing = sorted(required - available)
    count_gaps = []
    for gate in card["material_count_gates"][carrier]:
        actual = len(material_assets.get(gate["material_code"], set()))
        if actual < gate["min_distinct_asset_refs"]:
            count_gaps.append(
                {
                    "material_code": gate["material_code"],
                    "required": gate["min_distinct_asset_refs"],
                    "actual": actual,
                    "reason": gate["reason"],
                }
            )
    contraindications = sorted(
        set(card["suitable"]["contraindications"]) & active_contraindications
    )
    return {
        "card_id": card["card_id"],
        "name": card["name"],
        "missing_materials": missing,
        "material_count_gaps": count_gaps,
        "active_contraindications": contraindications,
        "nearest_alternative": card["nearest_alternative"],
    }


def selected_card(
    card: dict[str, Any], carrier: str, material_assets: dict[str, set[str]],
    binding: dict[str, Any] | None, mode: str
) -> dict[str, Any]:
    material_receipts = {
        code: sorted(material_assets[code])
        for code in card["suitable"]["required_materials"]
    }
    aesthetic_control = (
        {
            "source": "published_style_binding",
            "binding_id": binding["binding_id"],
            "snapshot_id": binding["snapshot_id"],
            "style_rule_ids": binding["style_rule_ids"],
            "aesthetic_contract": binding["aesthetic_contract"],
        }
        if binding
        else {
            "source": "unbound_exploration",
            "binding_id": None,
            "aesthetic_contract": None,
        }
    )
    return {
        "card_id": card["card_id"],
        "name": card["name"],
        "maturity": card["maturity"],
        "selection_eligibility": card["selection_eligibility"],
        "performance_evidence_status": card["performance_evidence_status"],
        "performance_evidence_scope": card["performance_evidence_scope"],
        "query_fit": {"primary_job": "exact", "carrier": "exact"},
        "material_receipts": material_receipts,
        "attention_path": card["attention_path"],
        "cover_job": card["cover"]["job"],
        "carrier_role_plan": card["carrier_role_plans"][carrier],
        "image_caption_division": card["image_caption_division"],
        "prompt_variables": card["prompt_variables"],
        "prompt_template": card["prompt_template"],
        "negative_prompt": card["negative_prompt"],
        "anti_ppt_check": card["anti_ppt_check"],
        "failure_conditions": card["failure_conditions"],
        "rights": card["rights"],
        "aesthetic_control": aesthetic_control,
        "direction_card_controls": [
            "attention_path",
            "proof_order",
            "carrier_role_plan",
            "image_caption_division",
            "truth_and_rights_boundaries",
        ],
        "direction_card_controls_aesthetics": False,
        "sole_direction_allowed": mode == "exploration",
        "output_ceiling": (
            "prototype_only" if mode == "exploration" else "rendered_needs_review"
        ),
    }


def select(
    library: dict[str, Any], job: str, carrier: str,
    manifest: dict[str, Any] | None, binding: dict[str, Any] | None,
    active_contraindications: set[str], mode: str, limit: int
) -> tuple[dict[str, Any], int]:
    invalid = []
    if job not in library["primary_job_taxonomy"]:
        invalid.append(f"primary_job={job}")
    if carrier not in library["carrier_taxonomy"]:
        invalid.append(f"carrier={carrier}")
    unknown_contraindications = active_contraindications - set(
        library["contraindication_taxonomy"]
    )
    invalid.extend(
        f"contraindication={value}" for value in sorted(unknown_contraindications)
    )
    if invalid:
        return {
            "status": "invalid_query",
            "message": "invalid taxonomy value(s): " + ", ".join(invalid),
            "matches": [],
        }, 2

    query = {
        "primary_job": job,
        "carrier": carrier,
        "mode": mode,
        "active_contraindications": sorted(active_contraindications),
    }
    if manifest is None:
        return {
            "status": "prototype_gap",
            "message": "asset_manifest_refs are required; no direction is inferred.",
            "query": query,
            "missing_requirements": ["asset_manifest_refs"],
            "matches": [],
        }, 2
    try:
        _, material_assets = validate_asset_manifest(
            manifest, library["asset_manifest_contract"]
        )
    except ContractError as exc:
        return {
            "status": "invalid_asset_manifest",
            "message": str(exc),
            "query": query,
            "matches": [],
        }, 2

    structural = [
        card
        for card in library["cards"]
        if job in card["suitable"]["primary_jobs"]
        and carrier in card["suitable"]["carriers"]
    ]
    if not structural:
        alternatives = [
            {
                "card_id": card["card_id"],
                "name": card["name"],
                "matching_jobs": sorted(set(card["suitable"]["primary_jobs"]) & {job}),
                "matching_carriers": sorted(set(card["suitable"]["carriers"]) & {carrier}),
                "nearest_alternative": card["nearest_alternative"],
            }
            for card in library["cards"]
            if job in card["suitable"]["primary_jobs"]
            or carrier in card["suitable"]["carriers"]
        ]
        return {
            "status": "no_eligible_card",
            "message": "No card exactly matches both primary_job and carrier.",
            "query": query,
            "prototype_gaps": alternatives,
            "matches": [],
        }, 2

    gaps = [
        card_gap(card, carrier, material_assets, active_contraindications)
        for card in structural
    ]
    eligible = [
        card
        for card, gap in zip(structural, gaps)
        if not gap["missing_materials"]
        and not gap["material_count_gaps"]
        and not gap["active_contraindications"]
    ]
    if not eligible:
        return {
            "status": "no_eligible_card",
            "message": "Exact candidates exist, but materials/count gates/contraindications fail.",
            "query": query,
            "prototype_gaps": gaps,
            "matches": [],
        }, 2

    if mode == "production":
        if binding is None:
            return {
                "status": "prototype_gap",
                "message": "Candidate skeletons cannot control production aesthetics.",
                "query": query,
                "missing_requirements": ["published_style_binding"],
                "prototype_candidates": [card["card_id"] for card in eligible],
                "matches": [],
            }, 2
        try:
            validated_binding = validate_style_binding(
                binding, library["style_binding_contract"], job, carrier
            )
        except ContractError as exc:
            return {
                "status": "prototype_gap",
                "message": str(exc),
                "query": query,
                "missing_requirements": ["exact_published_style_binding"],
                "prototype_candidates": [card["card_id"] for card in eligible],
                "matches": [],
            }, 2
        non_series = [
            card
            for card in eligible
            if card["selection_eligibility"] != "series_modifier_only"
        ]
        if not non_series:
            return {
                "status": "prototype_gap",
                "message": "A series modifier cannot be the sole production direction.",
                "query": query,
                "missing_requirements": ["base_direction_card"],
                "prototype_candidates": [card["card_id"] for card in eligible],
                "matches": [],
            }, 2
        ordered = non_series + [
            card for card in eligible if card not in non_series
        ]
        matches = [
            selected_card(card, carrier, material_assets, validated_binding, mode)
            for card in ordered[:limit]
        ]
        return {
            "status": "matched",
            "message": "Direction cards control evidence/attention only; binding controls aesthetics.",
            "query": query,
            "matches": matches,
        }, 0

    matches = [
        selected_card(card, carrier, material_assets, None, mode)
        for card in eligible[:limit]
    ]
    return {
        "status": "matched_exploration",
        "message": "Explicit exploration may use one candidate direction, but it remains prototype_only and cannot become ready.",
        "query": query,
        "matches": matches,
    }, 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Select Xiaohongshu visual evidence/attention skeletons."
    )
    parser.add_argument("--job", required=True, help="Exact primary_job taxonomy value")
    parser.add_argument("--carrier", required=True, help="Exact carrier taxonomy value")
    parser.add_argument(
        "--asset-manifest", type=Path, help="JSON object containing asset_manifest_refs"
    )
    parser.add_argument(
        "--style-binding", type=Path, help="Exact published style-binding receipt"
    )
    parser.add_argument(
        "--contraindication", action="append", default=[],
        help="Active contraindication code; repeat as needed",
    )
    parser.add_argument(
        "--mode", choices=("production", "exploration"), default="production"
    )
    parser.add_argument("--limit", type=int, default=2)
    parser.add_argument("--library", type=Path, default=DEFAULT_LIBRARY)
    parser.add_argument("--json", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.limit < 1:
        emit(
            {"status": "invalid_query", "message": "limit must be >= 1", "matches": []},
            args.json,
        )
        return 2
    try:
        library = load_library(args.library)
        manifest = (
            load_json(args.asset_manifest, "asset manifest")
            if args.asset_manifest
            else None
        )
        style_binding = (
            load_json(args.style_binding, "style binding")
            if args.style_binding
            else None
        )
    except ContractError as exc:
        emit(
            {"status": "invalid_contract", "message": str(exc), "matches": []},
            args.json,
        )
        return 2
    payload, code = select(
        library=library,
        job=args.job,
        carrier=args.carrier,
        manifest=manifest,
        binding=style_binding,
        active_contraindications=set(args.contraindication),
        mode=args.mode,
        limit=args.limit,
    )
    emit(payload, args.json)
    return code


if __name__ == "__main__":
    sys.exit(main())
