# Technical Due-Diligence Web Research Workflow

## Purpose

This workflow evaluates the public technical substance of a company or product for VC-style technical due diligence.

It does not inspect private code, private infrastructure, internal metrics, or non-public customer data. Its job is to produce a sourced web-research dossier that separates public claims, public evidence, reasonable technical inference, competitor context, and follow-up questions for later product/code review.

## Core Question

Is the product's technology likely a real asset, or does the public evidence suggest it is thin, commodity, easily replicated, or mostly a wrapper around existing tools or LLM APIs?

## Inputs

Required:

- `query`: natural-language diligence prompt.
- `target_company`: company or product name.
- `target_urls`: known URLs for the target company or product.

Recommended:

- `product_category`: category such as AI sales assistant, devtool, data platform, security product, vertical SaaS, infrastructure, etc.
- `known_claims`: user-provided pitch claims to verify.
- `competitor_urls`: known competitor URLs.
- `docs_urls`: docs, API references, changelogs, release notes, technical blogs.
- `pitch_or_demo_urls`: pitch deck, demo page, webinar, launch post, Product Hunt, marketplace page.
- `customer_or_case_study_urls`: customers, case studies, testimonials, integration pages.
- `constraints`: geography, market segment, deployment model, regulatory context, or diligence focus areas.

## Output

The workflow should return both:

- A readable Markdown investment diligence memo.
- A structured JSON dossier for downstream code/product review.

The output should be explicit about confidence:

- `evidenced`: directly supported by public sources.
- `inferred`: reasonable conclusion from public evidence.
- `unknown`: cannot be determined from web research.
- `contradicted`: company claim conflicts with public evidence.

## Workflow Shape

### 1. Intake Planner

Goal: convert the user prompt and URLs into a diligence plan.

Responsibilities:

- Identify the product being evaluated.
- Extract diligence dimensions from the prompt.
- Normalize known URLs into groups: company site, docs, API, blog, changelog, demo, pricing, customers, competitors.
- Decide which public evidence would be most probative.
- Define search strategy for missing materials.
- Define competitor discovery strategy if competitors are not supplied.

Output:

- Research questions.
- Known target URLs.
- Missing evidence targets.
- Competitor discovery queries.
- Risk areas to evaluate.

### 2. Claim Extractor

Goal: extract what the company publicly claims.

Sources to inspect:

- Homepage.
- Product pages.
- Docs.
- API reference.
- Technical blog.
- Changelog.
- Case studies.
- Pricing/packaging.
- Launch posts.
- Demo or pitch pages if provided.

Claims to extract:

- Product capability claims.
- Architecture or infrastructure claims.
- AI/model claims.
- Automation claims.
- Performance, scale, accuracy, or reliability claims.
- Integration/ecosystem claims.
- Security, compliance, deployment, or data-handling claims.
- Customer or production usage claims.

Output should distinguish:

- Verbatim or near-verbatim public claim.
- Source ID.
- Claim type.
- Diligence relevance.
- Whether the claim is testable later in code/product review.

### 3. Evidence Researcher

Goal: collect public evidence that supports, weakens, or contextualizes the claims.

Evidence types:

- API docs that show real surface area.
- SDKs, CLI tools, examples, schemas, integration guides.
- Changelogs showing sustained engineering.
- Technical blog posts with implementation detail.
- Architecture docs or deployment docs.
- Security docs, SOC2 pages, data handling docs.
- Public GitHub repositories or package registries.
- Marketplace listings and integration directories.
- Customer case studies with concrete usage.
- Benchmarks or evaluations, if credible.

Signals of product depth:

- Detailed docs beyond marketing pages.
- Non-trivial API surface.
- Real integration complexity.
- Versioned changelog or release cadence.
- Deployment/configuration detail.
- Error handling, auth, webhooks, SDKs, migration guides.
- Public technical artifacts that would be hard to fake quickly.

Signals of thinness:

- Marketing claims without docs.
- Demo-only flows.
- No API or integration detail despite claiming platform depth.
- Generic AI language without architecture or evaluation detail.
- No changelog, release history, or technical artifacts.
- Customer claims without concrete usage detail.
- Heavy reliance on generic screenshots or vague “agent” language.

### 4. Competitor Mapper

Goal: identify relevant competitors and establish product-category expectations.

Inputs:

- User-supplied competitor URLs.
- Search-discovered competitors.
- Category analyst lists, marketplace categories, review sites, GitHub alternatives, or comparison pages.

For each competitor:

- What do they claim?
- What technical surfaces are public?
- What integrations, APIs, docs, SDKs, or deployment features exist?
- How mature does the product look publicly?
- What is table stakes in this category?
- What, if anything, appears meaningfully differentiated about the target?

Competitor assessment should avoid treating marketing differences as technical differentiation unless backed by technical evidence.

### 5. Technical Substance Reviewer

Goal: assess whether the public evidence supports real product depth.

Evaluation dimensions:

- `claim_support`: are major claims backed by public evidence?
- `product_depth`: does the product look deep beneath the demo layer?
- `technical_specificity`: are docs and artifacts concrete or vague?
- `proprietary_architecture`: is there evidence of differentiated architecture?
- `commodity_risk`: could this be assembled from common SaaS, OSS, or LLM APIs?
- `wrapper_risk`: does it look like a thin wrapper around ChatGPT or another model/API?
- `functional_correctness_risk`: do claims appear technically plausible and internally consistent?
- `replicability`: could a competent competitor replicate the public feature set in six months?
- `category_fit`: does the product meet normal expectations for its category?

Important boundary:

The reviewer must label conclusions as public-evidence judgments. It must not claim to know private implementation details.

### 6. Gap Researcher

Goal: resolve critical missing evidence before final output.

Run only focused follow-up searches from the reviewer.

Examples:

- Official docs for a claimed API.
- Changelog for release cadence.
- Public package or SDK evidence.
- Competitor docs for similar feature claims.
- Customer case study details.
- Security or deployment docs for enterprise claims.

Stop after the configured max rounds and surface unresolved gaps explicitly.

### 7. Final Diligence Memo

Goal: produce a practical memo for an investor or technical diligence lead.

Memo sections:

1. Executive judgment.
2. Public claim inventory.
3. Evidence of real technical substance.
4. Evidence of thinness or facade risk.
5. Competitor comparison.
6. Proprietary/differentiation assessment.
7. Wrapper/commodity risk.
8. Replicability estimate.
9. Confidence and unresolved gaps.
10. Follow-up questions for product demo, founder diligence, and later code review.

The memo should be direct, evidence-backed, and clear about what web research can and cannot prove.

## Recommended Structured JSON Schema

```json
{
  "type": "object",
  "properties": {
    "target": {
      "type": "object",
      "properties": {
        "company": { "type": "string" },
        "product": { "type": "string" },
        "category": { "type": "string" },
        "target_urls": {
          "type": "array",
          "items": { "type": "string" }
        }
      },
      "required": ["company", "product", "category", "target_urls"]
    },
    "executive_judgment": {
      "type": "object",
      "properties": {
        "technical_substance_rating": {
          "type": "string",
          "enum": ["high", "medium", "low", "unknown"]
        },
        "wrapper_risk": {
          "type": "string",
          "enum": ["low", "medium", "high", "unknown"]
        },
        "replicability_risk": {
          "type": "string",
          "enum": ["low", "medium", "high", "unknown"]
        },
        "summary": { "type": "string" },
        "confidence": {
          "type": "string",
          "enum": ["high", "medium", "low"]
        }
      },
      "required": [
        "technical_substance_rating",
        "wrapper_risk",
        "replicability_risk",
        "summary",
        "confidence"
      ]
    },
    "claims": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "claim": { "type": "string" },
          "claim_type": { "type": "string" },
          "source_ids": {
            "type": "array",
            "items": { "type": "string" }
          },
          "support_status": {
            "type": "string",
            "enum": ["supported", "partially_supported", "unsupported", "contradicted", "unknown"]
          },
          "notes": { "type": "string" }
        },
        "required": ["claim", "claim_type", "source_ids", "support_status", "notes"]
      }
    },
    "technical_substance": {
      "type": "object",
      "properties": {
        "positive_signals": {
          "type": "array",
          "items": { "type": "string" }
        },
        "negative_signals": {
          "type": "array",
          "items": { "type": "string" }
        },
        "inferences": {
          "type": "array",
          "items": { "type": "string" }
        },
        "source_ids": {
          "type": "array",
          "items": { "type": "string" }
        }
      },
      "required": ["positive_signals", "negative_signals", "inferences", "source_ids"]
    },
    "competitors": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": { "type": "string" },
          "url": { "type": "string" },
          "claims": {
            "type": "array",
            "items": { "type": "string" }
          },
          "technical_surface": { "type": "string" },
          "differentiation_vs_target": { "type": "string" },
          "source_ids": {
            "type": "array",
            "items": { "type": "string" }
          }
        },
        "required": [
          "name",
          "url",
          "claims",
          "technical_surface",
          "differentiation_vs_target",
          "source_ids"
        ]
      }
    },
    "replicability": {
      "type": "object",
      "properties": {
        "estimated_time_to_replicate": { "type": "string" },
        "reasoning": { "type": "string" },
        "hard_parts": {
          "type": "array",
          "items": { "type": "string" }
        },
        "commodity_parts": {
          "type": "array",
          "items": { "type": "string" }
        }
      },
      "required": ["estimated_time_to_replicate", "reasoning", "hard_parts", "commodity_parts"]
    },
    "follow_up_for_code_review": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "question": { "type": "string" },
          "why_it_matters": { "type": "string" },
          "related_claims": {
            "type": "array",
            "items": { "type": "string" }
          }
        },
        "required": ["question", "why_it_matters", "related_claims"]
      }
    },
    "unresolved_gaps": {
      "type": "array",
      "items": { "type": "string" }
    }
  },
  "required": [
    "target",
    "executive_judgment",
    "claims",
    "technical_substance",
    "competitors",
    "replicability",
    "follow_up_for_code_review",
    "unresolved_gaps"
  ]
}
```

## Suggested Agent Prompts

### Claim Extractor Prompt

Extract explicit product and technology claims from the provided target URLs and search results. Separate marketing language from concrete technical claims. Only cite registered source IDs. Do not evaluate yet.

### Evidence Researcher Prompt

Find public artifacts that make the target product look technically real or technically thin. Prioritize docs, API references, SDKs, changelogs, architecture posts, customer case studies, security docs, and integration pages.

### Competitor Researcher Prompt

Identify category competitors and compare public technical surfaces. Focus on what competitors actually expose in docs, APIs, SDKs, integrations, and customer evidence. Avoid treating positioning language as differentiation.

### Technical Substance Reviewer Prompt

Evaluate claims against evidence. Label each conclusion as evidenced, inferred, unknown, or contradicted. Assess wrapper risk, commodity risk, proprietary differentiation, product depth, functional plausibility, and six-month replicability.

### Final Memo Prompt

Write an investor-facing technical diligence memo. Be direct. Cite source IDs. Clearly separate public evidence from inference. Include follow-up questions for founder diligence, product demo, and later code review.

## Scoring Rubric

Use this rubric for each major dimension:

- `high`: strong public evidence from docs, APIs, changelogs, architecture detail, customer usage, or differentiated technical surface.
- `medium`: some credible evidence, but important gaps remain.
- `low`: claims are mostly marketing, generic, unsupported, or easy to replicate.
- `unknown`: public evidence is insufficient to judge.

Specific risk interpretation:

- `wrapper_risk high`: product appears mostly prompt orchestration or UI around third-party LLMs, with little public evidence of proprietary data, workflow depth, evaluation, infrastructure, or integrations.
- `commodity_risk high`: product appears assembled from common SaaS/OSS components and standard APIs without meaningful technical differentiation.
- `replicability_risk high`: a focused competitor could plausibly reproduce the public feature set in six months.

## Recommended Workflow ID

`technical_due_diligence`

## Recommended Depth

Default to deep-style behavior:

- Research across target, category, and competitors.
- Run at least one review/gap loop.
- Prefer precision over speed.
- Make unresolved gaps explicit instead of overclaiming.

## Example User Prompt

```text
Evaluate Acme AI for technical due diligence.

Target URLs:
- https://acme.example
- https://docs.acme.example
- https://acme.example/blog/architecture

Known competitors:
- https://competitor-a.example
- https://competitor-b.example

Focus:
- Is this technically substantial or mostly a ChatGPT wrapper?
- Are the product claims backed by docs/API/changelog/customer evidence?
- How differentiated is the approach?
- Could a competitor replicate this in six months?
- What should we inspect later in code review?
```

## Non-Goals

- Proving private implementation details.
- Verifying production scale claims without private telemetry.
- Performing security audit.
- Performing code review.
- Replacing founder/product diligence.
- Treating lack of public evidence as proof of fraud.

## Success Criteria

A successful run should produce:

- A sourced inventory of public claims.
- A sourced assessment of technical substance.
- A competitor context map.
- A wrapper/commodity/replicability risk assessment.
- A clear list of unresolved gaps.
- A code-review follow-up checklist tied to public claims.
