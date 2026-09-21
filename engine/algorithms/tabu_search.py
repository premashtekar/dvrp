from __future__ import annotations

from collections import deque
from typing import Deque, List, Tuple

from .base import Strategy
from ..state import EngineState, RequestState
from ..models import Request
from ..distance import build_matrix

class TabuSearch(Strategy):
    def __init__(self, tenure: int = 5, evaluation_budget: int = 1000):
        self.tenure = tenure
        self.evaluation_budget = evaluation_budget
        self.tabu: Deque[Tuple[int, int]] = deque(maxlen=tenure)
        self.evaluations = 0
        self._dist_matrix = None

    def _ensure_matrix(self, state: EngineState) -> None:
        if self._dist_matrix is None:
            points = [(0.0, 0.0)] + state.scenario.customer_locations
            self._dist_matrix = build_matrix(points)

    def _is_tabu(self, request_id: int, vehicle_id: int) -> bool:
        return (request_id, vehicle_id) in self.tabu

    def _add_tabu(self, request_id: int, vehicle_id: int) -> None:
        self.tabu.append((request_id, vehicle_id))

    def _route_cost(self, route: List[int]) -> float:
        if not route: return 0.0
        cost = 0.0
        prev = 0
        for req_id in route:
            cur = req_id + 1
            cost += self._dist_matrix[prev][cur]
            prev = cur
        cost += self._dist_matrix[prev][0]
        return cost

    def _relocate_moves(self, state: EngineState):
        moves = []
        for req_id, req_state in state.request_states.items():
            if req_state != RequestState.SERVED: continue
            from_vid = next((v.vehicle_id for v in state.vehicles.values() if req_id in v.route), None)
            if from_vid is None: continue
            for to_vid, veh in state.vehicles.items():
                if to_vid == from_vid: continue
                for pos in range(len(veh.route) + 1):
                    new_route_from = state.vehicles[from_vid].route.copy()
                    new_route_from.remove(req_id)
                    new_route_to = veh.route.copy()
                    new_route_to.insert(pos, req_id)
                    delta = (self._route_cost(new_route_from) + self._route_cost(new_route_to)) - \
                            (self._route_cost(state.vehicles[from_vid].route) + self._route_cost(veh.route))
                    moves.append(('relocate', req_id, from_vid, to_vid, pos, delta))
        return moves

    def _swap_moves(self, state: EngineState):
        moves = []
        served = [rid for rid, rs in state.request_states.items() if rs == RequestState.SERVED]
        for i in range(len(served)):
            for j in range(i + 1, len(served)):
                r1, r2 = served[i], served[j]
                v1 = next((v.vehicle_id for v in state.vehicles.values() if r1 in v.route), None)
                v2 = next((v.vehicle_id for v in state.vehicles.values() if r2 in v.route), None)
                if v1 is None or v2 is None or v1 == v2: continue
                route1, route2 = state.vehicles[v1].route.copy(), state.vehicles[v2].route.copy()
                idx1, idx2 = route1.index(r1), route2.index(r2)
                route1[idx1], route2[idx2] = r2, r1
                delta = (self._route_cost(route1) + self._route_cost(route2)) - \
                        (self._route_cost(state.vehicles[v1].route) + self._route_cost(state.vehicles[v2].route))
                moves.append(('swap', r1, v1, r2, v2, delta))
        return moves

    def _two_opt_star_moves(self, state: EngineState):
        moves = []
        for vid, veh in state.vehicles.items():
            route = veh.route
            n = len(route)
            if n < 2: continue
            for i in range(n - 1):
                for j in range(i + 1, n):
                    new_route = route[:i] + list(reversed(route[i:j + 1])) + route[j + 1:]
                    delta = self._route_cost(new_route) - self._route_cost(route)
                    moves.append(('2opt', vid, i, j, delta))
        return moves

    def update(self, state: EngineState, request: Request) -> Tuple[int, EngineState]:
        self._ensure_matrix(state)
        assigned = False
        for vehicle in state.vehicles.values():
            if not self._is_tabu(request.request_id, vehicle.vehicle_id):
                state.assign(vehicle.vehicle_id, request.request_id)
                self._add_tabu(request.request_id, vehicle.vehicle_id)
                state.request_states[request.request_id] = RequestState.SERVED
                assigned = True
                break
        if not assigned:
            first_vid = next(iter(state.vehicles))
            state.assign(first_vid, request.request_id)
            self._add_tabu(request.request_id, first_vid)
            state.request_states[request.request_id] = RequestState.SERVED

        while self.evaluations < self.evaluation_budget:
            moves = []
            moves.extend(self._relocate_moves(state)[:5])
            moves.extend(self._swap_moves(state)[:5])
            moves.extend(self._two_opt_star_moves(state)[:5])
            if not moves: break
            best = min(moves, key=lambda m: m[-1])
            delta = best[-1]
            self.evaluations += 1
            if delta >= 0: break

            if best[0] == 'relocate':
                _, req_id, from_vid, to_vid, pos, _ = best
                state.vehicles[from_vid].route.remove(req_id)
                state.vehicles[to_vid].route.insert(pos, req_id)
                self._add_tabu(req_id, to_vid)
            elif best[0] == 'swap':
                _, r1, v1, r2, v2, _ = best
                route1, route2 = state.vehicles[v1].route, state.vehicles[v2].route
                idx1, idx2 = route1.index(r1), route2.index(r2)
                route1[idx1], route2[idx2] = r2, r1
                self._add_tabu(r1, v2)
                self._add_tabu(r2, v1)
            elif best[0] == '2opt':
                _, vid, i, j, _ = best
                route = state.vehicles[vid].route
                route[i:j + 1] = list(reversed(route[i:j + 1]))
                
        return self.evaluations, state
