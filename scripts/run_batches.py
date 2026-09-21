"""Run the fixed evaluation and disjoint tuning batches from the repository root."""
from __future__ import annotations
import copy, json, sqlite3
from collections import defaultdict
from engine.scenarios import generate_scenario
from engine.experiment_runner import ExperimentRunner, DB_PATH

STRATEGIES=['greedy_insertion','insertion_2opt_star','tabu_search']
# Preflight projected the uncut 300-run evaluation over eight minutes; both permitted cuts apply.
DESIGN={'customers':[50], 'dynamism':[.1,.2,.4,.6,.8], 'seeds':list(range(1,6))}
TUNING={'customers':[50], 'dynamism':[.1,.2,.4,.6,.8], 'seeds':list(range(101,106))}
BASE={'vehicles':5,'capacity':100,'map_size':100.,'horizon':480.}
def run(name, design):
    runs=[]
    for customers in design['customers']:
      for dynamism in design['dynamism']:
       for seed in design['seeds']:
        spec={'customers':customers,'dynamism':dynamism,**BASE}; generated=generate_scenario({'scenario':spec},seed)
        for strategy in STRATEGIES:
          runs.append({'scenario':spec,'scenario_obj':copy.deepcopy(generated),'seed':seed,'strategy':strategy,'budget':{'max_evaluations':500}})
    ExperimentRunner(name,runs,workers=1).run()
    with sqlite3.connect(DB_PATH) as conn:
      rows=conn.execute('SELECT strategy,metrics_json FROM experiment_runs WHERE experiment_id=?',(name,)).fetchall()
    values=defaultdict(lambda: defaultdict(list))
    for strategy, raw in rows:
      metric=json.loads(raw)
      for key in ('total_distance','evaluations','compute_time_s'): values[strategy][key].append(metric[key])
    for strategy in STRATEGIES:
      print(f"{name} {strategy}: mean total_distance={sum(values[strategy]['total_distance'])/len(values[strategy]['total_distance']):.6f}, mean evaluations={sum(values[strategy]['evaluations'])/len(values[strategy]['evaluations']):.6f}, mean compute_time_s={sum(values[strategy]['compute_time_s'])/len(values[strategy]['compute_time_s']):.6f}")
if __name__=='__main__':
    import sys
    selected=sys.argv[1:]
    if not selected or 'final' in selected: run('final',DESIGN)
    if not selected or 'tuning' in selected: run('tuning',TUNING)
