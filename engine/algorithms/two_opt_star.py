"""Capacity-feasible inter-route 2-opt* tail exchanges."""
from __future__ import annotations
from typing import Tuple
from ..state import EngineState
from ..distance import build_matrix

def _cost(state: EngineState, route: list[int]) -> float:
    matrix = build_matrix([(0.0, 0.0)] + state.scenario.customer_locations)
    nodes = [0] + [rid + 1 for rid in route] + [0]
    return sum(matrix[a][b] for a, b in zip(nodes, nodes[1:]))

def evaluate_two_opt_star(state: EngineState, a: int, b: int, split_a: int, split_b: int) -> tuple[bool, float, list[int], list[int]]:
    ra, rb = state.vehicles[a].route, state.vehicles[b].route
    na, nb = ra[:split_a] + rb[split_b:], rb[:split_b] + ra[split_a:]
    if sum(state.requests[r].demand for r in na) > state.vehicles[a].capacity or sum(state.requests[r].demand for r in nb) > state.vehicles[b].capacity:
        return False, 0.0, na, nb
    return True, _cost(state, na) + _cost(state, nb) - _cost(state, ra) - _cost(state, rb), na, nb

def two_opt_star_move(state: EngineState, veh_i_id: int, veh_j_id: int, split_i: int, split_j: int) -> Tuple[bool, float]:
    feasible, delta, na, nb = evaluate_two_opt_star(state, veh_i_id, veh_j_id, split_i, split_j)
    if feasible and delta < -1e-12:
        state.vehicles[veh_i_id].route, state.vehicles[veh_j_id].route = na, nb
        return True, delta
    return False, delta

def apply_two_opt_star(state: EngineState, budget: int | None = None) -> Tuple[int, float, int, int]:
    best = None; evaluations = 0; ids = sorted(state.vehicles)
    for index, a in enumerate(ids):
        for b in ids[index + 1:]:
            for sa in range(1, len(state.vehicles[a].route) + 1):
                for sb in range(1, len(state.vehicles[b].route) + 1):
                    if budget is not None and evaluations >= budget: break
                    evaluations += 1; feasible, delta, na, nb = evaluate_two_opt_star(state, a, b, sa, sb)
                    if feasible and delta < -1e-12 and (best is None or delta < best[0]): best = (delta, a, b, na, nb)
                if budget is not None and evaluations >= budget: break
            if budget is not None and evaluations >= budget: break
        if budget is not None and evaluations >= budget: break
    if best is None: return evaluations, 0.0, 0, evaluations
    delta, a, b, na, nb = best; state.vehicles[a].route, state.vehicles[b].route = na, nb
    return evaluations, delta, 1, evaluations - 1
