"""Refresh only replay traces; aggregate result values remain untouched."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from engine.models import Scenario
from engine.algorithms.greedy_insertion import GreedyInsertion
from engine.algorithms.greedy_then_two_opt_star import GreedyThenTwoOptStar
from engine.algorithms.tabu_search import TabuSearch
from engine.simulator import Simulator
from engine.state import EngineState

path=Path('web/public/demo/results.json'); data=json.loads(path.read_text(encoding='utf8'))
for demo in data['demo_scenarios']:
    payload=demo['scenario']; locations=[tuple(point) for point in payload['customers']]; rng=np.random.default_rng(1); generated_locations=[(float(rng.uniform(0,100)),float(rng.uniform(0,100))) for _ in locations]; demands=[int(rng.integers(1,11)) for _ in locations]; releases=[]
    for _ in locations: releases.append(float(rng.uniform(0,288)) if rng.random()<payload['dynamism'] else 0.)
    assert generated_locations==locations and releases==payload['release_times']
    scenario=Scenario(customers=len(locations),vehicles=5,dynamism=payload['dynamism'],capacity=100,horizon=480.,map_size=100.,seed=1,customer_locations=locations,request_demands=demands,release_times=releases)
    traces={}
    for name in ('greedy_insertion','insertion_2opt_star','tabu_search'):
        strategy={'greedy_insertion':GreedyInsertion,'insertion_2opt_star':GreedyThenTwoOptStar,'tabu_search':lambda:TabuSearch(evaluation_budget=500)}[name]()
        simulator=Simulator(EngineState(scenario),strategy); simulator.run(); traces[name]=simulator.trace
    demo['traces']=traces
path.write_text(json.dumps(data,indent=2),encoding='utf8')
