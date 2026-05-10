# Product Overview

**Web Research** is a Python SDK for building LLM-powered web research agents with real-time web access.

## What it does

Web Research automates the tedious parts of gathering information from the web. Instead of manually searching, clicking links, and summarizing, you can define high-level research goals, and the system will:
1. **Plan** the research strategy.
2. **Search** for relevant sources.
3. **Extract** content from web pages.
4. **Synthesize** findings into structured reports or markdown answers.
5. **Verify** and iterate to fill knowledge gaps.

## Key Use Cases

### 1. Deep Topic Research
Perfect for broad questions like "What are the latest trends in AI agents?" or "Summarize the current state of Node.js LTS." The `deep` workflow (install via [`webresearch-deep`](https://github.com/kodepo-com/web-research-deep)) handles multi-step research, reviewing its own work to find and fix gaps.

### 2. Technical Due Diligence
Evaluate technical products or companies by extracting claims, researching evidence, and producing structured diligence reports. Available as a separate workflow package.

### 3. Automated Monitoring
Track company news or specific topics by running workflows on a schedule (e.g., via GitHub Actions).

## Core Philosophy

- **Transparency**: Every step, tool call, and cost is logged and visible.
- **Accuracy**: Built-in review loops identify and address gaps in the research.
- **Flexibility**: Define your own research patterns using a declarative pipeline.
- **Cost Control**: Real-time cost tracking ensures you stay within budget.

## Who is it for?

- **Developers**: Building autonomous agents that need reliable web research capabilities.
- **Researchers & Analysts**: Automating the "first pass" of data gathering for reports.
- **Product Managers**: Tracking competitors and technical trends.
