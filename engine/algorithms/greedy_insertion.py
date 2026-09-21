from __future__ import annotations

from typing import Tuple

from ..state import EngineState, RequestState
from ..models import Request
from ..distance import euclidean, build_matrix
from .base import Strategy

class GreedyInsertion(Strategy):
    def __init__(self):
        self._dist_matrix = None

    def _ensure_matrix(self, state: EngineState) -> None:
        if self._dist_matrix is None:
            points = [(0.0, 0.0)] + state.scenario.customer_locations
            self._dist_matrix = build_matrix(points)

    def _cost_delta(self, veh_route: list[int], insert_pos: int, req: Request) -> float:
        prev_id = 0 if insert_pos == 0 else veh_route[insert_pos - 1] + 1
        next_id = 0 if insert_pos == len(veh_route) else veh_route[insert_pos] + 1
        req_id = req.request_id + 1
        return self._dist_matrix[prev_id][req_id] + self._dist_matrix[req_id][next_id] - self._dist_matrix[prev_id][next_id]

    def update(self, state: EngineState, request: Request) -> Tuple[int, EngineState]:
        self._ensure_matrix(state)
        best_vehicle = None
        best_pos = None
        best_delta = float('inf')
        evals = 0

        for vehicle in state.vehicles.values():
            # Check capacity
            current_load = sum(state.requests[rid].demand for rid in vehicle.route)
            if current_load + request.demand > vehicle.capacity:
                continue

            for pos in range(len(vehicle.route) + 1):
                evals += 1
                delta = self._cost_delta(vehicle.route, pos, request)
                if delta < best_delta:
                    best_delta = delta
                    best_vehicle = vehicle.vehicle_id
                    best_pos = pos

        if best_vehicle is None:
            # Fallback if no feasible (violating capacity)
            best_vehicle = list(state.vehicles.values())[0].vehicle_id
            best_pos = len(state.vehicles[best_vehicle].route)
            
        state.vehicles[best_vehicle].route.insert(best_pos, request.request_id)
        state.request_states[request.request_id] = RequestState.SERVED
        return evals, state
