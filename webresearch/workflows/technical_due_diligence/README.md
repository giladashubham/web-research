# Technical Due Diligence Workflow

Registered as `technical_due_diligence`. A public-facing due-diligence workflow that
collects product claims from marketing pages, verifies them against technical
documentation, assesses release activity, identifies evidence gaps, and produces a
structured report suitable for VC technical diligence.

## Pipeline

```
intake_planner
  (discover_urls_tool on seed URLs, categorise into docs/api/changelog/...)
       │
       ▼
url_selector
  (lightweight model trims URLs to budget limits per category)
       │
       ▼
claim_extractor
  (fetch priority pages, extract structured claims with categories)
       │
       ▼
evidence_researcher
  (for each high-relevance claim: fetch docs, changelog, API reference, search as last resort)
       │
       ▼
┌── technical_substance_reviewer ──┐
│  (no tools, checks depth floor)  │
│                                  │
│  unresolved_claims empty?        │
│  YES ─► final_memo               │
│  NO  ─► gap_researcher ─────────►│ (loop)
└──────────────────────────────────┘
       │
       ▼
final_memo
  (produces markdown + structured TechnicalDueDiligenceReport)
```

## Agents

| Step | Tools | Output | Notes |
|------|-------|--------|-------|
| `intake_planner` | All | `IntakePlan` | Expands seed URLs via `discover_urls_tool`, categorises, builds research plan |
| `url_selector` | None | `SelectedPriorityUrls` | LLM selects best URLs per category within budget; falls back to deterministic slice |
| `claim_extractor` | All | `ClaimExtraction` | Fetches priority pages, extracts structured claims with diligence relevance |
| `evidence_researcher` | All | `EvidenceResearch` | Verifies claims against docs, changelog, API surface; records release activity |
| `technical_substance_reviewer` | None | `TechnicalSubstanceReview` | Depth-floor check identifies unresolved claims and code-review follow-ups |
| `gap_researcher` | All | `DiligenceGapResearch` | Fetches unread high-value URLs; targeted search per unresolved claim |
| `final_memo` | None | `FinalMemoOutput` | Synthesises: public evidence / inference / unknowns |

## Hooks

| Hook | Agent | Behaviour |
|------|-------|-----------|
| `_url_selector_pre_hook` | `url_selector` | SKIP if intake plan has no discovered URLs |
| `_url_selector_post_hook` | `url_selector` | Validates selected URLs against candidates; enforces category budgets; falls back to deterministic slice on invalid output |
| `_reviewer_pre_hook` | `technical_substance_reviewer` | Computes `_pages_by_domain` and `_unread_high_value` for template rendering |
| `_gap_post_hook` | `gap_researcher` | Merges resolved claims back into reviewer state so loop condition sees updated `unresolved_claims` |

## URL Budgets

| Category | Max URLs |
|----------|----------|
| docs | 8 |
| api | 5 |
| changelog | 5 |
| security | 4 |
| pricing | 3 |
| customers | 3 |
| blog | 3 |
| careers | 2 |
| other | 4 |

Minimum coverage categories: `docs`, `api`, `changelog`, `security`

## Output

The workflow produces a `WorkflowResult` with:

- `answer_markdown` — Narrative memo labelling each finding as PUBLIC EVIDENCE, INFERENCE,
  or UNKNOWN (no holistic verdicts — those require code access).
- `structured_data` — A `TechnicalDueDiligenceReport` validated against `schema.json`
  containing claims, assessments, release activity, evidence gaps, and code-review follow-ups.
- `findings[]` — Per-claim confidence scores.
- `sources[]`, `evidence[]`, `warnings[]`.

## Prompts

All prompts are Jinja2 `.j2` templates rendered with the full pipeline state.
Template directory: `webresearch/workflows/technical_due_diligence/prompts/`
