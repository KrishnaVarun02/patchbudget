# PatchBudget

An research-oriented study of **candidate verification under a fixed test-query budget**.

The project examines how test-allocation policies distribute limited verification effort and how that allocation changes the trade-off between useful coverage and false acceptance.

## Research question

When candidate patches compete for a limited number of test queries, how does the allocation policy affect which candidates are accepted and how often accepted candidates fail held-out evaluation?

## Methodology

- Uses controlled **QuixBugs mutations** with reference oracles.
- Implements round-robin, candidate-focused, failure-count, and failure-history test-allocation policies.
- Keeps scheduling decisions separate from hidden evaluation labels.
- Applies prespecified acceptance thresholds and minimum passing-test requirements.
- Records candidate/test queries, policy selections, outcome matrices, and analysis artifacts.
- Evaluates multiple query budgets and developer-test gates to examine sensitivity to the verification protocol.

The scheduling implementation is intentionally a pure observable-state policy: it receives candidate/test outcomes revealed by its allocated queries rather than hidden held-out labels.

## Experiments / Evaluation

The full experiment evaluates **241 candidates across 16 benchmark programs** and records 116,640 selection records across the configured policy, budget, and gate settings.

The analysis reports acceptance coverage, useful coverage, false acceptance, query usage, and sensitivity to the minimum number of passing probes.

Useful coverage is an evaluation measure against the retained benchmark oracle; it is not a formal proof of correctness.

## Results / Findings

At a budget of **32 additional test queries** and a minimum of **8 passing probes**:

| Policy | Useful coverage | False acceptance |
| --- | ---: | ---: |
| Candidate-focused | **93.13%** | 3.75% |
| Round-robin | 62.08% | **1.46%** |

The results show a clear **coverage–risk trade-off** in this benchmark setting: candidate-focused allocation obtains higher useful coverage but also accepts more candidates that fail held-out tests.

The experiment therefore supports analysis of verification-policy behavior rather than a claim that one policy is universally optimal.

## Reproducibility

The repository retains benchmark adapters and execution code, policy implementations, raw outcome matrices and policy selections, experiment manifests, analysis scripts and figures, tests, verification utilities, and protocol documentation.

The main workflow can be regenerated from the pinned benchmark and retained artifacts.

## Scope and limitations

This is a controlled mutation study using trusted benchmark mutants and reference-oracle information. It does not establish end-to-end repository-scale software-repair quality, security guarantees, or general performance on arbitrary real-world codebases.

## Academic context

The project is presented as part of research-oriented academic work. Its emphasis is on controlled experimentation, quantitative evaluation, and reproducible analysis rather than on a production software-repair system.
