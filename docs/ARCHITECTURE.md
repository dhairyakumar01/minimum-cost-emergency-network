# System Architecture Documentation
**Project:** Minimum-Cost Emergency Communication Network Using Minimum Spanning Tree (MST)  
**Study Area:** BBMP Bengaluru, Karnataka, India  
**Technology Stack:** Python 3.11 + Flask, SQLite, HTML5, CSS3, Vanilla ES6 JavaScript, Leaflet.js, OSRM

---

## 1. High-Level System Architecture

The platform is architected as a lightweight, modular, decoupled web system consisting of:
1. **Presentation Layer (Frontend):** Responsive Single-Page Application (SPA) driven by Vanilla JavaScript and Leaflet GIS mapping.
2. **API & Service Layer (Backend):** Flask web server hosting RESTful API blueprints.
3. **Graph & Mathematical Engine:** Pure Python discrete math implementation featuring DSU Kruskal, Min-Heap Prim, and LCA Binary-Lifting Verification.
4. **Routing Engine:** OSRM Table API client with local and public failover, symmetric edge conversion, and SQLite route caching.
5. **Persistence & Data Layer:** SQLite scenario repository, SQLite persistent route cache, and canonical BBMP facilities dataset.

```
+-----------------------------------------------------------------------------------+
|                            CLIENT BROWSER (SPA)                                   |
|  index.html  |  app.js  |  api.js  |  navigation.js  |  Leaflet.js + MarkerCluster|
+-----------------------------------------------------------------------------------+
                                         |  JSON REST APIs (/api/...)
                                         v
+-----------------------------------------------------------------------------------+
|                               FLASK BACKEND                                       |
|  - flask_app.py (Server entry point & route registration)                         |
|  - scenarios_bp.py (Scenarios, audit, geocoding, benchmarks, manifest)             |
|  - facilities.py (Registry query, spatial filtering, single-node retrieval)        |
|  - mst.py (Global Haversine MST canonical retrieval)                              |
+-----------------------------------------------------------------------------------+
         |                                           |
         v                                           v
+---------------------------+               +---------------------------------------+
|    MATHEMATICAL ENGINE    |               |            ROUTING ENGINE             |
|  - graph_engine.py        |               |  - routing_service.py                 |
|  - Kruskal with DSU       |               |  - OSRM Table API client              |
|  - Prim with Min-Heap     |               |  - Symmetric edge generator (S_T, S_D)|
|  - LCA Binary Lifting     |               |  - Persistent route cache (routes.db) |
|  - Kendall Tau-b Analyzer |               +---------------------------------------+
+---------------------------+                                    |
         |                                                       v
         v                                          +-------------------------------+
+---------------------------+                       |    OSRM ROUTING SERVICE       |
|     SCENARIO SERVICE      |                       |  - Local: http://127.0.0.1:5001|
|  - scenario_service.py    |                       |  - Public: router.project-osrm|
|  - 8-Stage Pipeline       |                       +-------------------------------+
|  - Persistence (scenarios)|
+---------------------------+
         |
         v
+-----------------------------------------------------------------------------------+
|                                 DATA ASSETS                                       |
|  - data/processed/emergency_facilities.csv (1,255 BBMP facilities, UTF-8 BOM)     |
|  - data/cache/routes.db (SQLite pairwise decisecond/decimetre table)              |
|  - data/scenarios.db (SQLite persistent scenario runs, results, and traces)       |
+-----------------------------------------------------------------------------------+
```

---

## 2. Backend Components & Directory Structure

```
minimum_cost_emergency_network/
├── backend/
│   ├── flask_app.py                  # Main Flask application initialization
│   ├── routes/
│   │   ├── scenarios_bp.py           # Scenario execution, audit, & validation routes
│   │   ├── facilities.py             # Facilities catalog & filtering routes
│   │   └── mst.py                    # Global MST routes
│   └── services/
│       ├── audit_service.py          # Facilities CSV audit & geometric math
│       ├── graph_engine.py           # DMGT graph algorithms & LCA oracle
│       ├── routing_service.py        # OSRM client & symmetric edge formulation
│       ├── scenario_service.py       # 8-stage scenario pipeline execution
│       └── data_service.py           # Shared data access and memory cache
├── data/
│   ├── processed/
│   │   └── emergency_facilities.csv  # 1,255 facilities source of truth
│   ├── cache/
│   │   └── routes.db                 # SQLite persistent routing cache
│   └── scenarios.db                  # SQLite simulation scenarios repository
├── frontend/
│   ├── index.html                    # Single Page Application template
│   └── assets/
│       ├── css/
│       │   └── style.css             # Enterprise styling, CSS variables, & responsive grid
│       └── js/
│           ├── api.js                # Universal API fetch client
│           ├── navigation.js         # Section routing & view toggling
│           └── app.js                # Core UI controller & Leaflet orchestrator
└── tests/                            # 89 automated tests (pytest suite)
```

---

## 3. Database Schema

### 3.1 Scenarios Database (`data/scenarios.db`)
```sql
CREATE TABLE IF NOT EXISTS scenarios (
    scenario_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    status TEXT NOT NULL,
    stage_index INTEGER NOT NULL,
    stage_name TEXT NOT NULL,
    error_message TEXT,
    incident_lat REAL NOT NULL,
    incident_lon REAL NOT NULL,
    incident_label TEXT,
    agency TEXT NOT NULL,
    radius_km REAL NOT NULL,
    optimization_mode TEXT NOT NULL,
    k_param INTEGER NOT NULL,
    result_json TEXT
);
```

### 3.2 Persistent Route Cache (`data/cache/routes.db`)
```sql
CREATE TABLE IF NOT EXISTS route_measurements (
    origin TEXT NOT NULL,
    dest TEXT NOT NULL,
    duration_ds INTEGER NOT NULL,
    distance_dm INTEGER NOT NULL,
    timestamp TEXT NOT NULL,
    PRIMARY KEY (origin, dest)
);
```

---

## 4. API Endpoints Reference

| Endpoint | Method | Description |
|---|---|---|
| `/api/health` | GET | System health, service status, and facility breakdown |
| `/api/dataset/audit` | GET | Comprehensive mathematical and cryptographic audit |
| `/api/global-mst?algo={kruskal\|prim}` | GET | Global 1,254-edge Haversine MST |
| `/api/facilities` | GET | Query facilities with agency and text filters |
| `/api/geocode?q={query}` | GET | Landmark and facility coordinate search |
| `/api/scenarios` | POST | Trigger 8-stage emergency response scenario |
| `/api/scenarios/<id>/status` | GET | Poll scenario execution stage and progress |
| `/api/scenarios/<id>/result` | GET | Retrieve full 4-tab scenario results payload |
| `/api/scenarios/<id>/tradeoff` | GET | Retrieve compromise multi-objective trade-off curve |
| `/api/benchmarks` | GET | Latency, edge counts, and algorithm benchmarks |
| `/api/methodology/manifest` | GET | Academic methodology documentation manifest |
