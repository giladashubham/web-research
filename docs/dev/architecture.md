# Developer Guide: Core Architecture

Web Research is built with a strictly layered architecture to ensure that workflow logic remains independent of the underlying LLM framework or I/O providers.

## Architecture Layers

| Layer | Responsibility | Key Files |
|-------|----------------|-----------|
| **CLI** | User interface, input parsing, formatting output. | `cli/` |
| **Workflows** | High-level research logic and pipeline definitions. | `workflows/` |
| **Pipeline Engine** | Orchestrates step execution, hooks, loops, and events. | `pipeline/` |
| **Context** | Maintains state: pages, sources, evidence, and costs. | `context.py` |
| **Providers** | Low-level I/O (Search, Fetch, Extract). | `providers/` |
| **Events** | Real-time monitoring and logging system. | `events/` |

## The Pipeline Engine

The engine is the heart of the system. It executes a declarative sequence of steps:

- **`AgentStep`**: A single LLM agent call.
- **`Parallel`**: Runs multiple steps concurrently.
- **`FanOut`**: Runs one agent per item in a dynamic list.
- **`Loop`**: Repeats steps until a condition is met (e.g., "no more gaps").

### Declarative vs. Imperative
Workflows do not write logic like `if result == 'gap': search_again()`. Instead, they define a `Loop` step with an `until` condition. This keeps workflows clean and ensures that system-level features like cost tracking and event emission work automatically.

## Runtime Isolation

A key design goal is **Runtime Isolation**. Only `webresearch/pipeline/runtime.py` interacts with the LLM SDK (currently OpenAI Agents Python). 

If you want to use a different provider (e.g., Anthropic, Gemini) or a different agent framework, you only need to modify `runtime.py`. All workflow code remains untouched.

## Prompt Engineering with Jinja2

Prompts are stored as `.j2` files in each workflow's `prompts/` directory. They are rendered with access to:
- `{{ input }}`: The original workflow input.
- `{{ outputs }}`: Results from all previous steps in the pipeline.
- `{{ item }}`: The current item being processed in a `FanOut`.

This approach keeps prompt logic out of the Python code, making it easier to read and iterate on.

## Event System & Streaming

The system emits detailed events for every significant action:
- `StepStarted` / `StepCompleted`
- `ToolCallStarted` / `ToolCallCompleted`
- `TextDelta` (for streaming answers)

These events are used by the CLI to show progress and are saved to `.jsonc` logs for debugging.
