# Research summary

The question is whether allocation and test ordering change screening outcomes
under a shared query cap. We executed 241 candidate implementations across 16
selected QuixBugs algorithms and replayed four budgeted scheduling policies with
disjoint verification and evaluation pools, three developer gates, five budgets,
four acceptance thresholds, and 30 paired rankings.

At the primary setting, candidate-focused allocation gives 93.13% useful coverage
and 3.75% false acceptance, compared with 62.08% and 1.46% for round robin.
The larger acceptance coverage explains much of the trade-off: a minimum-evidence
rule penalizes policies that spread a small budget over many surviving candidates.
Failure-count ordering adds only 0.21 points of useful coverage over focused
allocation here. We retain that modest result instead of claiming a new method.

The artifact's value is an inspectable protocol and complete executed evidence.
The fixed reference oracle, planted reference candidate, mutation fault model,
selected algorithm corpus, and unit query costs limit external validity. Known
adaptive scheduling literature is credited. The paper is a finished technical
report draft of this scoped diagnostic, not a submission-ready full study.

The next research milestone is a fixed real candidate-patch dataset evaluated
with tests independent of the candidate generator, faithful relevant baselines,
and end-to-end cost measurement. A venue should be selected after that evidence
and an external review establish a distinct contribution; no venue deadline,
submission, affiliation, or acceptance is claimed here.
