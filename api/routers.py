"""Deployable API routes backed by a request-scoped SQLite connection."""
from __future__ import annotations
import copy,hashlib,json,os,shutil,sqlite3,time
from datetime import datetime,timezone
from pathlib import Path
from typing import Any
import numpy as np
from fastapi import APIRouter,HTTPException,Response
from pydantic import BaseModel,Field
from scipy.stats import friedmanchisquare,wilcoxon
from engine.scenarios import generate_scenario
from engine.state import EngineState,RequestState
from engine.simulator import Simulator
from engine.distance import build_matrix
from engine.algorithms.greedy_insertion import GreedyInsertion
from engine.algorithms.greedy_then_two_opt_star import GreedyThenTwoOptStar
from engine.algorithms.tabu_search import TabuSearch

router=APIRouter()
ROOT=Path(__file__).resolve().parents[1]; DB_PATH=ROOT/'data'/'dvrp.db'; SEED_PATH=ROOT/'data'/'seed'/'dvrp_seed.db'; DEMO_PATH=ROOT/'web'/'public'/'demo'/'results.json'
METRICS=['total_distance','mean_response_time_ms','route_disruption','compute_time_s','evaluations','customers_served','customers_unserved','pending_pool_size','feasibility_violations','accepted_moves','improving_moves_found','tabu_evaluations']; STRATEGIES=['greedy_insertion','insertion_2opt_star','tabu_search']

def ensure_database()->None:
    DB_PATH.parent.mkdir(parents=True,exist_ok=True)
    if (not DB_PATH.exists() or DB_PATH.stat().st_size==0) and SEED_PATH.exists(): shutil.copy2(SEED_PATH,DB_PATH)
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript('''CREATE TABLE IF NOT EXISTS scenarios (id TEXT PRIMARY KEY,created_at TEXT,seed INTEGER,params_json TEXT,scenario_json TEXT);
        CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY,scenario_id TEXT,strategy TEXT,budget_json TEXT,params_json TEXT,code_version TEXT,workers INTEGER,status TEXT,metrics_json TEXT,trace_path TEXT,created_at TEXT);
        CREATE TABLE IF NOT EXISTS experiment_runs (id TEXT PRIMARY KEY,experiment_id TEXT,run_id TEXT,strategy TEXT,params_json TEXT,metrics_json TEXT,created_at TEXT);''')

def get_conn()->sqlite3.Connection:
    ensure_database(); conn=sqlite3.connect(DB_PATH,check_same_thread=False); conn.row_factory=sqlite3.Row; return conn

class HealthResponse(BaseModel): status:str='OK'; timestamp:str
class StrategyInfo(BaseModel): name:str; implemented:bool
class ScenarioCreate(BaseModel):
    customers:int=Field(gt=0); vehicles:int=Field(gt=0); capacity:int=Field(gt=0); dynamism:float=Field(ge=0,le=1); seed:int; map_size:float=Field(gt=0); horizon:float=Field(gt=0)
class ScenarioResponse(BaseModel): id:str; created_at:str; params:dict[str,Any]; scenario:dict[str,Any]
class RunCreate(BaseModel): scenario_id:str; strategy:str=Field(pattern='^(greedy_insertion|insertion_2opt_star|tabu_search)$'); budget:dict[str,Any]=Field(default_factory=dict)
class RunResponse(BaseModel): run_id:str; status:str; metrics:dict[str,Any]|None=None
class CompareCreate(BaseModel):
    scenario_id:str
    strategies:list[str]=Field(default_factory=lambda:STRATEGIES.copy())
    budget:dict[str,Any]=Field(default_factory=dict)

def utcnow()->str:return datetime.now(timezone.utc).isoformat()
def scenario_hash(params:dict[str,Any])->str:return hashlib.sha256(json.dumps(params,sort_keys=True).encode()).hexdigest()[:24]
def choose_strategy(name:str,budget:dict[str,Any]):
    if name=='greedy_insertion': return GreedyInsertion()
    if name=='insertion_2opt_star': return GreedyThenTwoOptStar()
    if name=='tabu_search': return TabuSearch(evaluation_budget=budget.get('max_evaluations',500),tenure=budget.get('tenure',7))
    raise ValueError(f'Unknown strategy: {name}')
def total_distance(state:EngineState)->float:
    matrix=build_matrix([(0.,0.)]+state.scenario.customer_locations); total=0.
    for vehicle in state.vehicles.values():
        route=[0]+[r+1 for r in vehicle.route]+[0]; total+=sum(matrix[a][b] for a,b in zip(route,route[1:]))
    return total
def run_engine(scenario, strategy_name:str,budget:dict[str,Any])->tuple[dict[str,Any],list[dict[str,Any]]]:
    state=EngineState(scenario); strategy=choose_strategy(strategy_name,budget); simulator=Simulator(state,strategy); started=time.perf_counter(); final=simulator.run(); elapsed=time.perf_counter()-started
    metrics={'total_distance':total_distance(final),'mean_response_time_ms':float(np.mean(simulator.response_times)) if simulator.response_times else 0.,'max_response_time_ms':max(simulator.response_times,default=0.),'route_disruption':simulator.route_disruption,'evaluations':simulator.total_evaluations,'tabu_evaluations':getattr(strategy,'tabu_evaluations',0),'improving_moves_found':getattr(strategy,'improving_moves_found',0),'accepted_moves':strategy.accepted_moves,'rejected_moves':strategy.rejected_moves,'iterations':strategy.iterations,'customers_served':sum(s==RequestState.ASSIGNED for s in final.request_states.values()),'customers_unserved':sum(s!=RequestState.ASSIGNED for s in final.request_states.values()),'pending_pool_size':sum(s==RequestState.AVAILABLE for s in final.request_states.values()),'feasibility_violations':sum(sum(final.requests[r].demand for r in v.route)>v.capacity for v in final.vehicles.values()),'phase_timings_ms':simulator.phase_timings_ms,'compute_time_s':elapsed,'total_time_s':elapsed}
    return metrics,simulator.trace
def persist_run(scenario_id:str,strategy:str,budget:dict[str,Any],scenario)->RunResponse:
    metrics,trace=run_engine(copy.deepcopy(scenario),strategy,budget); run_id=hashlib.sha256(f'{scenario_id}{strategy}{time.time_ns()}'.encode()).hexdigest()[:24]; trace_path=ROOT/'data'/'traces'/f'{run_id}.jsonl'; trace_path.parent.mkdir(parents=True,exist_ok=True); trace_path.write_text(''.join(json.dumps(event)+'\n' for event in trace),encoding='utf8')
    with get_conn() as conn: conn.execute('INSERT INTO runs VALUES (?,?,?,?,?,?,?,?,?,?,?)',(run_id,scenario_id,strategy,json.dumps(budget),'{}','0.1.0',1,'finished',json.dumps(metrics),str(trace_path),utcnow()))
    return RunResponse(run_id=run_id,status='finished',metrics=metrics)

@router.get('/health',response_model=HealthResponse)
def health_check(): ensure_database(); return HealthResponse(timestamp=utcnow())
@router.get('/strategies',response_model=list[StrategyInfo])
def list_strategies(): return [StrategyInfo(name=name,implemented=True) for name in STRATEGIES]
@router.post('/scenarios',response_model=ScenarioResponse)
def create_scenario(request:ScenarioCreate):
    params=request.model_dump(); scenario_id=scenario_hash(params); created=utcnow(); scenario=generate_scenario({'scenario':{k:params[k] for k in ('customers','vehicles','capacity','dynamism','map_size','horizon')}},params['seed'])
    with get_conn() as conn: conn.execute('INSERT OR REPLACE INTO scenarios VALUES (?,?,?,?,?)',(scenario_id,created,params['seed'],json.dumps(params),json.dumps(scenario.__dict__)))
    return ScenarioResponse(id=scenario_id,created_at=created,params=params,scenario=scenario.__dict__)
@router.get('/scenarios/{scenario_id}',response_model=ScenarioResponse)
def get_scenario(scenario_id:str):
    with get_conn() as conn: row=conn.execute('SELECT * FROM scenarios WHERE id=?',(scenario_id,)).fetchone()
    if not row: raise HTTPException(404,'Scenario not found')
    return ScenarioResponse(id=row['id'],created_at=row['created_at'],params=json.loads(row['params_json']),scenario=json.loads(row['scenario_json']))
@router.post('/simulations',response_model=RunResponse)
def start_simulation(request:RunCreate):
    with get_conn() as conn: row=conn.execute('SELECT scenario_json FROM scenarios WHERE id=?',(request.scenario_id,)).fetchone()
    if not row: raise HTTPException(404,'Scenario not found')
    from engine.models import Scenario
    return persist_run(request.scenario_id,request.strategy,request.budget,Scenario(**json.loads(row['scenario_json'])))
@router.post('/compare')
def compare_scenario(request:CompareCreate):
    if not request.strategies or any(strategy not in STRATEGIES for strategy in request.strategies): raise HTTPException(422,'Strategies must be drawn from A, B, and C')
    with get_conn() as conn: row=conn.execute('SELECT scenario_json FROM scenarios WHERE id=?',(request.scenario_id,)).fetchone()
    if not row: raise HTTPException(404,'Scenario not found')
    from engine.models import Scenario
    scenario=Scenario(**json.loads(row['scenario_json'])); runs=[persist_run(request.scenario_id,strategy,request.budget,scenario) for strategy in request.strategies]
    return {'scenario_id':request.scenario_id,'runs':[run.model_dump() for run in runs]}
@router.get('/simulations/{run_id}',response_model=RunResponse)
def get_simulation(run_id:str):
    with get_conn() as conn: row=conn.execute('SELECT status,metrics_json FROM runs WHERE id=?',(run_id,)).fetchone()
    if not row: raise HTTPException(404,'Run not found')
    return RunResponse(run_id=run_id,status=row['status'],metrics=json.loads(row['metrics_json']))
@router.get('/traces/{trace_id}')
def get_trace(trace_id:str):
    with get_conn() as conn: row=conn.execute('SELECT trace_path FROM runs WHERE id=?',(trace_id,)).fetchone()
    if not row or not Path(row['trace_path']).exists(): raise HTTPException(404,'Trace not found')
    return {'id':trace_id,'events':[json.loads(x) for x in Path(row['trace_path']).read_text(encoding='utf8').splitlines() if x]}
@router.get('/simulations/{run_id}/trace')
def get_simulation_trace(run_id:str):
    with get_conn() as conn: row=conn.execute('SELECT trace_path FROM runs WHERE id=?',(run_id,)).fetchone()
    if not row or not Path(row['trace_path']).exists(): raise HTTPException(404,'Trace not found')
    return Response(Path(row['trace_path']).read_text(encoding='utf8'),media_type='application/x-ndjson')

def descriptive(values:list[float])->dict[str,Any]:
    sample=np.asarray(values,dtype=float); n=len(sample); sd=float(np.std(sample,ddof=1)) if n>1 else 0.; se=sd/(n**.5) if n else 0.; mean=float(np.mean(sample)) if n else 0.
    return {'mean':mean,'sd':sd,'se':se,'ci95':[mean-1.96*se,mean+1.96*se],'n':n}
def bootstrap(values:list[float])->list[float]:
    sample=np.asarray(values,dtype=float); rng=np.random.default_rng(0); means=[float(sample[rng.integers(0,len(sample),len(sample))].mean()) for _ in range(2000)]
    return [float(np.quantile(means,.025)),float(np.quantile(means,.975))]
def demo_scenarios()->list[Any]:
    if not DEMO_PATH.exists(): return []
    return json.loads(DEMO_PATH.read_text(encoding='utf8')).get('demo_scenarios',[])
@router.get('/demo-scenarios')
def get_demo_scenarios(): return {'demo_scenarios':demo_scenarios()}
@router.get('/results')
def results(batch:str='final'):
    with get_conn() as conn: rows=conn.execute('SELECT strategy,params_json,metrics_json FROM experiment_runs WHERE experiment_id=?',(batch,)).fetchall()
    grouped:dict[tuple[int,float,int],dict[str,dict[str,Any]]]={}
    for row in rows:
        params=json.loads(row['params_json']); key=(params['scenario']['customers'],params['scenario']['dynamism'],params['seed']); grouped.setdefault(key,{})[row['strategy']]=json.loads(row['metrics_json'])
    complete={key:value for key,value in grouped.items() if set(value)==set(STRATEGIES)}
    cells:dict[tuple[int,float],list[tuple[int,dict[str,dict[str,Any]]]]]={}
    for (customers,dynamism,seed),triple in complete.items(): cells.setdefault((customers,dynamism),[]).append((seed,triple))
    aggregates=[]; paired=[]
    for (customers,dynamism),triples in sorted(cells.items()):
        for strategy in STRATEGIES: aggregates.append({'customers':customers,'dynamism':dynamism,'strategy':strategy,'metrics':{metric:descriptive([triple[strategy].get(metric,0.) for _,triple in triples]) for metric in METRICS}})
        samples=[[triple[strategy]['total_distance'] for _,triple in triples] for strategy in STRATEGIES]
        try: fstat,fp=friedmanchisquare(*samples)
        except ValueError: fstat,fp=0.,1.
        comparisons=[]
        for left,right in ((0,1),(0,2),(1,2)):
            difference=np.asarray(samples[left])-np.asarray(samples[right]); zero=not np.any(difference); stat,p=(0.,1.) if zero else wilcoxon(difference,zero_method='pratt'); comparisons.append({'comparison':f'{STRATEGIES[left]}-{STRATEGIES[right]}','mean_difference':float(difference.mean()),'bootstrap_ci95':bootstrap(difference.tolist()),'effect_size':float(difference.mean()/difference.std(ddof=1)) if len(difference)>1 and difference.std(ddof=1)>0 else 0.,'wilcoxon_statistic':float(stat),'wilcoxon_p':float(p),'note':'no difference: all paired differences are 0' if zero else None})
        ordered=sorted(comparisons,key=lambda value:value['wilcoxon_p']); count=len(ordered)
        for rank,value in enumerate(ordered): value['holm_p']=min(1.,value['wilcoxon_p']*(count-rank)); value['holm_reject']=value['holm_p']<.05
        paired.append({'customers':customers,'dynamism':dynamism,'n':len(triples),'friedman':{'statistic':float(fstat),'p_value':float(fp)},'comparisons':comparisons})
    return {'generated_at':utcnow(),'source_experiment':batch,'note':'Small n: treat as descriptive if n < 10.','config':{'customers':sorted({k[0] for k in complete}),'dynamism':sorted({k[1] for k in complete}),'strategies':STRATEGIES,'seeds':sorted({k[2] for k in complete})},'aggregated':aggregates,'paired_comparisons':paired,'demo_scenarios':demo_scenarios()}
