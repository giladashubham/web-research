# API & Extension Guide

Web Research is designed to be easily extended with new workflows or by integrating its components into other applications.

## Running Workflows from Python

You can run any registered workflow using the `run_workflow` or `stream_workflow` functions.
Workflows are discovered via entry points — install a workflow package and call `load_workflows()`.

### Simple Run

```python
import asyncio
from webresearch import run_workflow
from webresearch.types import WorkflowInput
from webresearch.workflows import load_workflows

async def main():
    workflows = load_workflows()
    deep = workflows["deep"]

    result = await run_workflow(
        deep,
        WorkflowInput(query="What is the latest version of Python?")
    )
    print(f"Answer: {result.answer_markdown}")
    print(f"Cost: ${result.metadata.cost_usd:.4f}")

asyncio.run(main())
```

### Streaming Run

For real-time feedback (like in a UI or CLI), use `stream_workflow`:

```python
from webresearch import stream_workflow
from webresearch.workflows import load_workflows
from webresearch.types import WorkflowInput

async def stream_example():
    workflows = load_workflows()
    input = WorkflowInput(query="Research AI Trends")
    async for event in stream_workflow(workflows["deep"], input):
        if event.kind == "text_delta":
            print(event.delta, end="", flush=True)
        elif event.kind == "step_completed":
            print(f"\nStep {event.step_name} completed.")

asyncio.run(stream_example())
```

## Adding a New Workflow

Workflows ship as separate pip packages. No changes to the core `webresearch` package needed.

1. **Create a package**: A new Python package (e.g., `webresearch-my-workflow/`).
2. **Add dependency**: Add `webresearch` as a dependency in your `pyproject.toml`.
3. **Namespace layout**: Place workflow files under `src/webresearch/workflows/my_new_workflow/`.
4. **Define State**: Use `BaseModel` to define your input/output shapes in `models.py`.
5. **Draft Prompts**: Place `.j2` templates in `prompts/`.
6. **Build Pipeline**: In `pipeline.py`, define the sequence of `AgentStep`s.
7. **Entry Point**: In `workflow.py`, create the `run` function that calls `Pipeline.run()`.
8. **Register**: Add to your `pyproject.toml`:
   ```toml
   [project.entry-points."webresearch.workflows"]
   my_new_workflow = "webresearch.workflows.my_new_workflow.workflow:run_my_workflow"

   [project.entry-points."webresearch.workflows.metadata"]
   my_new_workflow = "webresearch.workflows.my_new_workflow:get_metadata"
   ```

## Using Providers Independently

You can use the low-level providers without the pipeline:

```python
from webresearch.providers.search import TavilySearchProvider
from webresearch.providers.fetch import HttpFetchProvider
from webresearch.providers.extract import TrafilaturaExtractProvider

# Search
search = TavilySearchProvider()
results = await search.search("Python 3.13")

# Fetch & Extract
fetcher = HttpFetchProvider()
extractor = TrafilaturaExtractProvider()

page_content = await fetcher.fetch(results[0].url)
text = extractor.extract(page_content.html)
```
