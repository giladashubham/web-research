# Deep Research Workflow

The `deep` workflow is the flagship research pattern. It is designed to go beyond a single search-and-summarize pass, instead using an iterative "Gap Analysis" loop to ensure thoroughness.

## Pipeline Structure

1. **Planner**: Analyzes the user query and creates a multi-pronged research plan.
2. **Parallel Research**: Three specialized agents run in parallel:
   - **Official Researcher**: Looks for documentation and official statements.
   - **Recent Researcher**: Focuses on the last 6-12 months for current news.
   - **Broad Researcher**: Looks for community discussions, blogs, and comparisons.
3. **Reviewer**: Evaluates the research gathered so far.
   - If information is missing or contradictory, it identifies "Gaps."
4. **Gap Loop (Iterative)**:
   - **Gap Researcher**: For each identified gap, performs targeted research.
   - **Reviewer**: Re-evaluates. This repeats until no more gaps exist or the max rounds are reached.
5. **Output Writer**: Synthesizes all gathered information into the final report.

## Usage

```bash
uv run webresearch run "Your research query" deep
```

### Depth Settings

- **`quick`**: Fewer search results, fewer loop iterations.
- **`standard`**: The default balanced setting.
- **`deep`**: Maxes out the number of search results and allows for more gap-filling rounds.

## Key Agents

- **Planner**: `prompts/planner.j2`
- **Reviewer**: `prompts/reviewer.j2`
- **Output Writer**: `prompts/output.j2`

## Specialized Tools

The `deep` workflow uses a suite of tools defined in `tools.py`:
- `search_web_tool`: High-level web search.
- `fetch_and_extract_tool`: Fetches a URL and pulls relevant text.
- `discover_urls_tool`: Finds high-value pages (docs, blog) from a root domain.
- `rank_sources_tool`: Helps the agent prioritize which links to follow.
