# PROJECT_SPEC.md — Adaptive Route Repair for Dynamic Last-Mile Delivery

## Problem
A depot dispatches identical capacitated vehicles. Delivery requests arrive both at the start and
dynamically during execution. When a new request is released, the routing system must decide how to
update existing routes — trading off **route quality**, **computation time**, and **route disruption**.

## Research Questions (RQ1–RQ5)
RQ1: Is greedy insertion sufficient at low dynamism?  
RQ2: When does 2-opt* local repair give a worthwhile gain over greedy?  
RQ3: When does periodic strong re-optimization justify its compute cost?  
RQ4: How much disruption does each strategy introduce?  
RQ5: Can an interpretable adaptive policy select the right strategy?

## Formal Model
- **Instance**: one depot, N customers (x, y, demand, release_time), V identical vehicles (capacity K).
- **Dynamism** Ω = dynamic requests / total requests (Larsen). Levels: 0.1, 0.2, 0.4, 0.6, 0.8.
- **Dynamic release times**: drawn from U(0, 0.6·H), seeded separately from the scenario.
- **Distance**: Euclidean, one cached matrix per scenario, shared by all strategies.
- **Objective**: minimize total travel distance subject to capacity, single-ownership, and release-time constraints.
- **Request lifecycle**: UNRELEASED → AVAILABLE → ASSIGNED → IN_SERVICE → SERVED.
- **Frozen prefix**: only stops after a vehicle's current target are mutable.
- **Pending pool**: infeasible requests wait AVAILABLE until retry.
- **Simulation clock**: independent of compute time (planning is instantaneous in simulated time).

## Strategies
| ID | Name | On arrival | Periodic |
|----|------|-----------|---------|
| A | Greedy Insertion | Cheapest feasible position across all vehicles | — |
| B | Insertion + 2-opt* | A then 2-opt* on affected routes | — |
| C | Periodic Tabu | A on arrival + Tabu Search every Δ arrivals | Relocate / swap / 2-opt* |
| D | Adaptive Selector | Chooses A/B/C from state features (built in P8) | — |

## Metrics
Per run: `total_distance`, `avg/max response_time_ms`, `route_disruption` (raw + normalized), `feasibility_violations`, `served`, `unserved`, `pending_wait`, `n_route_updates`, `evaluations`, `iterations`, `accepted/rejected_moves`, `phase_timings` (insertion, 2-opt*, tabu), `CPU_time`, `distance_before/after_repair`.

## Experiment Design
- **Factor matrix**: 5 dynamism × 3 customer counts × 3 strategies × 10 seeds = 450 pilot runs.
- **Fairness**: each scenario generated once; all strategies run on a deep copy with identical initial solution, seeds, budget.
- **Budgets** (evaluation limits): greedy ≤ 1000, 2-opt* ≤ 5000, tabu ≤ 10000 (configurable).
- **Tuning seeds** (1001–1030) are disjoint from **evaluation seeds** (1–30).
- **Storage**: raw per-run rows in SQLite (never overwritten) + CSV/JSON export; aggregates separate.

## Statistics
Paired data (same seeds per strategy). Omnibus: Friedman. Pairwise: Wilcoxon signed-rank + Holm correction. Effect sizes + bootstrap CIs. Each (customers, dynamism) cell is its own test family (α = 0.05 post-correction).

## Known Limitations
Synthetic Euclidean demand; single depot; identical vehicles; instantaneous planning; no traffic or uncertainty; evaluation-count budgets are deterministic but machine-specific runtime may differ. B and C differ by more than one factor (documented confound).

## Architecture
`engine/` (Python, no web) → `api/` (FastAPI + SQLite) → `web/` (Vite + React + TS + Three.js).  
The simulator knows only the `Strategy` interface: `update(state, event, budget) → UpdateResult`.  
Algorithms never touch the API or UI. Metrics are independent of visualization.
