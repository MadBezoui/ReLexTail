"""All manuscript artwork and numerical tables, built from saved observations."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from submission_analysis import holm_adjust, paired_effect_summary
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'submission/data';OUT=ROOT/'submission/figures'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.labelsize':10,'axes.titlesize':11,'xtick.labelsize':9,'ytick.labelsize':9,'legend.fontsize':9,'pdf.fonttype':42,'ps.fonttype':42,'axes.spines.top':False,'axes.spines.right':False,'axes.axisbelow':True,'savefig.dpi':300})
BLUE='#0072B2';ORANGE='#D55E00';GREEN='#009E73';GREY='#59636D';PURPLE='#AA4499'
ORIGIN_FRACTIONS=[0,.25,.5,.75]
def save(fig,name):
    fig.savefig(OUT/(name+'.pdf'),bbox_inches='tight',pad_inches=.08)
    fig.savefig(OUT/(name+'.png'),bbox_inches='tight',pad_inches=.08,dpi=180)
    plt.close(fig)
def box(ax,x,y,w,h,title,body,color=BLUE):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.012,rounding_size=0.025',ec=color,fc=color+'0D',lw=1.2))
    ax.text(x+w/2,y+h*.70,title,ha='center',va='center',weight='bold',color=color)
    ax.text(x+w/2,y+h*.31,body,ha='center',va='center',fontsize=9,linespacing=1.5)
def arrow(ax,a,b):ax.annotate('',xy=b,xytext=a,arrowprops=dict(arrowstyle='->',lw=1.4,color=GREY))
def ci(values,seed=42):
    a=np.array(values);rng=np.random.default_rng(seed);boots=a[rng.integers(0,len(a),(4000,len(a)))].mean(1);return np.quantile(boots,[.025,.975])
def main():
    d=pd.read_csv(DATA/'study.csv');sub=d[d.p==.05];g=sub.groupby('method').mean(numeric_only=True)
    fig,ax=plt.subplots(figsize=(8.5,3.0));ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off')
    box(ax,.02,.56,.27,.37,'1  Declare the decision','Candidates and probes\nBounds and resolutions')
    box(ax,.365,.56,.27,.37,'2  Build the profile','Probe disappointments\nMaximum and tail means')
    box(ax,.71,.56,.27,.37,'3  Compare categories','Maximum → tails → mean\nThen exact refinements')
    arrow(ax,(.29,.75),(.35,.75));arrow(ax,(.635,.75),(.695,.75))
    box(ax,.12,.04,.33,.33,'Fixed bounds','Category-optimal set\nFully refined recommendation',GREEN)
    box(ax,.55,.04,.33,.33,'Uncertain bounds','Sampled winners / interval bracket\nUnresolved volume',ORANGE)
    arrow(ax,(.83,.54),(.72,.39));arrow(ax,(.78,.54),(.29,.39));save(fig,'pipeline')
    fig,axes=plt.subplots(1,2,figsize=(8.5,2.8),layout='constrained')
    ax=axes[0];z=np.linspace(0,.151,500);ax.step(z,np.ceil(z/.05),where='post',color=BLUE)
    for j in [1,2,3]:
        ax.plot(j*.05,j,'o',color=BLUE);ax.plot(j*.05,j+1,'o',mfc='white',mec=BLUE)
    ax.set(xlabel='Risk score z',ylabel='Category ceil(z / 0.05)',xlim=(0,.155),ylim=(-.2,4.2),title='A  Fixed cells define an equivalence relation')
    ax=axes[1];a=[.041,.049,.051];cats=np.ceil(np.array(a)/.05)
    ax.scatter(a,[1]*3,s=60,c=[BLUE,BLUE,ORANGE]);ax.axvline(.05,color=GREY,ls='--');
    for i,(v,c) in enumerate(zip(a,cats)):ax.annotate(f'{v:.3f}\ncategory {int(c)}',(v,1),xytext=(0,15 if i!=1 else -35),textcoords='offset points',ha='center')
    ax.set(xlim=(.036,.058),ylim=(.6,1.5),yticks=[],xlabel='Risk score z',title='B  A small difference may cross a boundary');save(fig,'resolution_cells')
    fig,ax=plt.subplots(figsize=(8.5,2.6));ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off')
    box(ax,.025,.19,.40,.66,'Selection: tail across probes','One candidate → K declared concerns\nCVaR over the worst 25% of D\nEnters the ReLexTail preference profile',BLUE)
    box(ax,.575,.19,.40,.66,'Evaluation: tail across preferences','10,000 held-out preference vectors\nMean of the 2,500 largest regrets\nEvaluation only; never used to select',ORANGE)
    arrow(ax,(.44,.52),(.56,.52));save(fig,'two_risks')
    s=np.load(DATA/'supplier.npz');D=s['D'];scores=s['scores'];labels=list(s['labels'])+['Mean','Maximum'];cats=np.ceil(scores/.02).astype(int)
    fig,ax=plt.subplots(figsize=(7.8,2.6),layout='constrained');ind=np.argsort(D[6])[::-1];y=np.arange(9)
    ax.barh(y-.17,D[6,ind],height=.32,color=BLUE,label='S7 (recommended)');ax.barh(y+.17,D[5,ind],height=.32,color=ORANGE,label='S6 (nearest rival)')
    ax.set(yticks=y,yticklabels=np.array(labels)[ind],xlabel='Active-range disappointment',xlim=(0,1));ax.invert_yaxis();ax.legend(loc='lower right');save(fig,'fig_supplier_certificate')
    fig,axes=plt.subplots(1,2,figsize=(8.5,3),layout='constrained')
    a=np.linspace(.01,1,250)
    for i,col,name in [(6,BLUE,'S7'),(5,ORANGE,'S6')]:
        sort=np.sort(D[i])[::-1];v=[]
        for alpha in a:
            h=alpha*len(sort);k=int(h);theta=h-k;v.append((sum(sort[:k])+(theta*sort[k] if theta else 0))/h)
        axes[0].plot(a,v,color=col,label=name)
    axes[0].set(xlabel='Tail fraction α',ylabel='Upper-tail mean',title='A  Tail spectrum',ylim=(0,1));axes[0].legend()
    mat=cats[[6,5]];axes[1].imshow(mat,cmap='Blues',vmin=0,vmax=50,aspect='auto')
    for i in range(2):
        for j in range(4):axes[1].text(j,i,str(mat[i,j]),ha='center',va='center',color='white' if mat[i,j]>28 else 'black',weight='bold')
    axes[1].set(xticks=range(4),xticklabels=['Maximum','25% tail','50% tail','Mean'],yticks=[0,1],yticklabels=['S7','S6'],title='B  Categories at δ = 0.02')
    axes[1].add_patch(plt.Rectangle((.5,-.5),1,2,fill=False,ec=ORANGE,lw=3));save(fig,'relex_decision_profile')
    fig,axes=plt.subplots(1,2,figsize=(8.5,3.1),layout='constrained')
    for name,col,mk in [('LexPR',GREY,'s'),('Leximax',GREEN,'^'),('Mean-D',PURPLE,'D')]:
        row=g.loc[name];axes[0].scatter(row.tail_regret,row.flip*100,c=col,marker=mk,s=65,label=name)
    tested=[.001,.005,.01,.02,.03,.05,.075,.1]
    rg=g.loc[[f'ReLexTail {v:g}' for v in tested]]
    axes[0].plot(rg.tail_regret,rg.flip*100,'o-',color=BLUE,label='ReLexTail')
    offsets=[(18,-7),(8,9),(8,-13),(-25,8),(-25,-13),(-20,8),(-2,-15),(-3,10)]
    for j,(idx,row) in enumerate(rg.iterrows()):axes[0].annotate(idx.split()[1],(row.tail_regret,row.flip*100),xytext=offsets[j],textcoords='offset points',fontsize=8)
    axes[0].set(xlabel='Hidden-preference upper-tail regret',ylabel='Point changes (%)',title='A  Paired population at p = 0.05');axes[0].legend(loc='upper center',fontsize=9)
    for metric,label,style in [('flip','Point','o-'),('category_change','Category set','s--')]:axes[1].plot(tested,rg[metric]*100,style,color=BLUE if metric=='flip' else ORANGE,label=label)
    axes[1].set(xscale='log',xlabel='Resolution δ',ylabel='Changes (%)',title='B  Point and set stability differ');axes[1].legend();save(fig,'quality_stability_frontier')
    fig,ax=plt.subplots(figsize=(7.8,2.8),layout='constrained')
    nominal=sub.pivot(index='instance',columns='method',values='nominal_winner');families=sub.drop_duplicates('instance').set_index('instance').family
    names=['linear','concave','convex'];rates=[]
    for fam in names:
        x=nominal.loc[families[families==fam].index];rates.append((x['LexPR']!=x['ReLexTail 0.02']).mean()*100)
    ax.barh(names,rates,color=BLUE,height=.55)
    for j,v in enumerate(rates):ax.text(v+.6,j,f'{v:.1f}%',va='center')
    ax.set(xlim=(0,max(rates)+10),xlabel='Nominal recommendations differing from LexPR (%)');save(fig,'fig_divergence')
    fig,axes=plt.subplots(1,2,figsize=(8.5,2.8),layout='constrained')
    for ax,metric,title in zip(axes,['flip','tail_regret'],['A  Point-change difference (percentage points)','B  Upper-tail regret difference']):
      for j,fam in enumerate(names):
        p=sub[sub.family==fam].pivot(index='instance',columns='method',values=metric);v=(p['ReLexTail 0.02']-p['LexPR']).values*(100 if metric=='flip' else 1);lo,hi=ci(v);mu=v.mean();ax.errorbar(mu,j,xerr=[[mu-lo],[hi-mu]],fmt='o',color=BLUE,capsize=4)
      ax.axvline(0,color=GREY,ls='--',lw=1);ax.set(yticks=range(3),yticklabels=names,title=title,xlabel='ReLexTail δ = 0.02 minus LexPR');save_name='family_effects'
    save(fig,save_name)
    x=pd.DataFrame(json.loads((DATA/'supplier_sensitivity.json').read_text()))
    fig,axes=plt.subplots(1,2,figsize=(8.5,2.8),layout='constrained')
    axes[0].plot(x.p*100,x.flip*100,'o-',color=BLUE);axes[0].set(xlabel='Bound perturbation p (%)',ylabel='Point changes (%)',ylim=(0,100),title='A  Sampled point sensitivity')
    axes[1].step(x.p*100,x.sampled_possible_size,where='mid',color=BLUE);axes[1].scatter(x.p*100,x.sampled_possible_size,color=BLUE);axes[1].set(xlabel='Bound perturbation p (%)',ylabel='Distinct sampled winners',yticks=[1,2,3],ylim=(.5,3.2),title='B  Inner approximation from 300 draws');save(fig,'fig_supplier_interval')
    fig,axes=plt.subplots(1,2,figsize=(8.5,2.7),layout='constrained');m=np.arange(3,16)
    axes[0].plot(m,6*m+5,'s--',color=GREY,label='Exact LexPR: LP calls');axes[0].plot(m,6*m+8,'o-',color=BLUE,label='ReLexTail: LP calls');axes[0].set(xlabel='Number of criteria m',ylabel='LP stages including anchors',title='A  Continuous-polyhedral formulation');axes[0].legend()
    axes[1].bar(['LexPR','ReLexTail'],[0,4],color=[GREY,BLUE],width=.5);axes[1].set(ylabel='Additional integer category stages',ylim=(0,5),yticks=range(5),title='B  Integer stages are separate costs');save(fig,'fig_continuous_cost')
    cert=pd.DataFrame(json.loads((DATA/'certification.json').read_text()))
    fig,axes=plt.subplots(1,2,figsize=(8.5,2.8),layout='constrained')
    for (p,v),col in zip(cert.groupby('p'),[GREEN,BLUE,ORANGE]):
        axes[0].plot(v.processed,v.unresolved*100,'o-',color=col,label=f'p = {p:g}')
        axes[1].plot(v.processed,v.outer.map(len),'o-',color=col)
    axes[0].set(xlabel='Processed boxes (budget)',ylabel='Unresolved volume (%)',xscale='log',ylim=(-3,103),title='A  Interval slack');axes[0].legend()
    axes[1].set(xlabel='Processed boxes (budget)',ylabel='Outer possible-winner set size',xscale='log',ylim=(0,7),yticks=range(1,7),title='B  Six-candidate illustration');save(fig,'fig_certified_decay')
    grid=pd.read_csv(DATA/'grid_sensitivity.csv');ablation=pd.read_csv(DATA/'ablation.csv');decisive=pd.read_csv(DATA/'decisive_coordinates.csv')
    uci=json.loads((DATA/'uci_benchmark.json').read_text());uci_rows=pd.DataFrame(uci['results'])
    fig,axes=plt.subplots(2,2,figsize=(8.5,6.0),layout='constrained')
    grid_mean=grid.groupby(['delta','origin_fraction']).mean(numeric_only=True).reset_index()
    for delta,col,mk in zip([.01,.02,.05],[GREEN,BLUE,ORANGE],['^','o','s']):
        v=grid_mean[grid_mean.delta==delta]
        axes[0,0].plot(v.origin_fraction,v.flip*100,marker=mk,color=col,label=f'δ = {delta:g}')
    axes[0,0].set(xlabel='Grid-origin shift / δ',ylabel='Point changes (%)',title='A  Grid-origin sensitivity at p = 0.05',xticks=ORIGIN_FRACTIONS)
    axes[0,0].legend(ncol=3,fontsize=8)
    ab=ablation.groupby('variant').mean(numeric_only=True).loc[['prefix-1','prefix-2','prefix-4','aggregate-only']]
    xloc=np.arange(len(ab));width=.36
    axes[0,1].bar(xloc-width/2,ab.flip*100,width,color=BLUE,label='Point')
    axes[0,1].bar(xloc+width/2,ab.category_change*100,width,color=ORANGE,label='Category set')
    axes[0,1].set(xticks=xloc,xticklabels=['$C_M$','+$C_{25}$','All four','No singletons'],ylabel='Changes (%)',title='B  Declared-profile ablations')
    axes[0,1].legend(fontsize=8)
    counts=decisive.decisive_coordinate.value_counts().reindex(['Cmax','C25','C50','T25'],fill_value=0)
    axes[1,0].bar(['$C_M$','$C_{25}$','$C_{50}$','$T_{25}$'],counts,color=[BLUE,BLUE,BLUE,ORANGE])
    for j,value in enumerate(counts):axes[1,0].text(j,value+.8,str(int(value)),ha='center')
    axes[1,0].set(ylabel='Instances (of 90)',ylim=(0,max(counts)+9),title='C  First difference from nearest rival')
    uv=uci_rows[(uci_rows.p==.05)&uci_rows.method.str.startswith('ReLexTail')].copy()
    uv['delta']=uv.method.str.split().str[1].astype(float)
    axes[1,1].plot(uv.delta,uv.flip*100,'o-',color=BLUE)
    axes[1,1].axhline(float(uci_rows[(uci_rows.p==.05)&(uci_rows.method=='LexPR')].flip.iloc[0])*100,color=GREY,ls='--',label='LexPR')
    axes[1,1].set(xscale='log',xlabel='Resolution δ',ylabel='Point changes (%)',title='D  UCI simulation benchmark at p = 0.05')
    axes[1,1].legend(fontsize=8)
    save(fig,'sensitivity_extensions')
    # Every quantitative statement in the new comparison table is derived here.
    rows=[];summary=[]
    selected=['Weighted-sum','Mean-D','Leximax','Tail25-D','LexPR']+[f'ReLexTail {v:g}' for v in [.005,.01,.02,.05,.075,.1]]
    paired=sub.pivot(index='instance',columns='method',values='tail_regret')
    for name in selected:
        row=g.loc[name];effect=paired_effect_summary(paired[name].to_numpy(),paired.LexPR.to_numpy(),bootstrap_replicates=10000,seed=20260906);lo,hi=effect['ci_low'],effect['ci_high']
        nice=name.replace('ReLexTail ',r'ReLexTail $\delta=')+('$' if name.startswith('ReLexTail') else '')
        rows.append(f'{nice} & {row.mean_regret:.4f} & {row.tail_regret:.4f} & [{lo:+.5f}, {hi:+.5f}] & {100*row.flip:.2f} \\\\')
        summary.append(dict(method=name,**{k:float(row[k]) for k in ['mean_regret','tail_regret','flip','category_change','category_size']},tail_difference_ci=[float(lo),float(hi)]))
    (DATA/'comparison_rows.tex').write_text('\n'.join(rows)+'\n')
    effects=[]
    for metric,label,scale in [('flip','Point changes (pp)',100),('tail_regret','Upper-tail regret',1)]:
        pv=sub.pivot(index='instance',columns='method',values=metric)
        effect=paired_effect_summary(pv['ReLexTail 0.02'].to_numpy()*scale,pv.LexPR.to_numpy()*scale,bootstrap_replicates=20000,seed=20260906)
        effects.append(dict(metric=metric,label=label,**effect))
    adjusted=holm_adjust([effect['wilcoxon_p'] for effect in effects])
    effect_rows=[]
    for effect,p_adjusted in zip(effects,adjusted):
        effect['holm_p']=float(p_adjusted)
        effect_rows.append(f"{effect['label']} & {effect['mean_difference']:+.3f} & [{effect['ci_low']:+.3f}, {effect['ci_high']:+.3f}] & {effect['probability_of_superiority']:.3f} & {effect['wins']}/{effect['losses']}/{effect['ties']} & {p_adjusted:.3g} \\\\")
    (DATA/'primary_effects_rows.tex').write_text('\n'.join(effect_rows)+'\n')
    payload={'comparison':summary,'primary_effects':effects}
    (DATA/'summary.json').write_text(json.dumps(payload,indent=2).replace('NaN','null'))
    print('Generated 12 figures and numerical tables.')
if __name__=='__main__':main()
