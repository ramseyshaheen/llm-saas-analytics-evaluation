# LLM Reliability Evaluation on SaaS Analytics Metrics

## Overview

This project evaluates the reliability of large language models (LLMs) in generating executable and logically correct SQL for realistic core SaaS metrics. The tests and synthetic data set aim to recreate realistic tasks an analyst or analytics engineer may encounter.

Using synthetic SaaS subscription datasets designed to simulate part of a complex corporate database, I compare Claude Sonnet 4.5–generated SQL against a DuckDB ground-truth implementation across multiple financial and retention metrics. The primary goal is to measure the effectiveness, failure modes, and logical correctness of LLM in realistic analytical tasks under various levels of prompt detail.

## Dataset
Synthetic SaaS subscription dataset generated in Python with:

- 5 Tables
- 25 Fields
- 500 customers
- ~10,000 invoices
- Segment-based payment behavior (SMB / Mid-Market / Enterprise)
- Realistic churn, expansion, and contract timeline behavior

All data is stored as Parquet and queried via DuckDB.

# Evaluation Design

## LLM Configuration

Model: Claude Sonnet 4.5

Role: Analytics engineer working with a SaaS dataset (provided in all prompts).

Context: Full schema with available tables and fields within the tables (provided in all prompts). 

Minimal: Single-sentence task definition
- Minimal business context or edge case handling

Explicit: Typical business request detail
- Definition section with business context
- "Please:" section with output specifications
- "Rules" section added for Tests 3-4
- ~5 sentences total

Detailed: Comprehensive specification
- Business definitions and framing
- Explicit evaluation rules
- Edge case requirements
- Reconciliation constraints
- ~2x the content of Explicit prompts

All outputs were:
1) Automatically extract SQL from LLM response
2) Execute in DuckDB
3) Compare against ground truth
4) Logged as pass/fail with evaluation details 

## Metrics Tested

1) Monthly Recurring Revenue (MRR)
2) Logo Churn
3) Net Revenue Retention (NRR)
4) Revenue Decomposition (Expansion / Contraction / Churn)

## Key Results
- Minimal prompts failed systematically, primarily due to semantic drift (incorrect cohort definitions, revenue leakage, or defaulting to generic SaaS logic).
- Explicit prompts improved execution stability, but still exhibited logical inconsistencies under more complex metrics.
- Detailed prompts consistently aligned with specification, preserved cohort integrity, and satisfied reconciliation constraints. However, LLM assumptions could still not be fully predicted in all cases which can still introduce logical errors in more complex tests.

## Failure Mode Examples:
### 1. Semantic Drift
Issue: Undocumented assumptions added to queries
Example: LLM added `status = 'active'` filter for historical revenue calculations, incorrectly excluding churned customers and underreporting revenue

### 2. Time Constraint Errors  
Issue: Incorrect date boundary logic
Example: Prompt specified "January 2024", but LLM used `start_date <= '2023-12-31'`, including a day of December records

### 3. Cohort Leakage
Issue: Mixing customer cohorts in retention calculations
Example: Including new customer revenue in NRR calculations

### 4. Output Structure Violations
Issue: LLM attempting to expand scope beyond specifications
Example: Adding unrequested aggregation rows, introducing complex UNION structures not needed for the task

## Conclusion
Across 15 prompt variations and 4 core SaaS business tests, level of prompt detail significantly affected the quality of logical output. At the “Detailed” prompt level, Claude’s output returned the correct values for Tests 1 through 4. However, Test 3 and Test 4 can be considered logically fragile and not optimal. “Minimal” and “Explicit” prompts produced unreliable output with significantly more room for inaccurate model assumptions and logical errors. 

Only at the “Detailed” prompt level did outputs consisitently align with the defined business logic. However, to produce a “Detailed” level prompt, the user required a strong understanding of specific assumptions and risk points with the selected LLM and data set. This may be unrealistic for a user working with a specific LLM or data set for the first time. This creates a "cold-start" problem: users working with a new LLM or dataset for the first time may lack the domain knowledge needed to write sufficiently detailed prompts, leading to silently incorrect analytical outputs.

## Tech Stack
- Python (data generation, evaluation framework)
- DuckDB (SQL execution)
- Anthropic Claude Sonnet 4.5 API (LLM API)

## Repository Structure
llm-saas-analytics-eval/

├── data/              # Synthetic parquet files

├── prompts/           # Prompt variations by metric and detail level

├── scripts/           # Data generation and evaluation scripts

├── results/           # Evaluation outputs 

└── saas_analytics.duckdb

## Potential Next Steps
- Expand to additional LLM APIs (ChatGPT, Gemini)
- Test additional prompt engineering techniques 
- Add automated retry/refinement loops

# Additional Considerations
## LLM API Token Limits
- Increasing the token limit above reasonable limits for the complexity of prompts and tests did not materially change SQL logic or assumptions used in the LLM response.
- Token limits only impacted detail of description and wording, and the LLM was not able to use additional tokens in budget to fix semantic errors.
- Token limits will not be a test variable with a standard set at a limit of 1000 to 2000 API tokens depending on the specific test in the project.

## LLM Incomplete Code Block Outputs
- In some cases, such as the Test #4 minimal prompt, the LLM would output a full response, but the response would not close out the code block.
- To ensure responses in these cases could still be evaluated, I included additions in python to capture cases of incomplete code block outputs while still noting the occurrence as an error.
