"""Reproducible experiment execution and SQLite persistence."""
from __future__ import annotations
import copy, hashlib, json, os, sqlite3, time
from datetime import datetime, timezone
from .scenarios import generate_scenario
from .state import EngineState, RequestState
from .simulator import Simulator
from .distance import build_matrix
from .algorithms.greedy_insertion import GreedyInsertion
from .algorithms.greedy_then_two_opt_star import GreedyThenTwoOptStar
from .algorithms.tabu_search import TabuSearch

DB_PATH=os.path.join(os.path.dirname(__file__), '..', 'data', 'dvrp.db')
def get_conn():
    os.makedirs(os.path.dirname(DB_PATH),exist_ok=True); conn=sqlite3.connect(DB_PATH); conn.row_factory=sqlite3.Row
    conn.execute('CREATE TABLE IF NOT EXISTS experiment_runs (id TEXT PRIMARY KEY, experiment_id TEXT, run_id TEXT, strategy TEXT, params_json TEXT, metrics_json TEXT, created_at TEXT)')
    return conn
def strategy_factory(name, budget=None):
    budget=budget or {}
    if name=='greedy_insertion': return GreedyInsertion()
    if name=='insertion_2opt_star': return GreedyThenTwoOptStar()
    if name=='tabu_search': return TabuSearch(tenure=budget.get('tenure',7), evaluation_budget=budget.get('max_evaluations',500))
    raise ValueError(f'Unknown strategy: {name}')
class ExperimentRunner:
    def __init__(self, experiment_id, runs, workers=1): self.experiment_id,self.runs,self.workers=experiment_id,runs,workers
    def _distance(self,state):
        m=build_matrix([(0.,0.)]+state.scenario.customer_locations); total=0.
        for vehicle in state.vehicles.values():
            nodes=[0]+[r+1 for r in vehicle.route]+[0]; total += sum(m[a][b] for a,b in zip(nodes,nodes[1:]))
        return total
    def _run_single(self,cfg):
        scenario=copy.deepcopy(cfg.get('scenario_obj') or generate_scenario({'scenario':cfg['scenario']},cfg['seed']))
        state=EngineState(scenario); strategy=strategy_factory(cfg['strategy'],cfg.get('budget')); sim=Simulator(state,strategy)
        start=time.perf_counter(); final=sim.run(); compute=time.perf_counter()-start
        metrics={'total_distance':self._distance(final),'mean_response_time_ms':sum(sim.response_times)/len(sim.response_times) if sim.response_times else 0.0,'max_response_time_ms':max(sim.response_times,default=0.0),'route_disruption':sim.route_disruption,'evaluations':sim.total_evaluations,'tabu_evaluations':getattr(strategy,'tabu_evaluations',0),'improving_moves_found':getattr(strategy,'improving_moves_found',0),'iterations':strategy.iterations,'accepted_moves':strategy.accepted_moves,'rejected_moves':strategy.rejected_moves,'feasibility_violations':sum(sum(final.requests[r].demand for r in v.route)>v.capacity for v in final.vehicles.values()),'customers_served':sum(s==RequestState.ASSIGNED for s in final.request_states.values()),'customers_unserved':sum(s!=RequestState.ASSIGNED for s in final.request_states.values()),'pending_pool_size':sum(s==RequestState.AVAILABLE for s in final.request_states.values()),'phase_timings_ms':sim.phase_timings_ms,'compute_time_s':compute,'total_time_s':compute}
        scenario_key=hashlib.sha256(json.dumps(cfg['scenario'],sort_keys=True).encode()).hexdigest()[:16]; run_id=hashlib.sha256((self.experiment_id+cfg['strategy']+str(cfg['seed'])+str(time.time_ns())).encode()).hexdigest()[:16]
        created=datetime.now(timezone.utc).isoformat()
        with get_conn() as conn:
            conn.execute('INSERT INTO experiment_runs VALUES (?,?,?,?,?,?,?)',(run_id,self.experiment_id,run_id,cfg['strategy'],json.dumps({k:v for k,v in cfg.items() if k!='scenario_obj'}),json.dumps(metrics),created)); conn.commit()
        return metrics
    def run(self):
        for index,cfg in enumerate(self.runs,1):
            metrics=self._run_single(cfg)
            if index%25==0: print(f'progress {index}/{len(self.runs)}')
        return len(self.runs)
