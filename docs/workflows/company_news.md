# Company News Workflow

The `company_news` workflow is designed to provide a comprehensive view of a company's recent activities by monitoring official, social, and web news channels.

## Purpose

This workflow is optimized for speed and breadth, capturing news from a variety of sources to build a holistic picture of a company's current status, public perception, and official announcements.

## Pipeline Structure

1. **Intake Planner**: Analyzes the company name and any specific areas of interest to create a targeted news research plan.
2. **Parallel Research**: Three specialized agents run in parallel to gather data from different angles:
   - **Web News Researcher**: Searches for news articles, press releases, and media mentions.
   - **Social Researcher**: Monitors social media platforms (Twitter, LinkedIn, etc.) for real-time discussions and updates.
   - **Company Researcher**: Focuses on the company's own domain to find blogs, newsrooms, and official changelogs.
3. **Output Writer**: Synthesizes the findings from all three channels into a unified news report.

## Usage

```bash
uv run webresearch run "Recent news for [Company Name]" company_news
```

## Key Agents

- **Intake Planner**: `prompts/intake_planner.j2`
- **Web News Researcher**: `prompts/web_news_researcher.j2`
- **Social Researcher**: `prompts/social_researcher.j2`
- **Company Researcher**: `prompts/company_researcher.j2`
- **Output Writer**: `prompts/output_writer.j2`

## Specialized Tools

The `company_news` workflow utilizes tools tailored for discovery and news searching:
- `search_news_tool`: Optimized for news queries with support for site-specific operators.
- `discover_company_pages_tool`: Specifically finds a company's own news outlets (blogs, press rooms).
- `fetch_and_extract_tool`: Standard content extraction to pull text from news articles and posts.
