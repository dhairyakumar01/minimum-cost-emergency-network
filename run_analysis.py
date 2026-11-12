from pathlib import Path
import json
import time

from src.mst_network import load_facilities, build_complete_edges, prim_mst, kruskal_mst
from src.validation import validate_mst

ROOT = Path(__file__).resolve().parent
nodes = load_facilities(ROOT / "data/processed/emergency_facilities.csv")
print(f"Loaded {len(nodes)} facilities")
print(nodes.facility_type.value_counts(dropna=False).to_string())

t = time.perf_counter()
edges = build_complete_edges(nodes)
edge_seconds = time.perf_counter() - t
print(f"Built {len(edges):,} candidate edges in {edge_seconds:.2f}s")

t = time.perf_counter()
p, pt = prim_mst(nodes, edges)
prim_seconds = time.perf_counter() - t

t = time.perf_counter()
k, kt = kruskal_mst(nodes, edges)
kruskal_seconds = time.perf_counter() - t

out = ROOT / "results"
out.mkdir(exist_ok=True)
edges.to_csv(out / "complete_graph_edges.csv", index=False)
p.to_csv(out / "prim_mst_edges.csv", index=False)
k.to_csv(out / "kruskal_mst_edges.csv", index=False)

prim_checks = validate_mst(nodes, p)
kruskal_checks = validate_mst(nodes, k)
weights_agree = abs(pt - kt) < 1e-7

report = {
    "node_count": len(nodes),
    "candidate_edge_count": len(edges),
    "expected_mst_edges": max(0, len(nodes) - 1),
    "prim_edge_count": len(p),
    "kruskal_edge_count": len(k),
    "prim_total_km": pt,
    "kruskal_total_km": kt,
    "absolute_total_difference_km": abs(pt - kt),
    "prim_runtime_seconds": round(prim_seconds, 4),
    "kruskal_runtime_seconds": round(kruskal_seconds, 4),
    "edge_generation_seconds": round(edge_seconds, 4),
    "prim_checks": prim_checks,
    "kruskal_checks": kruskal_checks,
    "totals_agree": bool(weights_agree),
    "validation_passed": bool(
        all(prim_checks.values()) and all(kruskal_checks.values()) and weights_agree
    ),
    "weight_definition": "Haversine straight-line distance in kilometres",
    "caveat": "Not road distance, travel time, actual financial cost, or emergency response time.",
}
(out / "validation_report.json").write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
if not report["validation_passed"]:
    raise SystemExit("MST validation failed")
