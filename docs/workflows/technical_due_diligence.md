# Technical Due Diligence Workflow

The `technical_due_diligence` (TDD) workflow is a highly specialized pattern for evaluating the technical substance, security, and maturity of a product or company.

## Purpose

Unlike general research, TDD is focused on **verification**. It starts with specific claims or a general target and looks for evidence in technical artifacts like:
- API Documentation
- Architecture Diagrams
- Security Whitepapers
- Changelogs and Release Notes

## Pipeline Structure

1. **Intake Planner**: Sets the stage and identifies the technical categories to investigate.
2. **URL Selector**: Finds the most "high-value" pages on the target's domain (e.g., `/docs`, `/security`, `/changelog`).
3. **Claim Extractor**: Reads the selected pages to find specific technical claims made by the company.
4. **Evidence Researcher**: Searches the broader web (GitHub, Reddit, StackOverflow, news) to find evidence that supports or refutes those claims.
5. **Technical Substance Reviewer**: Evaluates the findings. Like the `deep` workflow, it can trigger a **Gap Loop** if the evidence is insufficient.
6. **Final Memo**: Generates a structured technical memo.

## Structured Output

This workflow is unique because it produces a structured JSON output validated against `schema.json`. This ensures that the report always includes specific fields like `verdict`, `evidence_quality`, and `risk_factors`.

## Usage

```bash
uv run webresearch run \
  "Evaluate ProductX for technical diligence. Target: https://productx.com" \
  technical_due_diligence
```

## Key Components

- **Hooks**: Uses `pre_hook` and `post_hook` extensively to manage the complex state transitions between claims and evidence.
- **Tools**: Includes `search_technical_tool` which is tuned to find official and community technical discussions.
- **Example Data**: See `examples/input.example.json` and `examples/output.example.json` for the expected data shapes.
