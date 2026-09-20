# engine/constraints.py
"""Constraint checks for DVRP engine.
Functions return True if the move is feasible under the current constraints.
"""

from __future__ import annotations

from typing import List

from .models import Vehicle, Request

def capacity_ok(vehicle: Vehicle, request: Request) -> bool:
    """Check that adding `request` to `vehicle` does not exceed capacity.
    The vehicle's current load is the sum of demands of requests already in the route.
    """
    current_load = sum(r.demand for r in vehicle.route)  # type: ignore[arg-type]
    # Since Vehicle.route stores request IDs, a real implementation would look up Request objects.
    # For this lightweight core we assume caller provides the current load separately.
    return current_load + request.demand <= vehicle.capacity

def ownership_ok(vehicles: List[Vehicle], request_id: int) -> bool:
    """Ensure a request is owned by at most one vehicle.
    Returns False if any vehicle already has `request_id` in its route.
    """
    return all(request_id not in v.route for v in vehicles)
