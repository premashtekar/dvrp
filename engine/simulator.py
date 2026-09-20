# engine/simulator.py
"""Event‑driven simulator for the DVRP engine.
It processes a pre‑generated list of request arrivals (time‑ordered).
When a request is released, the configured ``Strategy`` is invoked to
assign it to a vehicle.  The simulator records a JSONL trace of events
for later replay.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

from .state import EngineState, RequestState
from .models import Request
from .algorithms.base import Strategy

@dataclass
class Event:
    time: float
    request_id: int

class Simulator:
    """Simple deterministic simulator.
    Parameters
    ----------
    state: EngineState
        The initial engine state (scenario already loaded).
    strategy: Strategy
        Strategy to handle each new request.
    """

    def __init__(self, state: EngineState, strategy: Strategy):
        self.state = state
        self.strategy = strategy
        self.trace: List[dict] = []

    def run(self) -> EngineState:
        # collect all release events
        events = [Event(req.release_time, rid) for rid, req in self.state.requests.items()]
        events.sort(key=lambda e: e.time)
        for ev in events:
            # advance clock and release request
            self.state.advance_time(ev.time)
            req = self.state.requests[ev.request_id]
            # only handle if now AVAILABLE
            if self.state.request_states[ev.request_id] == RequestState.AVAILABLE:
                evals, new_state = self.strategy.update(self.state, req)
                self.state = new_state
                self.trace.append({
                    "time": ev.time,
                    "event": "request_assigned",
                    "request_id": ev.request_id,
                    "evaluations": evals,
                })
        return self.state

    def dump_trace(self, path: str | Path) -> None:
        with open(path, "w", encoding="utf-8") as f:
            for entry in self.trace:
                f.write(json.dumps(entry) + "\n")
