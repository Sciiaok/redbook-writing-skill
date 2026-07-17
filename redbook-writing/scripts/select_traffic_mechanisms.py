#!/usr/bin/env python3
"""Select bounded Xiaohongshu traffic-mechanism cards from the packaged library."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


DEFAULT_LIBRARY = Path(__file__).resolve().parents[1] / "assets" / "traffic-mechanisms-v1.json"


def emit(payload: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    print(f"status: {payload['status']}")
    if payload.get("message"):
        print(payload["message"])
    for match in payload.get("matches", []):
        print(f"\n{match['mechanism_id']}  {match['name']}  score={match['selection_score']}")
        print(match["one_line_formula"])
        print("inputs: " + "；".join(match["inputs"]))
        print("failure: " + "；".join(match["failure_conditions"]))


def load_library(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if payload.get("schema_version") != "1.0.0" or not isinstance(
        payload.get("mechanisms"), list
    ):
        raise ValueError("unsupported or malformed mechanism library")
    return payload


def score_card(card: dict[str, Any], stage: str, job: str, carrier: str | None) -> int:
    traffic = card["traffic_stage"]
    score = 4 if traffic["primary"] == stage else 2
    if job not in card["primary_jobs"]:
        return -1
    score += 4
    if carrier:
        fit = card["carrier_task_fit"]
        if carrier in fit["preferred"]:
            score += 3
        elif carrier in fit["compatible"]:
            score += 1
        else:
            return -1
    return score


def select(
    library: dict[str, Any],
    stage: str,
    job: str,
    carrier: str | None,
    limit: int,
) -> tuple[dict[str, Any], int]:
    invalid: list[str] = []
    if stage not in library["traffic_stage_taxonomy"]:
        invalid.append(f"traffic_stage={stage}")
    if job not in library["primary_job_taxonomy"]:
        invalid.append(f"primary_job={job}")
    if carrier and carrier not in library["carrier_taxonomy"]:
        invalid.append(f"carrier={carrier}")
    if invalid:
        return (
            {
                "status": "invalid_query",
                "message": "invalid taxonomy value(s): " + ", ".join(invalid),
                "matches": [],
            },
            2,
        )

    ranked: list[tuple[int, dict[str, Any]]] = []
    for card in library["mechanisms"]:
        stages = [card["traffic_stage"]["primary"], *card["traffic_stage"]["secondary"]]
        if stage not in stages:
            continue
        score = score_card(card, stage, job, carrier)
        if score >= 0:
            ranked.append((score, card))
    ranked.sort(key=lambda item: (-item[0], item[1]["mechanism_id"]))

    matches: list[dict[str, Any]] = []
    for score, card in ranked[:limit]:
        selected = {
            key: card[key]
            for key in (
                "mechanism_id",
                "name",
                "one_line_formula",
                "traffic_stage",
                "primary_jobs",
                "carrier_task_fit",
                "inputs",
                "actions",
                "metrics",
                "failure_conditions",
                "anti_cargo_cult",
                "source_refs",
            )
        }
        selected["selection_score"] = score
        matches.append(selected)

    if not matches:
        return (
            {
                "status": "needs_research",
                "message": (
                    "No exact task-fit mechanism. Keep the same primary job and carrier; "
                    "collect real materials, a counterexample, and current comparable samples."
                ),
                "query": {"traffic_stage": stage, "primary_job": job, "carrier": carrier},
                "matches": [],
            },
            2,
        )
    return (
        {
            "status": "matched",
            "library_id": library["library_id"],
            "snapshot_date": library["snapshot_date"],
            "query": {"traffic_stage": stage, "primary_job": job, "carrier": carrier},
            "warning": library["non_guarantee"],
            "matches": matches,
        },
        0,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Select task-fit mechanism cards; output is not a viral prediction."
    )
    parser.add_argument("--stage", required=True)
    parser.add_argument("--job", required=True)
    parser.add_argument("--carrier")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--library", type=Path, default=DEFAULT_LIBRARY)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if args.limit < 1:
        emit({"status": "invalid_query", "message": "limit must be >= 1", "matches": []}, args.json)
        return 2
    try:
        library = load_library(args.library.expanduser().resolve())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        emit({"status": "library_error", "message": str(exc), "matches": []}, args.json)
        return 2
    payload, exit_code = select(library, args.stage, args.job, args.carrier, args.limit)
    emit(payload, args.json)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
