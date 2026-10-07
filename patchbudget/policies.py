"""Pure scheduling: the interface contains no hidden evaluation labels."""
import random

POLICIES = ['round_robin', 'candidate_focused', 'failure_count', 'failure_history']

class QueryBudget:
    def __init__(self, query, cap):
        self._query, self.cap, self.spent = query, cap, 0
        self.seen = set()
    def check(self, candidate, test):
        if self.spent >= self.cap: raise RuntimeError('budget exhausted')
        if (candidate, test) in self.seen: raise RuntimeError('duplicate query')
        self.seen.add((candidate, test))
        self.spent += 1
        return bool(self._query(candidate, test))

def schedule(candidates, n_tests, query, budget, policy, seed):
    """Return full observable state; caller applies a prespecified pass threshold."""
    if policy not in POLICIES: raise ValueError(policy)
    ranks = list(candidates)
    rng = random.Random(seed)
    rng.shuffle(ranks)
    test_order = list(range(n_tests))
    rng.shuffle(test_order)
    test_rank = {t: i for i, t in enumerate(test_order)}
    observed = {c: set() for c in ranks}
    alive = set(ranks)
    failures, counts = [0]*n_tests, [0]*n_tests
    api = QueryBudget(query, budget)
    while api.spent < budget:
        available = [c for c in ranks if c in alive and len(observed[c]) < n_tests]
        if not available: break
        if policy == 'round_robin':
            candidate = min(available, key=lambda c: len(observed[c]))
        else:
            candidate = available[0]
        choices = [t for t in test_order if t not in observed[candidate]]
        if policy == 'failure_count':
            test = max(choices, key=lambda t: (failures[t], -test_rank[t]))
        elif policy == 'failure_history':
            test = max(choices, key=lambda t: ((failures[t]+1)/(counts[t]+2), -test_rank[t]))
        else:
            test = choices[0]
        passed = api.check(candidate, test)
        observed[candidate].add(test)
        counts[test] += 1
        if not passed:
            alive.remove(candidate)
            failures[test] += 1
    return {'ranks': ranks, 'alive': alive, 'checks': {c: len(v) for c,v in observed.items()},
            'spent': api.spent, 'trace': sorted(api.seen)}

def choose(state, minimum):
    return next((c for c in state['ranks'] if c in state['alive']
                 and state['checks'][c] >= minimum), None)
