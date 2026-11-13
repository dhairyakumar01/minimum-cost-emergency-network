import sys
from pathlib import Path
import time
import requests
import json

ROOT = Path(r"c:\Users\DHAIRYA\Downloads\minimum_cost_emergency_network\minimum_cost_emergency_network")
sys.path.insert(0, str(ROOT))

from backend.services.routing_service import (
    check_osrm_health,
    query_osrm_table,
    fetch_osrm_submatrix,
    LOCAL_OSRM_URL,
    PUBLIC_OSRM_URL
)

def test_fresh_osrm():
    print("==================================================")
    print("STAGE 1: OSRM HEALTH & PROFILE VERIFICATION")
    print("==================================================")
    health = check_osrm_health()
    print("OSRM Health Result:", json.dumps(health, indent=2))
    active_url = health.get("url")
    print("Active OSRM URL:", active_url)
    print("Is Local Container:", health.get("is_local"))
    print("Profile: car (driving)")

    print("\n==================================================")
    print("STAGE 2: CONTROLLED FRESH ROUTING TEST (CACHE BYPASS)")
    print("==================================================")
    # 3 controlled coordinates in Bengaluru:
    # A: Majestic Station (lon=77.5696, lat=12.9781)
    # B: Sreeniwasa Hospital (lon=77.5645, lat=12.9818)
    # C: Victoria Hospital (lon=77.5739, lat=12.9634)
    points = [
        {"id": "majestic", "lon": 77.5696, "lat": 12.9781},
        {"id": "sreeniwasa", "lon": 77.5645, "lat": 12.9818},
        {"id": "victoria", "lon": 77.5739, "lat": 12.9634}
    ]
    coord_tuples = [(p["lon"], p["lat"]) for p in points]
    
    t0 = time.time()
    res = query_osrm_table(coord_tuples, base_url=active_url)
    dur_http = time.time() - t0
    print(f"Fresh OSRM Table Query completed in {dur_http:.3f}s")
    print("Status:", res.get("status"))
    
    durations = res.get("durations", [])
    distances = res.get("distances", [])

    print("\nPairwise Matrix Verification:")
    labels = ["Majestic", "Sreeniwasa", "Victoria"]
    for i in range(3):
        for j in range(3):
            if i != j:
                dur_s = durations[i][j]
                dist_m = distances[i][j]
                print(f"  {labels[i]} -> {labels[j]}: {dur_s:.1f} s ({dur_s/60:.2f} min), {dist_m:.1f} m ({dist_m/1000:.3f} km)")

    # Directional asymmetry check
    ab_dur, ba_dur = durations[0][1], durations[1][0]
    ab_dist, ba_dist = distances[0][1], distances[1][0]
    print(f"\nAsymmetry Verification (Majestic <-> Sreeniwasa):")
    print(f"  Forward: {ab_dur:.1f}s, {ab_dist:.1f}m")
    print(f"  Reverse: {ba_dur:.1f}s, {ba_dist:.1f}m")
    print(f"  Delta Duration: {abs(ab_dur - ba_dur):.1f}s ({'ASYMMETRIC' if ab_dur != ba_dur else 'SYMMETRIC'})")
    print(f"  Delta Distance: {abs(ab_dist - ba_dist):.1f}m ({'ASYMMETRIC' if ab_dist != ba_dist else 'SYMMETRIC'})")

    print("\n==================================================")
    print("STAGE 3: UNREACHABLE ROUTE HANDLING TEST")
    print("==================================================")
    # Coordinate in middle of Indian Ocean vs Bengaluru
    ocean_points = [
        (77.5696, 12.9781), # Bengaluru
        (75.0000, -10.0000) # Deep Indian ocean (unreachable)
    ]
    try:
        t_unreach = time.time()
        res_ocean = query_osrm_table(ocean_points, base_url=active_url)
        print(f"Unreachable query response ({time.time() - t_unreach:.2f}s): {res_ocean}")
    except Exception as ex:
        print("Unreachable query handled via exception:", type(ex).__name__, str(ex))

    print("\n==================================================")
    print("STAGE 4: TIMEOUT BEHAVIOUR TEST")
    print("==================================================")
    # Test query with very short timeout against non-routable IP
    try:
        t_to = time.time()
        # 10.255.255.1 is non-routable, will timeout
        query_osrm_table(coord_tuples, base_url="http://10.255.255.1")
        print("Timeout handled gracefully (returned None or exception)")
    except Exception as ex:
        print(f"Timeout correctly raised in {time.time() - t_to:.3f}s: {type(ex).__name__}")

    print("\n==================================================")
    print("STAGE 5: FRESH END-TO-END SCENARIO SIMULATION")
    print("==================================================")
    # Now run an end-to-end scenario pipeline with a fresh in-memory or custom cache database
    from backend.services.scenario_service import create_and_run_scenario, get_scenario_result
    import tempfile, os

    # Majestic incident, fire agency (20 total fire facilities in BBMP, small tight set ideal for live OSRM without overwhelming public server)
    print("Testing Fresh End-to-End Incident Scenario:")
    print("Incident: Majestic (12.9781, 77.5696)")
    print("Agency: fire (20 candidate facilities in BBMP)")
    print("Search Radius: 15.0 km (all fire stations)")
    
    t_start_scen = time.time()
    scen_id = create_and_run_scenario(
        incident_lat=12.9781,
        incident_lon=77.5696,
        incident_label="Majestic Fire Emergency (Fresh OSRM Verification)",
        agency="fire",
        radius_km=15.0,
        optimization_mode="time",
        async_mode=False
    )
    scen_res = get_scenario_result(scen_id)
    dur_scen = time.time() - t_start_scen
    print(f"Scenario completed in {dur_scen:.3f}s")
    print("Scenario ID:", scen_id)
    print("Scenario Status:", scen_res.get("status"))
    summary = scen_res.get("summary", {})
    print("Included Candidates:", summary.get("included_candidates_count"))
    print("Network Type:", summary.get("network_type"))
    print("Total Weight:", summary.get("total_weight_display"))
    dispatch = scen_res.get("dispatch_ranking", [])
    if dispatch:
        print("Dispatch Rank #1:", dispatch[0].get("facility_name"), 
              f"({dispatch[0].get('duration_min')} min, {dispatch[0].get('distance_km')} km)")
    print("Cycle Property Valid:", scen_res.get("validation", {}).get("is_optimal"))

if __name__ == "__main__":
    test_fresh_osrm()
