# Technical Due Diligence — Deeper Research + Lower Cost

Three problems with the current `technical_due_diligence` run:

1. **Shallow research.** Each agent stage runs once over whatever URLs are in context. There's no real *investigation* — no walking the docs tree, no reading the changelog end-to-end, no chasing a claim from the marketing page into the API reference to verify it. The output reads like a summary of search snippets, not a diligence memo.
2. **No URL discovery from seeds.** If the user passes a single `product_url`, the workflow does not actively expand it into obvious neighbouring pages (docs, pricing, changelog, security, blog, careers, sitemap). Discovery falls back to Tavily — the expensive path.
3. **Tavily called when we already have the URL.** Once a URL is known, fetching + extracting it is free (`httpx` + readability). Search should be the *fallback* for "I don't know where this lives," not the default.

This doc lists the changes that produce a deeper, more grounded report **and** spend fewer Tavily calls — the two goals are aligned, because primary-source content (docs, changelog, schemas) is both richer and free to fetch.

> **Replacement, not migration.** This is a clean rewrite of the current `technical_due_diligence` workflow's research behaviour. There are no compatibility shims, no feature flags, no "old path / new path" toggles, and no dual-mode prompts. The current workflow has not been used outside this repo, so the old behaviour is removed in the same change that introduces the new one. Where this doc says "replace," it means delete-and-rewrite, not extend.

---

## 1. Replace `intake_planner` with a planner that does seed expansion

Right now the pipeline goes `intake_planner → claim_extractor → evidence_researcher → …`. The planner produces `priority_urls`, but nothing actively walks those seeds to find sibling pages.

Rewrite `intake_planner` so seed expansion is part of its contract, not a separate optional stage. Its new job is **plan + expand**:

- Input: `product_url` + `known_urls` from `DiligenceTarget`.
- Behaviour:
  1. Fetch the seed URL with `fetch_url_tool` (already free / no Tavily).
  2. Extract anchor links from the body. Keep links that are same-origin or that match high-value patterns: `/docs`, `/api`, `/pricing`, `/security`, `/changelog`, `/release-notes`, `/blog`, `/customers`, `/case-studies`, `/careers`, `/about`, `/trust`, `/status`.
  3. Try canonical well-known paths even if not linked: `/sitemap.xml`, `/robots.txt`, `/.well-known/security.txt`, `/llms.txt`, `/feed`, `/rss`.
  4. From `sitemap.xml` (cheap, structured), pull URLs matching the same high-value patterns.
- Output: an enriched `priority_urls` list ranked by category (docs > changelog > pricing > customers > blog > marketing).
- Tavily calls used: **0**.

This is the single highest-leverage change — most B2B SaaS targets expose 80% of the technical signal on their own domain, and you can get to it without ever hitting search.

### Where the code goes

- New tool in `webresearch/tools/`: `discover_urls.py` that takes a seed URL and returns a categorised list (uses existing `fetch_url` + an HTML link parser; no new external API).
- Register it in `webresearch/agents/tools.py` and add it to `RESEARCH_TOOLS`. The planner stage gets it too — give it the same `RESEARCH_TOOLS` set the other research stages have, since it now does work, not just synthesis.
- Rewrite `intake_planner.md` end-to-end. It instructs the planner to call `discover_urls_tool` on `product_url` and every entry in `known_urls`, merge the results into `priority_urls`, and never call `search_web_tool` for URLs the seed domain itself exposes.
- Extend `IntakePlan` (`models.py`) to carry the categorised URL map (e.g., `priority_urls_by_category: dict[Literal["docs","changelog","api","pricing","security","customers","blog","careers","other"], list[str]]`) so downstream stages can pick the right artefact for each claim without re-discovering. Drop the flat `priority_urls` list — replace, don't keep both.

---

## 2. Rewrite the research-stage prompts with explicit tool selection

The current prompts (`claim_extractor.md`, `evidence_researcher.md`, `competitor_mapper.md`, `gap_researcher.md`) are short and tool-agnostic — they say "use tools to search, fetch, extract, and rank sources." The agent has no rule for *when* to prefer one over another, so it defaults to `search_web_tool`.

Replace each of these prompts in full with a version built around the rules below. Don't bolt the tool-budget rule onto the existing text — the existing text is too thin to anchor the new behaviour, and patches always drift back to the prior tone. Each rewritten prompt should contain: (a) the stage's goal, (b) the tool-selection rule below, (c) the tool-call ordering, (d) the investigation-discipline block from §3, and (e) the structured-output expectations.

The tool-selection rule, dropped into each rewritten prompt verbatim:

> **Tool budget rule.** Before calling `search_web_tool`, check the running list of known URLs (from the IntakePlan, prior stage outputs, and `discover_urls_tool` results). If a relevant URL is already known, use `fetch_url_tool` + `extract_content_tool` instead. Reserve `search_web_tool` for cases where: (a) you need information the target domain does not host (competitor pricing, third-party benchmarks, news, filings), or (b) two prior fetch attempts have not produced the evidence and you need a new candidate URL.

Also tighten the *order* the agent should try things in:

1. Look at known URLs already in context.
2. `discover_urls_tool` to expand seeds (one call per new domain, max).
3. `fetch_url_tool` + `extract_content_tool` on the most relevant candidates.
4. `search_web_tool` only if 1–3 didn't produce evidence for the specific claim.

Files to rewrite (full replacement, not edits): `claim_extractor.md`, `evidence_researcher.md`, `competitor_mapper.md`, `gap_researcher.md`. The old text goes; nothing of it carries forward by reference.

---

## 3. Actually do research — the "investigator" loop

This is the quality piece. Right now each `RESEARCH_TOOLS`-using agent makes a flat pass: a few searches, a few fetches, write the section. Real diligence is iterative — you read one page, it raises three questions, you chase those, they resolve into a claim or a gap.

Bake that loop into the prompts. Each research-stage agent should follow this investigative pattern:

1. **Map the surface area.** Use `discover_urls_tool` on the target's domain. Categorise what exists: docs site? public API? changelog? security/trust page? customer logos with case studies? engineering blog? job postings? open-source repos linked from the site?
2. **Read primary sources end-to-end, not just the homepage.**
   - Docs: skim the table of contents, then deep-read the *architecture / how-it-works / data-model / integrations* sections — those are where wrapper risk is exposed.
   - Changelog / release notes: read the **last 12–18 months** chronologically. Velocity, depth of changes, and whether changes are model swaps vs. real product work are all visible here.
   - API reference: count endpoints, look at request/response shape, auth model, rate limits. A "platform" with 6 endpoints is a wrapper; a "platform" with a typed schema and webhooks is not.
   - Pricing: tier structure, usage units, enterprise gates — tells you the actual product shape vs. marketing claims.
   - Security / trust: SOC2, data handling, model providers named — also tells you which foundation models they sit on top of.
   - Careers: job postings reveal the real stack ("experience with pgvector / Triton / CUDA / Postgres logical replication") more honestly than the marketing site.
3. **Cross-check every marketing claim against a primary artefact.** If the homepage says "proprietary retrieval engine," the diligence is *not done* until the agent has either (a) found a docs page or blog post describing it, (b) found a job posting or talk that confirms it exists, or (c) marked it explicitly as **claimed but unverifiable from public sources** in `evidence_gaps`.
4. **Follow the citations.** When the target's blog cites a paper, benchmark, or external system, fetch that too — it's how you tell a team that *reads* the literature from a team that name-drops it.
5. **Keep going until a claim is closed.** A claim is closed when it is `supported`, `partially_supported`, `unsupported`, or explicitly listed as a code-review follow-up. `unclear` is not a terminal state — it means "research more or move it to follow-ups with a reason."

The orchestrator should support this:

- Raise `input.depth.max_rounds` default for this workflow, or add a per-claim round counter so a single stubborn claim can get more rounds without inflating the global count.
- Track `pages_read_per_domain` in context. If the target's domain has only 2 pages read after `evidence_researcher`, the reviewer should automatically force another round — that's a tell-tale sign of shallow work.
- Add `unread_high_value_urls` to the reviewer's output: any URL `discover_urls_tool` returned in the docs/changelog/api categories that no agent ever fetched. The next gap round should fetch those before doing anything else.

### Prompt scaffolding to add

Add a section like this to `evidence_researcher.md` and `gap_researcher.md`:

> **Investigation discipline.** You are doing diligence, not summarisation. For each high-relevance claim:
> 1. Find the most authoritative public artefact for it (docs page, changelog entry, API reference, schema, RFC, signed blog post). Marketing pages do not count as evidence on their own.
> 2. Read the artefact in full via `extract_content_tool` — do not stop at the snippet.
> 3. If the artefact raises a sub-question (e.g., "they mention vector search — on what backend?"), open a sub-investigation: search the docs for the backend, check `careers` postings, check the changelog for the migration. Record what you find.
> 4. Only mark a claim `unclear` after at least two distinct primary sources have been checked. Otherwise, keep going.

This is what turns the workflow from "stitched-together search results" into something that reads like an analyst sat down with the website for an hour.

---

## 4. Replace the gap loop with a per-claim investigation loop

The workflow already has one loop — `gap_researcher` runs while `review.has_critical_gaps and round_index < input.depth.max_rounds`. The current shape (one global "any gaps?" boolean, one round per gap pass) is the wrong abstraction. Replace it.

The new loop:

- The reviewer's output is a **list of unresolved claims**, each with its own follow-up queries — not a single `has_critical_gaps` flag. Drop `has_critical_gaps` and `follow_up_queries` from `TechnicalSubstanceReview` and replace them with `unresolved_claims: list[UnresolvedClaim]` where each entry carries the claim id, why it's unresolved, and which artefact types to chase (docs/changelog/api/careers/etc.).
- Each gap round operates per-claim, not globally. The orchestrator iterates over `unresolved_claims` and runs the gap researcher with a tightly scoped prompt for each. A claim exits the loop when it's `supported` / `partially_supported` / `unsupported`, or when it's promoted to a code-review follow-up with a stated reason. `unclear` is no longer a terminal output.
- Add a hard floor in the reviewer: if `pages_read_per_domain[target_domain] < 5`, every high-relevance claim is automatically marked unresolved, regardless of what evidence text was produced. Shallow runs cannot exit early.
- Carry `unread_high_value_urls` (docs/changelog/api category URLs from `discover_urls_tool` that no stage fetched) into the next round. The gap researcher must consume those before it's allowed to call `search_web_tool`.

This is a `workflow.py` rewrite of the gap loop plus replacements of `gap_researcher.md` and the relevant fields in `models.py`. The old `has_critical_gaps` boolean and the flat `gap_results` list go away; no shim keeps them.

---

## 5. Cache + dedupe at the tool layer

The `WorkflowContext` already tracks fetched pages and sources. Two changes at the tool layer (not the prompt layer — prompts shouldn't have to remember):

- In `search_web_tool`, dedupe by normalised `query` for the run. Identical queries return the cached `SearchResults` without hitting the provider. No prompt-level "remember to check the cache" note — the tool just doesn't double-bill.
- In `fetch_url_tool`, short-circuit on `ctx.pages` hit. Already partially true; tighten it so a re-fetch is impossible within a run unless the caller passes an explicit `force=True`.

---

## Expected impact

For a typical run (one seed URL, two named competitors, default depth):

| Stage                   | Today (approx Tavily calls) | After changes |
|-------------------------|-----------------------------|---------------|
| intake_planner          | 0                           | 0             |
| claim_extractor         | 3–5                         | 0–1           |
| evidence_researcher     | 8–15                        | 2–4           |
| competitor_mapper       | 4–8                         | 2–3 (only for competitor domains we don't know) |
| gap_researcher (per round) | 4–8                      | 1–3 (focused per-claim)|

Rough estimate: **60–75% fewer Tavily calls** with substantially better evidence coverage, because (a) most of the substance lives on the target's own domain and we now actually walk it, and (b) primary-source pages (docs, changelog, API ref) carry far more signal than search snippets — so the trade is "fewer Tavily calls **and** richer evidence," not a tradeoff.

Quality signals to expect in the output after these changes:
- `claim_assessments[*].evidence_source_urls` should point to *deep* paths (`/docs/architecture/...`, `/changelog/2025-...`, `/api/reference/...`) — not just the homepage.
- `evidence_gaps` should be specific ("changelog does not mention how multi-tenant isolation is enforced") rather than generic ("more info needed").
- `code_review_follow_ups` should be grounded in a specific public artefact ("docs claim X but do not say Y — verify Y in code").
- `competitor_assessments` should cite each competitor's docs/changelog, not their marketing page.

---

## Implementation order

This ships as a single replacement of the workflow's research behaviour. The steps below are the suggested authoring order within that one change — not phased releases with backwards-compatible intermediate states.

1. Build `discover_urls_tool` (`webresearch/tools/discover_urls.py`) and register it in `RESEARCH_TOOLS`.
2. Update `models.py`: replace flat `priority_urls` with categorised map; replace `has_critical_gaps` + `follow_up_queries` with `unresolved_claims`. Delete the old fields outright.
3. Tighten `search_web_tool` (per-query dedupe) and `fetch_url_tool` (no re-fetch within a run) at the tool layer.
4. Rewrite the five prompts end-to-end: `intake_planner.md`, `claim_extractor.md`, `evidence_researcher.md`, `competitor_mapper.md`, `gap_researcher.md`. Each rewrite is a delete-and-replace; the old text is not preserved.
5. Rewrite the gap loop in `workflow.py` to be per-claim, with `pages_read_per_domain` floor and `unread_high_value_urls` carry-over. Raise `max_rounds` default (e.g., 3 → 5).
6. Update tests to the new `IntakePlan` / `TechnicalSubstanceReview` shape and to assert the new behaviours (seed expansion runs, `search_web_tool` is not called when a relevant URL is already in context, `unclear` claims are not present in terminal output unless promoted to follow-ups).

There is no intermediate state where the old prompts run against the new models or vice versa. Land it as one cohesive change.
