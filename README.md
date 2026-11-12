# Minimum-Cost Emergency Communication Network Using Minimum Spanning Tree (MST)

**Study Area:** Bruhat Bengaluru Mahanagara Palike (BBMP), Karnataka, India  
**Academic Focus:** Discrete Mathematics and Graph Theory (DMGT) Experiential Learning  
**Backend:** Python 3.11 + Flask REST Architecture  
**Frontend:** HTML5 + CSS3 + Vanilla JavaScript + Leaflet.js (Multi-Scale MarkerCluster)  
**Fallback Baseline:** Streamlit GIS Application (Port 8501)  

---

## 1. Project Overview

This project models and optimizes a regional emergency communication network linking **1,255 public safety and acute healthcare facilities** across the metropolitan area of Bengaluru using Minimum Spanning Tree (MST) algorithms.

The network models 1,097 hospitals and clinics, 138 police stations, and 20 fire stations as an undirected complete graph $K_{1255}$ containing **786,885 candidate transmission links**. Edge weights are defined as spherical great-circle geographic distances computed via the Haversine formula ($R = 6,371.0088\text{ km}$).

Custom, self-contained implementations of **Prim's** and **Kruskal's** algorithms converge on an identical total network distance of **480.1784 km** across exactly **1,254 spanning edges** ($|V| - 1$ Cayley tree invariant), differing by only $5.68 \times 10^{-14}\text{ km}$ due to floating-point rounding.

---

## 2. Dual-Layer Infrastructure Architecture

The project strictly segregates two distinct operational layers:
- **Layer 1: Communication Backbone (Minimum Spanning Tree):**
  An acyclic spanning tree connecting all 1,255 facilities with 1,254 links totaling **480.1784 km**. Represents a municipal microwave RF / optical fiber coordination backbone minimizing capital deployment outlay.
- **Layer 2: Vehicular Transit Network (Physical Road Routing):**
  The actual urban roadway network traversed by emergency vehicles (ambulances, police cruisers, fire engines), governed by one-way restrictions, speed limits, and street topology ($D_{\text{road}} \ge D_{\text{haversine}}$).

---

## 3. Web Application Modules (Six Single-Page Views)

1. **📊 System Dashboard (`#dashboard`):** Real-time metrics (1,255 facilities, 1,254 MST connections, 480.1784 km), dual-layer model overview, agency distribution bars, and the mathematical proof of balanced optimization equivalence.
2. **🗺️ Facilities Map (`#facilities-map`):** Interactive Leaflet GIS map with multi-scale marker clustering, agency filter toggles, fuzzy text search, draggable pulsating incident selection pin, live coordinate tracking, landmark presets, and live incident-to-facility Haversine distance inspection.
3. **🕸️ MST Network (`#mst-network`):** Geospatial visualization of all 1,254 precomputed global MST links with Kruskal/Prim toggles, prominent architectural disclaimer, and an interactive floating Edge Inspector card detailing Cut/Cycle Property rationales.
4. **🚨 Emergency Simulation Setup (`#simulation`):** A 6-step interactive workflow covering incident coordinates, emergency category, single-agency dispatch constraint, configurable radius slider ($R_s = 2.0 - 15.0\text{ km}$), optimization mode selection, and a top-3 candidate dispatch staging preview.
5. **📈 Project Analysis & Results (`#project-analysis`):** Comparative mathematical audit table (Prim vs. Kruskal), algorithmic complexity analysis, zero-weight edge investigation, and the 785,631-edge LCA optimality certificate.
6. **❓ Help & Methodology (`#help`):** Complete documentation of graph formulations, statutory fuel benchmarks (GOK Notification No. FD 31 CSL 2024 at ₹88.94/L), agency fleet rates (Ambulance ₹12.50/km, Police ₹6.25/km, Fire ₹18.00/km), and the balanced equivalence proof.

---

## 4. Quickstart & Execution

### 4.1 Prerequisites & Installation
```powershell
# Navigate to project directory
cd minimum_cost_emergency_network

# Activate Python 3.11 virtual environment
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 4.2 Starting the Web Application (Primary Production Interface)
```powershell
python backend/flask_app.py
```
Open **`http://127.0.0.1:5000`** in your browser.

### 4.3 Starting the Streamlit Baseline (Fallback Reference)
```powershell
python -m streamlit run app.py --server.headless true --server.port 8501
```
Open **`http://localhost:8501`** in your browser.

### 4.4 Running Automated Verification Test Suites
```powershell
# Run complete 87-test pytest suite
python -m pytest tests/

# Run headless Playwright browser verification
python test_phase1_5_browser.py
```

---

## 5. Verified Results & Performance Metrics

| Metric | Kruskal's Algorithm | Prim's Algorithm | Parity / Invariant |
| :--- | :--- | :--- | :--- |
| **Vertices ($|V|$)** | 1,255 | 1,255 | Exact match |
| **Complete Graph Edges ($|E|$)** | 786,885 | 786,885 | $V(V-1)/2$ |
| **MST Spanning Edges ($|E_T|$)** | 1,254 | 1,254 | Exact Cayley invariant ($|V| - 1$) |
| **Total Tree Length** | 480.1783984126 km | 480.1783984126 km | $\Delta = 5.68 \times 10^{-14}\text{ km}$ |
| **Minimum Edge** | 0.0000 km | 0.0000 km | Co-located facility pair |
| **Maximum Edge** | 7.8256 km | 7.8256 km | Budigere Hosp $\leftrightarrow$ Vikrant Hosp |
| **Median Runtime (10 runs)** | **1.5811 s** (3.18× faster) | **5.0293 s** | Native mergesort vs. Python heap |
| **Cycle Property Test** | 0 violations (785,631 edges) | 0 violations | LCA binary-lifting certificate |

---

## 6. Technical Documentation Index

Detailed engineering reports and demonstration scripts are located in the [`docs/`](docs/) directory:
- [`docs/final_methodology.md`](docs/final_methodology.md): Full mathematical formulation, graph theory definitions, distance metrics, and balanced equivalence proof.
- [`docs/system_architecture.md`](docs/system_architecture.md): Architectural block diagrams, sequence diagrams, REST API specs, and data layer specifications.
- [`docs/algorithm_analysis.md`](docs/algorithm_analysis.md): Theoretical and empirical evaluation of Prim vs. Kruskal, mergesort vs. binary heap, scaling curves, and LCA verification.
- [`docs/data_documentation.md`](docs/data_documentation.md): OpenStreetMap provenance, coordinate validation, duplicate coordinate investigation, and data boundaries.
- [`docs/limitations.md`](docs/limitations.md): Explicit disclosure of traffic, routing, facility capacity, and network survivability limitations.
- [`docs/faculty_demo_guide.md`](docs/faculty_demo_guide.md): 15-step faculty presentation protocol with talking points and anticipated defense Q&A.
- [`docs/final_test_summary.md`](docs/final_test_summary.md): Test execution logs, Playwright output, and 12-case mathematical audit matrix.
- [`docs/final_completion_report.md`](docs/final_completion_report.md): Final executive handover report.

---

## 7. Methodological Limitations

- **Conceptual Model:** The global MST represents a theoretical communication backbone, not a civil engineering trenching blueprint or vehicular response route.
- **Topological Redundancy:** As an acyclic tree ($k=1$), severing any single link partitions the network.
- **Traffic Speeds:** Road transit durations reflect free-flow speed limits, not live time-varying congestion.
- **Fuel-Only Cost:** Operating cost ($C = D \times R_a$) models marginal diesel consumption under the ₹88.94/L statutory benchmark, excluding capital depreciation and crew payroll.
