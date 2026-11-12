# Minimum-Cost Emergency Communication Network Using MST

## Project Overview
This project models and optimizes a regional emergency communication network linking 1,255 public safety and healthcare facilities across the Bengaluru metropolitan region using Minimum Spanning Tree (MST) algorithms.

The network models 1,097 hospitals and clinics, 138 police stations, and 20 fire stations as a complete undirected weighted graph $K_{1255}$ with 786,885 candidate transmission links. Edge weights are computed using the spherical Haversine distance formula with Earth radius $R = 6,371.0088\text{ km}$. Custom implementations of Prim's and Kruskal's algorithms are verified through an independent 8-point structural validation suite.

## Application Architecture (Six Functional Screens)
1. **Dashboard (`/dashboard`):** Real-time metrics, facility distributions by category, candidate and MST edge counts, algorithm runtimes, and graph connectivity status.
2. **Facilities Map (`/facilities-map`):** Interactive Folium GIS map with multi-select category filters, full-text fuzzy search by facility name or OpenStreetMap ID, and individual attribute inspection.
3. **MST Network (`/mst-network`):** Geospatial visualization of the computed spanning tree with Prim/Kruskal toggle, layer controls, longest 10 transmission links table, and CSV download.
4. **Emergency Incident Simulation (`/simulation`):** Dynamic multi-agency responder selection and MST communication path reconstruction. Users can place an incident anywhere via interactive map clicking or manual coordinate inputs. Responders are assigned based on scenario (Fire, Medical Emergency, Road Accident) and unique tree paths are reconstructed across the MST without modifying the base network.
5. **Algorithm Comparison & Validation (`/comparison`):** Side-by-side performance evaluation of Prim vs. Kruskal, edge length distributions, 8-point independent structural validation results, data quality audits, and execution environment architectural analysis.
6. **Experimental Laboratory (`/laboratory`):** Two-part empirical research harness:
   - **Tab 1: Scalability Benchmark:** Evaluates complete geometric subgraphs from $N = 50$ to $N = 1,255$, interactive Plotly runtime and distance curves, and trial-level telemetry exports.
   - **Tab 2: Controlled Graph-Density Experiment (Approach C):** Controlled non-tree edge sparsification across 7 density levels ($\rho \in [0.0, 1.0]$) and 3 independent seeds on 786,885 edges, verifying algorithmic runtime scaling while preserving the invariant 480.1784 km MST backbone.

## Quickstart & Execution

### 1. Installation
```bash
# Clone / navigate to project directory
cd minimum_cost_emergency_network

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 2. Run the Analysis Pipeline
```bash
# Recomputes complete graph, Prim and Kruskal MSTs, and independent validation
python run_analysis.py
```

### 3. Run Benchmark Trials
```bash
# Executes 10-trial performance benchmark
python benchmark.py
```

### 4. Run Automated Test Suite
```bash
# Executes 24 unit tests covering Haversine, MST correctness, simulations, and experiments
python -m pytest -v
```

### 5. Launch Interactive Website
```bash
# Starts the Streamlit application on localhost port 8501
python -m streamlit run app.py --server.headless true --server.port 8501
```
Open **`http://localhost:8501`** in your browser.

## Verified Results Summary (Provided Dataset)
- **Vertices (|V|):** 1,255 emergency facilities
- **Candidate Edges (|E|):** 786,885 links ($V(V-1)/2$)
- **MST Edges (|V| - 1):** 1,254 spanning links
- **Prim Total Distance:** 480.1784 km
- **Kruskal Total Distance:** 480.1784 km
- **Discrepancy:** $5.68 \times 10^{-14}\text{ km}$ (floating-point summation rounding)
- **Edge Identity:** 1,254 of 1,254 edges (100.0%) identical between Prim and Kruskal
- **Median Runtime (10 runs):** Kruskal: 1.5811 s  |  Prim: 5.0293 s
- **Independent Validation:** 8 / 8 Checks Passed

## Modelling Limitations
- Edge weights are spherical Haversine straight-line distances in kilometres. They do not represent actual financial construction costs, street-network driving distances, traffic congestion, or ambulance travel times.
- An MST connects all nodes with minimal total distance but contains zero cycles. Severing any edge partitions the network into two disconnected components (no path redundancy).
- The complete graph is a theoretical optimization model assuming feasible communication channels between any two facilities.
