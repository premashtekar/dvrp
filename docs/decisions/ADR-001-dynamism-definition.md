# ADR-001 — Dynamism Definition and Levels

**Status:** Accepted  
**Applies to:** scenario generation, experiment matrix

## Decision
Dynamism Ω = dynamic_requests / total_requests (Larsen's degree of dynamism).  
Levels: 0.1, 0.2, 0.4, 0.6, 0.8.  
Dynamic release times ~ U(0, 0.6·H) drawn from a seeded RNG stream separate from the scenario stream,  
where H is the shift horizon in the YAML config.

## Rationale
Larsen's definition is standard in DVRP literature (also used by Costa et al. 2025).  
U(0, 0.6·H) concentrates arrivals in the first 60% of the shift, matching realistic delivery windows.  
Separate RNG streams ensure an algorithm's randomness does not perturb the scenario.

## Alternatives considered
Time-window tightness as a dynamism proxy — rejected (adds scope, changes problem class).

## Consequences
Every experiment row must record Ω and the arrival stream seed.  
The same fraction can be harder or easier depending on arrival timing, so the arrival model is logged.
