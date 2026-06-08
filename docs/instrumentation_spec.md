# Instrumentation Spec

## Required Events

### `experiment_exposed`

Fire when a user is actually exposed to the experiment.

Required properties:

- `experiment_id`
- `variant`
- `user_id`
- `session_id`
- `exposed_at`
- `surface`
- `platform`

### `metric_event`

Fire when a user performs an action that contributes to a primary or guardrail metric.

Required properties:

- `event_name`
- `user_id`
- `session_id`
- `occurred_at`
- `experiment_id`, when attributable
- `variant`, when attributable

## Example Events

For a last-mile delivery chatbot launch experiment:

- `experiment_exposed`
- `delivery_intent_detected`
- `chatbot_resolution_offered`
- `customer_confirmed_resolution`
- `agent_handoff_requested`
- `repeat_contact_24h`
- `delivery_issue_unresolved`
- `customer_complaint_submitted`

## Tracking Rules

- Use stable user IDs for assignment and analysis.
- Do not log exposure on page load if the feature is below the fold or hidden.
- Include experiment metadata on downstream metric events when possible.
- Preserve raw events; build metric tables downstream.
- Add bot, internal-user, and QA-user filters before analysis.
