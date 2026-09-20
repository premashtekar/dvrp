# ADR-002 — Frozen Prefix Rule

**Status:** Accepted  
**Applies to:** simulator, all strategies

## Decision
A moving vehicle's current position and current target are frozen.  
Only stops **after** the current target (the mutable suffix) may be reordered, removed, or have new customers inserted.  
Route repair operates exclusively on mutable suffixes.

## Rationale
A vehicle already committed to a stop cannot be recalled without real-world cost.  
This rule prevents phantom disruption from replanning decisions that are physically impossible.

## Alternatives considered
Full-route replanning (including current target) — rejected; causes infeasible routing in a real system.  
Freeze only the current position — rejected; a vehicle en route to a customer cannot be redirected mid-travel.

## Consequences
Every strategy must check `mutable_suffix(vehicle)` before enumerating insertion positions or 2-opt* moves.  
Unit test: a strategy must never modify `vehicle.current_target`.
