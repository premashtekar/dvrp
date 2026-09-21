"""Deterministic Tabu repair with a fixed candidate budget per replan event."""
from __future__ import annotations
from collections import deque
from .greedy_insertion import GreedyInsertion
from .two_opt_star import evaluate_two_opt_star
from ..distance import build_matrix

class TabuSearch(GreedyInsertion):
    def __init__(self, tenure: int = 7, evaluation_budget: int = 500):
        super().__init__(); self.tenure=tenure; self.tabu_budget=evaluation_budget; self.tabu_evaluations=0; self.tabu=deque(maxlen=tenure); self.improving_moves_found=0
    def _cost(self,state,route):
        matrix=getattr(state,'_distance_matrix',None)
        if matrix is None: matrix=build_matrix([(0.,0.)]+state.scenario.customer_locations); state._distance_matrix=matrix
        nodes=[0]+[r+1 for r in route]+[0]; return sum(matrix[a][b] for a,b in zip(nodes,nodes[1:]))
    def improve(self,state):
        """Search and apply improving inter-route tail swaps within one event budget."""
        used=0
        while used < self.tabu_budget:
            best=None
            for a in sorted(state.vehicles):
                for b in sorted(state.vehicles):
                    if a==b: continue
                    ra,rb=state.vehicles[a].route,state.vehicles[b].route
                    for sa in range(1,len(ra)+1):
                        for sb in range(1,len(rb)+1):
                            if used>=self.tabu_budget: break
                            used+=1; self.evaluations+=1; self.tabu_evaluations+=1
                            feasible,delta,na,nb=evaluate_two_opt_star(state,a,b,sa,sb); move=(delta,a,b,na,nb)
                            if feasible and (a,b,sa,sb) not in self.tabu and (best is None or move[0]<best[0]): best=move
                        if used>=self.tabu_budget: break
                    if used>=self.tabu_budget: break
                if used>=self.tabu_budget: break
            if best is None or best[0]>=-1e-12: self.rejected_moves+=1; break
            _,a,b,na,nb=best; state.vehicles[a].route,state.vehicles[b].route=na,nb; self.tabu.append((a,b,len(na),len(nb))); self.accepted_moves+=1; self.improving_moves_found+=1; self.iterations+=1
        return used
    def update(self,state,request):
        before=self.evaluations; _,state=super().update(state,request); self.improve(state)
        return self.evaluations-before,state
