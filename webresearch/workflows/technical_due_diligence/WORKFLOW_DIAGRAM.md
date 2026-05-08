# Technical Due Diligence Workflow

```
INPUT: WorkflowInput (query, company URL, depth)
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│  STAGE 1: intake_planner  (has RESEARCH_TOOLS)          │
│  prompt: intake_planner.md                              │
│  output: IntakePlan                                     │
│                                                         │
│  1. discover_urls_tool on all seed URLs                 │
│  2. Categorize into: docs/api/changelog/pricing/        │
│     security/customers/blog/careers/other               │
│  3. Build research_questions + likely_claim_areas       │
└───────────────────────┬─────────────────────────────────┘
                        │ IntakePlan (with ALL discovered URLs)
                        ▼
┌─────────────────────────────────────────────────────────┐
│  STAGE 2: url_selector  (lightweight model: gpt-4.1-mini│
│  prompt: url_selector.md                                │
│  output: SelectedPriorityUrls                           │
│                                                         │
│  Trims discovered URLs to budget limits:                │
│  docs≤8, api≤5, changelog≤5, security≤4,               │
│  pricing≤3, customers≤3, blog≤3, careers≤2, other≤4    │
│                                                         │
│  Fallback: deterministic head-truncation if it fails    │
└───────────────────────┬─────────────────────────────────┘
                        │ IntakePlan (with PRUNED URLs)
                        ▼
┌─────────────────────────────────────────────────────────┐
│  STAGE 3: claim_extractor  (has RESEARCH_TOOLS)         │
│  prompt: claim_extractor.md                             │
│  output: ClaimExtraction                                │
│                                                         │
│  Fetches priority pages (docs→changelog→pricing→api→    │
│  security→careers→blog). Extracts each claim with:      │
│  - stable id (claim_1, claim_2…)                        │
│  - category: product/architecture/ai_ml/integration…    │
│  - diligence_relevance: high/medium/low                 │
│  Also records release_activity (changelog observations) │
└───────────────────────┬─────────────────────────────────┘
                        │ ClaimExtraction
                        ▼
┌─────────────────────────────────────────────────────────┐
│  STAGE 4: evidence_researcher  (has RESEARCH_TOOLS)     │
│  prompt: evidence_researcher.md                         │
│  output: EvidenceResearch                               │
│                                                         │
│  For each high-relevance claim:                         │
│  1. Fetch priority URLs first                           │
│  2. discover_urls_tool to expand target domain          │
│  3. search_web_tool only as last resort                 │
│  Output: assessment (supported/partially/unsupported/   │
│  unclear) + confidence + evidence_source_urls           │
└───────────────────────┬─────────────────────────────────┘
                        │ EvidenceResearch
                        ▼
┌─────────────────────────────────────────────────────────┐
│  STAGE 5: competitor_mapper  (has RESEARCH_TOOLS)       │
│  prompt: competitor_mapper.md                           │
│  output: CompetitorMapping                              │
│                                                         │
│  For each competitor: discover their docs/changelog/    │
│  pricing, compare API surface, release velocity,        │
│  architecture claims, certifications                    │
└───────────────────────┬─────────────────────────────────┘
                        │ CompetitorMapping
                        ▼
┌─────────────────────────────────────────────────────────┐
│  STAGE 6: technical_substance_reviewer  (no tools)      │
│  prompt: technical_substance_reviewer.md                │
│  output: TechnicalSubstanceReview                       │
│                                                         │
│  Depth floor check: if target domain <5 pages read,     │
│  force all unclear/partial claims → unresolved          │
│  Produces:                                              │
│  - unresolved_claims (with follow_up_queries)           │
│  - code_review_follow_ups (for private diligence)       │
└───────────────────────┬─────────────────────────────────┘
                        │
              ┌─────────▼──────────────────────────────┐
              │  unresolved_claims empty?               │
              │  OR  max_rounds reached (depth=0→0,     │
              │       else min 5 rounds)?               │
              └──┬────────────────────────┬────────────┘
         YES ◄───┘                        └───► NO
          │                                     │
          │                                     ▼
          │              ┌──────────────────────────────────────┐
          │              │  STAGE 7: gap_researcher (LOOP)      │
          │              │  prompt: gap_researcher.md           │
          │              │  output: DiligenceGapResearch        │
          │              │                                      │
          │              │  Round N:                            │
          │              │  1. Fetch ALL unread_high_value_urls │
          │              │     (docs+api+changelog+security     │
          │              │      not yet read)                   │
          │              │  2. For each unresolved claim:       │
          │              │     fetch targeted category pages    │
          │              │  3. search_web_tool as last resort   │
          │              │                                      │
          │              │  _merge_gap_into_review() marks      │
          │              │  resolved claims removed from loop   │
          │              │                                      │
          │              │  STOP EARLY if: no new assessments   │
          │              │  AND unresolved count unchanged      │
          │              └──────────────┬───────────────────────┘
          │                             │
          │                    still unresolved?
          │                    + rounds left?
          │                     YES ──► loop back
          │                     NO  ──►─────────────┐
          │                                         │
          └───────────────────┬─────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────┐
│  STAGE 8: final_memo  (no tools)                        │
│  prompt: final_memo.md                                  │
│  output: FinalMemoOutput                                │
│                                                         │
│  Writes markdown memo labeling:                         │
│  PUBLIC EVIDENCE / INFERENCE / UNKNOWNS                 │
│  Covers: claims, release activity, competitors,         │
│  evidence gaps, code-review follow-ups                  │
│  NO holistic verdicts (those need code access)          │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
              WorkflowResult
              ├── answer_markdown  (the memo)
              ├── structured_data  (validated against schema.json)
              ├── findings[]       (claim + confidence score)
              ├── sources[]
              ├── evidence[]
              └── warnings[]
```

---

## Key design decisions

| Aspect | Detail |
|---|---|
| **URL budget enforcement** | Stage 2 (url_selector) runs a cheap model to pick the best URLs per category before any reading happens — avoids wasting tokens on low-value pages |
| **Tool discipline** | Every prompt enforces the same priority: priority_urls → discover_urls_tool → fetch_and_extract_tool → search_web_tool (last resort). No search for pages already in the plan |
| **Gap loop early exit** | If `gap_researcher` produces zero new assessments AND unresolved count didn't change, it stops — avoids burning rounds when public evidence ceiling is hit |
| **depth=0 skip** | `max_rounds=0` skips the gap loop entirely (quick mode) |
| **Evidence labeling** | Every prompt enforces: public evidence / inference / unknown — no presenting inferred facts as proven |
| **No-tool reviewers** | `technical_substance_reviewer` and `final_memo` get no tools — they synthesize only from prior stage JSON passed in the prompt |

The entire prior-stage context is passed forward as serialized JSON in `_stage_prompt()`, so each agent sees all upstream outputs but has no shared memory — pure data pipeline.
