# engine/scenarios.py
"""Scenario generation utilities.
Read the pilot.yaml config (or any config) and produce a deterministic Scenario instance.
All randomness is driven by a numpy.Generator seeded from the scenario ``seed``.
"""

from __future__ import annotations

import yaml
import numpy as np
from pathlib import Path
from typing import List

from .models import Scenario, Point

def load_yaml(path: str | Path) -> dict:
    """Load a YAML file and return the dictionary."""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def generate_scenario(config: dict, seed: int) -> Scenario:
    """Create a Scenario object from a config dictionary and a seed.
    The config must contain ``scenario`` section with the parameters.
    """
    sc = config["scenario"]
    rng = np.random.default_rng(seed)

    customers = sc["customers"]
    vehicles = sc["vehicles"]
    dynamism = sc["dynamism"]
    capacity = sc["capacity"]
    horizon = sc["horizon"]
    map_size = sc["map_size"]

    # locations: uniform in [0, map_size]
    locations: List[Point] = [
        (float(rng.uniform(0, map_size)), float(rng.uniform(0, map_size))) for _ in range(customers)
    ]
    # demands: random int 1..10
    demands = [int(rng.integers(1, 11)) for _ in range(customers)]
    # release times: fraction dynamism of requests get a random release in (0, 0.6*H)
    release_times = []
    max_release = 0.6 * horizon
    for _ in range(customers):
        if rng.random() < dynamism:
            release_times.append(float(rng.uniform(0, max_release)))
        else:
            release_times.append(0.0)  # immediate availability

    return Scenario(
        customers=customers,
        vehicles=vehicles,
        dynamism=dynamism,
        capacity=capacity,
        horizon=horizon,
        map_size=map_size,
        seed=seed,
        customer_locations=locations,
        request_demands=demands,
        release_times=release_times,
    )
