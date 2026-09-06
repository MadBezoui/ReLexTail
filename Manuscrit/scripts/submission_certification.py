"""Fixed-retention interval illustration; strict budget, terminal-leaf union."""
from pathlib import Path
import sys,json
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'Experimental/code'));sys.path.insert(0,str(Path(__file__).parent))
from lexpr.certified import _r_enclosure, _probe_enclosure, _isub, _idiv_pos, _split
from fractions import Fraction
import math
from submission_study import representation,choices
OUT=ROOT/'Manuscrit/submission/data'
RES={k:'0.02' for k in ['maximum','tail_025','tail_050','tail_100']}

def exact_profile(row):
    values=sorted(map(Fraction,row),reverse=True);K=len(values)
    tails=[]
    for alpha in [Fraction(1,4),Fraction(1,2),Fraction(1)]:
        h=alpha*K;k=h.numerator//h.denominator;theta=h-k
        tails.append((sum(values[:k])+(theta*values[k] if theta else 0))/h)
    scores=[values[0],*tails]
    return tuple(math.ceil(v/Fraction('0.02')) for v in scores)+tuple(tails)+tuple(values)

def enclosure(F,probes,box):
    rlo,rhi=_r_enclosure(F,*box);los=[];his=[]
    for kind,idx in probes:
        if kind=='single':
            i=idx[0];lo=F[:,i].min();hi=F[:,i].max()
            # Uniform singleton retention over the entire current box.
            if (hi-lo)/(box[3][i]-box[0][i])<=1e-9:return None
            nlo,nhi=_isub(F[:,i],F[:,i],lo,lo);dlo,dhi=_isub(hi,hi,lo,lo)
        else:
            vlo,vhi=_probe_enclosure((kind,idx),rlo,rhi)
            dlo,dhi=_isub(vlo.max(),vhi.max(),vlo.min(),vhi.min())
            if dlo<=1e-9:return None
            nlo,nhi=_isub(vlo,vhi,vlo.min(),vhi.min())
        L,U=_idiv_pos(nlo,nhi,dlo,dhi)
        los.append(np.clip(L,0,1));his.append(np.clip(U,0,1))
    return np.column_stack(los),np.column_stack(his)

def certify(F,p,budget):
    lo=F.min(0);hi=F.max(0);span=hi-lo
    box=(lo-p*span,lo+p*span,hi-p*span,hi+p*span)
    probes=[('single',(i,)) for i in range(F.shape[1])]+[('mean',tuple(range(F.shape[1]))),('max',tuple(range(F.shape[1])))]
    stack=[(box,set(range(len(F))),1.)];inner=set();outer=set();unresolved=0.;used=0
    while stack and used<budget:
      b,alive,vol=stack.pop();used+=1;enc=enclosure(F,probes,b)
      if enc is not None:
        L,U=enc
        lower=[exact_profile(row) for row in L];upper=[exact_profile(row) for row in U]
        alive={y for y in alive if not any(x!=y and upper[x]<lower[y] for x in alive)}
      if len(alive)==1:
        inner|=alive;outer|=alive
      else:
        b1,b2=_split(b);stack.extend([(b2,alive,vol/2),(b1,alive,vol/2)])
    for b,alive,vol in stack:outer|=alive;unresolved+=vol
    return dict(p=p,budget=budget,processed=used,inner=sorted(inner),outer=sorted(outer),unresolved=unresolved)
def main():
    F=np.load(OUT/'candidates.npz')['concave-3-0'][:6]
    rows=[]
    for p in [.005,.02,.05]:
      rng=np.random.default_rng(20260906);lo=F.min(0);hi=F.max(0);span=hi-lo;witness=set()
      for _ in range(256):
        z=rng.uniform(-1,1,(2,3));r,D,k=representation(F,lo+p*span*z[0],hi+p*span*z[1]);c,_=choices(r,D);witness.add(c['ReLexTail 0.02'][0])
      previous=set(range(len(F)))
      for budget in [64,256,1024]:
        row=certify(F,p,budget);assert witness<=set(row['outer']);assert set(row['outer'])<=previous;previous=set(row['outer']);row['sampled_winners']=sorted(witness);rows.append(row);print(row,flush=True)
    np.save(OUT/'certification_candidates.npy',F)
    (OUT/'certification.json').write_text(json.dumps(rows,indent=2))
if __name__=='__main__':main()
