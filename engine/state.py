# engine/state.py
"""Central state machine for DVRP.
Tracks vehicles, requests, and request states.
All state transitions are deterministic given the same RNG streams.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List

from .models import Vehicle, Request, Scenario

class RequestState(Enum):
    UNRELEASED = auto()
    AVAILABLE = auto()
    ASSIGNED = auto()
    IN_SERVICE = auto()
    SERVED = auto()

@dataclass
class EngineState:
    """Holds mutable simulation state.
    Vehicles and requests are stored by ID for O(1) lookup.
    """
    scenario: Scenario
    vehicles: Dict[int, Vehicle] = field(default_factory=dict)
    requests: Dict[int, Request] = field(default_factory=dict)
    request_states: Dict[int, RequestState] = field(default_factory=dict)
    current_time: float = 0.0

    def __post_init__(self) -> None:
        # initialise vehicles
        for vid in range(self.scenario.vehicles):
            self.vehicles[vid] = Vehicle(vehicle_id=vid, capacity=self.scenario.capacity)
        # initialise requests (IDs 0..customers-1)
        for rid, (loc, dem, rel) in enumerate(
            zip(self.scenario.customer_locations, self.scenario.request_demands, self.scenario.release_times)
        ):
            req = Request(request_id=rid, location=loc, demand=dem, release_time=rel)
            self.requests[rid] = req
            self.request_states[rid] = RequestState.UNRELEASED

    def advance_time(self, t: float) -> None:
        """Advance simulation clock; release any requests whose release_time <= t."""
        self.current_time = t
        for rid, req in self.requests.items():
            if self.request_states[rid] == RequestState.UNRELEASED and req.release_time <= t:
                self.request_states[rid] = RequestState.AVAILABLE

    def assign(self, vehicle_id: int, request_id: int) -> None:
        """Assign a request to a vehicle (AVAILABLE -> ASSIGNED)."""
        assert self.request_states[request_id] == RequestState.AVAILABLE
        veh = self.vehicles[vehicle_id]
        veh.route.append(request_id)
        self.request_states[request_id] = RequestState.ASSIGNED

    def serve(self, request_id: int) -> None:
        """Mark request as SERVED (after completion)."""
        assert self.request_states[request_id] == RequestState.IN_SERVICE
        self.request_states[request_id] = RequestState.SERVED
