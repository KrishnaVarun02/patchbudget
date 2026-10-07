# PatchBudget diagnostic protocol v1

Frozen before final evaluation on 2026-10-01. This is a controlled mutation
experiment on small QuixBugs algorithms, not an evaluation of AI-generated
repository patches. No paid computation or model calls are used.

## Question and estimands

How do candidate allocation and failure-history test ordering change the
reliability/coverage trade-off under a cap on additional test executions?
The primary comparison is candidate-focused versus round-robin allocation at
budget 32 and minimum 8 distinct passing verification tests. Failure-history
ordering is an ablation of the same allocation, not a claimed novel algorithm.
Report the full budget/threshold grid and retain negative findings.

## Data and separation

Use QuixBugs commit 4257f44b0ff1181dedaedee6a447e133219fcebf.
Select 16 self-contained integer/list/string algorithms with bounded input
domains: bitcount, bucketsort, find_first_in_sorted, gcd, get_factors,
is_valid_parenthesization, knapsack, kth, lcs_length, lis, max_sublist_sum,
mergesort, next_permutation, pascal, quicksort, sieve.
Selection is based on simple deterministic input adapters, before results.

Candidates comprise the reference, original buggy implementation, and at most
40 single-edit AST mutations sampled by source hash from a predeclared grammar.
No mutation is selected or discarded using hidden labels. Compile failures are
logged. Equivalent mutants remain. This mutation process is a diagnostic fault
model; a reference patch is always available and randomly ranked.

Developer suites contain the first 1, first 3, or all distributed JSON cases
(when fewer exist, use all available). Every policy gets the same developer
gate and its cost is reported separately. Main results use the first case;
the deliberately weak gate exposes verification behavior. Stronger gates are
mandatory sensitivity analyses, never a hidden change to the primary setting.

Generate 64 distinct verification inputs and 256 distinct held-out inputs per
algorithm with separate deterministic seed streams, excluding developer inputs
and overlap across splits. Expected outputs come from the reference; cross-check
all inputs against independently implemented standard-library/brute-force oracles
where available. Reference disagreements abort the run. Scheduler code sees only
verification outcomes through a charged query API. Hidden outcomes and reference
identity are not passed to it. This is oracle-backed test generation, with oracle
cost excluded and explicitly disclosed; no claim of realistic oracle availability.

## Policies and budget

Existing-only chooses the highest-ranked gate passer with no extra verification.
Round-robin gives one test at a time to the least-tested active candidate.
Candidate-focused verifies the highest-ranked surviving candidate until rejected
or all verification tests run, then moves on. Both use a shuffled fixed test order.
Failure-history uses the same candidate allocation but orders untried tests by
observed failures divided by observations (Beta(1,1) smoothing); ties use the
same fixed order. It learns only from charged outcomes within the current issue.
This is a transparent failure-history heuristic, not a full FRTP reproduction.

For each policy, budgets are 8, 16, 32, 64, 128 additional candidate-test queries.
After the cap, choose the highest-ranked non-rejected candidate with at least
k distinct passing tests, k in {1,4,8,16}; otherwise abstain. Exhausted policies
may spend less than the cap and must report actual queries. No hidden-oracle
early stopping. Thirty fixed candidate/test ordering seeds (0..29) per algorithm;
seed 999 on bitcount and gcd is reserved for a runtime pilot and excluded.

## Metrics and inference

Test-supported correct means matching all 256 held-out cases; it is not semantic
correctness. Report accepted-and-held-out-passing fraction of all tasks (useful
coverage), false-accept fraction of all tasks, acceptance coverage, conditional
held-out pass rate (undefined if no acceptance), additional queries, developer
gate queries, and execution/decision wall time. At each setting average over
rank seeds within algorithm, then equally weight algorithms. Paired percentile
bootstrap intervals resample the 16 algorithms, with 5,000 fixed-seed draws.
They describe this small selected corpus, not a representative population of
software projects. Do not treat ranking seeds as independent bugs.

## Stopping, costs, and deviations

Execute the predeclared matrix once, then rerun only to repair verified code or
reporting errors. Validate central artifacts in a fresh environment. A 20,000
Python-line-event cap prevents nonterminating mutants; exceptions and cap hits
count as failed tests. Resource behavior is part of this bounded diagnostic.
Keep raw outcome matrices, selection records, exclusions, timing and provenance.
Record deviations in RESEARCH_LOG.md before revised final evaluation.

## Publication limits

This package can support a reproducible technical report. It cannot establish a
new state of the art or submission readiness. A stronger publication needs real
candidate patches, independent non-reference test oracles, repository-level
benchmarks and comparison with the closest reproducible published schedulers.
