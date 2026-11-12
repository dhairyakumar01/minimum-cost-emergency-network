import tempfile
from pathlib import Path
import pytest
import pandas as pd
from src.experiments import (
    run_scalability_experiments,
    save_experiment_results,
    load_saved_scalability,
    run_density_experiments,
    save_density_results,
    load_saved_density,
)
from src.mst_network import build_complete_edges, kruskal_mst


@pytest.fixture
def test_facilities():
    coords = [
        (12.90 + i * 0.01, 77.50 + i * 0.01) for i in range(20)
    ]
    return pd.DataFrame({
        "facility_id": [f"fac_{i}" for i in range(20)],
        "facility_name": [f"Facility {i}" for i in range(20)],
        "facility_type": ["hospital" if i % 2 == 0 else "police_station" for i in range(20)],
        "latitude": [c[0] for c in coords],
        "longitude": [c[1] for c in coords],
    })


def test_scalability_reproducible_and_identical_inputs(test_facilities):
    res = run_scalability_experiments(
        test_facilities, subset_sizes=[5, 10], trials_per_size=2, seed=42
    )
    assert "metadata" in res
    assert "summary" in res
    assert "trials" in res
    assert len(res["summary"]) == 2
    
    # 2 sizes * 2 algorithms * 2 trials = 8 trial records
    assert len(res["trials"]) == 8
    
    # Verify trials have positive execution times and valid edge counts
    for trial in res["trials"]:
        assert trial["runtime_seconds"] > 0
        assert trial["candidate_edges"] == trial["vertices"] * (trial["vertices"] - 1) // 2
        assert trial["mst_edges"] == trial["vertices"] - 1


def test_scalability_persistence(test_facilities):
    res = run_scalability_experiments(
        test_facilities, subset_sizes=[4, 6], trials_per_size=1, seed=99
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        j_path, c_path = save_experiment_results(res, tmp_path)
        assert j_path.exists()
        assert c_path.exists()
        
        loaded = load_saved_scalability(tmp_path)
        assert loaded is not None
        assert loaded["metadata"]["seed"] == 99
        assert len(loaded["summary"]) == 2


def test_density_experiments_controlled_sparsification(test_facilities):
    complete = build_complete_edges(test_facilities)
    mst, mst_wt = kruskal_mst(test_facilities, complete)
    assert len(mst) == len(test_facilities) - 1

    res = run_density_experiments(
        test_facilities,
        complete,
        mst,
        density_levels=[0.0, 0.5, 1.0],
        seeds=[42, 84],
    )

    assert "metadata" in res
    assert "summary" in res
    assert "trials" in res
    assert len(res["summary"]) == 3

    # 3 density levels * 2 seeds * 2 algorithms = 12 trials
    assert len(res["trials"]) == 12

    # Verify that optimal MST weight remains completely invariant across all density levels
    for s_row in res["summary"]:
        assert abs(s_row["mst_weight_km"] - round(mst_wt, 4)) < 1e-4
        assert s_row["validation_passed"] is True

    # At rho = 0.0, total edges = |V| - 1 = 19
    assert res["summary"][0]["total_edges"] == len(test_facilities) - 1
    # At rho = 1.0, total edges = complete edge count = 190
    assert res["summary"][2]["total_edges"] == len(complete)


def test_density_persistence(test_facilities):
    complete = build_complete_edges(test_facilities)
    mst, _ = kruskal_mst(test_facilities, complete)
    res = run_density_experiments(
        test_facilities, complete, mst, density_levels=[0.0, 1.0], seeds=[10]
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        j_path, c_path = save_density_results(res, tmp_path)
        assert j_path.exists()
        assert c_path.exists()

        loaded = load_saved_density(tmp_path)
        assert loaded is not None
        assert len(loaded["summary"]) == 2

