"""Export final-only database results for the static web application."""
from __future__ import annotations
import csv,json,sqlite3
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
from scipy.stats import friedmanchisquare,wilcoxon
from engine.experiment_runner import DB_PATH,strategy_factory
from engine.scenarios import generate_scenario
from engine.state import EngineState
from engine.simulator import Simulator

OUT=Path('web/public/demo'); STRATS=['greedy_insertion','insertion_2opt_star','tabu_search']; METRICS=['total_distance','mean_response_time_ms','route_disruption','compute_time_s','evaluations','customers_served','customers_unserved','pending_pool_size','feasibility_violations']
def summary(xs):
    a=np.array(xs,dtype=float); n=len(a); sd=float(a.std(ddof=1)) if n>1 else 0.; se=sd/(n**.5) if n else 0.
    return {'mean':float(a.mean()) if n else 0.,'sd':sd,'se':se,'ci95':[float(a.mean()-1.96*se) if n else 0.,float(a.mean()+1.96*se) if n else 0.],'n':n}
def boot(xs):
    a=np.array(xs,dtype=float); rng=np.random.default_rng(0); means=[a[rng.integers(0,len(a),len(a))].mean() for _ in range(2000)]
    return [float(np.quantile(means,.025)),float(np.quantile(means,.975))]
def main():
    with sqlite3.connect(DB_PATH) as conn: rows=conn.execute("SELECT strategy,params_json,metrics_json FROM experiment_runs WHERE experiment_id='final'").fetchall()
    grouped=defaultdict(dict)
    for strategy,p,m in rows:
        p=json.loads(p); grouped[(p['scenario']['customers'],p['scenario']['dynamism'],p['seed'])][strategy]=json.loads(m)
    complete={k:v for k,v in grouped.items() if set(v)==set(STRATS)}; aggregates=[]; paired=[]
    cells=defaultdict(list)
    for (customers,dyn,seed),triple in complete.items(): cells[(customers,dyn)].append((seed,triple))
    for (customers,dyn),triples in sorted(cells.items()):
        for strategy in STRATS:
            entry={'customers':customers,'dynamism':dyn,'strategy':strategy,'metrics':{metric:summary([t[strategy][metric] for _,t in triples]) for metric in METRICS}}
            aggregates.append(entry)
        distances=[[t[s]['total_distance'] for _,t in triples] for s in STRATS]
        fstat,fp=friedmanchisquare(*distances)
        comparisons=[]
        for i,j in ((0,1),(0,2),(1,2)):
            diff=np.array(distances[i])-np.array(distances[j]); stat,p=wilcoxon(diff,zero_method='pratt') if np.any(diff) else (0.,1.)
            comparisons.append({'comparison':f'{STRATS[i]}-{STRATS[j]}','mean_difference':float(diff.mean()),'bootstrap_ci95':boot(diff),'effect_size':float(diff.mean()/diff.std(ddof=1)) if len(diff)>1 and diff.std(ddof=1)>0 else 0.,'wilcoxon_statistic':float(stat),'wilcoxon_p':float(p)})
        ordered=sorted(comparisons,key=lambda x:x['wilcoxon_p']); m=len(ordered)
        for rank,item in enumerate(ordered): item['holm_p']=min(1.,item['wilcoxon_p']*(m-rank)); item['holm_reject']=item['holm_p']<.05
        paired.append({'customers':customers,'dynamism':dyn,'n':len(triples),'friedman':{'statistic':float(fstat),'p_value':float(fp)},'comparisons':comparisons})
    demos=[]
    for dyn in (.1,.4,.8):
        spec={'customers':50,'dynamism':dyn,'vehicles':5,'capacity':100,'map_size':100.,'horizon':480.}; scenario=generate_scenario({'scenario':spec},1)
        traces={}
        for s in STRATS:
            sim=Simulator(EngineState(scenario),strategy_factory(s,{'max_evaluations':500})); sim.run(); traces[s]=sim.trace
        demos.append({'scenario':{'customers':scenario.customer_locations,'release_times':scenario.release_times,'dynamism':dyn},'traces':traces})
    OUT.mkdir(parents=True,exist_ok=True); data={'generated_at':datetime.now(timezone.utc).isoformat(),'source_experiment':'final','note':'Small n: treat as descriptive if n < 10.','config':{'customers':[50],'dynamism':[.1,.2,.4,.6,.8],'strategies':STRATS,'seeds':[1,2,3,4,5]},'aggregated':aggregates,'paired_comparisons':paired,'demo_scenarios':demos}
    (OUT/'results.json').write_text(json.dumps(data,indent=2),encoding='utf8')
    with (OUT/'aggregated.csv').open('w',newline='',encoding='utf8') as f:
        writer=csv.writer(f); writer.writerow(['customers','dynamism','strategy','metric','mean','sd','se','ci95_low','ci95_high','n'])
        for a in aggregates:
            for metric,v in a['metrics'].items(): writer.writerow([a['customers'],a['dynamism'],a['strategy'],metric,v['mean'],v['sd'],v['se'],*v['ci95'],v['n']])
    print(f'exported complete_triples={len(complete)} aggregate_cells={len(aggregates)}')
if __name__=='__main__': main()
