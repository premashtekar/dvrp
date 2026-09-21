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

    def run(self) -> EngineState:
        events = [Event(req.release_time, rid) for rid, req in self.state.requests.items()]
        events.sort(key=lambda e: e.time)
        for ev in events:
            self.state.advance_time(ev.time)
            req = self.state.requests[ev.request_id]
            if self.state.request_states[ev.request_id] == RequestState.AVAILABLE:
                t0 = time.perf_counter()
                evals, new_state = self.strategy.update(self.state, req)
                t1 = time.perf_counter()
                self.total_evaluations += evals
                rt_ms = (t1 - t0) * 1000
                self.response_times.append(rt_ms)
                self.state = new_state
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
