import copy
import math
import pytest
from engine.models import Scenario
from engine.state import EngineState
from engine.algorithms.greedy_insertion import GreedyInsertion
from engine.algorithms.tabu_search import TabuSearch
from engine.algorithms.two_opt_star import two_opt_star_move
from engine.simulator import Simulator
from engine.scenarios import generate_scenario

def scenario(points, demands=None, capacity=10):
    return Scenario(len(points), 2, 0.0, capacity, 10., 10., 7, points, demands or [1]*len(points), [0.]*len(points))

def test_insertion_handcheck():
    state=EngineState(scenario([(1.,0.),(2.,0.),(0.,2.)])); state.vehicles[0].route=[0,1]
    strategy=GreedyInsertion(); strategy._dist_matrix=None
    # D-A-B-D is 4; inserting C at the end is 2*sqrt(2) more.
    from engine.distance import euclidean
    total=euclidean((0,0),(1,0))+euclidean((1,0),(2,0))+euclidean((2,0),(0,2))+euclidean((0,2),(0,0))
    assert total == pytest.approx(6.8284271247, abs=1e-6)

def test_two_opt_star_handcheck_and_capacity_rejection():
    state=EngineState(scenario([(1.,1.),(5.,-1.),(1.,-1.),(5.,1.)])); state.vehicles[0].route=[0,1]; state.vehicles[1].route=[2,3]
    from engine.algorithms.two_opt_star import _cost
    assert _cost(state,state.vehicles[0].route)+_cost(state,state.vehicles[1].route) == pytest.approx(21.9707381, abs=1e-6)
    accepted, delta=two_opt_star_move(state,0,1,1,1)
    assert accepted and delta == pytest.approx(-0.94427191, abs=1e-6)
    assert _cost(state,state.vehicles[0].route)+_cost(state,state.vehicles[1].route) == pytest.approx(21.0264662, abs=1e-6)
    state=EngineState(scenario([(1.,1.),(5.,-1.),(1.,-1.),(5.,1.)],[2,2,2,2],3)); state.vehicles[0].route=[0,1]; state.vehicles[1].route=[2,3]
    assert two_opt_star_move(state,0,1,1,1)[0] is False

def test_tabu_never_exceeds_budget():
    state=EngineState(scenario([(float(i),0.) for i in range(5)])); state.vehicles[0].route=[0,1]; state.vehicles[1].route=[2,3]
    tabu=TabuSearch(evaluation_budget=8); tabu.improve(state)
    assert tabu.tabu_evaluations <= 8

def test_tabu_repairs_crossing_routes():
    state=EngineState(scenario([(1.,1.),(5.,-1.),(1.,-1.),(5.,1.)])); state.vehicles[0].route=[0,1]; state.vehicles[1].route=[2,3]
    tabu=TabuSearch(evaluation_budget=500); tabu.improve(state)
    from engine.algorithms.two_opt_star import _cost
    assert _cost(state,state.vehicles[0].route)+_cost(state,state.vehicles[1].route) <= 21.0265
    assert tabu.accepted_moves >= 1

def test_same_seed_and_config_same_result():
    config={'scenario':{'customers':8,'vehicles':2,'capacity':20,'dynamism':.4,'map_size':10.,'horizon':20.}}
    outcomes=[]
    for _ in range(2):
        state=EngineState(generate_scenario(config,9)); outcomes.append((Simulator(state,GreedyInsertion()).run().vehicles,))
    assert outcomes[0] == outcomes[1]
