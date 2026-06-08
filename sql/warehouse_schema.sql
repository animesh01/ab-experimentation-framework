-- Core tables for an A/B experimentation warehouse model.

CREATE TABLE IF NOT EXISTS experiments (
    experiment_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    owner TEXT NOT NULL,
    hypothesis TEXT NOT NULL,
    primary_metric TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS experiment_variants (
    experiment_id TEXT NOT NULL,
    variant TEXT NOT NULL,
    allocation_pct NUMERIC NOT NULL,
    description TEXT,
    PRIMARY KEY (experiment_id, variant)
);

CREATE TABLE IF NOT EXISTS experiment_exposures (
    exposure_id TEXT PRIMARY KEY,
    experiment_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    session_id TEXT,
    variant TEXT NOT NULL,
    exposed_at TIMESTAMP NOT NULL,
    surface TEXT,
    platform TEXT
);

CREATE TABLE IF NOT EXISTS metric_events (
    event_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    session_id TEXT,
    event_name TEXT NOT NULL,
    occurred_at TIMESTAMP NOT NULL,
    experiment_id TEXT,
    variant TEXT,
    properties_json TEXT
);

CREATE TABLE IF NOT EXISTS experiment_decisions (
    experiment_id TEXT PRIMARY KEY,
    decision TEXT NOT NULL,
    decision_date DATE NOT NULL,
    primary_metric_result TEXT NOT NULL,
    guardrail_summary TEXT,
    notes TEXT,
    decided_by TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_exposures_experiment_variant
    ON experiment_exposures (experiment_id, variant);

CREATE INDEX IF NOT EXISTS idx_metric_events_experiment
    ON metric_events (experiment_id, event_name);

