import pytest
import pandas as pd
from src.mst_network import build_complete_edges, prim_mst

@pytest.fixture
def sample_facilities():
    data = {
        "facility_id": ["h1", "h2", "p1", "f1"],
        "facility_name": ["Hospital 1", "Hospital 2", "Police 1", "Fire 1"],
        "facility_type": ["hospital", "hospital", "police_station", "fire_station"],
        "latitude": [12.9716, 12.9800, 12.9750, 12.9650],
        "longitude": [77.5946, 77.6000, 77.5900, 77.5850],
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_mst(sample_facilities):
    edges = build_complete_edges(sample_facilities)
    mst, _ = prim_mst(sample_facilities, edges)
    return mst

