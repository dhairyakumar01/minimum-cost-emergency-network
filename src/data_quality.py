"""Exploratory data-quality checks. Nothing is deleted or modified.

Run from the project root:  python -m src.data_quality
Requires results/complete_graph_edges.csv and results/prim_mst_edges.csv
(created by run_analysis.py).
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
FAC = ROOT / "data/processed/emergency_facilities.csv"
EDGES = ROOT / "results/complete_graph_edges.csv"
PRIM = ROOT / "results/prim_mst_edges.csv"
REPORTS = ROOT / "reports"
REPORTS.mkdir(exist_ok=True)

# Exploratory thresholds in km (10 m, 25 m, 50 m). They are arbitrary and
# only meant to show how many facilities are suspiciously close together.
THRESHOLDS_KM = [0.010, 0.025, 0.050]
LAT_RANGE, LON_RANGE = (12.85, 13.15), (77.45, 77.75)

nodes = pd.read_csv(FAC)
edges = pd.read_csv(EDGES)
prim = pd.read_csv(PRIM)

names = nodes["facility_name"].astype("string").str.strip()
missing_name = names.isna() | (names == "")

dup_coord = nodes.duplicated(["latitude", "longitude"], keep=False)

named = nodes[~missing_name].copy()
named["facility_name"] = named["facility_name"].astype(str).str.strip().str.lower()
dup_name_type = named.duplicated(["facility_name", "facility_type"], keep=False)

outside = ~(
    nodes["latitude"].between(*LAT_RANGE) & nodes["longitude"].between(*LON_RANGE)
)

summary = {
    "total_facilities": int(len(nodes)),
    "by_type": nodes["facility_type"].value_counts().to_dict(),
    "missing_names": int(missing_name.sum()),
    "records_sharing_exact_coordinates": int(dup_coord.sum()),
    "records_sharing_name_and_type": int(dup_name_type.sum()),
    "outside_provisional_rectangle": int(outside.sum()),
    "pairs_closer_than_km": {
        f"{int(t * 1000)}m": int((edges.weight_km <= t).sum()) for t in THRESHOLDS_KM
    },
    "prim_mst_edges_at_or_below_km": {
        f"{int(t * 1000)}m": int((prim.weight_km <= t).sum()) for t in THRESHOLDS_KM
    },
    "prim_mst_edge_length_km": {
        "min": float(prim.weight_km.min()),
        "median": float(prim.weight_km.median()),
        "mean": float(prim.weight_km.mean()),
        "max": float(prim.weight_km.max()),
    },
    "note": "Exploratory checks only. Close pairs may be separate buildings of "
    "one campus, duplicate OSM mappings, or genuinely distinct facilities; "
    "this script cannot tell which. No records were removed.",
}

close = edges[edges.weight_km <= max(THRESHOLDS_KM)].copy()
close["cross_type"] = close.u_type != close.v_type
close.sort_values("weight_km").to_csv(REPORTS / "near_duplicate_pairs.csv", index=False)

(REPORTS / "data_quality_summary.json").write_text(json.dumps(summary, indent=2))
print(json.dumps(summary, indent=2))
print(f"\nWrote {len(close)} close pairs to reports/near_duplicate_pairs.csv")
