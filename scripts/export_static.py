import sqlite3
import json
import os
from datetime import datetime
import csv
from pathlib import Path

# Paths
DB_PATH = Path('data/dvrp.db')
OUTPUT_JSON = Path('web/public/demo/results.json')

# Load experiment runs
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute("SELECT run_id, strategy, metrics_json, params_json FROM experiment_runs WHERE experiment_id='pilot_v2'")
rows = cur.fetchall()
conn.close()

# Group by (scenario_customers, scenario_dynamism, seed)
groups = {}
for run_id, strategy, metrics_json, params_json in rows:
    metrics = json.loads(metrics_json)
    params = json.loads(params_json)
    sig = (params['scenario']['customers'], params['scenario']['dynamism'], params['seed'])
    if sig not in groups:
        groups[sig] = {}
    groups[sig][strategy] = {
        'run_id': run_id,
        'strategy': strategy,
        'metrics': metrics
    }

per_run = []
strategies_expected = {'greedy_insertion', 'insertion_2opt_star', 'tabu_search'}
for sig, strats in groups.items():
    if set(strats.keys()) == strategies_expected:
        for s in strats.values():
            per_run.append(s)

# Load aggregated stats (we'll just compute them here instead of CSV to ensure they match triples)
agg = {}
metric_by_strategy = {}
for entry in per_run:
    strat = entry['strategy']
    metrics = entry['metrics']
    agg.setdefault(strat, {'total_time_s': [], 'evaluations': [], 'delta_distance': []})
    agg[strat]['total_time_s'].append(metrics.get('total_time_s', 0))
    agg[strat]['evaluations'].append(metrics.get('evaluations', 0))
    agg[strat]['delta_distance'].append(metrics.get('delta_distance', 0))
    
    metric_by_strategy.setdefault(strat, []).append(metrics.get('total_time_s', 0))

aggregated = []
for strat, vals in agg.items():
    mean_time = sum(vals['total_time_s']) / len(vals['total_time_s']) if vals['total_time_s'] else 0
    mean_eval = sum(vals['evaluations']) / len(vals['evaluations']) if vals['evaluations'] else 0
    mean_delta = sum(vals['delta_distance']) / len(vals['delta_distance']) if vals['delta_distance'] else 0
    aggregated.append({
        'strategy': strat,
        'mean_time_s': mean_time,
        'mean_evaluations': mean_eval,
        'mean_delta_distance': mean_delta
    })

try:
    from engine.stats import compute_friedman_wilcoxon
    friedman, wilcoxon = compute_friedman_wilcoxon(metric_by_strategy)
    paired_stats = {'friedman': friedman, 'wilcoxon': wilcoxon}
except Exception as e:
    paired_stats = {'error': str(e)}

result = {
    'generated_at': datetime.utcnow().isoformat() + 'Z',
    'seed_count': 3,
    'config': {
        'customers': [50],
        'vehicles': 5,
        'dynamism': [0.1, 0.4, 0.8],
        'strategies': ['greedy_insertion', 'insertion_2opt_star', 'tabu_search'],
        'seeds': [1, 2, 3]
    },
    'per_run': per_run,
    'aggregated': aggregated,
    'paired_stats': paired_stats
}

OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
with OUTPUT_JSON.open('w') as f:
    json.dump(result, f, indent=2)

print('Exported', OUTPUT_JSON, 'with', len(per_run), 'rows.')
