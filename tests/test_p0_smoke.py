# P0 smoke test — verifies the scaffold is importable and pytest can run.
# Real engine tests begin in P1.


def test_engine_importable() -> None:
    """Engine package must import without errors."""
    import engine  # noqa: F401


def test_api_importable() -> None:
    """API package must import without errors."""
    import api  # noqa: F401


def test_configs_pilot_yaml_loadable() -> None:
    """Pilot YAML config must be parseable and contain required keys."""
    import pathlib
    import yaml  # type: ignore[import-untyped]  # stdlib-like, always present

    config_path = pathlib.Path(__file__).parent.parent / "configs" / "pilot.yaml"
    assert config_path.exists(), f"configs/pilot.yaml not found at {config_path}"
    with config_path.open() as f:
        cfg = yaml.safe_load(f)
    assert "experiment" in cfg
    assert "scenario" in cfg
    assert "strategies" in cfg
    assert "budgets" in cfg
    seeds = cfg["experiment"]["seeds"]
    tuning = cfg.get("tuning_seeds", [])
    overlap = set(seeds) & set(tuning)
    assert not overlap, f"Evaluation seeds and tuning seeds must be disjoint; overlap={overlap}"
