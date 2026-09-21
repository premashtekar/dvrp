from __future__ import annotations
from typing import Tuple
from ..state import EngineState, RequestState
from ..models import Request
from ..distance import build_matrix
from .base import Strategy

class GreedyInsertion(Strategy):
    """Deterministic cheapest feasible insertion; every position costs one evaluation."""
    def __init__(self): self.evaluations = self.iterations = self.accepted_moves = self.rejected_moves = 0; self.evaluation_budget = None
    def update(self, state: EngineState, request: Request) -> Tuple[int, EngineState]:
        matrix = build_matrix([(0.0, 0.0)] + state.scenario.customer_locations); best = None; count = 0
        for vid in sorted(state.vehicles):
            route = state.vehicles[vid].route
            if sum(state.requests[x].demand for x in route) + request.demand > state.vehicles[vid].capacity: continue
            for pos in range(len(route) + 1):
                if self.evaluation_budget is not None and self.evaluations + count >= self.evaluation_budget: break
                count += 1; left, right = (0 if pos == 0 else route[pos-1]+1), (0 if pos == len(route) else route[pos]+1)
                candidate = (matrix[left][request.request_id+1] + matrix[request.request_id+1][right] - matrix[left][right], vid, pos)
                if best is None or candidate < best: best = candidate
            if self.evaluation_budget is not None and self.evaluations + count >= self.evaluation_budget: break
        self.evaluations += count; self.iterations += 1
        if best is None: self.rejected_moves += 1; return count, state
        _, vid, pos = best; state.vehicles[vid].route.insert(pos, request.request_id); state.request_states[request.request_id] = RequestState.ASSIGNED; self.accepted_moves += 1
        return count, state
