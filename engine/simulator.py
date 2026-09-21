from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List

from .state import EngineState, RequestState
from .models import Request
from .algorithms.base import Strategy

@dataclass
class Event:
    time: float
    request_id: int

class Simulator:
    def __init__(self, state: EngineState, strategy: Strategy):
        self.state = state
        self.strategy = strategy
        self.trace: List[dict] = []
        self.response_times = []
        self.total_evaluations = 0
        self.route_disruption = 0
        self.phase_timings_ms = {"insertion": 0.0, "two_opt_star": 0.0, "tabu": 0.0}

    def run(self) -> EngineState:
        events = [Event(req.release_time, rid) for rid, req in self.state.requests.items()]
        events.sort(key=lambda e: e.time)
        for ev in events:
            self.state.advance_time(ev.time)
            req = self.state.requests[ev.request_id]
            if self.state.request_states[ev.request_id] == RequestState.AVAILABLE:
                before = {vid: tuple(v.route) for vid, v in self.state.vehicles.items()}
                t0 = time.perf_counter()
                evals, new_state = self.strategy.update(self.state, req)
                t1 = time.perf_counter()
                self.total_evaluations += evals
                rt_ms = (t1 - t0) * 1000
                self.response_times.append(rt_ms)
                self.state = new_state
                after = {vid: tuple(v.route) for vid, v in self.state.vehicles.items()}
                old_edges = {(vid, a, b) for vid, route in before.items() for a, b in zip((-1,) + route, route + (-1,))}
                new_edges = {(vid, a, b) for vid, route in after.items() for a, b in zip((-1,) + route, route + (-1,))}
                moved = sum(1 for rid in self.state.requests if next((vid for vid,r in before.items() if rid in r), None) != next((vid for vid,r in after.items() if rid in r), None))
                self.route_disruption += len(old_edges - new_edges) + moved
                key = "tabu" if self.strategy.__class__.__name__ == "TabuSearch" else ("two_opt_star" if self.strategy.__class__.__name__ == "GreedyThenTwoOptStar" else "insertion")
                self.phase_timings_ms[key] += rt_ms
                self.trace.append({
                    "time": ev.time,
                    "event": "request_assigned",
                    "request_id": ev.request_id,
                    "evaluations": evals,
                    "response_time_ms": rt_ms
                })
        return self.state

    def dump_trace(self, path: str | Path) -> None:
        with open(path, "w", encoding="utf-8") as f:
            for entry in self.trace:
                f.write(json.dumps(entry) + "\n")
