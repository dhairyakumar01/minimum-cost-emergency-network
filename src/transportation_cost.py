"""Shared Transportation Cost and Road Routing Engine for Emergency Responders in Bengaluru.

Provides research-backed per-kilometer vehicular operating rates, road routing via
OpenStreetMap (OSRM) with persistent disk caching, and transportation expenditure calculations.
"""
import json
import math
import os
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

CACHE_FILE = Path(__file__).resolve().parent.parent / "data" / "cache" / "routes_cache.json"

# Retail High-Speed Diesel Price in Bengaluru Benchmark (INR / Liter)
# Established from Government of Karnataka Finance Department Notification (effective June 15, 2024),
# which revised state sales tax on diesel from 14.34% to 18.44% resulting in ₹88.94/L in Bengaluru
# (concurrently revising petrol to ₹102.86/L under 29.84% sales tax).
BENGALURU_DIESEL_PRICE_PER_LITER = 88.94

# Standardized vehicle rate matrix distinguishing secondary-source reported statutory tariffs from illustrative engineering estimates
VEHICLE_RATES = {
    "hospital": {
        "vehicle_category": "Ambulance",
        "vehicle_model": "Force Traveller / Tata Winger 2.2L CRDe",
        "fuel_efficiency_km_l": 10.0,
        "fuel_cost_per_km": 8.894,
        "maint_cost_per_km": 3.606,
        "direct_operating_cost_per_km": 12.50,
        "composite_cost_per_km": 38.50,
        "regulated_tariff_cap_per_km": 120.00,
        "tariff_verification_status": "SECONDARY_SOURCE_REPORTED_STATUTORY_TARIFF_CAP",
        "tariff_source_title": "Secondary Media Reporting (The Hindu / Times of India / Canara Post, May 2021) of Karnataka Health & Family Welfare / Transport Dept Tariff Cap Order",
        "operating_cost_verification_status": "ILLUSTRATIVE_ENGINEERING_DERIVED_ESTIMATE",
        "operating_cost_status_label": "Illustrative Estimate — Not an Official or Verified Operating Rate",
        "source_doc": "NHM Fleet Baseline & May 2021 Secondary Tariff Cap Reports",
        "derivation_formula": "R_operating = (Fuel Price / Efficiency) + Estimated Maintenance Provision = (88.94 / 10.0) + 3.606 = 12.50 INR/km",
        "unsupported_inputs_note": "Fuel efficiency (10.0 km/L) and routine maintenance (₹3.606/km) are illustrative academic assumptions, not verified from state audit reports.",
        "sensitivity": {
            "lower": 11.09,
            "base": 12.50,
            "upper": 14.38,
            "diesel_price": {"lower_rate": 11.17, "base_rate": 12.50, "upper_rate": 13.83, "delta_pct": "±15% Diesel (₹75.60 to ₹102.28/L)"},
            "fuel_efficiency": {"lower_rate": 11.69, "base_rate": 12.50, "upper_rate": 13.49, "param_range": "11.0 to 9.0 km/L"},
            "maintenance": {"lower_rate": 11.60, "base_rate": 12.50, "upper_rate": 13.40, "delta_pct": "±25% Maintenance (₹2.70 to ₹4.51/km)"},
            "combined_scenarios": {"lower_rate": 11.09, "base_rate": 12.50, "upper_rate": 14.38, "scenario": "Cruising vs Severe Congestion"},
        },
    },
    "police_station": {
        "vehicle_category": "Police Patrol Vehicle (Hoysala)",
        "vehicle_model": "Mahindra Bolero B6 / Maruti Ertiga 1.5L",
        "fuel_efficiency_km_l": 12.0,
        "fuel_cost_per_km": 7.412,
        "maint_cost_per_km": 2.588,
        "direct_operating_cost_per_km": 10.00,
        "composite_cost_per_km": 24.00,
        "regulated_tariff_cap_per_km": None,
        "tariff_verification_status": "NOT_APPLICABLE_PUBLIC_SECTOR_SERVICE",
        "tariff_source_title": "N/A — Dedicated State Law Enforcement Fleet (No Public Fare Tariff)",
        "operating_cost_verification_status": "ILLUSTRATIVE_ENGINEERING_DERIVED_ESTIMATE",
        "operating_cost_status_label": "Illustrative Estimate — Not an Official or Verified Operating Rate",
        "source_doc": "Karnataka Police Motor Transport (KPMT) Wing Fleet Baseline",
        "derivation_formula": "R_operating = (Fuel Price / Efficiency) + Estimated Maintenance Provision = (88.94 / 12.0) + 2.588 = 10.00 INR/km",
        "unsupported_inputs_note": "Fuel efficiency (12.0 km/L) and routine maintenance (₹2.588/km) are illustrative academic assumptions, not verified from police department accounts.",
        "sensitivity": {
            "lower": 8.79,
            "base": 10.00,
            "upper": 11.47,
            "diesel_price": {"lower_rate": 8.89, "base_rate": 10.00, "upper_rate": 11.11, "delta_pct": "±15% Diesel (₹75.60 to ₹102.28/L)"},
            "fuel_efficiency": {"lower_rate": 9.18, "base_rate": 10.00, "upper_rate": 11.06, "param_range": "13.5 to 10.5 km/L"},
            "maintenance": {"lower_rate": 9.35, "base_rate": 10.00, "upper_rate": 10.65, "delta_pct": "±25% Maintenance (₹1.94 to ₹3.24/km)"},
            "combined_scenarios": {"lower_rate": 8.79, "base_rate": 10.00, "upper_rate": 11.47, "scenario": "Cruising vs Severe Congestion"},
        },
    },
    "fire_station": {
        "vehicle_category": "Heavy Water Tender (Fire Engine)",
        "vehicle_model": "Ashok Leyland 16T Water Tender (4,500L, PTO Pump)",
        "fuel_efficiency_km_l": 2.8,
        "fuel_cost_per_km": 31.764,
        "maint_cost_per_km": 10.236,
        "direct_operating_cost_per_km": 42.00,
        "composite_cost_per_km": 110.00,
        "regulated_tariff_cap_per_km": None,
        "tariff_verification_status": "NOT_APPLICABLE_PUBLIC_SECTOR_SERVICE",
        "tariff_source_title": "N/A — Dedicated State Firefighting Fleet (No Public Fare Tariff)",
        "operating_cost_verification_status": "ILLUSTRATIVE_ENGINEERING_DERIVED_ESTIMATE",
        "operating_cost_status_label": "Illustrative Estimate — Not an Official or Verified Operating Rate",
        "source_doc": "Karnataka State Fire and Emergency Services (KSFES) Fleet Baseline",
        "derivation_formula": "R_operating = (Fuel Price / Efficiency) + Estimated Maintenance Provision = (88.94 / 2.8) + 10.236 = 42.00 INR/km",
        "unsupported_inputs_note": "Fuel efficiency (2.8 km/L) and routine maintenance (₹10.236/km) are illustrative academic assumptions, not verified from KSFES audit reports.",
        "sensitivity": {
            "lower": 33.91,
            "base": 42.00,
            "upper": 52.43,
            "diesel_price": {"lower_rate": 37.24, "base_rate": 42.00, "upper_rate": 46.76, "delta_pct": "±15% Diesel (₹75.60 to ₹102.28/L)"},
            "fuel_efficiency": {"lower_rate": 35.65, "base_rate": 42.00, "upper_rate": 50.66, "param_range": "3.5 to 2.2 km/L"},
            "maintenance": {"lower_rate": 39.44, "base_rate": 42.00, "upper_rate": 44.56, "delta_pct": "±25% Maintenance (₹7.68 to ₹12.80/km)"},
            "combined_scenarios": {"lower_rate": 33.91, "base_rate": 42.00, "upper_rate": 52.43, "scenario": "Cruising vs Severe Congestion & Pumping"},
        },
    },
}

# Aliases for flexible category lookups
VEHICLE_RATES["ambulance"] = VEHICLE_RATES["hospital"]
VEHICLE_RATES["police"] = VEHICLE_RATES["police_station"]
VEHICLE_RATES["fire"] = VEHICLE_RATES["fire_station"]


def normalize_vehicle_category(cat: str) -> str:
    """Normalize input category name to canonical key."""
    c = str(cat).lower().strip().replace(" ", "_")
    if "hosp" in c or "clinic" in c or "amb" in c:
        return "hospital"
    if "pol" in c:
        return "police_station"
    if "fire" in c:
        return "fire_station"
    if c in VEHICLE_RATES:
        return c
    return "hospital"


def get_vehicle_rate_data(category: str) -> Dict[str, Any]:
    """Retrieve full rate metadata for a vehicle category."""
    norm = normalize_vehicle_category(category)
    return VEHICLE_RATES.get(norm, VEHICLE_RATES["hospital"])


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle spherical distance in kilometers."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = phi2 - phi1
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    return 2.0 * 6371.0088 * math.asin(min(1.0, math.sqrt(a)))


def _load_route_cache() -> Dict[str, Any]:
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_route_cache(cache: Dict[str, Any]) -> None:
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2)
    except Exception:
        pass


def get_road_route(lat1: float, lon1: float, lat2: float, lon2: float) -> Dict[str, Any]:
    """Retrieve physical road route distance and travel duration between two coordinates.
    
    Uses OpenStreetMap (OSRM) driving profile with local persistent disk caching.
    Falls back gracefully to Bengaluru urban circuity approximation (1.35x Haversine) with explicit labeling.
    """
    key = f"{lat1:.5f},{lon1:.5f}->{lat2:.5f},{lon2:.5f}"
    cache = _load_route_cache()
    
    hav_km = haversine_km(lat1, lon1, lat2, lon2)

    if key in cache:
        cached_entry = cache[key].copy()
        if cached_entry.get("road_distance_km", 0) < hav_km:
            cached_entry["road_distance_km"] = round(hav_km, 4)
        return cached_entry
    
    # Reverse key check for undirected routing symmetry
    rev_key = f"{lat2:.5f},{lon2:.5f}->{lat1:.5f},{lon1:.5f}"
    if rev_key in cache:
        cached_entry = cache[rev_key].copy()
        if cached_entry.get("road_distance_km", 0) < hav_km:
            cached_entry["road_distance_km"] = round(hav_km, 4)
        return cached_entry
    
    # Extremely close points (< 20 meters)
    if hav_km < 0.02:
        res = {
            "road_distance_km": round(hav_km, 4),
            "travel_time_minutes": 0.5,
            "routing_source": "Coincident Location",
            "is_approximation": False,
        }
        cache[key] = res
        _save_route_cache(cache)
        return res

    # Attempt OSRM public API
    url = f"http://router.project-osrm.org/route/v1/driving/{lon1:.5f},{lat1:.5f};{lon2:.5f},{lat2:.5f}?overview=false"
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "BengaluruEmergencyNetworkAcademic/1.0 (DMGT-Research; Contact: academic-project)"}
        )
        with urllib.request.urlopen(req, timeout=3.5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("code") == "Ok" and data.get("routes"):
                route = data["routes"][0]
                dist_km = float(route["distance"]) / 1000.0
                dur_min = float(route["duration"]) / 60.0
                # Enforce physical and geometric consistency: road distance cannot be less than straight-line Haversine geodesic
                dist_km = max(dist_km, hav_km)
                res = {
                    "road_distance_km": round(dist_km, 4),
                    "travel_time_minutes": round(dur_min, 2),
                    "routing_source": "OpenStreetMap OSRM (Car Profile)",
                    "is_approximation": False,
                }
                cache[key] = res
                _save_route_cache(cache)
                return res
    except Exception:
        pass

    # Graceful, explicitly labeled fallback:
    # Bengaluru urban street circuity factor = 1.35x straight-line distance
    # Urban emergency vehicle average speed = 24 km/h (0.4 km/min)
    approx_dist = max(hav_km * 1.35, hav_km)
    approx_time = (approx_dist / 24.0) * 60.0
    res = {
        "road_distance_km": round(approx_dist, 4),
        "travel_time_minutes": round(approx_time, 2),
        "routing_source": "Circuity Approximation (1.35× Haversine)",
        "is_approximation": True,
    }
    cache[key] = res
    _save_route_cache(cache)
    return res


def calculate_journey_cost(
    category: str,
    road_distance_km: float,
    cost_mode: str = "direct_operating",
    round_trip: bool = False,
) -> Dict[str, Any]:
    """Calculate emergency vehicle transportation expenditure for a given journey.
    
    Modes:
    - 'direct_operating': Fuel + Maintenance (Illustrative derived engineering baseline)
    - 'fuel_only': Fuel consumption alone
    - 'composite': Fuel + Maintenance + Crew shift operational allocation
    """
    if road_distance_km < 0:
        raise ValueError(f"Road distance cannot be negative, got {road_distance_km}")
        
    rate_info = get_vehicle_rate_data(category)
    
    if cost_mode == "fuel_only":
        rate = rate_info["fuel_cost_per_km"]
        mode_label = "Fuel Only"
    elif cost_mode == "composite":
        rate = rate_info["composite_cost_per_km"]
        mode_label = "Composite (Fuel + Maint + Crew)"
    else:
        rate = rate_info["direct_operating_cost_per_km"]
        mode_label = "Direct Operating Cost (Fuel + Maint)"
        
    effective_dist = road_distance_km * (2.0 if round_trip else 1.0)
    expenditure = effective_dist * rate
    
    return {
        "vehicle_category": rate_info["vehicle_category"],
        "vehicle_model": rate_info["vehicle_model"],
        "road_distance_km": round(road_distance_km, 4),
        "effective_distance_km": round(effective_dist, 4),
        "is_round_trip": round_trip,
        "rate_per_km": rate,
        "cost_mode": mode_label,
        "expenditure_inr": round(expenditure, 2),
        "fuel_cost_inr": round(effective_dist * rate_info["fuel_cost_per_km"], 2),
        "maint_cost_inr": round(effective_dist * rate_info["maint_cost_per_km"], 2),
        "source_doc": rate_info["source_doc"],
        "verification_status": rate_info.get("operating_cost_verification_status", "ILLUSTRATIVE_ENGINEERING_DERIVED_ESTIMATE"),
        "status_label": rate_info.get("operating_cost_status_label", "Illustrative Estimate — Not an Official or Verified Operating Rate"),
    }


def calculate_aggregate_expenditure(
    journeys: list,
    cost_mode: str = "direct_operating",
    round_trip: bool = False,
) -> Dict[str, Any]:
    """Calculate aggregate vehicular expenditure across all dispatched responders.
    
    Each item in journeys must contain 'category' and 'road_distance_km'.
    """
    total_km = 0.0
    total_cost = 0.0
    total_fuel = 0.0
    total_maint = 0.0
    breakdowns = []
    
    for item in journeys:
        cat = item.get("category", "hospital")
        dist = float(item.get("road_distance_km", 0.0))
        item_rt = item.get("round_trip", round_trip)
        c_res = calculate_journey_cost(cat, dist, cost_mode=cost_mode, round_trip=item_rt)
        total_km += c_res["effective_distance_km"]
        total_cost += c_res["expenditure_inr"]
        total_fuel += c_res["fuel_cost_inr"]
        total_maint += c_res["maint_cost_inr"]
        breakdowns.append(c_res)
        
    return {
        "total_vehicle_km": round(total_km, 4),
        "aggregate_expenditure_inr": round(total_cost, 2),
        "aggregate_fuel_inr": round(total_fuel, 2),
        "aggregate_maint_inr": round(total_maint, 2),
        "responder_count": len(journeys),
        "is_round_trip": round_trip,
        "status_label": "Illustrative Estimate — Not an Official or Verified Operating Rate",
        "breakdowns": breakdowns,
    }


def get_sensitivity_expenditures(category: str, road_distance_km: float) -> Dict[str, Any]:
    """Calculate transportation expenditure across separated sensitivity dimensions.
    
    Dimensions separated:
    1. Diesel price sensitivity (+-15%)
    2. Fuel efficiency sensitivity (cruising vs congestion)
    3. Maintenance cost sensitivity (+-25%)
    4. Combined operating-condition scenarios
    """
    rate_info = get_vehicle_rate_data(category)
    sens = rate_info["sensitivity"]
    dist = float(road_distance_km)
    
    dp = sens.get("diesel_price", {})
    fe = sens.get("fuel_efficiency", {})
    mc = sens.get("maintenance", {})
    comb = sens.get("combined_scenarios", {})
    
    return {
        "lower_inr": round(dist * sens["lower"], 2),
        "base_inr": round(dist * sens["base"], 2),
        "upper_inr": round(dist * sens["upper"], 2),
        "lower_rate": sens["lower"],
        "base_rate": sens["base"],
        "upper_rate": sens["upper"],
        "diesel_price": {
            "lower_inr": round(dist * dp.get("lower_rate", sens["lower"]), 2),
            "base_inr": round(dist * dp.get("base_rate", sens["base"]), 2),
            "upper_inr": round(dist * dp.get("upper_rate", sens["upper"]), 2),
            "lower_rate": dp.get("lower_rate", sens["lower"]),
            "base_rate": dp.get("base_rate", sens["base"]),
            "upper_rate": dp.get("upper_rate", sens["upper"]),
            "description": dp.get("delta_pct", "±15% Diesel Price"),
        },
        "fuel_efficiency": {
            "lower_inr": round(dist * fe.get("lower_rate", sens["lower"]), 2),
            "base_inr": round(dist * fe.get("base_rate", sens["base"]), 2),
            "upper_inr": round(dist * fe.get("upper_rate", sens["upper"]), 2),
            "lower_rate": fe.get("lower_rate", sens["lower"]),
            "base_rate": fe.get("base_rate", sens["base"]),
            "upper_rate": fe.get("upper_rate", sens["upper"]),
            "description": fe.get("param_range", "Traffic Congestion Variance"),
        },
        "maintenance": {
            "lower_inr": round(dist * mc.get("lower_rate", sens["lower"]), 2),
            "base_inr": round(dist * mc.get("base_rate", sens["base"]), 2),
            "upper_inr": round(dist * mc.get("upper_rate", sens["upper"]), 2),
            "lower_rate": mc.get("lower_rate", sens["lower"]),
            "base_rate": mc.get("base_rate", sens["base"]),
            "upper_rate": mc.get("upper_rate", sens["upper"]),
            "description": mc.get("delta_pct", "±25% Maintenance Provision"),
        },
        "combined_scenarios": {
            "lower_inr": round(dist * comb.get("lower_rate", sens["lower"]), 2),
            "base_inr": round(dist * comb.get("base_rate", sens["base"]), 2),
            "upper_inr": round(dist * comb.get("upper_rate", sens["upper"]), 2),
            "lower_rate": comb.get("lower_rate", sens["lower"]),
            "base_rate": comb.get("base_rate", sens["base"]),
            "upper_rate": comb.get("upper_rate", sens["upper"]),
            "description": comb.get("scenario", "Combined Highway Cruising vs Urban Congestion"),
        },
    }

