import sqlite3, json, os, time
from engine.experiment_runner import ExperimentRunner

customers_list = [50]
dynamism_list = [0.1, 0.4, 0.8]
strategies = ['greedy_insertion', 'insertion_2opt_star', 'tabu_search']
seeds = [1, 2, 3]
exp_id = 'pilot_v3'

runs = []
for dyn in dynamism_list:
    for seed in seeds:
        for strat in strategies:
            runs.append({
                'scenario': {'customers':50, 'vehicles':5, 'capacity':100, 'dynamism':dyn, 'map_size':100.0, 'horizon':1000.0},
                'seed': seed,
                'strategy': strat,
                'budget': {'max_evaluations': 200} if strat == 'tabu_search' else {}
            })

runner = ExperimentRunner(experiment_id=exp_id, runs=runs, workers=1)
for i, cfg in enumerate(runs):
    runner._run_single(cfg)

conn = sqlite3.connect('data/dvrp.db')
cur = conn.cursor()
cur.execute("SELECT strategy, metrics_json FROM experiment_runs WHERE experiment_id='pilot_v3'")
stats = {}
for row in cur.fetchall():
    st = row[0]
    m = json.loads(row[1])
    if st not in stats: stats[st] = {'d': [], 'e': []}
    stats[st]['d'].append(m['total_distance'])
    stats[st]['e'].append(m['evaluations'])

for st, vals in stats.items():
    print(f"{st}: mean_dist={sum(vals['d'])/len(vals['d']):.2f}, mean_eval={sum(vals['e'])/len(vals['e']):.2f}")
