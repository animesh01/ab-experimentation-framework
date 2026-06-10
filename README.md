# A/B Experimentation Framework

A portfolio project that turns an A/B experimentation framework into a small, runnable showcase: a live dashboard plus the supporting artifacts a product and data team would actually use to define a hypothesis, assign users safely, instrument outcomes, watch guardrails, analyze results, and make a launch decision.

The worked example is a **Delivery-estimate chatbot** experiment — testing whether proactively showing a customer a live delivery estimate (before they ask) makes more of them confident enough to complete their order.

## Data Disclaimer

All data, metrics, experiment names, and scenarios in this repository are **fabricated for demonstration purposes**. The sample results file is a tiny hand-made dataset (two arms, a few hundred conversions) created solely to exercise the analysis script. Nothing here is derived from any employer, customer, or production system, and the repository contains no confidential, proprietary, or company-specific data.

## What This Project Demonstrates

This is built to show *experimentation judgment*, not just statistics. For a product team, the interesting questions an experiment has to answer are:

**Is the result real, or is it noise?** The dashboard runs a two-proportion z-test and reports the p-value, but it leads with the plain-language read ("160 out of 1,000 vs 120 out of 1,000") so the significance label supports the decision rather than replacing it.

**How big is the effect, and does it matter?** Statistical significance and practical significance are separated. The readout shows absolute lift (4 percentage points) and relative lift (33%) side by side, because a "significant" 0.1-point move and a "significant" 4-point move call for very different decisions.

**Did we break anything to win?** A primary metric decides the test, but guardrail metrics (repeat-contact rate, escalation complaints, unresolved-issue rate) can veto a win. The framework treats "we improved conversion but doubled complaints" as a *stop*, not a *ship*.

**Can we trust the measurement itself?** The playbook and instrumentation spec cover the failure modes that quietly invalidate experiments — sample ratio mismatch, exposure logged before the user actually sees the variant, missing experiment IDs on downstream events, and unfiltered bot/internal traffic.

**What happens after the readout?** Every experiment ends in one of four decisions — ship, iterate, stop, or re-run — with a decision record, an owner, and a follow-up. The goal is a repeatable governance loop, not a one-off analysis.

## How the Pieces Fit Together

The repository mirrors the lifecycle of a single experiment:

1. **Design** — `configs/sample_experiment.yaml` is the experiment spec: hypothesis, audience (with explicit exclusions like internal users and non-consenting users), 50/50 allocation, the primary metric, guardrails with thresholds, runtime/power, and the ship/iterate/stop decision policy.
2. **Instrument** — `docs/instrumentation_spec.md` defines the events and properties needed to make the experiment measurable, plus tracking rules that prevent common data-quality bugs.
3. **Store** — `sql/warehouse_schema.sql` models the warehouse tables for exposures, metric events, and decision records.
4. **Analyze** — `scripts/analyze_experiment.py` is a dependency-free statistics script for two-arm conversion tests (arm-level rates, absolute/relative lift, z-score, p-value, recommendation).
5. **Decide & communicate** — `streamlit_app.py` is the live dashboard: editable inputs, a plain-language statistical readout, interactive charts, guardrail monitoring, and a launch-decision brief written for a non-statistician audience.
6. **Govern** — `docs/experimentation_playbook.md` is the end-to-end process tying intake, design, launch gates, monitoring, analysis, and decision records together.

## Repository Contents

- `streamlit_app.py` — interactive dashboard with editable experiment inputs, live statistical readout, charts, guardrail monitoring, and a launch decision brief.
- `scripts/analyze_experiment.py` — no-dependency stats script for two-arm conversion-rate experiments.
- `docs/experimentation_playbook.md` — end-to-end process for intake, design, launch, analysis, and decisioning.
- `docs/instrumentation_spec.md` — events and properties needed to make experiments measurable, with tracking rules.
- `sql/warehouse_schema.sql` — warehouse tables for experiment exposure, metric events, and decision records.
- `configs/sample_experiment.yaml` — example experiment spec for an AI product feature.
- `data/sample_experiment_results.csv` — tiny fabricated dataset to verify the script.

## Quick Start

Run the Streamlit dashboard:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

The interface includes editable experiment inputs, a live statistical readout, interactive charts, setup and instrumentation details, guardrail monitoring, and a launch decision brief.

Run the sample analysis script from the project root:

```bash
python3 scripts/analyze_experiment.py data/sample_experiment_results.csv
```

Expected output includes arm-level conversion rates, absolute lift, relative lift, z-score, p-value, and a decision recommendation.

## Core Principles

1. Every experiment starts with a falsifiable hypothesis.
2. Assignment is deterministic and stable per experiment.
3. Exposure is logged exactly when the user could experience the variant.
4. One primary metric decides the test; guardrails prevent harmful wins.
5. Results are interpreted with product context, not p-values alone.

## Portfolio Scope

The app is intentionally lightweight: no backend, no production data dependencies. It exists to communicate experimentation judgment, metric design, launch governance, and product decision-making in a form a product manager can read end to end.

## Resume-Ready Explanation

"I built pre-launch A/B experimentation infrastructure with engineering for chatbot feature launches, including delivery-experience use cases. The framework standardized experiment intake, randomization, exposure logging, metric definitions, guardrails, and decision reviews so rollout and prioritization decisions were based on measurable customer outcomes."
