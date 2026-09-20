# tests/test_api.py
"""Integration tests for FastAPI endpoints (Phase P4)."""

import json
import pytest
from fastapi.testclient import TestClient

from api import app

client = TestClient(app)

def test_health_endpoint():
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "OK"
    assert "timestamp" in data

def test_scenario_and_simulation_flow():
    # create a simple scenario
    scen_payload = {
        "customers": 3,
        "vehicles": 1,
        "capacity": 10,
        "dynamism": 0.0,
        "seed": 123,
        "map_size": 10.0,
        "horizon": 100.0,
    }
    resp = client.post("/api/v1/scenarios", json=scen_payload)
    assert resp.status_code == 200
    scen_data = resp.json()
    scenario_id = scen_data["id"]
    # start a simulation with greedy insertion (A)
    run_payload = {
        "scenario_id": scenario_id,
        "strategy": "greedy_insertion",
        "budget": {},
    }
    resp = client.post("/api/v1/simulations", json=run_payload)
    assert resp.status_code == 200
    run_data = resp.json()
    run_id = run_data["run_id"]
    # poll run status (should be finished quickly)
    resp = client.get(f"/api/v1/simulations/{run_id}")
    assert resp.status_code == 200
    run_info = resp.json()
    assert run_info["status"] == "finished"
    # retrieve trace
    resp = client.get(f"/api/v1/simulations/{run_id}/trace")
    assert resp.status_code == 200
    # trace is raw JSONL string; ensure it contains at least one line
    trace_text = resp.text.strip()
    assert len(trace_text) > 0
    # parse first line
    first_line = json.loads(trace_text.splitlines()[0])
    assert "time" in first_line and "event" in first_line
