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
from .state import EngineState, RequestState
from .algorithms.greedy_insertion import GreedyInsertion
from .algorithms.tabu_search import TabuSearch
from .simulator import Simulator
from .algorithms.two_opt_star import apply_two_opt_star
from .algorithms.greedy_then_two_opt_star import GreedyThenTwoOptStar
from .distance import build_matrix

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "dvrp.db")

def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

class ExperimentRunner:
    def __init__(self, experiment_id: str, runs: List[Dict[str, Any]], workers: int = 1):
        self.experiment_id = experiment_id
        self.runs = runs
        self.workers = max(1, workers)
        self.base_trace_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "traces"))
        os.makedirs(self.base_trace_dir, exist_ok=True)

    def _compute_total_distance(self, state: EngineState) -> float:
        points = [(0.0, 0.0)] + state.scenario.customer_locations
        dist = build_matrix(points)
        cost = 0.0
        for veh in state.vehicles.values():
            if not veh.route: continue
            cost += dist[0][veh.route[0] + 1]
            for a, b in zip(veh.route, veh.route[1:]):
                cost += dist[a + 1][b + 1]
            cost += dist[veh.route[-1] + 1][0]
        return cost

    def _count_violations(self, state: EngineState) -> int:
        violations = 0
        for veh in state.vehicles.values():
            load = sum(state.requests[r].demand for r in veh.route)
            if load > veh.capacity: violations += 1
        return violations

    def _run_single(self, run_cfg: Dict[str, Any]) -> None:
        scenario_obj = generate_scenario({"scenario": run_cfg["scenario"]}, run_cfg["seed"])
        scenario_id = hashlib.sha256(json.dumps(run_cfg["scenario"], sort_keys=True).encode()).hexdigest()[:16]
        created = datetime.utcnow().isoformat()
        
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT OR REPLACE INTO scenarios (id, created_at, seed, params_json, scenario_json) VALUES (?,?,?,?,?)",
                (scenario_id, created, run_cfg["seed"], json.dumps(run_cfg["scenario"]), json.dumps(scenario_obj.__dict__))
            )
            conn.commit()

        state = EngineState(scenario_obj)
        strat_name = run_cfg["strategy"]
        if strat_name == "greedy_insertion":
            strat = GreedyInsertion()
        elif strat_name == "insertion_2opt_star":
            strat = GreedyThenTwoOptStar()
        elif strat_name == "tabu_search":
            strat = TabuSearch(evaluation_budget=run_cfg.get("budget", {}).get("max_evaluations", 200))
        else:
            raise ValueError(f"Unsupported strategy {strat_name}")

        sim = Simulator(state, strat)
        start = time.perf_counter()
        sim.run()

        evals = sim.total_evaluations
        route_disruption = 0
        iterations = 1
        
        if strat_name == "insertion_2opt_star":
            e, delta = apply_two_opt_star(state)
            evals += e
            route_disruption = e  # mock or real disruption

        total_time_s = time.perf_counter() - start
        
        served = sum(1 for rs in state.request_states.values() if rs == RequestState.SERVED)
        unserved = sum(1 for rs in state.request_states.values() if rs != RequestState.SERVED)
        mean_rt = sum(sim.response_times)/len(sim.response_times) if sim.response_times else 0
        max_rt = max(sim.response_times) if sim.response_times else 0

        metrics = {
            "total_time_s": total_time_s,
            "total_distance": self._compute_total_distance(state),
            "mean_response_time_ms": mean_rt,
            "max_response_time_ms": max_rt,
            "route_disruption": route_disruption,
            "evaluations": evals,
            "iterations": iterations,
            "feasibility_violations": self._count_violations(state),
            "customers_served": served,
            "customers_unserved": unserved,
        }

        trace_path = os.path.abspath(os.path.join(self.base_trace_dir, f"{scenario_id}.jsonl"))
        sim.dump_trace(trace_path)

        run_id = hashlib.sha256((scenario_id + strat_name + str(time.time())).encode()).hexdigest()[:16]
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO runs (id, scenario_id, strategy, budget_json, params_json, code_version, workers, status, metrics_json, trace_path, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (run_id, scenario_id, strat_name, json.dumps(run_cfg.get("budget", {})), json.dumps({}), "0.1.0", 1, "finished", json.dumps(metrics), trace_path, created)
            )
            cur.execute(
                "INSERT INTO experiment_runs (id, experiment_id, run_id, strategy, params_json, metrics_json, created_at) VALUES (?,?,?,?,?,?,?)",
                (hashlib.sha256((run_id + self.experiment_id).encode()).hexdigest()[:16], self.experiment_id, run_id, strat_name, json.dumps(run_cfg), json.dumps(metrics), created)
            )
            conn.commit()

    def run(self) -> None:
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            for cfg in self.runs:
                executor.submit(self._run_single, cfg)
