import math, csv, json
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP

ROOT = Path(r"c:\Users\DHAIRYA\Downloads\minimum_cost_emergency_network\minimum_cost_emergency_network")
CSV_PATH = ROOT / "data" / "processed" / "emergency_facilities.csv"

records = []
with open(CSV_PATH, "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for r in reader:
        records.append((r["facility_id"], float(r["latitude"]), float(r["longitude"])))

records.sort(key=lambda x: x[0])
print(f"Total facilities: {len(records)}")

# 1. Inspect results/kruskal_mst_edges.csv
kruskal_csv = ROOT / "results" / "kruskal_mst_edges.csv"
prim_csv = ROOT / "results" / "prim_mst_edges.csv"

if kruskal_csv.exists():
    with open(kruskal_csv, "r") as f:
        k_edges = list(csv.DictReader(f))
    print(f"kruskal_mst_edges.csv rows: {len(k_edges)}")
    float_weights = [float(r["weight_km"]) for r in k_edges]
    print(f"Sum of floats: {sum(float_weights):.12f} km")
    print(f"Float sum * 1e6: {sum(float_weights) * 1e6:.6f}")
    
    # Check rounding each edge to mm (round half up)
    mm_edges_half_up = [int(math.floor(w * 1e6 + 0.5)) for w in float_weights]
    print(f"Sum of round_half_up(w * 1e6): {sum(mm_edges_half_up)} mm")
    
    # Check round(w * 1e6) using Python's round (bankers rounding)
    mm_edges_banker = [round(w * 1e6) for w in float_weights]
    print(f"Sum of banker round(w * 1e6): {sum(mm_edges_banker)} mm")

    # Check decimal round half up
    mm_edges_dec = [int(Decimal(str(r["weight_km"])).scaleb(6).quantize(Decimal('1'), rounding=ROUND_HALF_UP)) for r in k_edges]
    print(f"Sum of Decimal(str(w))*1e6 ROUND_HALF_UP: {sum(mm_edges_dec)} mm")
    
    # Check if sum is rounded at the end
    print(f"Round-half-up of float sum: {int(math.floor(sum(float_weights) * 1e6 + 0.5))} mm")
    print(f"Bankers round of float sum: {round(sum(float_weights) * 1e6)} mm")

# Check validation report
val_json = ROOT / "results" / "validation_report.json"
if val_json.exists():
    with open(val_json, "r") as f:
        vdata = json.load(f)
    print("validation_report.json keys:", list(vdata.keys()))
    print("prim_total_km:", vdata.get("prim_total_km"))
    print("kruskal_total_km:", vdata.get("kruskal_total_km"))
