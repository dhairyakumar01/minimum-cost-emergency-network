"""Repeated timing of Prim vs Kruskal on the real facility graph.

Run from the project root:  python benchmark.py
Edge generation is excluded; both algorithms receive the same prebuilt
candidate-edge table. Results go to results/benchmark.json.
"""
import json
import platform
import statistics
import sys
import time
from pathlib import Path

from src.mst_network import build_complete_edges, kruskal_mst, load_facilities, prim_mst

RUNS = 10
ROOT = Path(__file__).resolve().parent

nodes = load_facilities(ROOT / "data/processed/emergency_facilities.csv")
edges = build_complete_edges(nodes)

# Warm-up run (not recorded)
prim_mst(nodes, edges)
kruskal_mst(nodes, edges)

prim_times, kruskal_times = [], []
for i in range(RUNS):
    t = time.perf_counter()
    prim_mst(nodes, edges)
    prim_times.append(time.perf_counter() - t)

    t = time.perf_counter()
    kruskal_mst(nodes, edges)
    kruskal_times.append(time.perf_counter() - t)
    print(f"run {i + 1}/{RUNS}: prim {prim_times[-1]:.3f}s, kruskal {kruskal_times[-1]:.3f}s")


def stats(xs):
    return {
        "min": round(min(xs), 4),
        "median": round(statistics.median(xs), 4),
        "mean": round(statistics.mean(xs), 4),
        "stdev": round(statistics.stdev(xs), 4),
    }


result = {
    "runs": RUNS,
    "node_count": len(nodes),
    "candidate_edge_count": len(edges),
    "prim_seconds": stats(prim_times),
    "kruskal_seconds": stats(kruskal_times),
    "python": sys.version.split()[0],
    "platform": platform.platform(),
    "note": "Edge generation excluded. Timings depend on this machine and "
    "its load at the time; they are not general performance claims.",
}

(ROOT / "results").mkdir(exist_ok=True)
(ROOT / "results/benchmark.json").write_text(json.dumps(result, indent=2))
print(json.dumps(result, indent=2))
