from __future__ import annotations

from webresearch.pipeline.runner import Pipeline
from webresearch.pipeline.step import Parallel
from webresearch.workflows.company_news import agents

PIPELINE = Pipeline(
    steps=[
        agents.intake_planner,
        Parallel(
            [
                agents.web_news_researcher,
                agents.social_researcher,
                agents.company_researcher,
            ]
        ),
        agents.output_writer,
    ],
    final_output_key="output_writer",
    workflow_id="company_news",
)
