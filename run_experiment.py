# run_experiment.py
"""Execute the P6 pilot experiment and produce aggregated CSV.

Creates an experiment with ID based on configuration hash, runs all combinations
(customers, dynamism, strategies, seeds) and stores raw runs via
Engine.ExperimentRunner. After completion it aggregates metrics (mean total_time_s
and evaluations) per strategy and writes a CSV to data/experiments/agg/summary.csv.
"""

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path

from engine.experiment_runner import ExperimentRunner
import sqlite3

# Configuration parameters
customers_list = [50, 100]
vehicles = 5
capacity = 100  # arbitrary, must be enough
dynamism_list = [0.1, 0.4, 0.8]
map_size = 100.0
horizon = 1000.0
seeds = list(range(5))  # 0-4
strategies = ["greedy_insertion", "insertion_2opt_star", "tabu_search"]

# Build run specifications
runs = []
for customers in customers_list:
    for dyn in dynamism_list:
        scenario_cfg = {
            "customers": customers,
            "vehicles": vehicles,
            "capacity": capacity,
            "dynamism": dyn,
            "map_size": map_size,
            "horizon": horizon,
        }
        for strat in strategies:
            for seed in seeds:
                runs.append({
                    "scenario": scenario_cfg,
                    "seed": seed,
                    "strategy": strat,
                    "budget": {},
                })

# Experiment identifier (hash of config)
exp_id = hashlib.sha256(json.dumps(runs, sort_keys=True).encode()).hexdigest()[:12]

runner = ExperimentRunner(experiment_id=exp_id, runs=runs, workers=4)
print(f"Starting experiment {exp_id} with {len(runs)} runs...")
runner.run()
print("All runs dispatched. Waiting for completion...")
# Simple wait loop (since run() is asynchronous via ThreadPoolExecutor, we join)
# The Executor is used inside run, but we didn't keep a reference. We'll just poll DB until all runs are finished.
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "dvrp.db")
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
# Wait until experiment_runs count matches runs length
import time
while True:
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as cnt FROM experiment_runs WHERE experiment_id=?", (exp_id,))
    cnt = cur.fetchone()["cnt"]
    if cnt >= len(runs):
        break
    time.sleep(2)
print(f"Experiment completed: {cnt} runs recorded.")

# Aggregation: compute mean total_time_s and evaluations per strategy
agg = {}
cur.execute("SELECT strategy, metrics_json FROM experiment_runs WHERE experiment_id=?", (exp_id,))
for row in cur.fetchall():
    strat = row["strategy"]
    metrics = json.loads(row["metrics_json"])
    agg.setdefault(strat, {"total_time_s": [], "evaluations": []})
    agg[strat]["total_time_s"].append(metrics.get("total_time_s", 0))
    agg[strat]["evaluations"].append(metrics.get("evaluations", 0))

# Write CSV
out_dir = Path(__file__).parent / "data" / "experiments" / "agg"
out_dir.mkdir(parents=True, exist_ok=True)
csv_path = out_dir / "summary.csv"
with open(csv_path, "w", encoding="utf-8") as f:
    f.write("strategy,mean_time_s,mean_evaluations\n")
    for strat, vals in agg.items():
        mean_time = sum(vals["total_time_s"]) / len(vals["total_time_s"]) if vals["total_time_s"] else 0
        mean_eval = sum(vals["evaluations"]) / len(vals["evaluations"]) if vals["evaluations"] else 0
        f.write(f"{strat},{mean_time:.4f},{mean_eval:.2f}\n")
print(f"Aggregated CSV written to {csv_path}")
