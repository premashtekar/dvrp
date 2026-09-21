# engine/experiment_runner.py
"""Simple experiment runner for DVRP.

It receives a list of run specifications, creates scenarios, executes
simulations (using the same logic as the /simulations endpoint) and stores the
results in the ``experiment_runs`` table.

The runner is deliberately lightweight – it runs synchronously in a background
task and records each run's ``run_id`` together with the experiment identifier.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import List, Dict, Any

import sqlite3

from .scenarios import generate_scenario, Scenario
from .state import EngineState
from .algorithms.greedy_insertion import GreedyInsertion
from .algorithms.tabu_search import TabuSearch
from .simulator import Simulator
from .algorithms.two_opt_star import apply_two_opt_star
from .algorithms.greedy_then_two_opt_star import GreedyThenTwoOptStar

# Helper to get DB connection (same as in api/routers.py)
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "dvrp.db")

def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

class ExperimentRunner:
    """Runs a collection of simulation runs as a single experiment.

    Parameters
    ----------
    experiment_id: str
        Identifier for the experiment (hash of the config).
    runs: List[Dict[str, Any]]
        Each dict must contain ``scenario`` (dict for generate_scenario), ``seed``
        (int), ``strategy`` (str, one of ``greedy_insertion``, ``insertion_2opt_star``
        or ``tabu_search``) and optional ``budget`` (dict).
    workers: int
        Number of parallel workers for the ThreadPoolExecutor.
    """

    def __init__(self, experiment_id: str, runs: List[Dict[str, Any]], workers: int = 1):
        self.experiment_id = experiment_id
        self.runs = runs
        self.workers = max(1, workers)
        self.base_trace_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "traces"))
        os.makedirs(self.base_trace_dir, exist_ok=True)

    def _run_single(self, run_cfg: Dict[str, Any]) -> None:
        # Create scenario
        scenario_obj = generate_scenario({"scenario": run_cfg["scenario"]}, run_cfg["seed"])
        scenario_id = hashlib.sha256(json.dumps(run_cfg["scenario"], sort_keys=True).encode()).hexdigest()[:16]
        created = datetime.utcnow().isoformat()
        # Store scenario in DB (reuse same logic as /scenarios endpoint)
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT OR REPLACE INTO scenarios (id, created_at, seed, params_json, scenario_json) VALUES (?,?,?,?,?)",
                (
                    scenario_id,
                    created,
                    run_cfg["seed"],
                    json.dumps(run_cfg["scenario"]),
                    json.dumps(scenario_obj.__dict__),
                ),
            )
            conn.commit()
        # Build engine state
        state = EngineState(scenario_obj)
        # Choose strategy
        strat_name = run_cfg["strategy"]
        if strat_name == "greedy_insertion":
            strat = GreedyInsertion()
        elif strat_name == "insertion_2opt_star":
            strat = GreedyThenTwoOptStar()
        elif strat_name == "tabu_search":
            strat = TabuSearch()
        else:
            raise ValueError(f"Unsupported strategy {strat_name}")
        # Simulate
        sim = Simulator(state, strat)
        start = time.perf_counter()
        sim.run()
        if strat_name == "insertion_2opt_star":
            evals, delta = apply_two_opt_star(state)
            metrics = {
                "total_time_s": time.perf_counter() - start,
                "evaluations": getattr(strat, "evaluations", 0) + evals,
                "delta_distance": delta,
            }
        else:
            metrics = {
                "total_time_s": time.perf_counter() - start,
                "evaluations": getattr(strat, "evaluations", 0),
                "delta_distance": 0.0,
            }
        # Write trace
        trace_path = os.path.abspath(os.path.join(self.base_trace_dir, f"{scenario_id}.jsonl"))
        with open(trace_path, "w", encoding="utf-8") as f:
            for ev in sim.trace:
                f.write(json.dumps(ev) + "\n")
        # Insert run record (same schema as /simulations)
        run_id = hashlib.sha256((scenario_id + strat_name + str(time.time())).encode()).hexdigest()[:16]
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO runs (id, scenario_id, strategy, budget_json, params_json, code_version, workers, status, metrics_json, trace_path, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (
                    run_id,
                    scenario_id,
                    strat_name,
                    json.dumps(run_cfg.get("budget", {})),
                    json.dumps({}),
                    "0.1.0",
                    1,
                    "finished",
                    json.dumps(metrics),
                    trace_path,
                    datetime.utcnow().isoformat(),
                ),
            )
            # Record in experiment_runs table
            cur.execute(
                "INSERT INTO experiment_runs (id, experiment_id, run_id, strategy, params_json, metrics_json, created_at) VALUES (?,?,?,?,?,?,?)",
                (
                    hashlib.sha256((run_id + self.experiment_id).encode()).hexdigest()[:16],
                    self.experiment_id,
                    run_id,
                    strat_name,
                    json.dumps(run_cfg),
                    json.dumps(metrics),
                    datetime.utcnow().isoformat(),
                ),
            )
            conn.commit()

    def run(self) -> None:
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            for cfg in self.runs:
                executor.submit(self._run_single, cfg)
