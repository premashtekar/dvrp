# engine/algorithms/two_opt_star.py
"""2‑opt* (tail‑exchange) algorithm.
Implements the move that swaps the mutable suffixes of two routes
and accepts the move if it improves total distance and respects capacity.
Used by Strategy B after a greedy insertion.
"""

from __future__ import annotations

from typing import Tuple, List

from ..state import EngineState
from ..distance import build_matrix, euclidean
from ..models import Vehicle, Request

def two_opt_star_move(state: EngineState, veh_i_id: int, veh_j_id: int, split_i: int, split_j: int) -> Tuple[bool, float]:
    """Attempt a tail‑exchange between two vehicles.
    ``split_i``/``split_j`` are the indices *after* which the suffix is taken.
    Returns ``(accepted, delta)`` where ``delta`` is the change in total distance
    (negative means improvement).  The state is mutated only if the move is accepted.
    """
    veh_i = state.vehicles[veh_i_id]
    veh_j = state.vehicles[veh_j_id]
    # compute loads of prefixes
    prefix_i = veh_i.route[:split_i]
    suffix_i = veh_i.route[split_i:]
    prefix_j = veh_j.route[:split_j]
    suffix_j = veh_j.route[split_j:]
    # compute load after swap
    load_i = sum(state.requests[rid].demand for rid in prefix_i + suffix_j)
    load_j = sum(state.requests[rid].demand for rid in prefix_j + suffix_i)
    if load_i > veh_i.capacity or load_j > veh_j.capacity:
        return False, 0.0
    # build distance matrix (including depot at index 0)
    points = [(0.0, 0.0)] + state.scenario.customer_locations
    dist = build_matrix(points)
    def route_cost(route: List[int]) -> float:
        if not route:
            return 0.0
        # start from depot (0)
        cost = dist[0][route[0] + 1]
        for a, b in zip(route, route[1:]):
            cost += dist[a + 1][b + 1]
        # return to depot (optional, not counted here)
        return cost
    old_cost = route_cost(veh_i.route) + route_cost(veh_j.route)
    new_route_i = prefix_i + suffix_j
    new_route_j = prefix_j + suffix_i
    new_cost = route_cost(new_route_i) + route_cost(new_route_j)
    delta = new_cost - old_cost
    if delta < 0:
        # accept move
        veh_i.route = new_route_i
        veh_j.route = new_route_j
        return True, delta
    return False, delta

def apply_two_opt_star(state: EngineState) -> Tuple[int, float]:
    """Search all pairwise tail‑exchanges and apply the best improving move.
    Returns ``(evaluations, total_delta)``.
    """
    evals = 0
    total_delta = 0.0
    veh_ids = list(state.vehicles.keys())
    for i in range(len(veh_ids)):
        for j in range(i + 1, len(veh_ids)):
            vi = state.vehicles[veh_ids[i]]
            vj = state.vehicles[veh_ids[j]]
            # try all split points (including after first element up to len)
            for split_i in range(1, len(vi.route) + 1):
                for split_j in range(1, len(vj.route) + 1):
                    evals += 1
                    accepted, delta = two_opt_star_move(state, veh_ids[i], veh_ids[j], split_i, split_j)
                    if accepted:
                        total_delta += delta
    return evals, total_delta
