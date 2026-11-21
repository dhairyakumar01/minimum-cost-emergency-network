# Minimum-Cost Emergency Communication Network Using Minimum Spanning Tree (MST)
## Bengaluru BBMP Emergency Infrastructure Optimization — Execution & Demonstration Guide

---

## 📌 Project Overview

This project implements a graph-theoretic **Minimum-Cost Emergency Communication Network** for the **1,255 municipal emergency facilities** across Bengaluru (BBMP jurisdiction), spanning:
- **Police Stations**
- **Fire Stations**
- **Government & Multi-Specialty Hospitals**

The system models the facility topology as a complete weighted graph $K_{1255}$ containing **786,885 edges** (with weights computed via high-precision Haversine distance), and extracts the optimal communication backbone using **Prim's** and **Kruskal's** Minimum Spanning Tree algorithms.

### Key Architectural Invariants & Benchmark Values
- **Facility Count ($V$):** 1,255 vertices
- **Complete Graph Edges ($E$):** $\frac{V(V-1)}{2} = \frac{1255 \times 1254}{2} = 786,885$ edges
- **MST Edge Count:** Exactly $V - 1 = 1,254$ edges
- **Total Minimum Network Weight ($W$):** $480.1784\text{ km}$ (exact to $\le 10^{-6}\text{ km}$ between Prim and Kruskal)
- **Frontend Architecture:** Lightweight Vanilla JS (ES6+), HTML5, Leaflet 1.9.4, Chart.js — **zero Node.js/npm dependencies**
- **Backend Architecture:** Python Flask 3.0+ REST API with route caching in SQLite

---

## 🤖 1. Quick Start for Antigravity AI Assistants

If you are receiving this project and running it inside **Antigravity**, simply open this folder and give your Antigravity assistant the following prompt:

```text
Please inspect this project, install dependencies from requirements.txt if needed, run the automated test suite with pytest tests/, and start the Flask web server in the background using python backend/flask_app.py. Confirm that the server is responding on http://127.0.0.1:5000 and provide the local access link so I can open the application in my browser.
```

### What Antigravity Will Automatically Do:
1. Validate the Python 3.10+ runtime.
2. Run `pytest tests/` (all **107 unit, regression, and algorithmic parity tests** pass in ~12 seconds).
3. Start `backend/flask_app.py` as a background daemon process.
4. Verify HTTP 200 OK from `http://127.0.0.1:5000/api/health`.
5. Deliver the local web link (`http://127.0.0.1:5000`) ready for interactive demonstration.

---

## ⚡ 2. Quick Start for Human Users (One-Click Launch)

### On Windows
1. Double-click the file:
   ```cmd
   run_server.bat
   ```
2. The script will check Python, install required packages quietly, start the Flask server, and automatically open your default browser to `http://127.0.0.1:5000`.

### On macOS / Linux
1. Open a terminal in the project directory and run:
   ```bash
   chmod +x run_server.sh run_tests.sh
   ./run_server.sh
   ```
2. The script will start the Flask server and launch the web interface in your browser.

---

## 💻 3. Manual Step-by-Step Installation

If you prefer using your terminal manually:

### Prerequisites
- **Python 3.10, 3.11, or 3.12** installed on your system.
- Modern web browser (Google Chrome, Microsoft Edge, Mozilla Firefox, or Safari).

### Step 1: Clone or Extract the Archive
Extract the project archive to any directory on your computer and navigate into it:
```bash
cd minimum_cost_emergency_network
```

### Step 2: (Recommended) Create a Virtual Environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Required Dependencies
```bash
pip install -r requirements.txt
```

*Key dependencies: `flask`, `requests`, `pandas`, `numpy`, `plotly`, `folium`, `pytest`.*

### Step 4: Launch the Server
```bash
python backend/flask_app.py
```

You will see:
```text
=======================================================
  Emergency Communication Network — Flask Web Server
  URL: http://127.0.0.1:5000
  Health Check: http://127.0.0.1:5000/api/health
  Facilities API: http://127.0.0.1:5000/api/facilities
  Global MST API: http://127.0.0.1:5000/api/mst/full
=======================================================
 * Running on http://127.0.0.1:5000
```

### Step 5: Open the Application in Your Browser
Open your browser and navigate to:
```
http://127.0.0.1:5000
```
*(or `http://localhost:5000`)*

---

## 🧪 4. Running the Automated Test Suite

The project includes an exhaustive suite of **107 unit, regression, algorithm validation, and API contract tests**.

To execute the test suite:
```bash
# Windows
run_tests.bat
# or
python -m pytest tests/ -v

# macOS / Linux
./run_tests.sh
# or
pytest tests/ -v
```

### Expected Output
```text
============================= test session starts =============================
platform win32 / linux -- Python 3.11+, pytest-9.x
rootdir: .../minimum_cost_emergency_network
collected 107 items

tests/test_adversarial_suite.py .............                            [ 12%]
tests/test_experiments.py ....                                           [ 15%]
tests/test_flask_backend.py .................                            [ 31%]
tests/test_local_comparison.py ......                                    [ 37%]
tests/test_mst.py ...........................                            [ 62%]
tests/test_phase1_6_audit.py ......                                      [ 68%]
tests/test_scenario_pipeline.py ..                                       [ 70%]
tests/test_simulation.py ..............                                  [ 83%]
tests/test_simulator.py .....                                            [ 87%]
tests/test_transportation_cost.py .............                          [100%]

============================ 107 passed in ~12s ===============================
```

### Key Properties Verified by Tests
1. **Tree Edge-Count Property:** A connected spanning tree on $V$ vertices strictly contains $V - 1$ edges ($E = 1,254$ for $V = 1,255$).
2. **Weight Equivalence:** Total weight computed by Prim's equals Kruskal's ($480.1784\text{ km}$) within floating-point tolerance ($< 10^{-6}$).
3. **Cycle Property:** For every non-tree edge $(u, v)$ with weight $w$, all tree edges on the unique path between $u$ and $v$ have weight $\le w$.
4. **Cut Property:** Every tree edge is a minimum-weight link crossing some cut of the graph.
5. **Deterministic Tie-Breaking:** Endpoints are lexicographically sorted to guarantee identical output regardless of graph storage order.
6. **Integer Decisecond & Millimetre Precision:** Route durations and distances use exact integer units internally before display conversion.

---

## 🗺️ 5. Walkthrough of the Application (Faculty Demonstration Guide)

The web application is structured into **5 integrated views**, accessible via the top navigation bar:

### 1. 📊 System Dashboard
- **Executive Summary:** Live metrics displaying 1,255 geocoded facilities, 786,885 edges reduced to 1,254 MST links.
- **Algorithm Equivalence Banner:** Visual confirmation that Prim's and Kruskal's algorithms yield identical total weight ($480.1784\text{ km}$).
- **Facility Distribution Chart:** Breakdown of facilities across Police, Fire, and Healthcare agencies.
- **System Telemetry:** Real-time backend status, memory footprint, and route cache hit rate.

### 2. 🗺️ Facilities Map
- **Geocoded Bengaluru Map:** Interactive Leaflet canvas plotting all 1,255 facilities.
- **Agency Color Coding & Filters:**
  - 🔵 Blue: Police Stations (Law enforcement & traffic hubs)
  - 🔴 Red: Fire Stations (Fire & rescue response centres)
  - 🟢 Green: Hospitals (Government, multi-specialty, trauma centres)
- **Search & Selection:** Click any marker to view facility details, coordinates, and contact metadata.
- **Map Toolbar:** Quick-action controls for Fullscreen, Fit Bounds, Reset View, and Layer toggling.

### 3. 🌐 MST Network & Step-by-Step Algorithm Construction Simulator
This page offers two distinct modes via tab controls:
- **Tab A — Global Static MST:**
  - Displays the full 1,254-link minimum spanning tree across Bengaluru.
  - Interactive edge inspection, showing endpoints, link length in km, and agency types.
  - Complete edge list table with search and pagination.
- **Tab B — Algorithm Construction Simulator (Interactive Visualizer):**
  - **Live Step-by-Step Visualization:** Demonstrates the internal mechanics of Prim's and Kruskal's algorithms on realistic Bengaluru subgraphs (Koromangala, Indiranagar, Whitefield, Central, etc.).
  - **Prim's Algorithm Mode:** Visualizes the growing tree boundary (cut frontier), candidate heap edges, and the greedy selection of the minimum cut-crossing link.
  - **Kruskal's Algorithm Mode:** Visualizes global edge sorting, Disjoint Set Union (DSU) component merging, and **Cycle Rejection** (highlighting the completed fundamental cycle when an edge is discarded).
  - **VCR Controls:** Play/Pause, Step Forward, Step Backward, Reset, and adjustable Speed slider (0.5x to 5x).
  - **Decision Audit Log:** Plain-English explanation for every single accepted or rejected edge.

### 4. 🚨 Incident Simulation & Emergency Dispatch
- **Incident Scenario Configuration:**
  - Set incident location (click on map or choose presets: Majestic, Electronic City, Whitefield, MG Road, Hebbal).
  - Select incident type: Fire Emergency, Law & Order, Medical/Trauma.
  - Configure operational search radius (e.g., 5 km to 20 km) and traffic multiplier.
- **Recommended Facility Hero Card (#1 Dispatch):**
  - Dominant hero card displaying the optimal primary responding facility.
  - Shows estimated road transit time (OSRM driving route) vs direct Haversine distance.
  - Clear rationale badge (fastest response time, resource suitability).
- **Secondary Alternatives (#2 and #3):**
  - Ranked backup facilities displayed for multi-unit escalation or contingency routing.
- **Interactive Dual Map:**
  - **Dispatch Route View:** High-visibility polyline tracing actual Bengaluru road driving route from facility to incident.
  - **Local Emergency MST View:** Shows the minimum-cost communication tree connecting all facilities in the incident zone ($E = V - 1$).
- **Collapsible Technical Pipeline:**
  - Complete candidate dispatch evaluation table and incident MST edge ledger tucked inside a clean, modern accordion.

### 5. 📈 Results, Statistics & Methodology Guide
- **Comparative Performance Benchmarks:** Execution runtime, memory scaling, and edge-evaluation count between Prim's and Kruskal's algorithms.
- **Scalability Analysis:** Graph density analysis demonstrating $\mathcal{O}(E \log V)$ vs $\mathcal{O}(V^2)$ behavior.
- **Formal Mathematical Reference:**
  - Cayley's Theorem & Spanning Tree Edge Count ($V - 1$).
  - Cut Property Proof & Prim's correctness invariant.
  - Cycle Property Proof & Kruskal's cycle-avoidance invariant.
  - High-Precision Haversine geodesic distance formulation.

---

## 🔌 6. REST API Endpoints Reference

The backend provides clean JSON REST APIs that can be queried directly:

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/health` | `GET` | Health check, server uptime, cache status |
| `/api/facilities` | `GET` | All 1,255 geocoded emergency facilities |
| `/api/facilities/<id>` | `GET` | Single facility details and metadata |
| `/api/mst/full` | `GET` | Global 1,254-edge MST with pre-computed statistics |
| `/api/simulator/data` | `GET` | Algorithmic step trace data for Prim & Kruskal simulator |
| `/api/simulate` | `POST` | Execute incident dispatch simulation and local MST generation |
| `/api/network` | `GET` | Live telemetry, edge statistics, and component counts |

---

## 📁 7. Project Directory Structure

```text
minimum_cost_emergency_network/
│
├── backend/                        # Flask 3.0+ REST API Application
│   ├── flask_app.py                # Server entry point & static SPA router
│   ├── config.py                   # Configuration constants & path bindings
│   └── routes/                     # Blueprint API handlers
│       ├── health.py               # Health & telemetry endpoints
│       ├── facilities.py           # Facility query & filter endpoints
│       ├── network.py              # MST & graph computation endpoints
│       └── scenarios.py            # Dynamic incident simulation endpoints
│
├── frontend/                       # Client-Side Single Page Application
│   ├── index.html                  # Semantic HTML5 single-page layout
│   └── assets/
│       ├── css/
│       │   ├── style.css           # Master stylesheet (clean 3-level visual hierarchy)
│       │   └── simulator.css       # Algorithm Construction Simulator styling
│       └── js/
│           ├── app.js              # Application state & page router
│           ├── dashboard.js        # Dashboard statistics & charts
│           ├── facilities_map.js   # Leaflet facilities mapping & clustering
│           ├── mst_network.js      # Global MST visualization & edge inspection
│           ├── simulator.js        # Step-by-step Prim & Kruskal interactive visualizer
│           ├── simulation.js       # Incident dispatch & local MST simulation
│           └── results.js          # Results, telemetry & methodology guide
│
├── src/                            # Core Algorithmic & Mathematical Library
│   ├── mst_network.py              # Prim's & Kruskal's algorithms with decision tracing
│   ├── simulation.py               # Incident dispatch pipeline & candidate ranking
│   ├── validation.py               # Tree invariants, cycle property, & cut property verifiers
│   └── graph_utils.py              # Haversine distance & graph builder utilities
│
├── data/                           # Facility Datasets & Local Caches
│   ├── processed/
│   │   └── emergency_facilities.csv # 1,255 validated, geocoded Bengaluru facility records
│   └── cache/
│       └── routes.db               # Pre-computed SQLite OSRM road route cache
│
├── tests/                          # Automated Verification Suite (107 Tests)
│   ├── test_mst.py                 # Prim & Kruskal correctness, invariants, tie-breaking
│   ├── test_simulator.py           # Visualizer trace contract and cycle-path tests
│   ├── test_simulation.py          # Incident dispatch calculation tests
│   ├── test_flask_backend.py       # REST API contract and status tests
│   ├── test_adversarial_suite.py   # Edge cases, disconnected graphs, collinear coordinates
│   └── test_local_comparison.py    # Cut and cycle property formal verification
│
├── docs/                           # Academic Project Documentation
│   ├── PROJECT_REPORT.md           # Full engineering and mathematical report
│   └── DEMO_SCRIPT.md              # 5-minute academic presentation script
│
├── requirements.txt                # Python package dependencies
├── run_server.bat                  # 1-Click Windows server launcher
├── run_server.sh                   # 1-Click macOS/Linux server launcher
├── run_tests.bat                   # 1-Click Windows test runner
├── run_tests.sh                    # 1-Click macOS/Linux test runner
└── HOW_TO_RUN.md                   # This comprehensive execution guide
```

---

## 🔧 8. Frequently Asked Questions & Troubleshooting

### Q1: The server says `Address already in use` (Port 5000 is occupied).
**Solution:** You can launch the server on an alternate port using the `PORT` environment variable:
```bash
# Windows (PowerShell)
$env:PORT="5001"; python backend/flask_app.py

# Windows (Command Prompt)
set PORT=5001 && python backend/flask_app.py

# macOS / Linux
PORT=5001 python3 backend/flask_app.py
```
Then open `http://127.0.0.1:5001` in your browser.

### Q2: Is an active internet connection required?
**No.** All 1,255 facility coordinates are stored locally in `data/processed/emergency_facilities.csv`, and road routes are cached in `data/cache/routes.db`. The application operates fully offline. If an uncached route is requested, it gracefully falls back to the high-precision Haversine transit estimate.

### Q3: Why does the MST have exactly 1,254 edges?
**Mathematical Principle:** By fundamental graph theory (Cayley's theorem and the tree edge-count property), any minimally connected, acyclic graph spanning $V$ distinct vertices strictly contains $V - 1$ edges:
$$E = V - 1 = 1255 - 1 = 1254$$
Both Prim's and Kruskal's algorithms independently terminate at exactly 1,254 edges with an identical total weight of **480.1784 km**.

---

*Bengaluru BBMP Minimum-Cost Emergency Communication Network Project — Faculty Demonstration Release.*
