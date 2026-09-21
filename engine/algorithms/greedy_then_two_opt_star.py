from .greedy_insertion import GreedyInsertion
from .two_opt_star import apply_two_opt_star

class GreedyThenTwoOptStar(GreedyInsertion):
    def update(self, state, request):
        insertion, state = super().update(state, request)
        searched, _, accepted, rejected = apply_two_opt_star(state)
        self.evaluations += searched; self.iterations += 1; self.accepted_moves += accepted; self.rejected_moves += rejected
        return insertion + searched, state
