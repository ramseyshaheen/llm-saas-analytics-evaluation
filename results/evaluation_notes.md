## Test #1 MRR – Intial Prompt (Draft)

Ground truth:
- MRR as of 2024-01-01: 50,000
    Sonnet 4.5 incorrectly failed the intial prompt due to filtering on "active" customers despite a historical sumation of MRR in fact including all customers in the point in time. 
    Numeric comparison:
    - Ground-truth MRR: 50,000
    - Claude MRR: 47,200
    - Difference: -2,800 (-5.6%)

    Root cause:
    - Claude filtered on `status = 'active'`
    - Date-active subscriptions with non-active status were excluded
    - Status field not authoritative in this dataset

## Test #2 Logo Churn – Intial Prompt (Draft)

Ground truth (January 2024):
- Customers active at start of month: 165
- Customers churned during month: 0
- Logo churn rate: 0.0%

Claude evaluation:
- Generated customer-level churn logic
- Correctly identified denominator (active at start of month)
- Correctly identified numerator (last subscription ending in Jan)
- Avoided subscription-level double counting
- Included NULL / divide-by-zero safeguards

Execution result:
- Claude SQL executed successfully in DuckDB
- Returned exact ground-truth result (0.0%)

Notes:
- Logic slightly overengineered for synthetic data
- Would be appropriate for real-world datasets with overlapping subscriptions

## Test #3 NRR – Intial Prompt (Draft)

Numeric comparison:
- Ground-truth start revenue: 50,000
- Claude start revenue: 47,200 (−5.6%)
- Claude end revenue: 47,900 (−5.5%)

NRR comparison:
- Ground-truth NRR: ~101.41%
- Claude NRR: 101.48%

Key insight:
- Systematic undercounting in both numerator and denominator caused the NRR ratio to appear correct
- Absolute revenue was materially incorrect while the derived metric looked plausible

Risk:
- This failure mode would be difficult to detect in production dashboards
- Highlights danger of trusting ratios without validating base metrics

## Test #1 MRR - Minimal Prompt

Result:
- Claude produced runnable, professional SQL
- Returned MRR lower than ground truth

Failures:
- Relied on non-authoritative `status = 'active'`
- Used end-of-month date bounds instead of snapshot on 2024-01-01
- Introduced unnecessary billing-period normalization (could be helpful but beyond prompt scope)

Risk:
- Output appears reasonable and well-explained
- Would likely pass superficial review while materially undercounting revenue

## Test #1 MRR - Explicit Prompt

Result:
- Claude produced clean, well-scoped SQL
- Snapshot date logic was correct
- Returned MRR lower than ground truth

Failure mode:
- Continued use of `status = 'active'` despite explicit date-based definition
- Heuristic redundancy overrode semantic correctness

Observation:
- Claude acknowledged the assumption explicitly but still applied it
- Suggests defensive filtering bias when status fields are present

## Test #1 MRR - Detailed Prompt 

Result:
- Claude produced SQL that matches the ground-truth MRR definition
- Status field was ignored entirely
- Returned MRR matches ground truth (50,000)

Key difference:
- Explicit prioritization of date-based activity logic
- Forced reasoning step before SQL generation

Observation:
- Claude can self-correct when semantic hierarchy is clarified
- Indicates heuristic reliance is prompt-sensitive, not unavoidable


## Test #2 Logo Churn - Minimal Prompt

Result:
- SQL executed successfully
- Returned correct logo churn (0.0%)

Observations:
- Correct customer-level churn logic
- Unnecessary and inconsistent use of status fields
- End-of-month boundary choice not justified
- Extra joins/columns not required for metric

Interpretation:
- For event-based metrics like churn, Claude can return correct results
  even when internal logic is fragile or over-engineered

## Test #2 Logo Churn - Explicit Prompt 

Result:
- SQL executed successfully
- Returned correct logo churn (0.0%)

Observations:
- Correct cohort definition (customers active on 2024-01-01)
- Correct customer-level churn logic
- No reliance on status fields
- Clean temporal boundaries and assumptions

Comparison:
- Explicit prompt eliminated fragile status heuristics seen in minimal prompt
- Churn metric appears more robust to prompt ambiguity than revenue metrics

## Test #2 Logo Churn - Detailed Prompt

Result:
- Returned correct logo churn (0.0%)
- Logic fully aligned with explicit definition

Key difference vs prior run:
- Status heuristics fully removed
- Reasoning, SQL, and assumptions internally consistent

Conclusion:
- Prompt phrasing materially affects whether defensive heuristics are introduced
- Correctness can be restored without changing the underlying metric definition

## Test #3 NRR - Minimal Prompt 

Result:
- SQL executed but does not represent correct NRR

Failure modes:
- Incorrect billing-period normalization (inflated revenue)
- Reliance on non-authoritative `status = 'active'`
- Incorrect cohort boundary (`start_date < 2024-01-01`)
- Metric definition drift (invoice-based YoY revenue)

Interpretation:
- Without explicit guidance, Claude fails to infer NRR correctly
- NRR is substantially more error-prone than MRR or churn under ambiguity

## Test #3 NRR - Explicit Prompt 

Result:
- SQL structure matches correct NRR definition
- Returned plausible but incorrect NRR value

Failure mode:
- Continued reliance on non-authoritative `status = 'active'`
- Revenue undercounted at both start and end of period

Interpretation:
- Explicit metric definitions alone are insufficient for correct NRR
- Claude defaults to defensive status heuristics even when date logic is complete

## Test #3 NRR - Detailed Prompt

Result:
- total_start_revenue = 47,200 (undercounted)
- total_end_revenue = 47,900 (undercounted)
- nrr_percentage = 101.48% (matches ground truth)

Interpretation:
- Correct NRR value was achieved via symmetric revenue undercounting
- Ratio preserved despite incorrect absolute revenue
- Represents a high-risk silent failure mode for AI-generated analytics

## Test #4 Revenue Decomposition - Minimal Prompt

Result: 
- Executable SQL generation succeeded, but execution failed due to dialect error (ORDER BY with UNION).

Failure Modes:
- Incorrect baseline (Dec 31 → Jan 31 instead of Jan 1 → Jan 31)
- Inclusion of “new” revenue (cohort leakage)
- Output violated single-row requirement
- Dialect-specific SQL error (DuckDB binder failure)
- Reliance on status-based filtering

Interpretation:
- Under minimal prompting, the model defaulted to a standard month-over-month movement taxonomy rather than the specified decomposition, and generated non-executable SQL.

## Test #4 Revenue Decomposition - Explicit Prompt 

Result:
- Executable but semantically incorrect.

Failure Modes:
- Used Dec 31 baseline instead of Jan 1.
- Included new customer revenue (cohort violation).
- Returned multiple rows and extra columns.
- Reintroduced status-based filtering.
- Produced internally consistent but incorrect reconciliation.

Interpretation:
- With explicit metric definitions, the model was able to run a reasonble revenue decomposition process. However, it retained multiple key assumption errors.

### Test #4 Revenue Decomposition - Detailed Prompt

Result: 
- Executable SQL generation succeeded and reconciled mathematically, producing a single-row decomposition output with internally consistent movement logic.

Notes: 
- Cohort correctly fixed at January 1 snapshot
- Movement buckets mutually exclusive (expansion, contraction, churn)
- Mathematical reconciliation holds: ending_mrr = starting_mrr + expansion − contraction − churn
- Output adheres to aggregation-level requirement (single summary row)
- No dialect or execution errors in DuckDB

Conclusion:
- Under detailed prompting, the model produced structurally sound, executable SQL that enforced cohort consistency and guaranteed reconciliation of components to total MRR change. The logic correctly decomposed revenue movement into mutually exclusive categories and satisfied the mathematical integrity constraint specified in the prompt.