import pytest
import pandas as pd
from src.simulation import (
    SCENARIOS,
    find_nearest_facilities,
    build_mst_adjacency,
    find_tree_path,
    simulate_emergency_incident,
)
from src.geocoding import geocode_bengaluru_location, KNOWN_LANDMARKS
from src.mst_network import load_facilities, build_complete_edges, prim_mst


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


def test_responder_mappings():
    # Verify fixed responder mapping scenarios
    assert SCENARIOS["Fire"]["primary_type"] == "fire_station"
    assert "hospital" in SCENARIOS["Fire"]["supporting_types"]
    assert "police_station" in SCENARIOS["Fire"]["supporting_types"]

    assert SCENARIOS["Medical Emergency"]["primary_type"] == "hospital"
    assert "police_station" in SCENARIOS["Medical Emergency"]["supporting_types"]
    assert "fire_station" in SCENARIOS["Medical Emergency"]["supporting_types"]

    assert SCENARIOS["Road Accident"]["primary_type"] == "hospital"
    assert "police_station" in SCENARIOS["Road Accident"]["supporting_types"]
    assert "fire_station" in SCENARIOS["Road Accident"]["supporting_types"]


def test_find_nearest_facilities(sample_facilities):
    # Incident close to h1
    res = find_nearest_facilities(12.9717, 77.5947, sample_facilities)
    assert res["hospital"]["facility"]["facility_id"] == "h1"
    assert res["police_station"]["facility"]["facility_id"] == "p1"
    assert res["fire_station"]["facility"]["facility_id"] == "f1"
    assert res["hospital"]["distance_km"] < 0.1


def test_tree_path_reconstruction(sample_facilities, sample_mst):
    adj = build_mst_adjacency(sample_mst)
    res = find_tree_path(adj, "h1", "f1")
    assert res["found"] is True
    assert res["nodes"][0] == "h1"
    assert res["nodes"][-1] == "f1"
    assert res["total_distance_km"] > 0
    assert len(res["edges"]) == len(res["nodes"]) - 1


def test_simulate_fire_incident(sample_facilities, sample_mst):
    sim = simulate_emergency_incident(
        "Fire", 12.9700, 77.5900, sample_facilities, sample_mst
    )
    assert sim["incident_type"] == "Fire"
    assert sim["primary_responder"]["facility"]["facility_type"] == "fire_station"
    supp_types = [s["facility"]["facility_type"] for s in sim["supporting_responders"]]
    assert "hospital" in supp_types
    assert "police_station" in supp_types
    assert sim["all_connected"] is True
    assert sim["total_mst_communication_distance_km"] > 0


def test_original_mst_immutable_during_simulation(sample_facilities, sample_mst):
    orig_len = len(sample_mst)
    orig_sum = sample_mst["weight_km"].sum()
    
    # Run multiple simulations
    for sc in ["Fire", "Medical Emergency", "Road Accident"]:
        simulate_emergency_incident(sc, 12.95, 77.55, sample_facilities, sample_mst)
        
    assert len(sample_mst) == orig_len
    assert sample_mst["weight_km"].sum() == orig_sum


def test_geocoding_preset_landmarks():
    ok, res, msg = geocode_bengaluru_location("Lalbagh, Bengaluru")
    assert ok is True
    assert 12.70 <= res["latitude"] <= 13.30
    assert 77.30 <= res["longitude"] <= 77.90
    assert "Lalbagh" in res["display_name"]

    ok2, res2, _ = geocode_bengaluru_location("Forum Mall, Konankunte Cross")
    assert ok2 is True
    assert 12.80 <= res2["latitude"] <= 12.95


def test_geocoding_short_or_invalid_query():
    ok, res, msg = geocode_bengaluru_location("x")
    assert ok is False
    assert res is None
    assert "too short" in msg.lower()


def test_geocoding_dataset_facility_fallback(sample_facilities):
    custom_facs = sample_facilities.copy()
    custom_facs.loc[0, "facility_name"] = "UniqueSpecialtyTraumaCenterXYZ"
    ok, res, msg = geocode_bengaluru_location("UniqueSpecialtyTraumaCenterXYZ", facilities_df=custom_facs)
    assert ok is True
    assert res["latitude"] == 12.9716
    assert res["longitude"] == 77.5946
    assert "Dataset Record" in res["source"]


def test_geocoding_spelling_tolerance_and_variants():
    variants = [
        ("Konankunte", "Konankunte"),
        ("Konanakunte", "Konanakunte"),
        ("Lalbagh", "Lalbagh"),
        ("Lal Bagh", "Lalbagh"),
        ("Majestic Bus Station", "Majestic"),
        ("Majestic", "Majestic"),
        ("Indiranagr", "Indiranagar"),
        ("Indiranagar", "Indiranagar"),
        ("Whitefeild", "Whitefield"),
        ("Whitefield", "Whitefield"),
        ("Silk Institute", "Silk Institute"),
    ]
    for query, expected_sub in variants:
        ok, res, msg = geocode_bengaluru_location(query)
        assert ok is True, f"Failed to geocode '{query}': {msg}"
        assert 12.70 <= res["latitude"] <= 13.30
        assert 77.30 <= res["longitude"] <= 77.90
        assert any(
            token.lower() in res["display_name"].lower()
            for token in expected_sub.split()
        ), f"Expected token from '{expected_sub}' in '{res['display_name']}'"


def test_medical_emergency_priority_and_responders(sample_facilities, sample_mst):
    sim = simulate_emergency_incident(
        "Medical Emergency", 12.9720, 77.5950, sample_facilities, sample_mst
    )
    assert sim["incident_type"] == "Medical Emergency"
    assert sim["primary_responder"]["facility"]["facility_type"] == "hospital"
    supp_types = [s["facility"]["facility_type"] for s in sim["supporting_responders"]]
    assert "police_station" in supp_types
    assert "fire_station" in supp_types
    assert sim["all_connected"] is True


def test_road_accident_priority_and_responders(sample_facilities, sample_mst):
    sim = simulate_emergency_incident(
        "Road Accident", 12.9730, 77.5960, sample_facilities, sample_mst
    )
    assert sim["incident_type"] == "Road Accident"
    assert sim["primary_responder"]["facility"]["facility_type"] == "hospital"
    supp_types = [s["facility"]["facility_type"] for s in sim["supporting_responders"]]
    assert "police_station" in supp_types
    assert "fire_station" in supp_types
    assert sim["all_connected"] is True


def test_scene_arrival_time_is_max_not_sum(sample_facilities, sample_mst):
    sim = simulate_emergency_incident(
        "Fire", 12.9700, 77.5900, sample_facilities, sample_mst
    )
    agg = sim["aggregate_transportation"]
    responders = [sim["primary_responder"]] + sim["supporting_responders"]
    times = [r["road_route"]["travel_time_minutes"] for r in responders]
    
    expected_max = max(times)
    calculated_arrival = agg["scene_arrival_time_minutes"]
    calculated_secure = agg["scene_secure_minutes"]
    
    # Mathematical proof: Arrival/scene secure time MUST equal max(T_j), strictly less than sum(T_j)
    assert calculated_arrival == pytest.approx(expected_max, rel=1e-3)
    assert calculated_secure == pytest.approx(expected_max, rel=1e-3)
    if len(times) > 1 and any(t > 0 for t in times):
        assert calculated_arrival < sum(times)


def test_geocoding_out_of_bounds_and_ambiguous():
    # Completely invalid / unresolvable query
    ok, res, msg = geocode_bengaluru_location("zzxyqwer9999notrealplace")
    assert ok is False
    assert res is None
    assert "Could not resolve" in msg

    # Whitespace only
    ok_ws, res_ws, msg_ws = geocode_bengaluru_location("   ")
    assert ok_ws is False
    assert res_ws is None
    assert "too short" in msg_ws.lower()


def test_missing_facility_category_fallback(sample_mst):
    # Facilities missing fire stations entirely
    facs_no_fire = pd.DataFrame({
        "facility_id": ["h1", "p1"],
        "facility_name": ["Hospital 1", "Police 1"],
        "facility_type": ["hospital", "police_station"],
        "latitude": [12.9716, 12.9750],
        "longitude": [77.5946, 77.5900],
    })
    
    nearest = find_nearest_facilities(12.9716, 77.5946, facs_no_fire)
    assert nearest["hospital"] is not None
    assert nearest["police_station"] is not None
    assert nearest["fire_station"] is None
    
    # Missing primary responder raises explicit ValueError
    with pytest.raises(ValueError, match="No facility found for primary responder category 'fire_station'"):
        simulate_emergency_incident("Fire", 12.9716, 77.5946, facs_no_fire, sample_mst)

    # Missing supporting responder does not crash Medical Emergency simulation
    sim_med = simulate_emergency_incident("Medical Emergency", 12.9716, 77.5946, facs_no_fire, sample_mst)
    assert sim_med["primary_responder"]["facility"]["facility_type"] == "hospital"
    assert len(sim_med["supporting_responders"]) == 1
    assert sim_med["supporting_responders"][0]["facility"]["facility_type"] == "police_station"




