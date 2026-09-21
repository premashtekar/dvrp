import sqlite3, json, os, time
from datetime import datetime
from engine.experiment_runner import ExperimentRunner

customers_list = [50]
dynamism_list = [0.1, 0.4, 0.8]
strategies = ['greedy_insertion', 'insertion_2opt_star', 'tabu_search']
seeds = [1, 2, 3]
exp_id = 'pilot_v2'

DB_PATH = 'data/dvrp.db'
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute("SELECT params_json FROM experiment_runs WHERE experiment_id=?", (exp_id,))
existing = set()
for row in cur.fetchall():
    try:
        p = json.loads(row['params_json'])
        existing.add((p['scenario']['customers'], p['scenario']['dynamism'], p['strategy'], p['seed']))
    except: pass
conn.close()

runs = []
for dyn in dynamism_list:
    for seed in seeds:
        for strat in strategies:
            sig = (50, dyn, strat, seed)
            if sig not in existing:
                runs.append({
                    'scenario': {'customers':50, 'vehicles':5, 'capacity':100, 'dynamism':dyn, 'map_size':100.0, 'horizon':1000.0},
                    'seed': seed,
                    'strategy': strat,
                    'budget': {'max_evaluations': 200} if strat == 'tabu_search' else {}
                })

print(f"Missing runs: {len(runs)}")
runner = ExperimentRunner(experiment_id=exp_id, runs=runs, workers=1)
for i, cfg in enumerate(runs):
    print(f"Running {i+1}/{len(runs)}")
    runner._run_single(cfg)

print("Done.")
