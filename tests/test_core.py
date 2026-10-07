import random
import unittest
from patchbudget.domains import oracle
from patchbudget.execution import evaluate, mutants
from patchbudget.policies import POLICIES, QueryBudget, choose, schedule

class CoreTests(unittest.TestCase):
    def test_budget_duplicate_and_no_hidden_access(self):
        q = QueryBudget(lambda c,t:True,1)
        self.assertTrue(q.check('x',0))
        with self.assertRaises(RuntimeError):q.check('y',0)
        q = QueryBudget(lambda c,t:True,2)
        q.check('x',0)
        with self.assertRaises(RuntimeError):q.check('x',0)
    def test_policies_use_exactly_charged_observations(self):
        for policy in POLICIES:
            log = []
            def query(c,t):
                log.append((c,t))
                return c == 'good' or t != 0
            state = schedule(['bad','good'],4,query,6,policy,11)
            self.assertEqual(state['spent'],len(log))
            self.assertLessEqual(len(log),6)
            self.assertEqual(len(set(log)),len(log))
            for c in ['bad','good']:
                if c not in state['alive']:
                    self.assertTrue(any(cc==c and tt==0 for cc,tt in log))
            if choose(state,4) is not None:self.assertEqual(choose(state,4),'good')
    def test_known_allocation_and_abstention(self):
        rr = schedule(['a','b','c','d'],10,lambda c,t:True,8,'round_robin',0)
        cf = schedule(['a','b','c','d'],10,lambda c,t:True,8,'candidate_focused',0)
        self.assertIsNone(choose(rr,4))
        self.assertIsNotNone(choose(cf,4))
        self.assertEqual(sum(rr['checks'].values()),8)
    def test_step_limit_and_exception(self):
        self.assertEqual(evaluate('def f():\n while True: pass','f',[],limit=20)['error'],'StepLimit')
        self.assertEqual(evaluate('def f():\n return 1/0','f',[])['error'],'ZeroDivisionError')
    def test_input_isolation(self):
        args = [[1,2]]
        evaluate('def f(a):\n a.append(3)\n return a','f',args)
        self.assertEqual(args,[[1,2]])
    def test_oracle_edge_cases(self):
        self.assertEqual(oracle('max_sublist_sum',[[-2,-1]]),0)
        self.assertEqual(oracle('knapsack',[0,[[1,3]]]),0)
        self.assertEqual(oracle('lcs_length',['abc','ac']),1)
        self.assertEqual(oracle('next_permutation',[[2,1]]),None)
        self.assertEqual(oracle('to_base',[31,16]),'1F')
    def test_mutations_deterministic_unique(self):
        source = 'def f(x):\n return x+1\n'
        a,b = mutants(source),mutants(source)
        self.assertEqual(a,b)
        self.assertEqual(len(a),len({x[0] for x in a}))

if __name__=='__main__':unittest.main()
