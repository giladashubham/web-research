# Technical Due Diligence — Workflow Diagram

```
INPUT: WorkflowInput (query, company URL, depth)
       │
       ▼
┌──────────────────────────────────────────────────────────┐
│ STAGE 1: intake_planner (has RESEARCH_TOOLS)              │
│ prompt: intake_planner.j2                                 │
│ output: IntakePlan                                        │
│                                                           │
│ 1. discover_urls_tool on all seed URLs                    │
│ 2. Categorize into: docs/api/changelog/pricing/           │
│    security/customers/blog/careers/other                  │
│ 3. Build research_questions + likely_claim_areas          │
└──────────────────────┬────────────────────────────────────┘
                       │ IntakePlan (with ALL discovered URLs)
                       ▼
┌──────────────────────────────────────────────────────────┐
│ STAGE 2: url_selector (lightweight model: gpt-4.1-mini)  │
│ prompt: url_selector.j2                                   │
│ output: SelectedPriorityUrls                              │
│                                                           │
│ Trims discovered URLs to budget limits:                   │
│ docs≤8, api≤5, changelog≤5, security≤4,                  │
│ pricing≤3, customers≤3, blog≤3, careers≤2, other≤4       │
│                                                           │
│ pre_hook: SKIP if no URLs discovered                      │
│ post_hook: validates against candidates,                  │
│           enforces budgets, fills min coverage            │
└──────────────────────┬────────────────────────────────────┘
                       │ IntakePlan (with PRUNED URLs)
                       ▼
┌──────────────────────────────────────────────────────────┐
│ STAGE 3: claim_extractor (has RESEARCH_TOOLS)             │
│ prompt: claim_extractor.j2                                │
│ output: ClaimExtraction                                   │
│                                                           │
│ Fetches priority pages (docs→changelog→pricing→api→       │
│ security→careers→blog). Extracts each claim with:         │
│ - stable id (claim_1, claim_2…)                           │
│ - category: product/architecture/ai_ml/integration/…      │
│ - diligence_relevance: high/medium/low                    │
│ Also records release_activity (changelog observations)    │
└──────────────────────┬────────────────────────────────────┘
                       │ ClaimExtraction
                       ▼
┌──────────────────────────────────────────────────────────┐
│ STAGE 4: evidence_researcher (has RESEARCH_TOOLS)         │
│ prompt: evidence_researcher.j2                            │
│ output: EvidenceResearch                                  │
│                                                           │
│ For each high-relevance claim:                            │
│ 1. Fetch priority URLs first                              │
│ 2. discover_urls_tool to expand target domain             │
│ 3. search_web_tool only as last resort                    │
│ Output: assessment (supported/partially/unsupported/      │
│ unclear) + confidence + evidence_source_urls              │
└──────────────────────┬────────────────────────────────────┘
                       │ EvidenceResearch
                       ▼
┌──────────────────────────────────────────────────────────┐
│ STAGE 5: technical_substance_reviewer (no tools)          │
│ prompt: technical_substance_reviewer.j2                   │
│ output: TechnicalSubstanceReview                          │
│                                                           │
│ pre_hook: computes _pages_by_domain + _unread_high_value  │
│ Depth floor check: if target domain < 5 pages read,       │
│ force all unclear/partial claims → unresolved             │
│ Produces:                                                 │
│ - unresolved_claims (with follow_up_queries)              │
│ - code_review_follow_ups (for private diligence)          │
└──────────────────────┬────────────────────────────────────┘
                       │
              ┌────────▼──────────────────────────────┐
              │  unresolved_claims empty?              │
              │  OR  max_rounds reached?               │
              └──┬───────────────────────┬────────────┘
         YES ◄──┘                       └───► NO
          │                                    │
          │                                    ▼
          │             ┌──────────────────────────────────────────────┐
          │             │ STAGE 6: gap_researcher (has RESEARCH_TOOLS) │
          │             │ prompt: gap_researcher.j2                    │
          │             │ output: DiligenceGapResearch                 │
          │             │                                              │
          │             │ 1. Fetch ALL unread_high_value URLs          │
          │             │    (docs+api+changelog+security not yet read)│
          │             │ 2. For each unresolved claim:                │
          │             │    fetch targeted category pages             │
          │             │ 3. search_web_tool as last resort            │
          │             │                                              │
          │             │ post_hook: _merge_gap_into_review() marks    │
          │             │ resolved claims as removed from loop         │
          │             └──────────────────────┬───────────────────────┘
          │                                    │
          │                           still unresolved?
          │                           + rounds left?
          │                            YES ──► loop back
          │                            NO  ──►─────────────┐
          │                                                │
          └──────────────────────┬─────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────┐
│ STAGE 7: final_memo (no tools)                            │
│ prompt: final_memo.j2                                     │
│ output: FinalMemoOutput                                   │
│                                                           │
│ Writes markdown memo labelling:                           │
│ PUBLIC EVIDENCE / INFERENCE / UNKNOWNS                    │
│ Covers: claims, release activity, evidence gaps,          │
│ code-review follow-ups                                    │
│ NO holistic verdicts (those need code access)             │
└──────────────────────┬────────────────────────────────────┘
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
|--------|--------|
| **URL budget enforcement** | Stage 2 (`url_selector`) runs a cheap model to pick the best URLs per category before any reading happens — avoids wasting tokens on low-value pages |
| **Tool discipline** | Every prompt enforces the same priority: priority_urls → `discover_urls_tool` → `fetch_and_extract_tool` → `search_web_tool` (last resort). No search for pages already in the plan |
| **Gap loop** | `technical_substance_reviewer` identifies unresolved claims; `gap_researcher` fetches unread high-value URLs for each; `_gap_post_hook` merges results back into reviewer state so the loop condition sees updated `unresolved_claims` |
| **Evidence labelling** | Every prompt enforces: public evidence / inference / unknown — no presenting inferred facts as proven |
| **No-tool reviewers** | `technical_substance_reviewer` and `final_memo` get no tools — they synthesise only from prior stage outputs passed via Jinja2 templates |
| **Pipeline integration** | The entire prior-stage context is passed forward via `{{ outputs.step_name }}` in Jinja2 templates, so each agent sees all upstream outputs but has no shared memory — pure data pipeline |
