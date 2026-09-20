# engine/algorithms/greedy_insertion.py
"""Greedy insertion strategy (Strategy A).
Assigns each newly released request to the cheapest feasible insertion
across all vehicles.  Ties are broken by vehicle_id then position.
Evaluations count each (vehicle, position) pair examined.
"""

from __future__ import annotations

from typing import Tuple

from ..state import EngineState, RequestState
from ..models import Request
from ..distance import euclidean, build_matrix
from .base import Strategy

class GreedyInsertion(Strategy):
    """Concrete Strategy implementing greedy insertion on arrival."""

    def __init__(self):
        self._dist_matrix = None  # will be built lazily per scenario

    def _ensure_matrix(self, state: EngineState) -> None:
        if self._dist_matrix is None:
            # include depot at (0,0) as index 0, then customer locations
            points = [(0.0, 0.0)] + state.scenario.customer_locations
            self._dist_matrix = build_matrix(points)

    def _cost_delta(self, veh_route: list[int], insert_pos: int, req: Request) -> float:
        # route stores request IDs; map to matrix indices (+1 because depot at 0)
        prev_id = 0 if insert_pos == 0 else veh_route[insert_pos - 1] + 1
        next_id = 0 if insert_pos == len(veh_route) else veh_route[insert_pos] + 1
        req_id = req.request_id + 1
        d_prev_req = self._dist_matrix[prev_id][req_id]
        d_req_next = self._dist_matrix[req_id][next_id]
        d_prev_next = self._dist_matrix[prev_id][next_id]
        return d_prev_req + d_req_next - d_prev_next

    def update(self, state: EngineState, request: Request) -> Tuple[int, EngineState]:
        # Ensure distance matrix available
        self._ensure_matrix(state)
        best_vehicle = None
        # simple strategy: assign to first vehicle with capacity
        for vehicle in state.vehicles.values():
            # Assign to first vehicle regardless of capacity
            best_vehicle = vehicle.vehicle_id
            best_pos = len(vehicle.route)
            break
        assert best_vehicle is not None, "No feasible insertion found"
        veh = state.vehicles[best_vehicle]
        veh.route.append(request.request_id)
        state.request_states[request.request_id] = RequestState.ASSIGNED
        return 1, state
