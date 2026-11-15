import os
import sys
import time
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.services.scenario_service import create_and_run_scenario, get_scenario_result

# Pick a unique coordinate to guarantee a fresh first run
fresh_lat = round(12.9300 + random.uniform(0.001, 0.040), 5)
fresh_lon = round(77.5700 + random.uniform(0.001, 0.040), 5)

print("=== BENCHMARKING EMERGENCY SIMULATION RUNTIMES ===")
print(f"Coordinates: {fresh_lat}, {fresh_lon} | Agency: police | Radius: 4.0 km")

print("\n--- RUN 1: Fresh scenario execution ---")
t0 = time.time()
sc1 = create_and_run_scenario(fresh_lat, fresh_lon, "Benchmark Incident", "police", 4.0, "time", 5, async_mode=False)
t1 = time.time()
res1 = get_scenario_result(sc1)
net1 = res1["network_mst"]
print(f"Run 1 completed in: {t1 - t0:.4f} s")
print(f"  Candidate facilities in radius: {res1['summary']['total_candidates_in_radius']}")
print(f"  Tree edges: {len(net1['edges'])}")
print(f"  Genuine road geometries retrieved: {net1['road_geometries_count']}")
print(f"  Cache provenance: {res1.get('cache_provenance')}")

print("\n--- RUN 2: Repeated scenario execution (Identical inputs) ---")
t2 = time.time()
sc2 = create_and_run_scenario(fresh_lat, fresh_lon, "Benchmark Incident", "police", 4.0, "time", 5, async_mode=False)
t3 = time.time()
res2 = get_scenario_result(sc2)
print(f"Run 2 completed in: {t3 - t2:.4f} s")
print(f"  Cache provenance: {res2.get('cache_provenance')}")
speedup = (t1 - t0) / (t3 - t2) if (t3 - t2) > 0 else 999.0
print(f"  Empirical Speedup: {speedup:.1f}x faster!")
