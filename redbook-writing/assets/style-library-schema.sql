PRAGMA foreign_keys = ON;

BEGIN;

CREATE TABLE IF NOT EXISTS style_accounts (
    library_account_id TEXT PRIMARY KEY NOT NULL,
    platform TEXT NOT NULL,
    platform_account_id TEXT,
    profile_url TEXT,
    identity_confidence REAL NOT NULL DEFAULT 1.0
        CHECK (identity_confidence >= 0.0 AND identity_confidence <= 1.0),
    first_seen_at TEXT,
    last_seen_at TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_style_accounts_platform_identity
    ON style_accounts(platform, platform_account_id)
    WHERE platform_account_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS style_assets (
    asset_id TEXT PRIMARY KEY NOT NULL,
    asset_kind TEXT NOT NULL
        CHECK (asset_kind IN ('image', 'caption', 'ocr', 'thumbnail', 'generated')),
    source_url TEXT,
    asset_path TEXT,
    asset_sha256 TEXT NOT NULL UNIQUE,
    mime_type TEXT,
    width INTEGER CHECK (width IS NULL OR width >= 0),
    height INTEGER CHECK (height IS NULL OR height >= 0),
    collected_at TEXT,
    access_status TEXT NOT NULL DEFAULT 'available',
    observation_method TEXT NOT NULL DEFAULT 'direct',
    copyright_notes TEXT NOT NULL DEFAULT '',
    sensitivity TEXT NOT NULL DEFAULT 'unknown',
    retention_until TEXT,
    derivative_of TEXT,
    FOREIGN KEY (derivative_of) REFERENCES style_assets(asset_id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    CHECK (derivative_of IS NULL OR derivative_of <> asset_id),
    CHECK (
        asset_path IS NULL
        OR (
            (asset_path GLOB 'raw/*' OR asset_path GLOB 'derived/*')
            AND replace(asset_path, '\', '/') NOT LIKE '../%'
            AND replace(asset_path, '\', '/') NOT LIKE '%/../%'
            AND replace(asset_path, '\', '/') NOT LIKE '%/..'
        )
    )
);

CREATE INDEX IF NOT EXISTS ix_style_assets_derivative
    ON style_assets(derivative_of);

CREATE TABLE IF NOT EXISTS style_posts (
    library_post_id TEXT PRIMARY KEY NOT NULL,
    platform TEXT NOT NULL,
    note_id TEXT,
    canonical_url TEXT,
    library_account_id TEXT NOT NULL,
    identity_confidence REAL NOT NULL DEFAULT 1.0
        CHECK (identity_confidence >= 0.0 AND identity_confidence <= 1.0),
    category TEXT NOT NULL DEFAULT '',
    published_at TEXT,
    format TEXT NOT NULL DEFAULT '',
    caption_asset_id TEXT,
    duplicate_of TEXT,
    cluster_id TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    FOREIGN KEY (library_account_id) REFERENCES style_accounts(library_account_id)
        ON UPDATE CASCADE,
    FOREIGN KEY (caption_asset_id) REFERENCES style_assets(asset_id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    FOREIGN KEY (duplicate_of) REFERENCES style_posts(library_post_id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    CHECK (duplicate_of IS NULL OR duplicate_of <> library_post_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_style_posts_platform_note
    ON style_posts(platform, note_id)
    WHERE note_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS ix_style_posts_account
    ON style_posts(library_account_id);

CREATE INDEX IF NOT EXISTS ix_style_posts_cluster
    ON style_posts(cluster_id);

CREATE TABLE IF NOT EXISTS run_account_refs (
    run_id TEXT NOT NULL,
    run_account_id TEXT NOT NULL,
    library_account_id TEXT NOT NULL,
    PRIMARY KEY (run_id, run_account_id),
    FOREIGN KEY (library_account_id) REFERENCES style_accounts(library_account_id)
        ON UPDATE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_run_account_refs_library_account
    ON run_account_refs(library_account_id);

CREATE TABLE IF NOT EXISTS run_post_refs (
    run_id TEXT NOT NULL,
    run_post_id TEXT NOT NULL,
    library_post_id TEXT NOT NULL,
    PRIMARY KEY (run_id, run_post_id),
    UNIQUE (run_id, run_post_id, library_post_id),
    FOREIGN KEY (library_post_id) REFERENCES style_posts(library_post_id)
        ON UPDATE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_run_post_refs_library_post
    ON run_post_refs(library_post_id);

CREATE TABLE IF NOT EXISTS run_query_refs (
    run_id TEXT NOT NULL,
    run_query_id TEXT NOT NULL,
    query_fingerprint TEXT NOT NULL,
    PRIMARY KEY (run_id, run_query_id)
);

CREATE INDEX IF NOT EXISTS ix_run_query_refs_fingerprint
    ON run_query_refs(query_fingerprint);

CREATE TABLE IF NOT EXISTS account_baseline_snapshots (
    baseline_snapshot_id TEXT PRIMARY KEY NOT NULL,
    library_account_id TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    window_start TEXT,
    window_end TEXT,
    sample_n INTEGER NOT NULL DEFAULT 0 CHECK (sample_n >= 0),
    median_value REAL,
    format_filter TEXT NOT NULL DEFAULT '',
    paid_or_pinned_filter TEXT NOT NULL DEFAULT '',
    missing_value_policy TEXT NOT NULL DEFAULT '',
    source_run_id TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (library_account_id) REFERENCES style_accounts(library_account_id)
        ON UPDATE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_account_baselines_account_metric
    ON account_baseline_snapshots(library_account_id, metric_name);

CREATE TABLE IF NOT EXISTS style_post_observations (
    post_observation_id TEXT PRIMARY KEY NOT NULL,
    library_post_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    run_post_id TEXT NOT NULL,
    source_csv_sha256 TEXT NOT NULL,
    collected_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    baseline_snapshot_id TEXT,
    account_baseline_multiple REAL
        CHECK (account_baseline_multiple IS NULL OR account_baseline_multiple >= 0.0),
    performance_tier TEXT NOT NULL DEFAULT 'unknown'
        CHECK (performance_tier IN ('high', 'ordinary', 'low', 'unknown')),
    query_fingerprints TEXT NOT NULL DEFAULT '[]',
    search_surface TEXT NOT NULL DEFAULT '',
    sort_or_filter TEXT NOT NULL DEFAULT '',
    known_confounds TEXT NOT NULL DEFAULT '[]',
    FOREIGN KEY (run_id, run_post_id, library_post_id)
        REFERENCES run_post_refs(run_id, run_post_id, library_post_id)
        ON UPDATE CASCADE,
    FOREIGN KEY (baseline_snapshot_id)
        REFERENCES account_baseline_snapshots(baseline_snapshot_id)
        ON UPDATE CASCADE ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS ix_style_post_observations_post
    ON style_post_observations(library_post_id);

CREATE INDEX IF NOT EXISTS ix_style_post_observations_run_post
    ON style_post_observations(run_id, run_post_id);

CREATE INDEX IF NOT EXISTS ix_style_post_observations_baseline
    ON style_post_observations(baseline_snapshot_id);

CREATE TABLE IF NOT EXISTS post_metrics (
    post_metric_id TEXT PRIMARY KEY NOT NULL,
    post_observation_id TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    observed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    post_age_hours REAL CHECK (post_age_hours IS NULL OR post_age_hours >= 0.0),
    visibility_scope TEXT NOT NULL DEFAULT 'unknown',
    FOREIGN KEY (post_observation_id)
        REFERENCES style_post_observations(post_observation_id)
        ON UPDATE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_post_metrics_observation_metric
    ON post_metrics(post_observation_id, metric_name);

CREATE TABLE IF NOT EXISTS style_slides (
    slide_id TEXT PRIMARY KEY NOT NULL,
    library_post_id TEXT NOT NULL,
    slide_index INTEGER NOT NULL CHECK (slide_index >= 0),
    slide_role TEXT NOT NULL DEFAULT 'other',
    asset_id TEXT,
    ocr_asset_id TEXT,
    ocr_confidence REAL
        CHECK (ocr_confidence IS NULL OR (ocr_confidence >= 0.0 AND ocr_confidence <= 1.0)),
    access_status TEXT NOT NULL DEFAULT 'available',
    observation_method TEXT NOT NULL DEFAULT 'direct',
    taxonomy_version INTEGER NOT NULL DEFAULT 1 CHECK (taxonomy_version >= 1),
    UNIQUE (library_post_id, slide_index),
    UNIQUE (slide_id, library_post_id),
    FOREIGN KEY (library_post_id) REFERENCES style_posts(library_post_id)
        ON UPDATE CASCADE,
    FOREIGN KEY (asset_id) REFERENCES style_assets(asset_id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    FOREIGN KEY (ocr_asset_id) REFERENCES style_assets(asset_id)
        ON UPDATE CASCADE ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS ix_style_slides_post
    ON style_slides(library_post_id, slide_index);

CREATE INDEX IF NOT EXISTS ix_style_slides_asset
    ON style_slides(asset_id);

CREATE TABLE IF NOT EXISTS visual_observations (
    visual_observation_id TEXT PRIMARY KEY NOT NULL,
    slide_id TEXT NOT NULL,
    composition TEXT NOT NULL DEFAULT 'unknown',
    dominant_material TEXT NOT NULL DEFAULT 'unknown',
    background_type TEXT NOT NULL DEFAULT 'unknown',
    subject_presence TEXT NOT NULL DEFAULT 'unknown',
    crop_and_subject_ratio TEXT NOT NULL DEFAULT '',
    layout_structure TEXT NOT NULL DEFAULT 'unknown',
    text_zones TEXT NOT NULL DEFAULT '[]',
    text_density TEXT NOT NULL DEFAULT 'unknown',
    hierarchy_levels TEXT NOT NULL DEFAULT 'unknown',
    alignment TEXT NOT NULL DEFAULT 'unknown',
    spacing_pattern TEXT NOT NULL DEFAULT 'unknown',
    palette TEXT NOT NULL DEFAULT '[]',
    font_feel TEXT NOT NULL DEFAULT 'unknown',
    decoration_types TEXT NOT NULL DEFAULT 'unknown',
    annotation_style TEXT NOT NULL DEFAULT 'unknown',
    imperfection_signals TEXT NOT NULL DEFAULT 'unknown',
    image_text_relationship TEXT NOT NULL DEFAULT 'unknown',
    evidence_level TEXT NOT NULL DEFAULT '',
    observation_method TEXT NOT NULL DEFAULT 'direct',
    confidence REAL NOT NULL DEFAULT 1.0
        CHECK (confidence >= 0.0 AND confidence <= 1.0),
    taxonomy_version INTEGER NOT NULL DEFAULT 1 CHECK (taxonomy_version >= 1),
    notes TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (slide_id) REFERENCES style_slides(slide_id)
        ON UPDATE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_visual_observations_slide
    ON visual_observations(slide_id);

CREATE TABLE IF NOT EXISTS copy_observations (
    observation_id TEXT PRIMARY KEY NOT NULL,
    library_post_id TEXT NOT NULL,
    slide_id TEXT,
    text_surface TEXT NOT NULL DEFAULT 'unknown',
    point_of_view TEXT NOT NULL DEFAULT 'unknown',
    audience_address TEXT NOT NULL DEFAULT 'unknown',
    register TEXT NOT NULL DEFAULT 'unknown',
    sentence_length_pattern TEXT NOT NULL DEFAULT 'unknown',
    line_break_pattern TEXT NOT NULL DEFAULT 'unknown',
    punctuation_pattern TEXT NOT NULL DEFAULT 'unknown',
    emoji_pattern TEXT NOT NULL DEFAULT 'unknown',
    diction_markers TEXT NOT NULL DEFAULT '[]',
    hook_move TEXT NOT NULL DEFAULT 'unknown',
    narrative_moves TEXT NOT NULL DEFAULT 'unknown',
    evidence_move TEXT NOT NULL DEFAULT 'unknown',
    payoff_move TEXT NOT NULL DEFAULT 'unknown',
    cta_move TEXT NOT NULL DEFAULT 'unknown',
    image_caption_division TEXT NOT NULL DEFAULT 'unknown',
    quoted_fragments_hash TEXT,
    evidence_level TEXT NOT NULL DEFAULT '',
    observation_method TEXT NOT NULL DEFAULT 'direct',
    confidence REAL NOT NULL DEFAULT 1.0
        CHECK (confidence >= 0.0 AND confidence <= 1.0),
    taxonomy_version INTEGER NOT NULL DEFAULT 1 CHECK (taxonomy_version >= 1),
    notes TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (library_post_id) REFERENCES style_posts(library_post_id)
        ON UPDATE CASCADE,
    FOREIGN KEY (slide_id, library_post_id)
        REFERENCES style_slides(slide_id, library_post_id)
        ON UPDATE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_copy_observations_post
    ON copy_observations(library_post_id);

CREATE INDEX IF NOT EXISTS ix_copy_observations_slide
    ON copy_observations(slide_id);

CREATE TABLE IF NOT EXISTS style_archetypes (
    archetype_id TEXT PRIMARY KEY NOT NULL,
    name TEXT NOT NULL,
    category_scope TEXT NOT NULL DEFAULT '',
    carrier TEXT NOT NULL DEFAULT 'unknown',
    primary_job_scope TEXT NOT NULL DEFAULT '',
    audience_state TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    production_cost TEXT NOT NULL DEFAULT '',
    confidence REAL NOT NULL DEFAULT 0.0
        CHECK (confidence >= 0.0 AND confidence <= 1.0),
    status TEXT NOT NULL DEFAULT 'candidate'
        CHECK (status IN ('candidate', 'supported', 'reusable', 'stale', 'deprecated')),
    current_version INTEGER NOT NULL DEFAULT 1 CHECK (current_version >= 1),
    snapshot_sha256 TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    taxonomy_version INTEGER NOT NULL DEFAULT 1 CHECK (taxonomy_version >= 1)
);

CREATE INDEX IF NOT EXISTS ix_style_archetypes_retrieval
    ON style_archetypes(category_scope, carrier, status);

CREATE TABLE IF NOT EXISTS archetype_rules (
    rule_id TEXT PRIMARY KEY NOT NULL,
    archetype_id TEXT NOT NULL,
    archetype_version INTEGER NOT NULL CHECK (archetype_version >= 1),
    rule_type TEXT NOT NULL
        CHECK (rule_type IN ('cover', 'rhythm', 'visual', 'copy', 'material', 'anti_pattern')),
    rule_payload_json TEXT NOT NULL DEFAULT '{}',
    applicability_scope TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'active',
    FOREIGN KEY (archetype_id) REFERENCES style_archetypes(archetype_id)
        ON UPDATE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_archetype_rules_archetype_version
    ON archetype_rules(archetype_id, archetype_version);

CREATE TABLE IF NOT EXISTS rule_evidence (
    rule_evidence_id TEXT PRIMARY KEY NOT NULL,
    rule_id TEXT NOT NULL,
    observation_type TEXT NOT NULL
        CHECK (observation_type IN ('visual', 'copy', 'post_metric')),
    observation_id TEXT NOT NULL,
    evidence_role TEXT NOT NULL
        CHECK (evidence_role IN ('support', 'counterexample', 'boundary')),
    limitations TEXT NOT NULL DEFAULT '',
    UNIQUE (rule_id, observation_type, observation_id, evidence_role),
    UNIQUE (rule_id, observation_type, observation_id),
    FOREIGN KEY (rule_id) REFERENCES archetype_rules(rule_id)
        ON UPDATE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_rule_evidence_rule
    ON rule_evidence(rule_id);

CREATE INDEX IF NOT EXISTS ix_rule_evidence_observation
    ON rule_evidence(observation_type, observation_id);

CREATE TABLE IF NOT EXISTS draft_style_bindings (
    draft_binding_id TEXT PRIMARY KEY NOT NULL,
    draft_id TEXT NOT NULL,
    archetype_id TEXT NOT NULL,
    binding_role TEXT NOT NULL
        CHECK (binding_role IN ('primary', 'secondary')),
    archetype_version INTEGER NOT NULL CHECK (archetype_version >= 1),
    archetype_snapshot_sha256 TEXT NOT NULL,
    selected_rule_ids TEXT NOT NULL DEFAULT '[]',
    reference_library_post_ids TEXT NOT NULL DEFAULT '[]',
    counterexample_library_post_ids TEXT NOT NULL DEFAULT '[]',
    material_plan_json TEXT NOT NULL DEFAULT '{}',
    intentional_deviations_json TEXT NOT NULL DEFAULT '[]',
    anti_patterns_checked_json TEXT NOT NULL DEFAULT '[]',
    retrieved_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    review_status TEXT NOT NULL DEFAULT 'pending'
        CHECK (review_status IN ('pending', 'PASS', 'PARTIAL', 'FAIL')),
    FOREIGN KEY (archetype_id) REFERENCES style_archetypes(archetype_id)
        ON UPDATE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_draft_style_bindings_primary
    ON draft_style_bindings(draft_id)
    WHERE binding_role = 'primary';

CREATE UNIQUE INDEX IF NOT EXISTS ux_draft_style_bindings_secondary
    ON draft_style_bindings(draft_id)
    WHERE binding_role = 'secondary';

CREATE INDEX IF NOT EXISTS ix_draft_style_bindings_archetype
    ON draft_style_bindings(archetype_id, archetype_version);

CREATE TABLE IF NOT EXISTS draft_assets (
    draft_asset_id TEXT PRIMARY KEY NOT NULL,
    draft_binding_id TEXT NOT NULL,
    asset_id TEXT NOT NULL,
    slide_index INTEGER CHECK (slide_index IS NULL OR slide_index >= 0),
    asset_role TEXT NOT NULL DEFAULT 'generated',
    review_status TEXT NOT NULL DEFAULT 'pending'
        CHECK (review_status IN ('pending', 'PASS', 'PARTIAL', 'FAIL')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (draft_binding_id, asset_id),
    FOREIGN KEY (draft_binding_id)
        REFERENCES draft_style_bindings(draft_binding_id)
        ON UPDATE CASCADE,
    FOREIGN KEY (asset_id) REFERENCES style_assets(asset_id)
        ON UPDATE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_draft_assets_binding
    ON draft_assets(draft_binding_id);

CREATE TABLE IF NOT EXISTS draft_outcomes (
    draft_outcome_id TEXT PRIMARY KEY NOT NULL,
    draft_binding_id TEXT NOT NULL,
    published_at TEXT,
    observed_at TEXT,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    post_age_hours REAL CHECK (post_age_hours IS NULL OR post_age_hours >= 0.0),
    baseline_snapshot_id TEXT,
    known_confounds TEXT NOT NULL DEFAULT '[]',
    decision TEXT NOT NULL
        CHECK (decision IN ('win', 'loss', 'inconclusive')),
    next_single_variable TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (draft_binding_id)
        REFERENCES draft_style_bindings(draft_binding_id)
        ON UPDATE CASCADE,
    FOREIGN KEY (baseline_snapshot_id)
        REFERENCES account_baseline_snapshots(baseline_snapshot_id)
        ON UPDATE CASCADE ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS ix_draft_outcomes_binding
    ON draft_outcomes(draft_binding_id, observed_at);

CREATE TABLE IF NOT EXISTS ingest_receipts (
    ingest_receipt_id INTEGER PRIMARY KEY,
    run_id TEXT NOT NULL,
    input_bundle_sha256 TEXT NOT NULL,
    ingested_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    record_counts_json TEXT NOT NULL DEFAULT '{}',
    UNIQUE (run_id, input_bundle_sha256)
);

PRAGMA user_version = 1;

COMMIT;
