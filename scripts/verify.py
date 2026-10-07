"""Audit retained evidence, replay all selections, optionally compare a fresh run."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'scripts'))
from run import digest, evaluate_policies
from patchbudget.domains import PROGRAMS
from patchbudget.execution import canonical, evaluate, mutants

def stable_matrix(m):
    return {k:v for k,v in m.items() if k not in ['execution_seconds','oracle_seconds']}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--results',type=Path,default=ROOT/'results'/'full')
    parser.add_argument('--reproduction',type=Path)
    parser.add_argument('--execute-sample',action='store_true')
    args=parser.parse_args()
    results=args.results.resolve()
    original=list(csv.DictReader((results/'selections.csv').open()))
    reconstructed=[]
    replayed=0
    for name in PROGRAMS:
        matrix=json.loads((results/'matrices'/f'{name}.json').read_text())
        assert matrix['program']==name
        assert len(matrix['verifier_cases'])==64 and len(matrix['hidden_cases'])==256
        developer={digest(a) for a,y in matrix['official_cases']}
        verifier={digest(a) for a,y in matrix['verifier_cases']}
        hidden={digest(a) for a,y in matrix['hidden_cases']}
        assert len(verifier)==64 and len(hidden)==256
        assert not developer & verifier and not developer & hidden and not verifier & hidden
        candidates=matrix['candidates']
        assert len({c['id'] for c in candidates})==len(candidates)
        references=[c for c in candidates if c['origin']=='reference']
        assert len(references)==1
        for split in ['developer','verifier','hidden']:
            assert all(references[0][split]), f'Reference failure: {name}/{split}'
            assert all(len(c[split])==len(matrix[{'developer':'official_cases','verifier':'verifier_cases','hidden':'hidden_cases'}[split]]) for c in candidates)
        reconstructed.extend(evaluate_policies(matrix,list(range(30)),[8,16,32,64,128],[1,4,8,16]))
        if args.reproduction:
            fresh=json.loads((args.reproduction/'matrices'/f'{name}.json').read_text())
            assert stable_matrix(matrix)==stable_matrix(fresh), f'Matrix mismatch {name}'
        if args.execute_sample:
            base=ROOT/'data'/'quixbugs'
            ref=canonical((base/'correct_python_programs'/f'{name}.py').read_text())
            bug=canonical((base/'python_programs'/f'{name}.py').read_text())
            sources={hashlib.sha256(s.encode()).hexdigest():s for s in [ref,bug]}
            sources.update({sha:source for sha,source,description in mutants(ref)})
            assert set(sources)=={c['sha256'] for c in candidates}
            for candidate in candidates:
                for split,key in [('developer','official_cases'),('verifier','verifier_cases'),('hidden','hidden_cases')]:
                    for index in sorted({0,len(matrix[key])-1}):
                        a,y=matrix[key][index]
                        value=evaluate(sources[candidate['sha256']],name,a,
                                       limit=100000 if split=='developer' else 20000)
                        outcome=value['ok'] and value['value']==y
                        assert outcome==candidate[split][index],(name,candidate['id'],split,index)
                        replayed+=1
    assert len(original)==len(reconstructed)
    for retained,replayed_row in zip(original,reconstructed):
        for field in retained:
            if field=='decision_seconds':continue
            assert retained[field]==str(replayed_row[field]),(field,retained,replayed_row)
        assert int(retained['queries'])<=int(retained['budget'])
        assert int(retained['accepted'])==int(retained['correct'])+int(retained['false_accept'])
    report={'programs':len(PROGRAMS),'selection_rows_verified':len(original),
            'candidate_test_outcomes_reexecuted':replayed,
            'disjoint_splits':True,'reference_controls_pass':True,
            'all_policy_selections_replayed':True,'reproduction_matrices_match':bool(args.reproduction)}
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
