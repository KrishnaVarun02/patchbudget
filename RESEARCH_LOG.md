# Research log

## 2026-10-01: scope and protocol

- Read supplied resumes as self-reported background; no historical metric reused.
- Audited existing IssueForge and MARL repositories. Existing artifacts do not
  supply suitable seed-level data for the proposed research questions.
- Chose a fresh, controlled QuixBugs mutation experiment because no paid model
  budget or existing candidate-patch dataset was supplied. This narrows the
  proposed AI-patch project to a reproducible diagnostic technical report.
- Primary-source review found prior adaptive scheduling (FRTP, MPTPS, COLEMAN).
  The investigation is an empirical allocation/abstention study, not a new
  scheduling algorithm or an established novel contribution.
- Wrote PROTOCOL.md before final matrix execution.
- Protocol v1.1, before pilot/final: replace pascal with to_base. Pascal has only
  360 distinct proposed inputs, forcing large quadratic-output cases solely to
  obtain a disjoint 320-case split. to_base offers a cheap, much broader domain.
  Add FRTP-inspired failure-count policy after identifying its exact published
  algorithm. The original requires full-suite passing and seeds an originally
  failing test; our generated pool starts all counts at zero and shares the
  common threshold rule. Retain smoothed failure rate as a separate heuristic.
- Developer-suite executions use a 2,000,000 line-event cap because some original
  official tests are larger than the controlled generated domain. Generated
  tests retain a 20,000-event cap. All policies use identical recorded outcomes.

## Status

## Protocol v1.2: resource preflight corrections

- Pilot on bitcount and gcd completed in 4.32 seconds (seed 999; excluded from
  final analysis). All seven initial core tests passed.
- First full-matrix construction stopped on the official knapsack case with
  capacity 6,404,180 and 24 items: reference DP exceeded 2,000,000 line events.
  No policy comparison/aggregate was produced. Independent preflight also found
  sieve(958) exceeded the generated-test limit on the reference (20,001 events).
- Before final policy evaluation, restrict sieve's generated domain to [0,600]
  (601 possible inputs; reference maximum 14,485 line events) and exclude official
  knapsack cases where capacity*item_count exceeds 1,000,000. This removes exactly
  one developer input; its full case, hash, and reason are saved in the matrix.
  'All' gate henceforth means all resource-eligible developer cases. Generated
  knapsack inputs are unchanged; no candidate/hidden-label-based exclusions.
- The aborted construction is retained in results/aborted-v1.1. Complete final
  runs use the amended fixed protocol. Measured matrix time includes reference
  oracle construction; gate queries are counterfactual short-circuit call counts,
  not the physical cost of exhaustively constructing all outcome matrices.

## Status

Implementation and manuscript status are recorded in README.md after execution.
Full real-world LLM-patch evaluation and academic submission remain future work.

## Protocol v1.3: bounded native-operation work

- Second construction was interrupted at a to_base mutant whose mutated division
  multiplies instead, making Python integers and strings grow for up to two million
  line events. This is a resource issue, not a policy result. Partial matrices are
  retained in results/aborted-v1.2.
- Independent preflight checked every resource-eligible developer reference case:
  maximum 43,631 line events (knapsack); all other programs at most 707. Set the
  shared developer cap to 100,000, retain 20,000 for generated tests, and rerun
  all matrices from scratch. Any mutant outcome changes under the stricter cap
  belong to the amended bounded-execution diagnostic and are not presumed absent.
- Primary metrics/budgets/thresholds/ranking seeds remain as declared. There was
  no aggregate final policy comparison before this correction.

## Completed evaluation and review

- Final v1.3 protocol completed in 29.17 seconds: 16 algorithms, 241 candidates,
  116,640 policy/seed/settings selection rows. These rows are repeated settings,
  not independent bugs. Physical matrix construction took 24.4 seconds.
- Primary focused allocation useful coverage 93.125%, false acceptance 3.75%;
  round robin 62.0833% and 1.4583%. This is a coverage/risk trade-off. Failure-count
  ordering adds only 0.2083 useful-coverage percentage points over focus here.
- Independent review verified 1,446 executed cells, all selection labels/accounting,
  all 243 aggregate settings, and the scope/numerical claims in the manuscript.
- The full protocol was rerun in a fresh Python 3.14.7 environment. All outcome
  matrices and every replayed policy selection matched. Seven substantive unit
  tests passed; records are in results/verification.json and clean-verification.json.
- LaTeX source and compiled PDF report the executed study with explicit limitations.
  Academic submission, peer review, and acceptance have not occurred.
