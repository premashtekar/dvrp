import sqlite3
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict
import csv

from engine.stats import mean, std, sem, friedman, wilcoxon_pairwise, bootstrap_ci

# Paths
DB_PATH = Path('data/dvrp.db')
OUTPUT_JSON = Path('web/public/demo/results.json')
CSV_PATH = Path('web/public/demo/aggregated.csv')

# Load experiment runs
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute("SELECT run_id, strategy, metrics_json, params_json FROM experiment_runs WHERE experiment_id='pilot_v3'")
rows = cur.fetchall()
conn.close()

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
strategies_expected = ['greedy_insertion', 'insertion_2opt_star', 'tabu_search']
for sig, strats in groups.items():
    if set(strats.keys()) == set(strategies_expected):
        for s in strats.values():
            s['dynamism'] = sig[1]
            per_run.append(s)

agg_by_dyn_strat = defaultdict(list)
distance_pooled = {s: [] for s in strategies_expected}
for entry in per_run:
    strat = entry['strategy']
    dyn = entry['dynamism']
    d = entry['metrics'].get('total_distance', 0)
    agg_by_dyn_strat[(dyn, strat)].append(d)
    
# for paired stats, we must align the same instances
aligned_distances = []
for sig, strats in groups.items():
    if set(strats.keys()) == set(strategies_expected):
        aligned_distances.append([strats[s]['metrics'].get('total_distance', 0) for s in strategies_expected])

# paired tests
friedman_stat, friedman_p = friedman(list(zip(*aligned_distances))) if aligned_distances else (0.0, 1.0)
wilcoxon_results = wilcoxon_pairwise(list(zip(*aligned_distances))) if aligned_distances else []

paired_diffs = []
if aligned_distances:
    for (i, j, stat, p, reject) in wilcoxon_results:
        diffs = [row[i] - row[j] for row in aligned_distances]
        m_diff = mean(diffs)
        ci_lower, ci_upper = bootstrap_ci(diffs)
        paired_diffs.append({
            'compare': f"{strategies_expected[i]} vs {strategies_expected[j]}",
            'mean_diff': m_diff,
            'ci_95': [ci_lower, ci_upper],
            'p_value': p,
            'significant_holm': reject
        })

aggregated = []
for (dyn, strat), dists in agg_by_dyn_strat.items():
    aggregated.append({
        'dynamism': dyn,
        'strategy': strat,
        'mean_distance': mean(dists),
        'sd_distance': std(dists) if len(dists)>1 else 0,
        'se_distance': sem(dists),
        'n': len(dists)
    })

# Gather all data for JSON
result = {
    'generated_at': datetime.now(timezone.utc).isoformat(),
    'seed_count': 3,
    'config': {
        'customers': [50],
        'dynamism': [0.1, 0.4, 0.8],
        'strategies': strategies_expected,
        'seeds': [1, 2, 3]
    },
    'per_run': per_run,
    'aggregated': aggregated,
    'paired_stats': {
        'friedman': {'statistic': friedman_stat, 'p_value': friedman_p},
        'pairwise': paired_diffs
    }
}

OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
with OUTPUT_JSON.open('w') as f:
    json.dump(result, f, indent=2)

# Write CSV
with CSV_PATH.open('w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['dynamism', 'strategy', 'mean_distance', 'sd_distance', 'se_distance', 'n'])
    writer.writeheader()
    for row in aggregated:
        writer.writerow(row)
        
print('Exported', OUTPUT_JSON, 'with', len(per_run), 'rows.')
