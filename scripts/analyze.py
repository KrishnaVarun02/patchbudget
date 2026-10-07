"""Regenerate all reported numerical claims and figures from actual run records."""
import csv
from collections import defaultdict
import json
from pathlib import Path
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
LABELS = {'existing_only':'Existing tests only','round_robin':'Round robin',
          'candidate_focused':'Candidate focused','failure_count':'Failure count',
          'failure_history':'Smoothed failure rate'}
POLICIES = list(LABELS)

def main():
    result = ROOT/'results'/'full'
    rows = list(csv.DictReader((result/'selections.csv').open()))
    programs = sorted({r['program'] for r in rows})
    grouped = defaultdict(lambda:defaultdict(list))
    for row in rows:
        key = (row['gate'],row['policy'],int(row['budget']),int(row['minimum']))
        grouped[key][row['program']].append(row)
    summaries, lookup, vectors = [], {}, {}
    for key, groups in grouped.items():
        means = np.array([[np.mean([float(r[m]) for r in groups[p]])
                           for m in ['accepted','correct','false_accept','queries','gate_queries']]
                          for p in programs])
        summary = dict(zip(['gate','policy','budget','minimum'],key))
        for m,value in zip(['coverage','useful_coverage','false_accept','queries','gate_queries'],means.mean(axis=0)):
            summary[m] = float(value)
        summary['reliability'] = summary['useful_coverage']/summary['coverage'] if summary['coverage'] else None
        summaries.append(summary); lookup[key] = summary; vectors[key] = means
    summaries.sort(key=lambda r:(r['gate'],r['minimum'],r['budget'],r['policy']))
    (result/'summary.json').write_text(json.dumps(summaries,indent=2)+'\n')
    with (result/'summary.csv').open('w',newline='') as stream:
        writer = csv.DictWriter(stream,fieldnames=list(summaries[0]))
        writer.writeheader();writer.writerows(summaries)
    rng = np.random.default_rng(62041)
    indices = rng.integers(0,len(programs),(5000,len(programs)))
    key_a,key_b = ('one','candidate_focused',32,8),('one','round_robin',32,8)
    differences = vectors[key_a]-vectors[key_b]
    boot = differences[indices].mean(axis=1)
    comparisons = {}
    for i,metric in enumerate(['coverage','useful_coverage','false_accept','queries','gate_queries']):
        comparisons[metric] = {'difference':float(differences[:,i].mean()),
                               'ci95':np.quantile(boot[:,i],[.025,.975]).tolist()}
    (result/'primary_comparison.json').write_text(json.dumps(comparisons,indent=2)+'\n')
    (ROOT/'paper'/'generated').mkdir(exist_ok=True)
    with (ROOT/'paper'/'generated'/'table.tex').open('w') as f:
        f.write('\\begin{tabular}{llrrrr}\\toprule\nGate & Policy & Accept (\\%) & Useful (\\%) & False (\\%) & Calls\\\\\\midrule\n')
        for gate in ['one','three','all']:
            for policy in POLICIES:
                key = (gate,policy,0,0) if policy=='existing_only' else (gate,policy,32,8)
                s = lookup[key]
                f.write(f"{gate.title()} & {LABELS[policy]} & {100*s['coverage']:.1f} & {100*s['useful_coverage']:.1f} & {100*s['false_accept']:.1f} & {s['queries']:.1f}\\\\\n")
            if gate!='all':f.write('\\midrule\n')
        f.write('\\bottomrule\\end{tabular}\n')
    inventories=[]
    for p in programs:
        matrix=json.loads((result/'matrices'/f'{p}.json').read_text())
        inventories.append({'program':p,'candidates':len(matrix['candidates']),
                            'one_passers':sum(all(c['developer'][:1]) for c in matrix['candidates']),
                            'all_passers':sum(all(c['developer']) for c in matrix['candidates']),
                            'hidden_passing':sum(all(c['hidden']) for c in matrix['candidates']),
                            'execution_seconds':matrix['execution_seconds'],
                            'oracle_seconds':matrix['oracle_seconds'],
                            'developer_cases':len(matrix['official_cases']),
                            'errors':matrix['errors']})
    (result/'inventory.json').write_text(json.dumps(inventories,indent=2)+'\n')
    with (ROOT/'paper'/'generated'/'inventory.tex').open('w') as f:
        f.write('\\begin{tabular}{lrrrr}\\toprule\nProgram & Candidates & Gate 1 & Gate all & Holdout pass\\\\\\midrule\n')
        for item in inventories:
            f.write(f"{item['program'].replace('_',r'\_')} & {item['candidates']} & {item['one_passers']} & {item['all_passers']} & {item['hidden_passing']}\\\\\n")
        f.write('\\bottomrule\\end{tabular}\n')
    macros = {
        'ProgramCount':str(len(programs)), 'CandidateCount':str(sum(r['candidates'] for r in inventories)),
        'SelectionCount':f'{len(rows):,}',
        'MatrixSeconds':f"{sum(r['execution_seconds'] for r in inventories):.1f}",
        'OracleSeconds':f"{sum(r['oracle_seconds'] for r in inventories):.1f}",
    }
    for label,policy in [('Focused','candidate_focused'),('RoundRobin','round_robin'),('FailureCount','failure_count'),('Existing','existing_only')]:
        s=lookup[('one',policy,0,0) if policy=='existing_only' else ('one',policy,32,8)]
        for suffix,m in [('Useful','useful_coverage'),('False','false_accept'),('Accept','coverage')]:
            macros[label+suffix]=f'{100*s[m]:.2f}'
    for key,suffix in [('useful_coverage','Useful'),('false_accept','False'),('coverage','Accept')]:
        entry=comparisons[key]
        macros['Delta'+suffix]=f"{100*entry['difference']:.2f}"
        macros['Delta'+suffix+'Lo']=f"{100*entry['ci95'][0]:.2f}"
        macros['Delta'+suffix+'Hi']=f"{100*entry['ci95'][1]:.2f}"
    (ROOT/'paper'/'generated'/'numbers.tex').write_text('\n'.join('\\newcommand{\\'+k+'}{'+v+'}' for k,v in macros.items())+'\n')
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,
                         'font.family':'DejaVu Sans','savefig.dpi':180})
    fig,axes=plt.subplots(2,2,figsize=(9.4,6.3),sharex=True)
    colors=['#23395b','#008880','#d47a22','#9254a1']
    for col,gate in enumerate(['one','all']):
        for policy,color in zip(POLICIES[1:],colors):
            ss=[lookup[(gate,policy,b,8)] for b in [8,16,32,64,128]]
            for row,metric in enumerate(['useful_coverage','false_accept']):
                axes[row,col].plot([s['budget'] for s in ss],[100*s[metric] for s in ss],'-o',
                                   label=LABELS[policy],color=color,markersize=4)
        for row,metric in enumerate(['useful_coverage','false_accept']):
            baseline=lookup[(gate,'existing_only',0,0)][metric]*100
            axes[row,col].axhline(baseline,color='#888888',ls=':',label='Existing only')
            axes[row,col].set_xscale('log',base=2)
            axes[row,col].grid(alpha=.16)
        axes[0,col].set_title('One developer test' if gate=='one' else 'All developer tests')
        axes[1,col].set_xlabel('Additional candidate-test query cap')
        axes[1,col].set_xticks([8,16,32,64,128],[8,16,32,64,128])
    axes[0,0].set_ylabel('Useful coverage (%)')
    axes[1,0].set_ylabel('False acceptance (% of tasks)')
    handles,labels=axes[0,0].get_legend_handles_labels()
    fig.legend(handles,labels,loc='lower center',ncol=3,frameon=False,bbox_to_anchor=(.5,-.02))
    fig.suptitle('Allocation and developer-suite strength determine the observed trade-off\n16 selected QuixBugs programs; 30 paired rankings; minimum 8 passing probes',fontsize=11)
    fig.tight_layout(rect=[0,.09,1,.91])
    figures=ROOT/'figures';figures.mkdir(exist_ok=True)
    fig.savefig(figures/'budget_tradeoff.pdf',bbox_inches='tight')
    fig.savefig(figures/'budget_tradeoff.png',bbox_inches='tight')
    plt.close(fig)
    # Threshold sensitivity disentangles spreading calls from abstention.
    fig,ax=plt.subplots(figsize=(7,4))
    for policy,color in zip(POLICIES[1:],colors):
        ss=[lookup[('one',policy,32,k)] for k in [1,4,8,16]]
        ax.plot([s['minimum'] for s in ss],[s['coverage']*100 for s in ss],'-o',label=LABELS[policy],color=color)
    ax.set(xlabel='Minimum passing verification tests',ylabel='Acceptance coverage (%)',
           title='Abstention sensitivity at budget 32 (one-test gate)',xticks=[1,4,8,16],ylim=(-3,103))
    ax.legend(frameon=False,fontsize=9);ax.grid(alpha=.16);fig.tight_layout()
    fig.savefig(figures/'threshold_ablation.pdf');fig.savefig(figures/'threshold_ablation.png');plt.close(fig)
    print(json.dumps({'primary':comparisons,'inventory':{'programs':len(programs),'candidates':sum(r['candidates'] for r in inventories)},'primary_rows':[lookup[('one',p,0,0) if p=='existing_only' else ('one',p,32,8)] for p in POLICIES]},indent=2))

if __name__=='__main__':main()
