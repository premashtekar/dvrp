"""Budgeted deterministic Tabu repair using relocate candidates."""
from __future__ import annotations
from collections import deque
from .greedy_insertion import GreedyInsertion
from ..distance import build_matrix

class TabuSearch(GreedyInsertion):
    def __init__(self, tenure: int = 7, evaluation_budget: int = 500):
        super().__init__(); self.tenure = tenure; self.evaluation_budget = evaluation_budget; self.tabu = deque(maxlen=tenure)
    def _cost(self, state, route):
        matrix = getattr(state, "_distance_matrix", None)
        if matrix is None:
            matrix = build_matrix([(0., 0.)] + state.scenario.customer_locations); state._distance_matrix = matrix
        nodes = [0] + [r+1 for r in route] + [0]
        return sum(matrix[a][b] for a, b in zip(nodes, nodes[1:]))
    def update(self, state, request):
        before = self.evaluations; _, state = super().update(state, request)
        while self.evaluations < self.evaluation_budget:
            best = None
            for a in sorted(state.vehicles):
                for rid in list(state.vehicles[a].route):
                    for b in sorted(state.vehicles):
                        if a == b: continue
                        ra, rb = state.vehicles[a].route, state.vehicles[b].route
                        if sum(state.requests[x].demand for x in rb) + state.requests[rid].demand > state.vehicles[b].capacity: continue
                        for pos in range(len(rb) + 1):
                            if self.evaluations >= self.evaluation_budget: break
                            self.evaluations += 1; na=[x for x in ra if x != rid]; nb=rb.copy(); nb.insert(pos,rid)
                            delta=self._cost(state,na)+self._cost(state,nb)-self._cost(state,ra)-self._cost(state,rb); move=(delta,rid,a,b,na,nb)
                            if ((rid,b) not in self.tabu or delta < -1e-12) and (best is None or move < best): best=move
                        if self.evaluations >= self.evaluation_budget: break
                    if self.evaluations >= self.evaluation_budget: break
                if self.evaluations >= self.evaluation_budget: break
            if best is None or best[0] >= -1e-12: self.rejected_moves += 1; break
            _,rid,a,b,na,nb=best; state.vehicles[a].route,state.vehicles[b].route=na,nb; self.tabu.append((rid,b)); self.accepted_moves += 1; self.iterations += 1
        return self.evaluations-before, state
