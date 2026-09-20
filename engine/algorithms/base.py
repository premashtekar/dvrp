# engine/algorithms/base.py
"""Base classes for DVRP algorithms.
Provides the abstract ``Strategy`` interface used by the simulator.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Tuple

class Strategy(ABC):
    """Abstract strategy for handling a new request.
    Implementations must return the number of evaluated candidate moves and the updated ``EngineState``.
    """

    @abstractmethod
    def update(self, state: "EngineState", request: "Request") -> Tuple[int, "EngineState"]:
        """Process ``request`` given the current ``state``.
        Returns ``(evaluations, new_state)``.
        """
        ...
