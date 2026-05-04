# P2-03 — `search_web` tool

**Phase:** 2 — Tools
**Depends on:** P2-01, P2-02, P1-04, P1-05, P3-01 (deferred)

## Goal
The `function_tool` agents call to search the web.

## Scope
- Decorated async function with the Agents SDK's `@function_tool` decorator (added once `openai-agents` is installed in P3-01 — leave a `TODO` import comment if implementing this task before P3-01).
- Signature: `async def search_web(ctx: RunContextWrapper[WorkflowContext], query: str, limit: int = 10) -> SearchResults`.
- Reads `ctx.context.search_provider`. Provider chosen at `WorkflowContext` construction time (Tavily if `TAVILY_API_KEY`, else Mock).
- Adds each result to `ctx.context.sources` (the `SourceRegistry`), reusing existing source IDs on dedup.
- Returns `SearchResults` (Pydantic) including the source IDs.
- Tool docstring is the description the SDK exposes to the model.

## Out of scope
- The `WorkflowContext` itself — defined alongside this task as a small dataclass holding registry, cache, provider.

## Files
- `webresearch/context.py` (`WorkflowContext` dataclass)
- `webresearch/tools/search_web.py`
- `tests/tools/test_search_web.py`

## Acceptance
- [ ] Tool returns provider results with source IDs attached.
- [ ] Repeated calls overlapping URLs reuse source IDs.
- [ ] Provider error → tool returns empty `SearchResults` and adds a warning to the context (does not raise).
