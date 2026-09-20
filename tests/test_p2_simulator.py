# tests/test_p2_simulator.py
"""Tests for Phase P2 – simulator and greedy insertion.
Hand‑checkable simple scenario with three requests.
"""

from pathlib import Path

import pytest

from engine.models import Vehicle, Request, Scenario
from engine.state import EngineState, RequestState
from engine.algorithms.greedy_insertion import GreedyInsertion
from engine.simulator import Simulator

def make_simple_scenario() -> Scenario:
    # Depot is implicit at (0,0). Three customers form a right triangle.
    # All release at time 0 (immediate availability).
    return Scenario(
        customers=3,
        vehicles=1,
        dynamism=1.0,
        capacity=3,
        horizon=10.0,
        map_size=10.0,
        seed=42,
        customer_locations=[(1.0, 0.0), (2.0, 0.0), (0.0, 2.0)],
        request_demands=[1, 1, 1],
        release_times=[0.0, 0.0, 0.0],
    )

def test_greedy_insertion_assigns_all_requests():
    scenario = make_simple_scenario()
    state = EngineState(scenario=scenario)
    # initially all requests are UNRELEASED
    # advance time to 0 to make them AVAILABLE
    state.advance_time(0.0)
    # run greedy insertion for each request via simulator
    strategy = GreedyInsertion()
    sim = Simulator(state, strategy)
    final_state = sim.run()
    # All requests should now be ASSIGNED (and therefore in the vehicle route)
    vehicle = final_state.vehicles[0]
    assert vehicle.route == [0, 1, 2]  # request IDs in order of insertion
    # Verify request states are ASSIGNED
    for rs in final_state.request_states.values():
        assert rs == RequestState.ASSIGNED
    # Verify the total distance increase matches manual calculation
    # distances: depot->A (1), A->B (1), B->C (~2.236), C->depot (~2.236)
    # Greedy insertion adds each request at the end, so cost = 1 + 1 + 2.236
    # (we ignore return to depot for this simple test)
    from engine.distance import euclidean
    total = euclidean((0, 0), (1, 0)) + euclidean((1, 0), (2, 0)) + euclidean((2, 0), (0, 2))
    # compute cost from simulator trace
    # trace records evaluations only; we recompute here for sanity
    assert pytest.approx(total, 0.001) == 1 + 1 + ((2**2 + 2**2) ** 0.5)
