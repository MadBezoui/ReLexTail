"""Frozen submission experiment: synthetic fronts, canonical retained probes.
Run from any directory. No network, fitted surrogate, or external solver.
"""
from pathlib import Path
import sys, json, hashlib
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'Experimental/code'))
from lexpr.problems import sample_front
from lexpr.orders.relex_tail import compute_profile
from lexpr.supplier import load_supplier_case
from submission_analysis import lexicographic_argmin, relex_choice
OUT=ROOT/'Manuscrit/submission/data'; OUT.mkdir(parents=True,exist_ok=True)
DELTAS=[.001,.005,.01,.02,.03,.05,.075,.1]
LEVELS=[.01,.025,.05,.1,.15,.2,.3,.4]
DRAWS=500
WEIGHTS=10000

def representation(F,ideal,nadir):
    r=(F-ideal)/(nadir-ideal)
    q=np.column_stack((r,r.mean(1),r.max(1)))
    ranges=np.ptp(q,axis=0); keep=ranges>1e-9
    return r,(q[:,keep]-q[:,keep].min(0))/ranges[keep],keep

def choices(r,D,origin_fraction=0.):
    s=np.sort(D,axis=1)[:,::-1]
    K=s.shape[1]
    tails=[]
    for a in [.25,.5,1.]:
        h=a*K; k=int(h); theta=h-k
        tails.append((s[:,:k].sum(1)+(theta*s[:,k] if theta else 0))/h)
    scores=np.column_stack((s[:,0],*tails))
    out={}
    out['LexPR']=(lexicographic_argmin(s),None)
    raw=np.sort(r,axis=1)[:,::-1]
    out['Leximax']=(lexicographic_argmin(raw),None)
    out['Mean-D']=(int(np.argmin(D.mean(1))),None)
    out['Tail25-D']=(int(np.argmin(tails[0])),None)
    out['Tail50-D']=(int(np.argmin(tails[1])),None)
    out['Weighted-sum']=(int(np.argmin(r.mean(1))),None)
    out['Chebyshev']=(int(np.argmin(r.max(1))),None)
    for delta in DELTAS:
        win,group=relex_choice(scores,s,delta,origin_fraction=origin_fraction)
        out[f'ReLexTail {delta:g}']=(win,group)
    return out,scores

def losses(F,rng):
    r=(F-F.min(0))/np.ptp(F,axis=0)
    W=rng.dirichlet(np.ones(F.shape[1]),size=WEIGHTS)
    L=r@W.T; span=np.ptp(L,axis=0)
    Z=np.divide(L-L.min(0),span,out=np.zeros_like(L),where=span>0)
    return Z.mean(1),np.partition(Z,7500,axis=1)[:,7500:].mean(1)

def main():
    rows=[]; matrices={}; seed=20260905
    for fam in ['linear','concave','convex']:
      for m in [3,6,10]:
       for rep in range(10):
        iid=f'{fam}-{m}-{rep}'; rng=np.random.default_rng(np.random.SeedSequence([seed,['linear','concave','convex'].index(fam),m,rep]))
        F=sample_front(fam,80,m,rng); matrices[iid]=F
        lo=F.min(0); hi=F.max(0); span=hi-lo
        r,D,keep=representation(F,lo,hi); nominal,scores=choices(r,D)
        # Independent agreement with exact Fraction category implementation.
        for d in DELTAS:
            profiles=[compute_profile(row,{k:str(d) for k in ['maximum','tail_025','tail_050','tail_100']}) for row in D]
            assert min(range(len(D)),key=lambda i:profiles[i])==nominal[f'ReLexTail {d:g}'][0]
        ml,tl=losses(F,rng)
        directions=rng.uniform(-1,1,size=(DRAWS,2,m)); matrices[iid+'-directions']=directions
        for p in LEVELS:
          obs={k:[] for k in nominal}
          for direction in directions:
            il=lo+p*span*direction[0]; nh=hi+p*span*direction[1]
            r1,D1,k1=representation(F,il,nh)
            assert np.array_equal(keep,k1),'Retained probe family changed'
            changed,_=choices(r1,D1)
            for name,(w,group) in changed.items():
              w0,g0=nominal[name]
              obs[name].append((w!=w0,ml[w],tl[w],group!=g0 if group is not None else np.nan,len(group) if group is not None else 1,len(set(group)&set(g0))/len(set(group)|set(g0)) if group is not None else np.nan,w0 in group if group is not None else np.nan))
          for name,v in obs.items():
            a=np.array(v,float); w0,g0=nominal[name]
            rows.append(dict(instance=iid,family=fam,m=m,rep=rep,p=p,method=name,flip=a[:,0].mean(),mean_regret=a[:,1].mean(),tail_regret=a[:,2].mean(),category_change=a[:,3].mean(),category_size=a[:,4].mean(),jaccard=a[:,5].mean(),retention=a[:,6].mean(),nominal_mean=ml[w0],nominal_tail=tl[w0],nominal_winner=w0,nominal_category_size=len(g0) if g0 else 1))
        print(iid,flush=True)
    pd.DataFrame(rows).to_csv(OUT/'study.csv',index=False)
    np.savez_compressed(OUT/'candidates.npz',**matrices)
    F,names,labels=load_supplier_case(); lo=F.min(0);hi=F.max(0)
    r,D,keep=representation(F,lo,hi); pick,scores=choices(r,D)
    np.savez(OUT/'supplier.npz',F=F,D=D,scores=scores,names=names,labels=labels)
    rng=np.random.default_rng(seed); supplier=[]
    for p in [0,.02,.05,.1,.2,.3,.5]:
      seen=set(); flips=0; catflips=0; nom,cat=pick['ReLexTail 0.02']
      for _ in range(300):
        directions=rng.uniform(-1,1,(2,7)); r1,D1,k=representation(F,lo+p*(hi-lo)*directions[0],hi+p*(hi-lo)*directions[1]); c,_=choices(r1,D1); w,g=c['ReLexTail 0.02']; seen.add(w); flips+=w!=nom;catflips+=g!=cat
      supplier.append(dict(p=p,flip=flips/300,category_change=catflips/300,sampled_possible_size=len(seen),winners=[names[i] for i in sorted(seen)]))
    (OUT/'supplier_sensitivity.json').write_text(json.dumps(supplier,indent=2))
    (OUT/'protocol.json').write_text(json.dumps(dict(seed=seed,families=['linear','concave','convex'],criteria=[3,6,10],replicates_per_cell=10,candidates=80,instances=90,weights=WEIGHTS,draws_per_level=DRAWS,levels=LEVELS,deltas=DELTAS,probe_family='singletons + mean + maximum; drop active ranges <=1e-9',perturbation='ideal and nadir independently uniform within +/- p times nominal criterion range; no clipping',evaluation='nominal criterion scale; upper 2500 of 10000 linear regrets; then average over perturbations and instances',category_boundary='closed upper endpoints; quotients within eight machine epsilons of an integer are snapped to that integer',script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),indent=2))
if __name__=='__main__':main()
