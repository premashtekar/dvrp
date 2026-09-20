# DVRP Research Lab — Workspace Rules (always-on)

Save as `AGENTS.md` or an Antigravity workspace rule. The agent reads this every session. Do not re-paste it into chats.

## 1. Mission
Build a reproducible research platform (Python engine + FastAPI backend + 3D web UI) that compares route-update strategies for the **Dynamic Vehicle Routing Problem (DVRP)** in last-mile delivery.

Question: when new delivery requests arrive while vehicles are already en route, how should routes be updated, trading off **route quality vs computation time vs route disruption**, under different dynamism levels and compute budgets?

Priority order: correctness > reproducibility > fair comparison > measured compute cost > UI polish. The UI must look outstanding, but it may only display real engine output.

## 2. Claims and integrity
- DVRP, greedy insertion, 2-opt, 2-opt*, Tabu Search and adaptive routing are established. Never claim to have invented them. The contribution is a controlled, budget-aware comparison plus an optional, evidence-derived, interpretable strategy selector.
- Never fabricate, hardcode or mock results, charts or metrics. Unfinished features display "Not implemented". No buttons that pretend to work.
- Never declare a "best algorithm". Show factual numbers with n, units and uncertainty. Report results that contradict hypotheses H1–H4.
- Do not tune seeds, parameters, metrics or stopping rules until a result looks good. Save every config; log every change to it.
- **Identity:** no personal, team, student or instructor names anywhere in UI, README, package metadata, footers, docs or commits you author. Use the product name only.

## 3. Locked stack
- `engine/`: Python 3.11+, NumPy, stdlib. **No web imports.**
- `api/`: FastAPI, Pydantic, SQLite (stdlib `sqlite3`), SSE for progress and streaming.
- `web/`: Vite, React, TypeScript (strict), Tailwind, three.js via react-three-fiber + drei + postprocessing, Recharts for charts.
- Tooling: pytest, ruff, YAML configs. Any extra dependency needs a one-line justification (scikit-learn is allowed only for a shallow decision tree in the selector).
- Out of scope: map tiles or APIs, GPS, traffic, RL or neural nets, drones, multi-depot, heterogeneous fleets, pickup-and-delivery, auth, payments, weather.

```
engine/ models, distance, constraints, state, events, simulator, scenarios,
        algorithms/{initial,greedy_insertion,two_opt_star,tabu,adaptive},
        metrics/, experiments/{runner,config,aggregation}, stats/
api/    routes, jobs, db, schemas
web/    app shell, scene3d/, charts/, pages/
configs/  data/{runs.db,exports}  docs/{PROJECT_SPEC.md,STATUS.md,decisions/}  tests/
```

Layer rules:
- The simulator knows only the `Strategy` interface: `update(state, event, budget) -> UpdateResult`.
- Algorithms never touch the API or UI.
- Metrics never depend on visualization.
- The runner orchestrates and contains no algorithm logic.
- The frontend renders API data only and contains no research logic.

## 4. Locked model decisions (defaults; owner may change, then record an ADR)
1. **Terminology:** 2-opt is intra-route. 2-opt* exchanges route tails between different routes. Never conflate them.
2. **Dynamism** = fraction of requests with release_time > 0 (Larsen's degree of dynamism). Levels: 0.1, 0.2, 0.4, 0.6, 0.8. Dynamic release times ~ U(0, 0.6·H) from a seeded stream, where H is the shift horizon in config.
3. **Distance:** Euclidean, one module, one cached matrix per scenario, used by every strategy.
4. **Frozen prefix:** a moving vehicle's current position and current target are frozen. Only stops after the current target are mutable. Repair operates on mutable suffixes only.
5. **Capacity:** the load of a vehicle's current trip must stay ≤ capacity. An idle vehicle at the depot may start a new trip. If no feasible insertion exists, the request waits in a **pending pool** (state AVAILABLE) and is retried when a vehicle returns or on the next replan. Report waiting time and unserved count.
6. **Request states:** UNRELEASED → AVAILABLE → ASSIGNED → IN_SERVICE → SERVED. Assignment is atomic in one central state. A customer can never be owned by two vehicles.
7. **Simulation clock is independent of compute time** (planning is instantaneous in simulated time). Compute is measured separately. A "latency-coupled" mode is a future flag, not built now.
8. **Budgets:** the primary budget is an **evaluation limit** (deterministic). Wall-clock is recorded and used only as a safety cap, because time limits break reproducibility. Count one evaluation as one candidate move's cost-delta computation. Every strategy gets an explicit, stored budget. Never give one strategy hidden extra compute.
9. **Strategies:**
   - A = greedy insertion on arrival.
   - B = A + 2-opt* on affected routes (first- or best-improvement, configurable, default deterministic).
   - C = A on arrival + periodic Tabu Search every Δ arrivals or sim-time, bounded by an evaluation budget. Neighborhoods: relocate, swap, 2-opt*. Config: tenure, aspiration and stopping rule.
   - D = adaptive selector (built last).
   - Note B and C differ by more than one factor; document this confound.
10. **Route disruption** = edges removed from mutable routes by an update + customers moved between vehicles. Also report it normalized by mutable edges. Insertion alone removes 1 edge; report "excess over insertion minimum". Document in an ADR.
11. **Determinism:** `numpy.random.Generator` seeded via `SeedSequence.spawn`, with separate streams for scenario, arrivals and each algorithm, so an algorithm's randomness never perturbs the scenario. Tie-break by vehicle_id, then position. Never rely on dict or set iteration order. Fixed experiment ordering.
12. **Initial solution:** nearest-neighbor / greedy capacity-aware construction, identical for all strategies.

## 5. Fairness
All strategies in a comparison receive the same scenario, release times, fleet, capacity, initial solution, seeds and budget definition. Generate the scenario once, then run every strategy on a deep copy. Tuning seeds (e.g. 1001–1030) are disjoint from evaluation seeds (e.g. 1–30). Pilot = 10 seeds; final = 30 (configurable). Run timing-sensitive final experiments with 1 worker. State the worker count in metadata.

## 6. Metrics (one engine, no UI dependency)
Per run: total_distance, avg and max response_time_ms (`perf_counter_ns`, algorithm only), route_disruption, feasibility_violations (target 0), served, unserved, pending wait, n_route_updates, evaluations, iterations, accepted and rejected moves, per-phase timings (insertion, 2-opt*, tabu), CPU time, distance before and after repair.

Per update record: chosen vehicle, position, cost delta, candidates evaluated. Store raw per-run rows and never overwrite them. Aggregates go in separate tables. Every row carries experiment_id, scenario hash, seed, strategy, params, budget, dynamism, n_customers, n_vehicles, capacity, code version and timestamp.

## 7. Statistics
Strategies run on the same seeds, so data is **paired**.
- Omnibus for 3+ strategies: Friedman.
- Pairwise: Wilcoxon signed-rank with Holm correction. Do not use Mann-Whitney for paired data.
- Report paired differences with bootstrap CIs and effect sizes, plus mean, SD, SE and 95% CI.
- Each (customers, vehicles, dynamism) cell is its own test family.
- Document the observation unit (scenario × seed), the test, the alpha, the correction and n. State low power honestly when n is small.

## 8. Testing (pytest, required before any phase is "done")
Distance known values; insertion cost math; capacity rejection; single ownership; no service before release; 2-opt* reduces cost on valid moves and rejects capacity-violating ones; simulator event ordering; same seed and config gives an identical scenario and identical results; metrics on known routes; runner produces the correct run count (customers × dynamism × strategies × seeds); frozen-prefix respected. Include a hand-checkable case (depot (0,0), A(1,0), B(2,0), C(0,2)) that prints before and after routes and costs for each algorithm.

## 9. UI spec
**Theme (dark, from the palette):**
- `--bg #0B0F0A`, `--fg #F2FFE9`, `--lime #B4FF39` (primary accent), `--mint #39FF88` (secondary accent).
- Derived tokens: surface `#121912`, surface-2 `#182018`, border `#243024`, muted text `#9DB39A`.
- One danger color `#FF5C5C`, used only for violations and errors.
- Text on lime or mint is `--bg`. Strategy colors: A lime, B mint, C `--fg`, D a derived cyan-mint. Always pair color with line dash or marker so it is not the only cue.
- Type: a geometric sans (e.g. Space Grotesk or Inter) plus JetBrains Mono for numbers.
- Style: serious research instrument. Glassy panels, thin borders, dense but legible. No gaming or "AI" branding.

**3D scene (react-three-fiber):**
- Dark procedural city-grid plane, in the spirit of a dark map with neon routes. No map tiles.
- Depot beacon, instanced customer points, vehicle heads with comet trails.
- Routes are glowing lime and mint lines (bloom) with dash-flow along the travel direction.
- Every animation encodes state. A dynamic request appears as a pulse ring at release. A served customer fades. On replan, removed edges dash-fade and new edges flash.
- Camera presets (top, tilted orbit), bloom toggle, `prefers-reduced-motion` support, 2D fallback if WebGL is unavailable.
- Performance: InstancedMesh, DPR cap, pause when the tab is hidden. Target 60 fps at 200 customers and 10 vehicles.

**Pages:**
1. Overview
2. Scenario Lab (builder + 3D preview)
3. Simulation Replay
4. Compare (2–3 synced viewports on the same scenario, sharing one context via drei `View`)
5. Experiments (configure, run, live progress)
6. Results
7. Methodology (renders docs)

**Replay:** driven by a JSONL event trace and route snapshots or diffs from the engine. Play, pause, 0.25–8× speed, scrubber with arrival ticks, and an event log synced to time. The engine emits the trace; the frontend never simulates.

**Charts (2D, honest):**
- Distance, response time, disruption and compute vs dynamism, faceted by customer count, with CI error bars.
- Quality–compute scatter (x = compute, y = distance, log axis where needed).
- Paired-difference plots.
- Runtime scaling.
- Cumulative distance curve.
- Every chart shows labeled axes, units, n, condition and strategy. Tables export to CSV.

## 10. Working protocol (token discipline)
- Start each session by reading only `RULES.md` and `docs/STATUS.md`, then the files named in the phase prompt. Do not scan the whole repo.
- Do one phase per conversation. Put code in files, not in chat. Do not paste file contents back.
- Do not generate long docs up front. `PROJECT_SPEC.md` stays under about 2 pages, ADRs under about 15 lines each.
- End each phase by running tests quietly, updating `docs/STATUS.md` (≤10 lines: done, next, open issues), and reporting in ≤10 lines.
- Use browser or screenshot verification once per UI phase, at the end.
- Debug root causes: identify whether the fault is in the model, state, event order, algorithm, constraints, metrics or visualization. Fix it, then add a regression test.
- Small meaningful commits (`feat:`, `test:`, `perf:`, `docs:`). Reuse existing abstractions and do not rewrite working code.
- If a major research decision is needed beyond §4, stop and ask: situation, options, tradeoffs, recommendation. Keep it under 8 lines.

## 11. Known limitations (state them in the UI and docs)
Synthetic demand; Euclidean plane; instantaneous planning in simulated time; simplified service model; no traffic, failures or uncertain travel times; single depot; identical vehicles; simplified arrival model. Empirical runtime is not Big-O. Document theory separately (greedy insertion: O(vehicles × route length) per request; a full 2-opt* neighborhood scan is quadratic in route sizes; Tabu depends on neighborhood size and evaluation budget).
