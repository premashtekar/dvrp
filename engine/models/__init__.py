# engine/models/__init__.py
"""Data model definitions for DVRP engine.
Contains dataclasses for Vehicle, Request, and Scenario.
All classes are plain Python; only `Vehicle` is mutable (routes are updated during simulation).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple, Optional

# Basic types
Point = Tuple[float, float]

@dataclass
class Vehicle:
    """Mutable vehicle object used by the simulator.
    ``route`` stores request IDs in the mutable suffix of the route.
    """
    vehicle_id: int
    capacity: int
    position: Optional[Point] = None  # None means at depot (0,0) before dispatch
    route: List[int] = field(default_factory=list)

@dataclass(frozen=True)
class Request:
    request_id: int
    location: Point
    demand: int
    release_time: float  # simulated time when request becomes AVAILABLE

@dataclass
class Scenario:
    """Immutable scenario description used to generate deterministic runs.
    Includes seeded RNG streams for reproducibility.
    """
    customers: int
    vehicles: int
    dynamism: float
    capacity: int
    horizon: float
    map_size: float
    seed: int
    # Derived fields populated by helper functions
    customer_locations: List[Point] = field(default_factory=list)
    request_demands: List[int] = field(default_factory=list)
    release_times: List[float] = field(default_factory=list)

    def __post_init__(self) -> None:
        assert 0.0 <= self.dynamism <= 1.0, "Dynamism must be between 0 and 1"
        assert self.customers > 0 and self.vehicles > 0
