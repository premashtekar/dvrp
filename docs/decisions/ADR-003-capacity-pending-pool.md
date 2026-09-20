# ADR-003 — Capacity and Pending Pool

**Status:** Accepted  
**Applies to:** constraints, state machine, all strategies

## Decision
The load of a vehicle's current trip must remain ≤ capacity at all times.  
An idle vehicle at the depot may start a new trip (multi-trip, single depot).  
If no feasible insertion exists for a released request, it stays AVAILABLE in the **pending pool**  
and is retried when a vehicle returns to the depot or on the next replanning event.  
Reported metrics: `pending_wait` (time in pool), `unserved` (requests never served by simulation end).

## Rationale
Strict capacity prevents phantom feasibility; the pending pool avoids silent request loss.  
Reporting waiting time and unserved count makes the capacity interaction visible for analysis.

## Alternatives considered
Pre-emptive request rejection — rejected; loses information and misrepresents real courier behaviour.  
Overflow route (new vehicle) — out of scope (fixed fleet size).

## Consequences
State machine must atomically assign a vehicle to a request.  
Unit test: an over-capacity insertion must be rejected and the request added to the pending pool.
