# Minimum-Cost Emergency Communication Network Using Minimum Spanning Tree (MST)

**Study Area:** Bruhat Bengaluru Mahanagara Palike (BBMP), Karnataka, India  
**Academic Domain:** Discrete Mathematics and Graph Theory (DMGT) Experiential Learning  
**Backend:** Python 3.11 + Flask REST Framework  
**Frontend:** HTML5 + CSS3 + Vanilla ES6 JavaScript + Leaflet.js (Multi-Scale MarkerCluster)  
**Routing Engine:** Open Source Routing Machine (OSRM) + SQLite Persistent Route Cache  
**Test Suite:** 89 Automated Tests Passed / 89 Total (100% Pass Rate)

---

## 1. Executive Summary

This project implements a decision-support and network-planning web application for the metropolitan area of Bengaluru, Karnataka, India. The system addresses two fundamentally distinct graph-theoretical problems:
1. **Network Backbone Topology (Layer 1):** Designing a minimum-cost, fault-resilient communication/interconnection backbone connecting critical emergency facilities (spanning all 1,255 facilities globally, or an incident-specific candidate cluster).
2. **First-Response Dispatch Routing (Layer 2):** Determining the optimal dispatch ranking of emergency vehicles from existing stations directly to an incident scene over the directed urban road network.

These two objectives are strictly decoupled in the architecture and user interface.

---

## 2. Core Features & Capabilities

- **1,255 BBMP Emergency Facilities:** Verified registry containing 1,097 hospitals and clinics, 138 police stations, and 20 fire stations with 0 coordinate errors (SHA-256: `293930b3db46e55910f68494a3c7bd6652a9af0ff7fa06a761f94d9bec78d943`).
- **Global Haversine MST:** Precomputed 1,254-edge minimal spanning tree on $K_{1255}$ ($786,885$ candidate links) using integer millimetre edge weights $w = \operatorname{round\_half\_up}(d_{\text{km}} \times 10^6)$ and strict tie-breaking $(w, \min(u,v), \max(u,v))$. Kruskal and Prim achieve exact weight parity: **480,178,397 mm** (480.1784 km).
- **LCA Binary-Lifting Optimality Oracle:** Complete tree verification testing all 785,631 non-tree candidate chords against tree path maximums ($O(\log V)$ per query), proving 0 cycle property violations.
- **8-Stage Road-Routing Scenario Pipeline:**
  - Snaps incident coordinates and candidate facilities to the OpenStreetMap road network.
  - Queries OSRM Table API with failover to local or public endpoints.
  - Formulates symmetric undirected edges $S_T(i, j) = T(i, j) + T(j, i)$ and $S_D(i, j) = D(i, j) + D(j, i)$.
  - Supports **3 discrete optimization modes**:
    1. **Mode 1: Minimum Response Time** ($S_T$)
    2. **Mode 2: Minimum Road Distance** ($S_D$)
    3. **Mode 3: Compromise Multi-Objective** ($N_e = k S_T D^* + (10 - k) S_D T^*$) with trade-off curve and regrets.
  - *Proof of Cost Mode Exclusion:* Proves that under Karnataka Gazette FD 31 CSL 2024 diesel benchmarks (₹88.94/L), single-agency fuel cost scaling is strictly isomorphic to road distance, rendering a 4th mode mathematically redundant.
- **Independent Dispatch Ranking:** Facilities ranked strictly by direct travel time $(T(F \to I), D(F \to I), \text{facility\_id})$ with assumed fuel expenditure, detour ratios, and vehicle specifications.
- **4-Tab Simulation Workspace:**
  1. *Tab 1: Dispatch Ranking* (Default view with Top 3 cards and complete ranking table)
  2. *Tab 2: Network Backbone* (MST/Forest edges, $V-1$ invariant, Kendall $\tau_b$ correlation, stretch ratios)
  3. *Tab 3: Mathematical Validation* (Structural tree check, LCA cycle property optimality, Prim/Kruskal parity)
  4. *Tab 4: Candidates & Exclusions* (Documented reconciliation of every BBMP facility with reason codes)
- **SQLite Persistent Caching:** Automatic decisecond/decimetre route caching in `data/cache/routes.db` and scenario storage in `data/scenarios.db`.

---

## 3. Quickstart & Installation

### Step 1: Environment Setup
```powershell
# Navigate to repository root
cd minimum_cost_emergency_network

# Activate Python 3.11 virtual environment
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Start Flask Web Server (Primary Interface)
```powershell
python backend/flask_app.py
```
Open **`http://127.0.0.1:5000`** in your web browser.

### Step 3: Run Legacy Streamlit Server (Optional Baseline)
```powershell
streamlit run app.py --server.port 8501
```
Open **`http://127.0.0.1:8501`** in your browser.

---

## 4. Running the Automated Test Suite

The test suite covers unit testing, graph invariants, routing failover, and end-to-end scenario pipeline execution:

```powershell
pytest tests/ -v
```
All **89 tests pass in ~13 seconds**.

---

## 5. Mathematical & Algorithmic Results

| Metric | Kruskal's Algorithm | Prim's Algorithm | Verification Status |
| :--- | :--- | :--- | :--- |
| **Vertices ($|V|$)** | 1,255 | 1,255 | Exact match |
| **Complete Graph Edges ($|E|$)** | 786,885 | 786,885 | $\binom{1255}{2}$ |
| **MST Spanning Edges ($|E_T|$)** | 1,254 | 1,254 | Exact Cayley invariant ($|V| - 1$) |
| **Total Tree Integer Weight** | 480,178,397 mm | 480,178,397 mm | **Exact Parity** |
| **Total Tree Metric Length** | 480.178397 km | 480.178397 km | **Exact Parity** |
| **Cycle Property Chords Tested** | 785,631 | 785,631 | 0 Violations (100% Optimal) |

---

## 6. Documentation Directory Index

Detailed technical reports and mathematical proofs are located in [`docs/`](docs/):
- [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md): Mathematical formulations, integer arithmetic, OSRM routing, 3 optimization modes, proof of cost-mode exclusion, and LCA oracle.
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md): Multi-tier system architecture, Flask blueprints, database schemas, and API documentation.
- [`docs/VERIFICATION_REPORT.md`](docs/VERIFICATION_REPORT.md): Cryptographic dataset audit, global MST parity proof, and 89-test verification summary.
- [`docs/DEPLOYMENT_GUIDE.md`](docs/DEPLOYMENT_GUIDE.md): Operations manual, environment setup, WSGI configuration, and OSRM deployment options.
- [`docs/KNOWN_LIMITATIONS.md`](docs/KNOWN_LIMITATIONS.md): Bounding box constraints, traffic model assumptions, and fleet rate constraints.
- [`docs/FINAL_IMPLEMENTATION_INVENTORY.md`](docs/FINAL_IMPLEMENTATION_INVENTORY.md): Comprehensive inventory of code assets, tests, and deliverables.
- [`reports/benchmarks/benchmark_summary.json`](reports/benchmarks/benchmark_summary.json): Measured performance numbers, memory footprint, and execution runtimes.
