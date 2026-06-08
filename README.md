# A/B Experimentation Framework Showcase

This portfolio project turns an A/B experimentation framework into a small, usable showcase app and supporting implementation artifacts. It demonstrates how a product/data team can define a hypothesis, assign users safely, instrument outcomes, monitor guardrails, analyze results, and make launch/ramp/iterate decisions.

## Data Disclaimer

This project uses synthetic demo data only. It does not contain confidential employer, customer, or production telemetry. Public CX and chatbot resources are used only as benchmark context for portfolio storytelling.

## What Is Included

- `app/`: static dashboard app for previewing mock chatbot A/B experiments.
- `docs/experimentation_playbook.md`: end-to-end process for intake, design, launch, analysis, and decisioning.
- `docs/instrumentation_spec.md`: events and properties needed to make experiments measurable.
- `sql/warehouse_schema.sql`: warehouse tables for experiment exposure, metric events, and decision records.
- `configs/sample_experiment.yaml`: example experiment spec for an AI product feature.
- `scripts/analyze_experiment.py`: no-dependency stats script for conversion-rate experiments.
- `data/sample_experiment_results.csv`: tiny sample dataset to verify the script.

## Quick Start

Run the Streamlit dashboard:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

The Streamlit interface includes editable experiment inputs, a live statistical
readout, interactive charts, setup and instrumentation details, guardrail
monitoring, and a launch decision brief.

Run the original static dashboard:

```bash
cd app
python3 -m http.server 8123
```

Then open:

```text
http://localhost:8123/
```

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

The app is intentionally lightweight: no backend, no package install, and no production data dependencies. It is meant to communicate experimentation judgment, metric design, launch governance, and product decision-making.

## Resume-Ready Explanation

"I built pre-launch A/B experimentation infrastructure with engineering for chatbot feature launches, including last-mile delivery use cases. The framework standardized experiment intake, randomization, exposure logging, metric definitions, guardrails, and decision reviews so rollout and prioritization decisions were based on measurable customer outcomes."
