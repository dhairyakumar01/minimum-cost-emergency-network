# Minimum-Cost Emergency Communication Network Using MST

## Implemented prototype
This project loads the combined facility CSV, validates IDs and coordinates, computes pairwise Haversine distances, runs custom Prim and Kruskal algorithms, compares results, and saves CSV/JSON outputs.

## Run on macOS
1. Unzip this project and open Terminal in the extracted folder.
2. Create a virtual environment: `python3 -m venv .venv`
3. Activate it: `source .venv/bin/activate`
4. Install dependency: `python -m pip install -r requirements.txt`
5. Run: `python run_analysis.py`

## Outputs
- `results/complete_graph_edges.csv`: every candidate edge in the complete graph
- `results/prim_mst_edges.csv`: edges selected by Prim
- `results/kruskal_mst_edges.csv`: edges selected by Kruskal
- `results/validation_report.json`: counts, total weights, runtimes, and validation result

## Current run (provided dataset)
- Vertices: 1,255 facilities
- Candidate edges in complete graph: 786,885
- MST edges expected and produced by both algorithms: 1,254
- Prim total: approximately 480.1784 km
- Kruskal total: approximately 480.1784 km
- Difference in totals: approximately 0 (floating-point rounding only)
- Validation: passed

## Modelling limitations
Weights are straight-line geographic distances in kilometres, not actual financial cost, road distance, traffic-aware travel time, or emergency-response time. The complete graph is a mathematical model, not an actual communications/road network. An MST does not provide redundant paths if an edge fails. Review unnamed and flagged facility records and the study-area boundary before final reporting. Preserve source attribution and review OpenStreetMap licence/ODbL obligations before publication.
