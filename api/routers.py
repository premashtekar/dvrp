"""API routers for DVRP Lab.
Implements endpoints defined in Phase P4 plan.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import json
import hashlib
import time
import os
from datetime import datetime
import sqlite3

from engine.scenarios import generate_scenario, Scenario
from engine.state import EngineState
from engine.algorithms.greedy_insertion import GreedyInsertion
from engine.algorithms.tabu_search import TabuSearch
from engine.simulator import Simulator
from engine.models import Vehicle, Request
from engine.distance import build_matrix

router = APIRouter()

# SQLite helper
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "dvrp.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Ensure tables exist
with get_conn() as conn:
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS scenarios (
            id TEXT PRIMARY KEY,
            created_at TEXT,
            seed INTEGER,
            params_json TEXT,
            scenario_json TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            id TEXT PRIMARY KEY,
            scenario_id TEXT,
            strategy TEXT,
            budget_json TEXT,
            params_json TEXT,
            code_version TEXT,
            workers INTEGER,
            status TEXT,
            metrics_json TEXT,
            trace_path TEXT,
            created_at TEXT,
            FOREIGN KEY(scenario_id) REFERENCES scenarios(id)
        )
    """)
    conn.commit()
    # experiment tables
    c.execute("""
        CREATE TABLE IF NOT EXISTS experiments (
            id TEXT PRIMARY KEY,
            config_json TEXT,
            aggregated_json TEXT,
            created_at TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS experiment_runs (
            id TEXT PRIMARY KEY,
            experiment_id TEXT,
            run_id TEXT,
            strategy TEXT,
            params_json TEXT,
            metrics_json TEXT,
            created_at TEXT,
            FOREIGN KEY(run_id) REFERENCES runs(id)
        )
    """)
    conn.commit()

# Pydantic models
class HealthResponse(BaseModel):
    status: str = "OK"
    timestamp: str

class StrategyInfo(BaseModel):
    name: str
    implemented: bool

class ScenarioCreate(BaseModel):
    customers: int = Field(..., gt=0)
    vehicles: int = Field(..., gt=0)
    capacity: int = Field(..., gt=0)
    dynamism: float = Field(..., ge=0.0, le=1.0)
    seed: int
    map_size: float = Field(..., gt=0)
    horizon: float = Field(..., gt=0)

class ScenarioResponse(BaseModel):
    id: str
    created_at: str
    params: Dict[str, Any]
    scenario: Dict[str, Any]

class RunCreate(BaseModel):
    scenario_id: str
    strategy: str = Field(..., pattern="^(greedy_insertion|insertion_2opt_star|tabu_search)$")
    budget: Dict[str, Any] = {}

class RunResponse(BaseModel):
    run_id: str
    status: str
    metrics: Optional[Dict[str, Any]] = None

class TraceEvent(BaseModel):
    time: float
    event: str
    request_id: Optional[int] = None
    evaluations: Optional[int] = None
    delta: Optional[float] = None

# Endpoints
@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(timestamp=datetime.utcnow().isoformat())

@router.get("/strategies", response_model=List[StrategyInfo])
async def list_strategies():
    return [
        StrategyInfo(name="greedy_insertion", implemented=True),
        StrategyInfo(name="insertion_2opt_star", implemented=True),
        StrategyInfo(name="tabu_search", implemented=True),
    ]

def compute_hash(params: Dict[str, Any]) -> str:
    # deterministic hash of sorted JSON
    json_str = json.dumps(params, sort_keys=True)
    return hashlib.sha256(json_str.encode()).hexdigest()

@router.post("/scenarios", response_model=ScenarioResponse)
async def create_scenario(scen: ScenarioCreate):
    params = scen.dict()
    scen_id = compute_hash(params)
    created = datetime.utcnow().isoformat()
    # generate scenario object
    # generate scenario object using proper signature
    config = {
        "scenario": {
            "customers": scen.customers,
            "vehicles": scen.vehicles,
            "capacity": scen.capacity,
            "dynamism": scen.dynamism,
            "map_size": scen.map_size,
            "horizon": scen.horizon,
        }
    }
    scenario_obj = generate_scenario(config, scen.seed)
    # store JSON representations
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO scenarios (id, created_at, seed, params_json, scenario_json) VALUES (?,?,?,?,?)",
            (scen_id, created, scen.seed, json.dumps(params), json.dumps(scenario_obj.__dict__)),
        )
        conn.commit()
    return ScenarioResponse(id=scen_id, created_at=created, params=params, scenario=scenario_obj.__dict__)

@router.get("/scenarios/{scenario_id}", response_model=ScenarioResponse)
async def get_scenario(scenario_id: str):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM scenarios WHERE id=?", (scenario_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Scenario not found")
    params = json.loads(row["params_json"])
    scenario = json.loads(row["scenario_json"])
    return ScenarioResponse(id=row["id"], created_at=row["created_at"], params=params, scenario=scenario)

def run_simulation(state: EngineState, strategy_name: str) -> Dict[str, Any]:
    # Choose strategy implementation
    if strategy_name == "greedy_insertion":
        strat = GreedyInsertion()
    elif strategy_name == "insertion_2opt_star":
        # compose greedy then 2-opt*
        class StrategyB(GreedyInsertion.__class__):
            pass
        # We'll reuse GreedyInsertion then apply two_opt_star
        strat = GreedyInsertion()
    else:
        raise ValueError("Unsupported strategy")
    sim = Simulator(state, strat)
    start = time.perf_counter()
    sim.run()
    if strategy_name == "insertion_2opt_star":
        # after greedy insertion, improve
        evals, delta = apply_two_opt_star(state)
    else:
        evals, delta = 0, 0.0
    end = time.perf_counter()
    metrics = {
        "total_time_s": end - start,
        "evaluations": getattr(strat, "evaluations", 0) + evals,
        "delta_distance": delta,
    }
    return metrics

@router.post("/simulations", response_model=RunResponse)
async def start_simulation(run: RunCreate, background: BackgroundTasks):
    # fetch scenario
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT scenario_json FROM scenarios WHERE id=?", (run.scenario_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Scenario not found")
    scenario_dict = json.loads(row["scenario_json"])
    # reconstruct Scenario dataclass (simplified)
    # Scenario class already imported from engine.scenarios at module level
    scenario = Scenario(**scenario_dict)
    state = EngineState(scenario)
    run_id = hashlib.sha256((run.scenario_id + run.strategy + str(time.time())).encode()).hexdigest()[:16]
    created = datetime.utcnow().isoformat()
    # paths
    trace_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "traces", f"{run_id}.jsonl"))
    os.makedirs(os.path.dirname(trace_path), exist_ok=True)
    # background execution
    def exec_run():
        # select strategy implementation
        if run.strategy == "greedy_insertion":
            strat = GreedyInsertion()
        elif run.strategy == "insertion_2opt_star":
            strat = GreedyInsertion()
        elif run.strategy == "tabu_search":
            strat = TabuSearch()
        else:
            raise ValueError("Unsupported strategy")
        sim = Simulator(state, strat)
        start = time.perf_counter()
        sim.run()
        if run.strategy == "insertion_2opt_star":
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
        # write trace
        with open(trace_path, "w", encoding="utf-8") as f:
            for ev in sim.trace:
                f.write(json.dumps(ev) + "\n")
        # store run record
        with get_conn() as conn2:
            cur2 = conn2.cursor()
            cur2.execute(
                "INSERT INTO runs (id, scenario_id, strategy, budget_json, params_json, code_version, workers, status, metrics_json, trace_path, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (
                    run_id,
                    run.scenario_id,
                    run.strategy,
                    json.dumps(run.budget),
                    json.dumps({}),
                    "0.1.0",
                    1,
                    "finished",
                    json.dumps(metrics),
                    trace_path,
                    created,
                ),
            )
            conn2.commit()
    background.add_task(exec_run)
    return RunResponse(run_id=run_id, status="running")

@router.get("/simulations/{run_id}", response_model=RunResponse)
async def get_simulation(run_id: str):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM runs WHERE id=?", (run_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Run not found")
    metrics = json.loads(row["metrics_json"]) if row["metrics_json"] else None
    return RunResponse(run_id=row["id"], status=row["status"], metrics=metrics)

@router.get("/simulations/{run_id}/trace")
async def get_trace(run_id: str):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT trace_path FROM runs WHERE id=?", (run_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Run not found")
    path = row["trace_path"]
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Trace not available")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    return content  # raw JSONL string

@router.get("/runs")
async def list_runs(limit: int = 10, offset: int = 0):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, scenario_id, strategy, status, created_at FROM runs ORDER BY created_at DESC LIMIT ? OFFSET ?", (limit, offset))
        rows = cur.fetchall()
    return [dict(row) for row in rows]
