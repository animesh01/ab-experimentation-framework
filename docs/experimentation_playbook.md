# Experimentation Playbook

> _All examples and data in this repository are fabricated for demonstration. Nothing here is derived from any employer, customer, or production system._

## 1. Intake

Use this checklist before a test is approved:

- Problem: What customer or business problem are we solving?
- Hypothesis: If we change X for audience Y, metric Z will improve because of mechanism M.
- Primary metric: The single metric that decides the experiment.
- Guardrail metrics: Metrics that must not degrade meaningfully.
- Target audience: Eligible users, exclusions, geography, platform, and lifecycle stage.
- Minimum runtime: Usually at least one full weekly cycle.
- Risk level: Low, medium, or high based on user impact and reversibility.

## 2. Experiment Design

Recommended default:

- Allocation: 50 percent control, 50 percent treatment.
- Unit of randomization: User ID for user-facing product changes.
- Assignment: Deterministic hash of `experiment_id + user_id`.
- Exposure event: Logged only when the user actually sees or can use the variant.
- Runtime: Stop only after minimum sample size and minimum runtime are both met.

Avoid peeking-based early stopping unless the team uses a sequential testing method.

## 3. Metrics

Use one primary metric. Good examples:

- Activation rate: completed target action within 7 days of exposure.
- Conversion rate: purchased, upgraded, or submitted within a defined window.
- Retention rate: returned or reused feature within N days.
- Task success: completed workflow without error or abandonment.

Guardrails commonly include:

- Latency
- Error rate
- Refunds or cancellations
- Support contact rate
- Abuse or safety escalation rate
- Long-term retention proxy

## 4. Launch Gates

Before ramping traffic:

- Experiment spec is reviewed.
- Event names and properties are implemented.
- QA confirms users are assigned consistently.
- Exposure logging fires once per user per experiment arm.
- Dashboard has primary, guardrail, and sample ratio mismatch checks.
- Rollback owner is named.

## 5. Monitoring

Monitor these during the experiment:

- Sample ratio mismatch: actual assignment differs from planned split.
- Data freshness: events arrive within the expected delay.
- Guardrail degradation: treatment causes unacceptable harm.
- Instrumentation drift: missing user IDs, experiment IDs, or variants.

## 6. Analysis

Decision logic:

- Ship: primary metric improves meaningfully and guardrails are acceptable.
- Iterate: signal is promising but not decisive, or segment learning suggests a better variant.
- Do not ship: primary metric misses, guardrails degrade, or user feedback is negative.
- Re-run: instrumentation, assignment, or traffic quality invalidates the test.

## 7. Decision Record

Every experiment should end with:

- Final sample size by arm
- Primary and guardrail outcomes
- Statistical result and practical effect size
- Segment notes
- Decision
- Follow-up action
- Owner and date

