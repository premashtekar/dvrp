# engine/algorithms/greedy_then_two_opt_star.py
"""Wrapper strategy for insertion_2opt_star.

The B strategy should first perform the greedy insertion (the same as
`GreedyInsertion`) and then, after the simulation, the runner will call
`apply_two_opt_star`.  The class does not need to implement any additional
logic – it simply inherits from `GreedyInsertion` so that the type name
reflects the intended strategy.
"""

from .greedy_insertion import GreedyInsertion


class GreedyThenTwoOptStar(GreedyInsertion):
    """Alias for the B strategy.

    No extra behaviour is required because the experiment runner invokes
    ``apply_two_opt_star`` independently when ``strategy == "insertion_2opt_star"``.
    """

    pass
