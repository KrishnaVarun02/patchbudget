"""Execute benchmark code first; replay budgeted policies without hidden access."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import random
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from patchbudget.domains import PROGRAMS, draw, oracle
from patchbudget.execution import canonical, evaluate, mutants
from patchbudget.policies import POLICIES, choose, schedule

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def read_official(name):
    path = ROOT/'data'/'quixbugs'/'json_testcases'/f'{name}.json'
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]

def cases(name, n, seed, excluded, reference):
    rng = random.Random(seed)
    result = []
    attempts = 0
    while len(result) < n:
        attempts += 1
        if attempts > n*1000: raise RuntimeError(f'Insufficient unique domain: {name}')
        args = draw(name,rng)
        h = digest(args)
        if h in excluded: continue
        excluded.add(h)
        value = evaluate(reference,name,args)
        if not value['ok']: raise RuntimeError(f'Reference failed {name}: {args}: {value}')
        independently = oracle(name,args)
        if value['value'] != independently:
            raise RuntimeError(f'Oracle mismatch {name}: {args}')
        result.append([args, independently])
    return result

def build_matrix(name, output, verifier_count, hidden_count):
    start = time.perf_counter()
    base = ROOT/'data'/'quixbugs'
    ref = canonical((base/'correct_python_programs'/f'{name}.py').read_text())
    bug = canonical((base/'python_programs'/f'{name}.py').read_text())
    original_official = read_official(name)
    excluded_official = [case for case in original_official
                         if name=='knapsack' and case[0][0]*len(case[0][1]) > 1_000_000]
    official = [case for case in original_official if case not in excluded_official]
    # Official cases are also checked against the original reference before use.
    for args, expected in official:
        value = evaluate(ref,name,args,limit=100_000)
        if not value['ok'] or value['value'] != expected:
            raise RuntimeError(f'Official/reference disagreement: {name}: {args}: {value}')
    excluded = {digest(args) for args,expected in original_official}
    seed = int(hashlib.sha256(name.encode()).hexdigest()[:8],16)
    verifier = cases(name,verifier_count,seed+1107,excluded,ref)
    hidden = cases(name,hidden_count,seed+9031,excluded,ref)
    sources = [(hashlib.sha256(ref.encode()).hexdigest(), ref, 'reference'),
               (hashlib.sha256(bug.encode()).hexdigest(), bug, 'original_bug')]
    sources += mutants(ref)
    # Deduplicate on source alone; never on test outcomes.
    unique = {}
    for sha,source,origin in sources:
        unique.setdefault(sha,(source,origin))
    matrix = {'program':name,'verifier_cases':verifier,'hidden_cases':hidden,
              'official_cases':official,'candidates':[],'errors':{},'oracle_seconds':time.perf_counter()-start,
              'official_exclusions':[{'input_sha256':digest(case[0]),'case':case,
                    'reason':'knapsack capacity*item_count exceeds 1000000'} for case in excluded_official]}
    for sha,(source,origin) in unique.items():
        candidate = {'id':sha[:16],'sha256':sha,'origin':origin}
        for label, dataset in [('developer',official),('verifier',verifier),('hidden',hidden)]:
            passed = []
            for args,expected in dataset:
                value = evaluate(source,name,args,limit=100_000 if label=='developer' else 20000)
                passed.append(value['ok'] and value['value'] == expected)
                if not value['ok']:
                    key = f'{label}:{value["error"]}'
                    matrix['errors'][key] = matrix['errors'].get(key,0)+1
            candidate[label] = passed
        matrix['candidates'].append(candidate)
    matrix['execution_seconds'] = time.perf_counter()-start
    (output/'matrices').mkdir(exist_ok=True)
    (output/'matrices'/f'{name}.json').write_text(json.dumps(matrix,separators=(',',':'))+'\n')
    print(json.dumps({'program':name,'candidates':len(matrix['candidates']),
                      'seconds':round(matrix['execution_seconds'],2),'errors':matrix['errors']}),flush=True)
    return matrix

def evaluate_policies(matrix, seeds, budgets, minima):
    rows = []
    indexed = {c['id']:c for c in matrix['candidates']}
    n_tests = len(matrix['verifier_cases'])
    for gate in ['one','three','all']:
        n_dev = {'one':1,'three':3,'all':len(matrix['official_cases'])}[gate]
        candidates = [c['id'] for c in indexed.values() if all(c['developer'][:n_dev])]
        # Gate evaluation short-circuits at first failure; count the actual necessary tests.
        gate_queries = sum(next((i+1 for i,p in enumerate(c['developer'][:n_dev]) if not p),
                                len(c['developer'][:n_dev])) for c in indexed.values())
        for seed in seeds:
            ordering = list(candidates)
            random.Random(seed).shuffle(ordering)
            base = ordering[0] if ordering else None
            def row(policy,budget,minimum,chosen,queries,seconds):
                correct = chosen is not None and all(indexed[chosen]['hidden'])
                return {'program':matrix['program'],'gate':gate,'seed':seed,'policy':policy,
                        'budget':budget,'minimum':minimum,'selected':chosen or '',
                        'accepted':int(chosen is not None),'correct':int(correct),
                        'false_accept':int(chosen is not None and not correct),
                        'queries':queries,'gate_queries':gate_queries,'gate_passers':len(candidates),
                        'decision_seconds':seconds}
            rows.append(row('existing_only',0,0,base,0,0))
            # Closure grants verification answers only; hidden labels stay outside scheduler.
            def query(candidate,test): return indexed[candidate]['verifier'][test]
            for budget in budgets:
                for policy in POLICIES:
                    started = time.perf_counter()
                    state = schedule(candidates,n_tests,query,budget,policy,seed)
                    seconds = time.perf_counter()-started
                    for minimum in minima:
                        selected = choose(state,minimum)
                        rows.append(row(policy,budget,minimum,selected,state['spent'],seconds))
    return rows

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pilot',action='store_true')
    parser.add_argument('--reuse-matrices',action='store_true')
    parser.add_argument('--output',type=Path)
    args = parser.parse_args()
    output = args.output or ROOT/'results'/('pilot' if args.pilot else 'full')
    if (output/'manifest.json').exists() and not args.reuse_matrices:
        raise ValueError('Completed run exists. Choose a fresh --output directory.')
    output.mkdir(parents=True,exist_ok=True)
    programs = ['bitcount','gcd'] if args.pilot else PROGRAMS
    seeds = [999] if args.pilot else list(range(30))
    started = time.perf_counter()
    rows = []
    for name in programs:
        path = output/'matrices'/f'{name}.json'
        if args.reuse_matrices:
            matrix = json.loads(path.read_text())
            if (matrix['program'] != name or len(matrix['verifier_cases']) != (16 if args.pilot else 64)
                    or len(matrix['hidden_cases']) != (32 if args.pilot else 256)):
                raise ValueError('Matrix program/count does not match requested protocol')
        else:
            matrix = build_matrix(name,output,16 if args.pilot else 64,32 if args.pilot else 256)
        rows.extend(evaluate_policies(matrix,seeds,[8,16,32,64,128],[1,4,8,16]))
    with (output/'selections.csv').open('w',newline='') as stream:
        writer = csv.DictWriter(stream,fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    try: commit = subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,stderr=subprocess.DEVNULL,text=True).strip()
    except subprocess.CalledProcessError: commit = None
    manifest = {'created_utc':datetime.now(timezone.utc).isoformat(),'python':sys.version,
                'platform':platform.platform(),'machine':platform.machine(),
                'source_commit':commit,'upstream_commit':'4257f44b0ff1181dedaedee6a447e133219fcebf',
                'programs':programs,'ranking_seeds':seeds,'verifier_count':16 if args.pilot else 64,
                'hidden_count':32 if args.pilot else 256,'wall_seconds':time.perf_counter()-started,
                'external_api_spend':0,'reused_matrices':args.reuse_matrices,
                'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                                 for folder in ['patchbudget','scripts'] for p in sorted((ROOT/folder).glob('*.py'))}}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'rows':len(rows),'wall_seconds':manifest['wall_seconds']}),flush=True)

if __name__ == '__main__': main()
