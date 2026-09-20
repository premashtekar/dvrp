# ADR-004 — Simulation Clock Independence

**Status:** Accepted  
**Applies to:** simulator, metrics

## Decision
The simulation clock is independent of wall-clock compute time.  
Planning is **instantaneous** in simulated time.  
Compute cost is measured separately using `perf_counter_ns` and reported in milliseconds.  
A "latency-coupled" mode (where compute time delays the routing decision) is a future flag and is not built now.

## Rationale
Decoupling the clock makes results reproducible across machines with different speeds.  
Mixing simulated time and compute time would conflate algorithm quality with hardware capability.

## Alternatives considered
Latency-coupled mode now — rejected; breaks reproducibility and is not needed for the core DAA question.

## Consequences
Response time is measured as the algorithm runtime only (from before `strategy.update()` to after it returns).  
Dashboard rendering time and experiment setup time are excluded from response_time_ms.  
Worker count is stored in every experiment row.
