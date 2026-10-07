"""Fetch the exact upstream snapshot, verify its Git object, and index inputs."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

COMMIT = '4257f44b0ff1181dedaedee6a447e133219fcebf'
ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path)
    args = parser.parse_args()
    destination = ROOT / 'data' / 'quixbugs'
    destination.parent.mkdir(exist_ok=True)
    if args.source:
        if not destination.exists():
            subprocess.run(['git','clone','--no-hardlinks',str(args.source.resolve()),str(destination)],check=True)
    elif not destination.exists():
        subprocess.run(['git','clone','https://github.com/jkoppel/QuixBugs.git',str(destination)],check=True)
    subprocess.run(['git','-C',str(destination),'checkout','--detach',COMMIT],check=True)
    actual = subprocess.check_output(['git','-C',str(destination),'rev-parse','HEAD'],text=True).strip()
    if actual != COMMIT: raise RuntimeError('Unexpected upstream revision')
    tracked = subprocess.check_output(['git','-C',str(destination),'status','--porcelain'],text=True)
    if tracked: raise RuntimeError('Dataset checkout has local modifications')
    manifest = {'url':'https://github.com/jkoppel/QuixBugs','commit':COMMIT,
                'license':'MIT; read upstream legal_notes.txt for historical provenance',
                'files':{str(p.relative_to(destination)):hashlib.sha256(p.read_bytes()).hexdigest()
                         for part in ['correct_python_programs','python_programs','json_testcases']
                         for p in sorted((destination/part).glob('*')) if p.is_file()}}
    (ROOT/'data'/'provenance.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(f'Prepared and verified QuixBugs {actual}')

if __name__ == '__main__': main()
