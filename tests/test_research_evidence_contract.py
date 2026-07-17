import hashlib
import json
import re
import unittest
from datetime import date
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
CLAIMS_PATH = ROOT / "docs/research/2026-07-17-production-claims.json"
HUMAN_LEDGER_PATH = (
    ROOT / "docs/research/2026-07-17-production-grade-xhs-operations-evidence.md"
)
LIVE_PATH = ROOT / "docs/research/2026-07-17-live-xhs-style-observations.jsonl"
QUALIFIED_PATH = ROOT / "docs/research/qualified-cells.json"
GATE_TEMPLATE_PATH = (
    ROOT / "redbook-writing/assets/production-gate-receipts-template.jsonl"
)
STYLE_TAXONOMY_PATH = ROOT / "redbook-writing/assets/style-taxonomy-v2.json"

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
GRADES = {"A", "B", "C", "D"}

ALLOWED_USE_CODES = {
    "compliance_gate",
    "product_capability_gate",
    "sensitive_commercial_scope_gate",
    "authorization_gate",
    "creator_disclosure_gate",
    "production_process",
    "query_design",
    "asset_rights_schema",
    "audit_schema",
    "brief_field_design",
    "commercial_delivery_audit",
    "creator_role_schema",
    "distribution_audit",
    "evidence_schema",
    "feedback_schema",
    "governance_schema",
    "industrialization_guardrail",
    "measurement_design",
    "model_lifecycle_design",
    "series_architecture",
    "surface_job_schema",
    "translation_trace",
    "schema_hypothesis",
    "risk_lead",
}
PROHIBITED_USE_CODES = {
    "algorithm_causality",
    "covert_capture",
    "default_production_quota",
    "fabricated_engagement",
    "fabricated_experience",
    "fixed_capacity_threshold",
    "fixed_kpi_threshold",
    "fixed_traffic_threshold",
    "hidden_commercial_relationship",
    "organic_randomized_ab_claim",
    "performance_tier",
    "platform_wide_ban_claim",
    "rule_evidence_support",
    "style_ready_evidence",
}
MANDATORY_EXTERNAL_PROHIBITIONS = {
    "performance_tier",
    "rule_evidence_support",
    "style_ready_evidence",
    "algorithm_causality",
    "fixed_traffic_threshold",
    "fixed_kpi_threshold",
}
GRADE_ALLOWED_USE_CODES = {
    "A": ALLOWED_USE_CODES,
    "B": {
        "production_process",
        "query_design",
        "asset_rights_schema",
        "audit_schema",
        "brief_field_design",
        "commercial_delivery_audit",
        "creator_role_schema",
        "distribution_audit",
        "evidence_schema",
        "feedback_schema",
        "governance_schema",
        "industrialization_guardrail",
        "measurement_design",
        "model_lifecycle_design",
        "series_architecture",
        "surface_job_schema",
        "translation_trace",
        "schema_hypothesis",
        "risk_lead",
    },
    "C": {"schema_hypothesis", "risk_lead"},
    "D": {"schema_hypothesis", "risk_lead"},
}

REQUIRED_CLAIM_FIELDS = {
    "claim_id",
    "source_id",
    "source_url",
    "grade",
    "primary_or_secondary",
    "published_at",
    "verified_at",
    "page_or_section",
    "claim_type",
    "claim",
    "claim_text_hash",
    "allowed_use_codes",
    "prohibited_use_codes",
    "verification_status",
    "machine_usable",
    "applies_to",
    "taxonomy_version",
    "review_by",
    "limitations",
    "snapshot_sha256",
}
LEGACY_CLAIM_KEYS = {"allowed_use", "prohibited_use", "use_notes"}

REQUIRED_OBSERVATION_FIELDS = {
    "observation_id",
    "capture_date",
    "review_by",
    "surface",
    "query_fingerprint",
    "source_url",
    "platform_note_id",
    "note_id_status",
    "library_post_id",
    "library_account_id",
    "taxonomy_version",
    "carrier",
    "primary_job",
    "material_codes",
    "production_constraint_codes",
    "contraindication_codes",
    "mechanism",
    "page_observations",
    "performance_recomputability",
    "derived_tier",
    "baseline_multiple",
    "performance_receipt",
    "visible_metrics",
    "asset_sha256s",
    "visual_observation_ids",
    "copy_observation_ids",
    "evidence_role",
    "counterexample_or_boundary_ids",
    "starter_eligible",
    "qualification_status",
    "limitations",
}

CARRIERS = {
    "real_photo_diary",
    "photo_annotation",
    "screenshot_markup",
    "chat_dramatization",
    "text_card",
    "checklist_steps",
    "comparison_warning",
    "collage_journal",
    "single_image_reminder",
    "unknown",
    "other",
}
PRIMARY_JOBS = {
    "feed_stop",
    "search_answer",
    "explain",
    "trust_build",
    "decision_support",
    "relationship_build",
    "conversion",
    "authority_statement",
    "unknown",
    "other",
}
CLAIM_KINDS = {
    "series_constant",
    "task_fit",
    "contrastive_performance_hypothesis",
}
PERFORMANCE_SCOPES = {
    "not_performance_evidence",
    "public_proxy_association",
    "first_party_traffic_validated",
}
FORBIDDEN_PRIVATE_KEYS = {
    "author",
    "author_name",
    "username",
    "nickname",
    "caption",
    "caption_text",
    "ocr",
    "ocr_text",
    "raw_text",
    "raw_caption",
    "image_bytes",
    "binary",
}


def canonical_sha256(value):
    raw = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def jsonl_rows(path):
    rows = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise AssertionError(f"invalid JSONL at line {line_no}: {exc}") from exc
    return rows


def walk(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key, child
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


class ProductionClaimLedgerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = json.loads(CLAIMS_PATH.read_text(encoding="utf-8"))
        cls.claims = cls.payload["claims"]
        cls.by_id = {row["claim_id"]: row for row in cls.claims}

    def test_taxonomy_is_the_exact_v2_contract(self):
        taxonomy = self.payload["taxonomy"]
        self.assertEqual(self.payload["schema_version"], 2)
        self.assertEqual(taxonomy["taxonomy_version"], 2)
        self.assertEqual(set(taxonomy["grade"]), GRADES)
        self.assertEqual(set(taxonomy["allowed_use_code"]), ALLOWED_USE_CODES)
        self.assertEqual(set(taxonomy["prohibited_use_code"]), PROHIBITED_USE_CODES)
        self.assertEqual(
            {key: set(value) for key, value in taxonomy["grade_allowed_use_codes"].items()},
            GRADE_ALLOWED_USE_CODES,
        )

    def test_claims_are_strictly_normalized_and_fail_closed(self):
        seen = set()
        snapshot_urls = {}
        for row in self.claims:
            with self.subTest(claim_id=row.get("claim_id")):
                self.assertTrue(REQUIRED_CLAIM_FIELDS.issubset(row))
                self.assertFalse(LEGACY_CLAIM_KEYS & set(row))
                self.assertNotIn(row["claim_id"], seen)
                seen.add(row["claim_id"])
                self.assertIn(row["grade"], GRADES)
                self.assertEqual(row["taxonomy_version"], 2)
                self.assertIsInstance(row["allowed_use_codes"], list)
                self.assertIsInstance(row["prohibited_use_codes"], list)
                self.assertTrue(row["allowed_use_codes"])
                self.assertTrue(
                    set(row["allowed_use_codes"]).issubset(
                        GRADE_ALLOWED_USE_CODES[row["grade"]]
                    )
                )
                self.assertTrue(
                    set(row["prohibited_use_codes"]).issubset(PROHIBITED_USE_CODES)
                )
                self.assertTrue(
                    MANDATORY_EXTERNAL_PROHIBITIONS.issubset(
                        row["prohibited_use_codes"]
                    )
                )
                self.assertFalse(
                    set(row["allowed_use_codes"]) & set(row["prohibited_use_codes"])
                )
                parsed = urlparse(row["source_url"])
                self.assertEqual(parsed.scheme, "https")
                self.assertTrue(parsed.netloc)
                self.assertRegex(row["verified_at"], ISO_DATE_RE)
                self.assertRegex(row["review_by"], ISO_DATE_RE)
                self.assertGreaterEqual(
                    date.fromisoformat(row["review_by"]),
                    date.fromisoformat(row["verified_at"]),
                )
                self.assertEqual(
                    row["claim_text_hash"],
                    hashlib.sha256(row["claim"].encode("utf-8")).hexdigest(),
                )
                self.assertTrue(row["limitations"])
                if row["machine_usable"]:
                    self.assertRegex(row["snapshot_sha256"], SHA256_RE)
                    prior_url = snapshot_urls.setdefault(
                        row["snapshot_sha256"], row["source_url"]
                    )
                    self.assertEqual(
                        prior_url,
                        row["source_url"],
                        "one SPA shell hash cannot authenticate different pages",
                    )
                else:
                    self.assertIsNone(row["snapshot_sha256"])
                    self.assertIn("non_supporting", row["verification_status"])

    def test_s3_is_only_a_research_lead(self):
        self.assertFalse(any(row["source_id"] == "S3" for row in self.claims))
        human = HUMAN_LEDGER_PATH.read_text(encoding="utf-8")
        section = human.split("### S3｜", 1)[1].split("### S4｜", 1)[0]
        self.assertIn(
            "grade=D / metadata_only / non_supporting / research-lead-only",
            section,
        )
        for forbidden in ("可复用", "视觉/叙事线索", "candidate"):
            self.assertNotIn(forbidden, section)

    def test_current_rule_dates_and_narrow_gate_mappings_are_exact(self):
        s7 = self.by_id["CLM-S7-02"]
        self.assertEqual(s7["published_at"], "2026-07-15")
        self.assertEqual(s7["allowed_use_codes"], ["sensitive_commercial_scope_gate"])
        self.assertFalse(s7["machine_usable"])
        s30 = self.by_id["CLM-S30-01"]
        self.assertEqual(s30["published_at"], "2026-06-18")
        self.assertEqual(s30["allowed_use_codes"], ["authorization_gate"])
        self.assertFalse(s30["machine_usable"])

        expected = {
            "CLM-S31-01": ("C", {"schema_hypothesis"}),
            "CLM-S32-01": ("C", {"schema_hypothesis", "risk_lead"}),
            "CLM-S33-01": ("C", {"schema_hypothesis", "risk_lead"}),
            "CLM-S34-01": ("D", {"risk_lead"}),
        }
        for claim_id, (grade, allowed) in expected.items():
            with self.subTest(claim_id=claim_id):
                row = self.by_id[claim_id]
                self.assertEqual(row["grade"], grade)
                self.assertEqual(set(row["allowed_use_codes"]), allowed)

    def test_product_decisions_are_a_separate_owned_namespace(self):
        required = {
            "decision_id",
            "owner",
            "status",
            "review_by",
            "basis_claim_ids",
            "decision_scope",
            "limitations",
        }
        known = set(self.by_id)
        seen = set()
        for row in self.payload["product_decisions"]:
            with self.subTest(decision_id=row.get("decision_id")):
                self.assertTrue(required.issubset(row))
                self.assertNotIn("basis", row)
                self.assertNotIn(row["decision_id"], seen)
                seen.add(row["decision_id"])
                self.assertFalse(row["decision_id"].startswith("CLM-"))
                self.assertRegex(row["review_by"], ISO_DATE_RE)
                self.assertTrue(row["owner"])
                self.assertTrue(row["limitations"])
                for claim_id in row["basis_claim_ids"]:
                    self.assertIn(claim_id, known)


class LiveObservationLedgerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = jsonl_rows(LIVE_PATH)
        cls.by_id = {row["observation_id"]: row for row in cls.rows}
        cls.style_taxonomy = json.loads(
            STYLE_TAXONOMY_PATH.read_text(encoding="utf-8")
        )

    def test_all_twelve_observations_are_sanitized_and_unverified(self):
        expected = {f"O-XHS-{number:03d}" for number in range(1, 13)}
        self.assertEqual({row["observation_id"] for row in self.rows}, expected)
        self.assertEqual(len(self.rows), 12)
        for row in self.rows:
            with self.subTest(observation_id=row.get("observation_id")):
                self.assertTrue(REQUIRED_OBSERVATION_FIELDS.issubset(row))
                self.assertEqual(row["taxonomy_version"], 2)
                self.assertIn(row["carrier"], self.style_taxonomy["carrier"])
                self.assertIn(row["primary_job"], self.style_taxonomy["primary_job"])
                self.assertTrue(
                    set(row["material_codes"]).issubset(
                        self.style_taxonomy["material_code"]
                    )
                )
                self.assertTrue(
                    set(row["production_constraint_codes"]).issubset(
                        self.style_taxonomy["production_constraint_code"]
                    )
                )
                self.assertTrue(
                    set(row["contraindication_codes"]).issubset(
                        self.style_taxonomy["contraindication_code"]
                    )
                )
                self.assertIn(row["mechanism"]["claim_kind"], CLAIM_KINDS)
                self.assertIn(
                    row["mechanism"]["performance_evidence_scope"],
                    PERFORMANCE_SCOPES,
                )
                self.assertEqual(row["performance_recomputability"], "unverified")
                self.assertEqual(row["derived_tier"], "unknown")
                self.assertIsNone(row["performance_receipt"])
                self.assertEqual(row["asset_sha256s"], [])
                self.assertEqual(row["visual_observation_ids"], [])
                self.assertEqual(row["copy_observation_ids"], [])
                self.assertFalse(row["starter_eligible"])
                self.assertEqual(row["qualification_status"], "ineligible_unverified")
                self.assertTrue(row["limitations"])
                self.assertEqual(
                    row["query_fingerprint"], canonical_sha256(row["query_context"])
                )

    def test_public_proxy_metrics_are_never_labeled_as_traffic(self):
        for row in self.rows:
            with self.subTest(observation_id=row["observation_id"]):
                metrics = row["visible_metrics"]
                self.assertEqual(metrics["visibility_scope"], "public_proxy")
                self.assertEqual(metrics["traffic_verdict"], "unavailable")
                self.assertNotIn(metrics["metric_name"], {"impressions", "reach"})
                self.assertIn("公开互动", metrics["scope_note"])

    def test_o11_and_o12_keep_their_narrow_evidence_roles(self):
        o11 = self.by_id["O-XHS-011"]
        self.assertEqual(o11["mechanism"]["claim_kind"], "series_constant")
        self.assertEqual(
            o11["mechanism"]["performance_evidence_scope"],
            "public_proxy_association",
        )
        self.assertEqual(o11["evidence_role"], "same_series_control_method")
        self.assertIn("not a performance rule", o11["mechanism"]["anti_copy_boundary"])

        o12 = self.by_id["O-XHS-012"]
        self.assertEqual(o12["mechanism"]["claim_kind"], "task_fit")
        self.assertEqual(
            o12["mechanism"]["performance_evidence_scope"],
            "not_performance_evidence",
        )
        self.assertEqual(o12["evidence_role"], "carrier_boundary")

    def test_no_private_identity_binary_or_long_copy_is_committed(self):
        for row in self.rows:
            with self.subTest(observation_id=row["observation_id"]):
                for key, value in walk(row):
                    self.assertNotIn(key, FORBIDDEN_PRIVATE_KEYS)
                    if isinstance(value, str):
                        self.assertNotIn("data:image", value)
                        self.assertLessEqual(len(value), 500)
                self.assertRegex(row["library_account_id"], r"^LACC-XHS-[0-9A-F]{3}$")
                self.assertRegex(row["library_post_id"], r"^LPOST-XHS-[0-9A-F]{3}$")
                for page in row["page_observations"]:
                    self.assertIsNone(page["asset_sha256"])
                    self.assertEqual(page["capture_status"], "observed_unhashed")


class ReleaseGateTests(unittest.TestCase):
    def test_qualified_cells_truthfully_stop_starter_work(self):
        payload = json.loads(QUALIFIED_PATH.read_text(encoding="utf-8"))
        gate = payload["release_gate"]
        self.assertEqual(payload["status"], "incomplete")
        self.assertEqual(payload["qualified_cell_count"], 0)
        self.assertEqual(payload["qualified_cells"], {})
        self.assertEqual(gate["minimum_qualified_cells"], 10)
        self.assertEqual(gate["minimum_distinct_carriers"], 6)
        self.assertEqual(gate["minimum_distinct_primary_jobs"], 4)
        self.assertEqual(payload["starter_pack_action"], "forbidden")
        self.assertTrue(payload["gap_reasons"])

    def test_production_gate_template_is_only_a_fail_closed_gate(self):
        rows = jsonl_rows(GATE_TEMPLATE_PATH)
        self.assertTrue(rows)
        required = {
            "receipt_id",
            "exact_sku_id",
            "library_account_id",
            "delivery_surface",
            "rule_claim_id",
            "rule_claim_sha256",
            "claim_ledger_snapshot_sha256",
            "reviewed_at",
            "reviewer_id",
            "gate_status",
            "authorization_claim_id",
            "authorization_claim_sha256",
            "query_matrix_origin",
            "query_matrix_status",
            "rights_evidence_origin",
            "rights_evidence_status",
            "ugc_lineage_origin",
            "ugc_lineage_status",
            "distribution_evidence_origin",
            "distribution_evidence_status",
            "limitations",
            "receipt_sha256",
        }
        forbidden = {
            "style_rule_id",
            "archetype_id",
            "performance_tier",
            "starter_eligible",
        }
        for row in rows:
            with self.subTest(receipt_id=row.get("receipt_id")):
                self.assertTrue(required.issubset(row))
                self.assertFalse(forbidden & set(row))
                self.assertIn(row["gate_status"], {"blocked", "not_applicable"})
                if row["gate_status"] == "not_applicable":
                    self.assertTrue(row["not_applicable_reason"])
                self.assertTrue(row["limitations"])
                self.assertRegex(row["receipt_sha256"], SHA256_RE)


if __name__ == "__main__":
    unittest.main()
