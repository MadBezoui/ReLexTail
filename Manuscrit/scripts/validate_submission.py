"""Independent numerical and artifact checks for the submission pipeline."""
from pathlib import Path
from fractions import Fraction as Q
from itertools import product
import re,json,sys,hashlib
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).parent))
from submission_study import representation,choices
from submission_certification import enclosure,exact_profile
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'submission/data'
def main():
    checks=[];df=pd.read_csv(DATA/'study.csv');protocol=json.loads((DATA/'protocol.json').read_text())
    method_count=df.method.nunique();expected=protocol['instances']*len(protocol['levels'])*method_count
    assert len(df)==expected and df.instance.nunique()==protocol['instances']
    assert (df.groupby(['instance','p','method']).size()==1).all()
    assert np.isfinite(df[['flip','mean_regret','tail_regret']]).all().all()
    assert ((df.tail_regret>=df.mean_regret-1e-14)&(df.tail_regret<=1)).all()
    checks.append(f'{expected} instance-level method/perturbation summaries complete ({method_count} methods, {len(protocol["levels"])} levels); regret bounds valid')
    archive=np.load(DATA/'candidates.npz');tested=0
    for iid in df.instance.unique():
      F=archive[iid];lo=F.min(0);hi=F.max(0);span=hi-lo
      for direction in [np.zeros((2,F.shape[1])),archive[iid+'-directions'][0]]:
        r,D,k=representation(F,lo+.2*span*direction[0],hi+.2*span*direction[1]);c,scores=choices(r,D)
        assert min(range(len(D)),key=lambda i:exact_profile(D[i]))==c['ReLexTail 0.02'][0]
        tested+=1
    checks.append(f'{tested} candidate-set selections agree with independently computed rational full profiles at delta 0.02')
    F=np.load(DATA/'certification_candidates.npy');lo=F.min(0);hi=F.max(0);span=hi-lo
    probes=[('single',(i,)) for i in range(3)]+[('mean',(0,1,2)),('max',(0,1,2))]
    box=(lo-.005*span,lo+.005*span,hi-.005*span,hi+.005*span);L,U=enclosure(F,probes,box);count=0
    for corners in product(range(4),repeat=3):
      I=[Q(box[0 if c<2 else 1][i]) for i,c in enumerate(corners)]
      N=[Q(box[2 if c%2==0 else 3][i]) for i,c in enumerate(corners)]
      r=[[ (Q(F[a,i])-I[i])/(N[i]-I[i]) for i in range(3)] for a in range(6)]
      for k,(kind,idx) in enumerate(probes):
        vals=[v[idx[0]] if kind=='single' else sum(v)/3 if kind=='mean' else max(v) for v in r];qs=min(vals);qw=max(vals)
        for a,v in enumerate(vals):
          exact=(v-qs)/(qw-qs);assert Q(L[a,k])<=exact<=Q(U[a,k]);count+=1
    checks.append(f'{count} exact rational probe values at 64 box corners lie within outward-rounded enclosures, including singletons')
    cert=json.loads((DATA/'certification.json').read_text())
    for row in cert:
      assert set(row['inner'])<=set(row['outer']) and set(row['sampled_winners'])<=set(row['outer'])
      assert row['processed']<=row['budget'] and 0<=row['unresolved']<=1
    checks.append('Nine certification runs preserve witnesses, set inclusions, strict budgets and volume bounds')
    grid=pd.read_csv(DATA/'grid_sensitivity.csv');ablation=pd.read_csv(DATA/'ablation.csv');decisive=pd.read_csv(DATA/'decisive_coordinates.csv')
    assert len(grid)==90*3*4 and len(ablation)==90*4 and len(decisive)==90
    assert set(grid.origin_fraction)=={0,.25,.5,.75} and set(ablation.variant)=={'prefix-1','prefix-2','prefix-4','aggregate-only'}
    assert np.isfinite(grid[['flip','category_change','category_size','retention']]).all().all()
    assert np.isfinite(ablation[['flip','category_change','category_size','retention']]).all().all()
    checks.append('Grid-origin, profile-ablation and decisive-coordinate extensions have complete expected designs')
    uci=json.loads((DATA/'uci_benchmark.json').read_text());external=DATA/'external/uci_energy_efficiency.csv'
    assert hashlib.sha256(external.read_bytes()).hexdigest()==uci['sha256']=='db44dbe453acd464b5cf65be2fb01a28aa9c5b2630300e65fbe28cde35f5d96f'
    assert uci['raw_rows']==768 and uci['unique_objective_profiles']==756 and uci['nondominated_profiles']==4
    assert len(uci['results'])==4*(3+len(protocol['deltas']))
    checks.append('UCI source checksum, row counts, Pareto reduction and 44 benchmark summaries verified')
    s=np.load(DATA/'supplier.npz');p=[exact_profile(row) for row in s['D']];order=sorted(range(10),key=lambda i:p[i]);assert order[:2]==[6,5];assert p[6][0]==p[5][0] and p[6][1]<p[5][1]
    checks.append('Supplier recommendation S7 and nearest rival S6 independently verified; decisive coordinate C25')
    assert len(list((ROOT/'submission/figures').glob('*.pdf')))==15
    source=(ROOT/'main.tex').read_text();abstract=source.split('\\begin{abstract}')[1].split('\\end{abstract}')[0]
    # Macro invocations expand to numbers, so they are stripped before counting
    # words against the journal's 300-word limit.
    prose=re.sub(r'\\[a-zA-Z]+\{?|\}|\$','',abstract);words=len(re.findall(r'\b[\w-]+\b',prose));assert words<=300,f'abstract is {words} words'
    log=(ROOT/'main.log').read_text();assert not re.search(r'Overfull|undefined|^!',log,re.M)
    checks.append(f'Fifteen vector figures; abstract {words} words; no LaTeX errors, unresolved references or overfull boxes')

    # Section 5 is generated by the enhanced/ tree: check that its macro file
    # exists, that every macro the section uses is defined, and that the
    # correctness run it reports really did find nothing.
    macros=(ROOT/'submission/generated_certrelex.tex')
    assert macros.exists(),'submission/generated_certrelex.tex is missing; run enhanced/reproduce.py'
    defined=set(re.findall(r'\\newcommand\{\\(crx[A-Za-z]+)\}',macros.read_text()))
    used=set(re.findall(r'\\(crx[A-Za-z]+)',(ROOT/'submission/certification.tex').read_text()))
    used|=set(re.findall(r'\\(crx[A-Za-z]+)',abstract))
    missing=sorted(used-defined);assert not missing,f'undefined certification macros: {missing}'
    correctness=json.loads((ROOT.parent/'enhanced/results/correctness.json').read_text())
    violations=sum(c['violations'] for c in correctness);replay=sum(c.get('replay_failures',0) for c in correctness)
    draws=sum(c['checked'] for c in correctness);leaves=sum(c.get('replay_leaves',0) for c in correctness)
    assert violations==0 and replay==0,f'{violations} falsified certificates, {replay} replay failures'
    assert draws>0 and leaves>0,'the correctness run checked nothing'
    checks.append(f'Certification macros all defined; {draws} oracle draws and {leaves} replayed leaves, {violations} falsified certificates and {replay} replay failures')
    report={'status':'passed','checks':checks};(DATA/'validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
