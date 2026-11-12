"""Unit tests for transportation cost model, vehicle rates, and road routing."""
import math
import pytest
import pandas as pd

from src.transportation_cost import (
    VEHICLE_RATES,
    normalize_vehicle_category,
    get_vehicle_rate_data,
    calculate_journey_cost,
    calculate_aggregate_expenditure,
    get_sensitivity_expenditures,
    get_road_route,
    haversine_km,
)
from src.simulation import simulate_emergency_incident


def test_vehicle_rates_structure_and_consistency():
    """Verify all vehicle categories have documented rates, components, and sensitivity bounds."""
    for cat in ["hospital", "police_station", "fire_station"]:
        assert cat in VEHICLE_RATES
        info = VEHICLE_RATES[cat]
        # Direct operating cost must equal fuel cost + maintenance cost within floating precision
        expected_direct = info["fuel_cost_per_km"] + info["maint_cost_per_km"]
        assert math.isclose(info["direct_operating_cost_per_km"], expected_direct, rel_tol=1e-3)
        # Sensitivity: lower <= base <= upper
        sens = info["sensitivity"]
        assert sens["lower"] <= sens["base"] <= sens["upper"]
        assert math.isclose(sens["base"], info["direct_operating_cost_per_km"], rel_tol=1e-3)


def test_category_normalization_and_aliases():
    """Verify alias resolution for user and facility category strings."""
    assert normalize_vehicle_category("Ambulance") == "hospital"
    assert normalize_vehicle_category("Clinic") == "hospital"
    assert normalize_vehicle_category("Police Station") == "police_station"
    assert normalize_vehicle_category("police") == "police_station"
    assert normalize_vehicle_category("Fire Station") == "fire_station"
    assert normalize_vehicle_category("fire") == "fire_station"


def test_journey_cost_calculation():
    """Verify journey expenditure formula C_j = D_road * R_j."""
    dist_km = 10.0
    res_amb = calculate_journey_cost("ambulance", dist_km)
    assert res_amb["road_distance_km"] == 10.0
    assert res_amb["rate_per_km"] == 12.50
    assert res_amb["expenditure_inr"] == 125.00
    assert res_amb["fuel_cost_inr"] == 88.94
    assert res_amb["maint_cost_inr"] == 36.06

    res_fire = calculate_journey_cost("fire_station", dist_km)
    assert res_fire["rate_per_km"] == 42.00
    assert res_fire["expenditure_inr"] == 420.00


def test_aggregate_expenditure_and_scene_arrival():
    """Verify multi-responder aggregate calculations."""
    journeys = [
        {"category": "hospital", "road_distance_km": 5.0},
        {"category": "police_station", "road_distance_km": 4.0},
        {"category": "fire_station", "road_distance_km": 6.0},
    ]
    agg = calculate_aggregate_expenditure(journeys)
    assert agg["total_vehicle_km"] == 15.0
    # Expected: 5*12.50 + 4*10.00 + 6*42.00 = 62.50 + 40.00 + 252.00 = 354.50
    assert agg["aggregate_expenditure_inr"] == 354.50
    assert agg["responder_count"] == 3


def test_sensitivity_analysis_bounds():
    """Verify lower, base, and upper sensitivity outputs."""
    sens = get_sensitivity_expenditures("ambulance", 10.0)
    assert sens["lower_inr"] == 110.90
    assert sens["base_inr"] == 125.00
    assert sens["upper_inr"] == 143.80
    assert sens["lower_inr"] < sens["base_inr"] < sens["upper_inr"]


def test_multidimensional_sensitivity_separation():
    """Verify separated sensitivity dimensions: diesel price, efficiency, maintenance, and combined."""
    sens = get_sensitivity_expenditures("ambulance", 10.0)
    
    # 1. Diesel price (+-15%)
    dp = sens["diesel_price"]
    assert dp["lower_rate"] == 11.17
    assert dp["base_rate"] == 12.50
    assert dp["upper_rate"] == 13.83
    assert dp["lower_inr"] == 111.70
    assert dp["base_inr"] == 125.00
    assert dp["upper_inr"] == 138.30
    assert dp["lower_inr"] < dp["base_inr"] < dp["upper_inr"]

    # 2. Fuel efficiency (cruising vs congestion)
    fe = sens["fuel_efficiency"]
    assert fe["lower_rate"] == 11.69
    assert fe["base_rate"] == 12.50
    assert fe["upper_rate"] == 13.49
    assert fe["lower_inr"] < fe["base_inr"] < fe["upper_inr"]

    # 3. Routine maintenance (+-25%)
    mc = sens["maintenance"]
    assert mc["lower_rate"] == 11.60
    assert mc["base_rate"] == 12.50
    assert mc["upper_rate"] == 13.40
    assert mc["lower_inr"] < mc["base_inr"] < mc["upper_inr"]

    # 4. Combined scenarios
    comb = sens["combined_scenarios"]
    assert comb["lower_rate"] == 11.09
    assert comb["base_rate"] == 12.50
    assert comb["upper_rate"] == 14.38
    assert comb["lower_inr"] < comb["base_inr"] < comb["upper_inr"]


def test_road_route_retrieval_and_caching():
    """Verify road routing returns distance, time, and valid labeling."""
    # Lalbagh to Forum Mall Konankunte
    lat1, lon1 = 12.9465, 77.5800
    lat2, lon2 = 12.8906, 77.5750
    hav = haversine_km(lat1, lon1, lat2, lon2)
    route = get_road_route(lat1, lon1, lat2, lon2)

    assert route["road_distance_km"] > 0
    assert route["travel_time_minutes"] > 0
    # Physical road distance must be greater than straight-line Haversine
    assert route["road_distance_km"] >= hav
    assert "routing_source" in route
    assert isinstance(route["is_approximation"], bool)


def test_simulation_integration_with_transportation_costs(sample_facilities, sample_mst):
    """Verify simulate_emergency_incident populates road routes, costs, and aggregate expenditure."""
    inc_lat, inc_lon = 12.9725, 77.5955
    sim = simulate_emergency_incident("Medical Emergency", inc_lat, inc_lon, sample_facilities, sample_mst)
    
    assert "aggregate_transportation" in sim
    agg = sim["aggregate_transportation"]
    assert agg["aggregate_expenditure_inr"] > 0
    assert agg["total_vehicle_km"] > 0
    assert agg["scene_secure_minutes"] > 0

    # Primary responder must contain road_route, cost_details, and sensitivity
    primary = sim["primary_responder"]
    assert "road_route" in primary
    assert "cost_details" in primary
    assert "sensitivity" in primary
    assert primary["cost_details"]["expenditure_inr"] > 0


def test_journey_cost_zero_distance():
    """Verify zero-distance journey yields zero expenditure."""
    res = calculate_journey_cost("ambulance", 0.0)
    assert res["road_distance_km"] == 0.0
    assert res["effective_distance_km"] == 0.0
    assert res["expenditure_inr"] == 0.0
    assert res["fuel_cost_inr"] == 0.0
    assert res["maint_cost_inr"] == 0.0


def test_journey_cost_negative_distance_raises():
    """Verify negative distance strictly raises ValueError."""
    with pytest.raises(ValueError, match="cannot be negative"):
        calculate_journey_cost("ambulance", -5.0)


def test_journey_cost_round_trip():
    """Verify round-trip journey correctly doubles distance and expenditure."""
    res_one_way = calculate_journey_cost("police_station", 10.0, round_trip=False)
    res_round = calculate_journey_cost("police_station", 10.0, round_trip=True)
    
    assert res_one_way["is_round_trip"] is False
    assert res_round["is_round_trip"] is True
    assert res_round["effective_distance_km"] == 20.0
    assert res_round["expenditure_inr"] == 2.0 * res_one_way["expenditure_inr"]
    assert res_round["fuel_cost_inr"] == 2.0 * res_one_way["fuel_cost_inr"]


def test_verification_metadata_presence():
    """Verify that all rate queries include explicit verification status and audit labels."""
    for cat in ["hospital", "police_station", "fire_station"]:
        data = get_vehicle_rate_data(cat)
        assert "operating_cost_verification_status" in data
        assert "operating_cost_status_label" in data
        assert "Illustrative Estimate" in data["operating_cost_status_label"]

    cost = calculate_journey_cost("hospital", 5.0)
    assert "verification_status" in cost
    assert "status_label" in cost
    assert "Illustrative Estimate" in cost["status_label"]


def test_aggregate_expenditure_round_trip_handling():
    """Verify aggregate calculation correctly processes round-trip flags."""
    journeys = [
        {"category": "hospital", "road_distance_km": 5.0, "round_trip": True},
        {"category": "police_station", "road_distance_km": 4.0, "round_trip": False},
    ]
    agg = calculate_aggregate_expenditure(journeys)
    # Hospital: 5.0 km * 2 = 10.0 km @ 12.50 = 125.00
    # Police: 4.0 km * 1 = 4.0 km @ 10.00 = 40.00
    # Total km = 14.0, Total cost = 165.00
    assert agg["total_vehicle_km"] == 14.0
    assert agg["aggregate_expenditure_inr"] == 165.00

