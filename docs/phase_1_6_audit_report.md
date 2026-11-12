# PHASE 1.6 — COMPREHENSIVE SOURCE-CODE AUDIT AND MATHEMATICAL VERIFICATION REPORT

**Project:** Minimum-Cost Emergency Communication Network Using Minimum Spanning Tree (MST)  
**Study Area:** BBMP Municipal Area, Bengaluru, Karnataka, India  
**Branch:** `migration-phase-1`  
**Latest Baseline Commit:** `e7ed56d`  
**Date of Audit:** November 12, 2026  
**Auditor:** Automated Engineering & Mathematical Verification Agent  

---

## 1. Executive Summary

This report delivers the factual source-code audit and mathematical verification of the Bengaluru Emergency Communication Network application as implemented in Phase 1.5.

All six core application views, 87 automated unit/integration tests, and automated Playwright headless browser runs were audited without rebuilding features or touching Phase 2 OSRM routing.

### Summary of Audit Classifications
| Audit Area | Item Inspected | Classification | Summary Finding |
| :--- | :--- | :--- | :--- |
| **Audit A** | Global Complete Graph Invariants | **Verified Correct** | $\|V\| = 1,255$, $\|E\| = 786,885$, self-loops excluded, Haversine $R = 6,371.0088\text{ km}$. |
| **Audit A** | MST Edge Count & Tree Weight | **Verified Correct** | Both Kruskal and Prim yield exactly 1,254 edges with weight $480.1783984126\text{ km}$ ($\Delta = 5.68 \times 10^{-14}\text{ km}$). |
| **Audit A** | Maximum Edge Weight Display Pill | **Defect Corrected** | Hardcoded display pill in `frontend/index.html` read $5.7336\text{ km}$; actual maximum MST edge is $7.8256\text{ km}$. Corrected. |
| **Audit B** | Minimum Edge (0.0000 km) | **Verified Correct** | Bit-for-bit identical coordinates between `way/1544830710` (SPS Surgicals) and `way/1544831540` at $(12.9541576^\circ\text{ N}, 77.6608368^\circ\text{ E})$. Handled without cycles. |
| **Audit C** | LCA Binary-Lifting Cycle Property | **Verified Correct** | Evaluated all 785,631 non-tree edges against LCA binary-lifting max path table; exactly 0 cycle violations at tolerance $10^{-9}$. |
| **Audit D** | Prim & Kruskal Manual Implementations | **Verified Correct** | Self-contained, custom implementations. Heap priority queue with visited tracking in Prim; DSU with union-by-rank and path compression in Kruskal. |
| **Audit E** | Simulation Ranking Calculation | **Defect Corrected** | Staged ranking uses straight-line Haversine distance, not road routing. Labeled accurately as a preliminary preview to prevent misattribution. |
| **Audit F** | Incident Location Data Flow | **Defect Corrected** | Stale coordinates persisted in simulation after clearing pin on map. Fixed `clearIncidentLocation()` and `updateSimulationUI()`. |
| **Audit G** | Facilities Map & Clustering | **Verified Correct** | Marker clustering and agency filters accurately reflect 1,097 hospitals, 138 police, and 20 fire stations. |
| **Audit H** | Cost Model & Balanced Equivalence | **Verified Correct** | Proved $C^{\text{norm}} = D^{\text{norm}}$ under constant $R_a$; clarified GOK Notification No. FD 31 CSL 2024 establishes diesel price benchmark ($₹88.94/\text{L}$), from which fleet rates are derived. |
| **Audit I** | Test Suite & Browser Verification | **Verified Correct** | 87/87 pytest tests passing; 0 console errors across desktop (1440×900) and mobile (375×667) viewports. |

---

## 2. Global MST Mathematical Correctness (Audit A)

### 2.1 Complete Graph Generation
The complete graph is generated via pairwise combinations:
$$|E| = \frac{|V|(|V| - 1)}{2} = \frac{1,255 \times 1,254}{2} = 786,885\text{ undirected edges}$$

Source verification in `src/mst_network.py::build_complete_edges`:
- Uses Python `itertools.combinations(range(len(r)), 2)`, strictly enforcing $i < j$, thereby excluding all self-loops ($u \ne v$) and guaranteeing exactly one undirected edge per vertex pair.
- Coordinates were validated across all 1,255 records:
  - Missing coordinates: `0`
  - Out-of-bounds coordinates: `0` (all latitudes $12.8^\circ\text{ N} - 13.2^\circ\text{ N}$, longitudes $77.4^\circ\text{ E} - 77.8^\circ\text{ E}$)
  - Duplicate facility IDs: `0`

### 2.2 Great-Circle Distance Metric
The distance function in `src/mst_network.py::haversine_km` uses the spherical Haversine formula with the IUGG mean Earth radius:
$$R = 6,371.0088\text{ km}$$
$$\Delta\phi = \text{radians}(\phi_2 - \phi_1), \quad \Delta\lambda = \text{radians}(\lambda_2 - \lambda_1)$$
$$a = \sin^2\left(\frac{\Delta\phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta\lambda}{2}\right)$$
$$d = 2 R \arcsin(\min(1, \sqrt{a}))$$

This metric is symmetric ($d(u,v) = d(v,u)$), strictly non-negative ($d(u,v) \ge 0$), and satisfies the triangle inequality.

### 2.3 Global MST Results Verification
Empirical values computed from `results/kruskal_mst_edges.csv` and `results/prim_mst_edges.csv`:

| Parameter | Kruskal MST Result | Prim MST Result | Discrepancy ($\Delta$) | Audit Assessment |
| :--- | :--- | :--- | :--- | :--- |
| **Vertex Count** | 1,255 | 1,255 | 0 | Exact match |
| **Edge Count** | 1,254 | 1,254 | 0 | Cayley invariant ($\|V\| - 1$) |
| **Sum of Floats** | 480.178398412586 km | 480.178398412643 km | $5.6843 \times 10^{-14}\text{ km}$ | Machine epsilon precision |
| **Rounded Total** | 480.1784 km | 480.1784 km | 0.0000 km | Exact match |
| **Minimum Edge** | 0.000000 km | 0.000000 km | 0.0000 km | Exact match |
| **Maximum Edge** | 7.825585 km | 7.825585 km | 0.0000 km | Exact match |
| **Unique Edge Pairs** | 1,254 | 1,254 | 0 | Identical edge set |

**Edge Set Equality Analysis:**
In general, identical total tree weights between Prim and Kruskal do not prove identical edge sets when duplicate weights exist. However, on this specific dataset, canonical edge pair set comparison (`min(u,v), max(u,v)`) established that `k_set == p_set` is **True** (all 1,254 edge pairs are identical).

---

## 3. Zero-Weight Edge Investigation (Audit B)

The minimum edge weight in both spanning trees is exactly `0.000000 km`.

### 3.1 Facility Pair Identification
- **Vertex U:**
  - ID: `way/1544830710`
  - Name: `SPS Surgicals`
  - Agency: `hospital`
  - Coordinates: Latitude `12.9541576° N`, Longitude `77.6608368° E`
- **Vertex V:**
  - ID: `way/1544831540`
  - Name: `""` (Unnamed healthcare feature in OpenStreetMap)
  - Agency: `hospital`
  - Coordinates: Latitude `12.9541576° N`, Longitude `77.6608368° E`

### 3.2 Root Cause
Coordinates are bit-for-bit identical across all decimal places. This occurs because the raw OpenStreetMap export contains two co-located polygon/way features at the same commercial healthcare premises.
In the complete graph of 786,885 edges, this is the **only** edge with weight 0.0000 km.

### 3.3 Algorithmic Treatment
Both Prim and Kruskal handle this edge deterministically:
- Kruskal sorts it at rank #1 and merges the two vertices into a single DSU component with zero added weight.
- Prim selects it immediately from the heap with zero cut weight.
- No self-loops or zero-weight cycles are introduced.

**Recommendation:** Per instruction, this record is retained in the dataset and explained accurately in the UI.

---

## 4. Independent MST Optimality Validation (Audit C)

### 4.1 Theoretical Foundation: The Cycle Property
For any weighted undirected graph $G = (V, E, w)$, a spanning tree $T$ is a Minimum Spanning Tree if and only if for every non-tree edge $e = (u, v) \in E \setminus T$:
$$w(u, v) \ge \max_{e' \in P_T(u, v)} w(e')$$
where $P_T(u, v)$ is the unique path between $u$ and $v$ in $T$.

Number of non-tree edges to evaluate:
$$|E \setminus T| = 786,885 - 1,254 = 785,631\text{ candidate edges}$$

### 4.2 Verifier Implementation
An independent verifier was constructed and verified:
1. **Adjacency Construction:** Built bidirectional tree adjacency list for all 1,254 tree edges.
2. **Binary Lifting Table (`LOGN = 12`):**
   - $2^{12} - 1 = 4,095$ levels, which completely bounds the empirical tree depth (measured at 137 levels) and theoretical worst-case chain depth (1,254).
   - BFS traversal rooted at node 0 visited $1,255 / 1,255$ vertices.
   - Precomputed $2^k$-ancestor jump table `up[k, i]` and maximum path weight table `max_edge[k, i]`.
3. **Cross-Validation against BFS Oracle:**
   - 100 randomly sampled vertex pairs evaluated against an independent BFS path reconstruction produced **0 discrepancies**.
   - Path maximum for the zero-weight edge `way/1544830710` $\leftrightarrow$ `way/1544831540` evaluated to $0.000000\text{ km}$ under both engines.
4. **Exhaustive 785,631 Non-Tree Edge Scan:**
   - Evaluated all 785,631 non-tree edges from `results/complete_graph_edges.csv`.
   - Tolerance threshold: $\tau = 10^{-9}\text{ km}$.
   - **Cycle violations detected: 0**.
   - Equal-weight alternatives ($w(u, v) = \text{path\_max} \pm \tau$): 1.
   - Verification execution time: 31.43 seconds.

---

## 5. Prim and Kruskal Implementation Audit (Audit D)

### 5.1 Prim's Algorithm (`src/mst_network.py::prim_mst`)
- **Data Structure:** Standard binary min-heap (`heapq`) maintaining cut-crossing candidate edges.
- **Tie-Breaking:** Deterministic comparison tuple `(w, str(s), str(t), s, t, sn, tn, st, tt)`. Float weight is strictly ordered first; ties are resolved lexicographically by facility ID string. No tolerance or non-deterministic comparators are used.
- **Visited Tracking:** Set of visited vertex IDs. Lazy deletion skips popped elements if destination $t \in \text{visited}$.
- **Termination:** Halts when all 1,255 vertices are spanned. Disconnection check raises `ValueError`.

### 5.2 Kruskal's Algorithm (`src/mst_network.py::kruskal_mst`)
- **Sorting:** `edges.sort_values(["weight_km", "u", "v"], kind="mergesort")`. Mergesort provides stable, deterministic $O(|E| \log |E|)$ total ordering.
- **DSU Implementation:**
  - Path compression: `while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]`.
  - Union by rank: Keeps tree shallow by attaching lower-rank root under higher-rank root.
- **Cycle Prevention:** Skips edge if `find(u) == find(v)`.
- **Termination:** Halts early when $|V| - 1 = 1,254$ edges have been accepted.

---

## 6. Simulation Ranking Calculation Findings (Audit E)

### 6.1 Findings on Current Calculation
Inspection of `frontend/assets/js/app.js::runSimulationPreview()`:
- **Input Parameters:** `State.incident.lat`, `State.incident.lon`, `State.simAgency`, `State.simRadiusKm`.
- **Candidate Filtering:** Filters facilities matching `agency == State.simAgency` within spherical Haversine distance $\le R_s$.
- **Sorting Metric:** Straight-line Haversine distance ($d_i = \text{haversine}(p_{\text{incident}}, p_i)$).
- **Displayed Cost:** $C_i = d_i \times R_a$.
- **Displayed Time:** $T_i = (d_i / v_a) \times 60$.

### 6.2 Assessment and Defect Correction
- **Finding:** The calculation uses straight-line Haversine distance, NOT road network distance ($D_{\text{road}}$), NOT OSRM driving duration, and NOT an incident-specific MST path.
- **Correction:** The user interface previously displayed "Top 3 Recommended Response Facilities &bull; Ranked by minimum traversal cost". This could be misinterpreted as road routing.
- **Changes Made:** Updated `frontend/index.html` and `frontend/assets/js/app.js` to label the module as:
  **"Top 3 Recommended Facilities (Preliminary Haversine Preview)"** with the disclaimer:
  *"Ranked by straight-line Haversine distance. (Full OSRM road-network routing & incident-specific MST dispatch scheduled for subsequent phases)."*

---

## 7. Incident Location Data Flow (Audit F)

### 7.1 Lifecycle Verification
Tested interaction pipeline:
`Facilities Map` $\rightarrow$ `Incident Placement` $\rightarrow$ `Confirm Location` $\rightarrow$ `Send to Simulation` $\rightarrow$ `Simulation Step 1`.
- Draggable marker: Updates coordinate input fields live during `drag` and commits on `dragend`.
- Six presets: All 6 landmarks correctly set coordinates and pan map.
- Confirmation: Sets badge to `✓ Incident Confirmed` (clarified in documentation as frontend application state confirmation).

### 7.2 Stale Coordinates Defect Corrected
- **Defect Identified:** In Phase 1.5, clicking "Clear Pin" called `clearIncidentLocation()` which set `State.incident.isSet = false`, but left `State.incident.lat` and `State.incident.lon` holding previous coordinate floats. When navigating to Simulation, `updateSimulationUI()` still displayed the cleared coordinates, and `updateSimulationCandidateCount()` still evaluated candidates around the cleared point.
- **Correction Applied:**
  - `clearIncidentLocation()` now sets `State.incident.lat = null`, `State.incident.lon = null`, and `State.incident.label = null`, and clears coordinate inputs.
  - `updateSimulationUI()` checks `if (State.incident.isSet && State.incident.lat != null)` and renders `"No incident location configured. Please drop a pin on the Facilities Map or select a landmark preset below."` when cleared.
  - `runSimulationPreview()` requires a confirmed incident location before executing.

---

## 8. Facility Map Verification (Audit G)

- **Agency Filters:**
  - All Agencies: 1,255 facilities.
  - Hospitals: 1,097 facilities.
  - Police Stations: 138 stations.
  - Fire Stations: 20 stations.
- **Marker Clustering:** Groups markers into cluster counts at low zoom; spiderfies or zooms to individual colored circles on click.
- **Grey Tile Observation:** When zooming rapidly, grey rectangles appear transiently for ~100–300 ms. Investigation confirmed this is standard OpenStreetMap raster tile HTTP fetching over the network, not a canvas clipping or memory leak defect. Leaflet's `invalidateSize()` is properly triggered upon tab navigation.

---

## 9. Cost Model and Balanced Objective Equivalence (Audit H)

### 9.1 Mathematical Proof of Equivalence
Project transit fuel cost model:
$$C_{ij} = D_{ij} \times R_a$$
where $R_a$ is the constant per-kilometer rate for the selected agency.
For any set of candidate facilities $\{1, \dots, m\}$ evaluated in a single agency dispatch run:
$$C_{\min} = D_{\min} \times R_a, \quad C_{\max} = D_{\max} \times R_a$$
$$C_i^{\text{norm}} = \frac{C_i - C_{\min}}{C_{\max} - C_{\min}} = \frac{D_i \times R_a - D_{\min} \times R_a}{D_{\max} \times R_a - D_{\min} \times R_a} = \frac{D_i - D_{\min}}{D_{\max} - D_{\min}} = D_i^{\text{norm}}$$

Substituting into the three-parameter objective:
$$W_i^{\text{balanced}} = 0.50 T_i^{\text{norm}} + 0.25 D_i^{\text{norm}} + 0.25 C_i^{\text{norm}} = 0.50 T_i^{\text{norm}} + 0.50 D_i^{\text{norm}}$$

### 9.2 Statutory Fuel Price Benchmark Attribution
- **Statutory Authority:** Government of Karnataka Finance Department Notification No. FD 31 CSL 2024 (effective June 15, 2024) revised state sales tax on diesel from 14.34% to 18.44%, establishing the Bengaluru retail diesel benchmark at **₹88.94 per liter**.
- **Agency Rates Derivation:** The notification establishes the fuel price benchmark, while the agency rates ($R_a$) are engineering fleet estimates:
  - Ambulance: Force Motors Traveller / Tata Winger diesel ($7.11\text{ km/L}$) $\implies ₹88.94 / 7.11 \approx ₹12.50/\text{km}$.
  - Police Patrol: Mahindra Bolero diesel ($14.23\text{ km/L}$) $\implies ₹88.94 / 14.23 \approx ₹6.25/\text{km}$.
  - Fire Engine: Ashok Leyland heavy water tender ($4.94\text{ km/L}$) $\implies ₹88.94 / 4.94 \approx ₹18.00/\text{km}$.
- **Audit Assessment:** Text in `frontend/index.html` was audited to ensure the statutory notification is cited strictly for the ₹88.94/L fuel price benchmark, avoiding misleading claims that the government mandated the vehicle rates directly.

---

## 10. Test Suite and Browser Verification Results (Audit I)

### 10.1 Pytest Suite Execution
Executed `pytest tests/`:
- `tests/test_experiments.py`: 4 passed
- `tests/test_flask_backend.py`: 17 passed
- `tests/test_local_comparison.py`: 6 passed
- `tests/test_mst.py`: 27 passed
- `tests/test_phase1_6_audit.py`: 6 passed (new audit test suite)
- `tests/test_simulation.py`: 14 passed
- `tests/test_transportation_cost.py`: 13 passed
- **Total: 87 passed in 16.55 seconds (100% passing)**.

### 10.2 Playwright Browser Verification
Executed `test_phase1_5_browser.py`:
- Tested navigation, clustering, incident placement, landmark presets, Prim/Kruskal toggles, simulation preview, mobile view (375×667), and desktop view (1440×900).
- **Console errors: 0**.

---

## 11. Defects Corrected

1. **Max Edge Weight Display Pill in `frontend/index.html`:**
   - *Original Defect:* Pill displayed `Max Edge: 5.7336 km`.
   - *Evidence:* Sorted edge list in `results/kruskal_mst_edges.csv` proved maximum edge is `7.825585 km` (Budigere Hospital $\leftrightarrow$ Vikrant Hospital).
   - *Correction:* Updated pill to `7.8256 km`.
2. **Simulation Staging Preview Labeling in `frontend/index.html` and `frontend/assets/js/app.js`:**
   - *Original Defect:* Output card read "Ranked by minimum traversal cost", risking misinterpretation as real OSRM road dispatch.
   - *Evidence:* Code inspection showed straight-line Haversine proxy ranking.
   - *Correction:* Labeled as "Top 3 Recommended Facilities (Preliminary Haversine Preview)" with explicit notice of upcoming OSRM routing.
3. **Stale Incident Coordinate Persistence in `frontend/assets/js/app.js`:**
   - *Original Defect:* Clearing pin left old coordinate values in `State.incident`, causing stale evaluation in Simulation.
   - *Evidence:* Resetting map pin did not clear Simulation Step 1 coordinates.
   - *Correction:* Nullified coordinates on clear, updated `updateSimulationUI()` and `runSimulationPreview()` guards.
4. **Earth Radius Constant in `app.py`:**
   - *Original Defect:* Line 480 used `6371.0 * c` instead of `6371.0088 * c`.
   - *Evidence:* Inconsistency with project standard $R = 6371.0088\text{ km}$.
   - *Correction:* Updated to `6371.0088 * c`.

---

## 12. Known Methodological Limitations

1. **Two-Dimensional Spherical Earth Approximation:** Great-circle Haversine distances do not model Bengaluru's elevation profile (~850m to ~960m above MSL).
2. **OSM Co-Located Facility Duplicate:** Two healthcare facilities share identical coordinates at `way/1544830710` and `way/1544831540`, producing one zero-weight edge.
3. **Phase 1.5 Preview vs. Phase 2 OSRM:** Current dispatch staging uses straight-line proxy metrics pending Phase 2 road routing.

---

## 13. Files Modified in Phase 1.6

- `app.py`: Line 480 corrected to use `6371.0088` Earth radius constant.
- `frontend/index.html`: Corrected max edge pill to `7.8256 km`; clarified simulation preview labeling.
- `frontend/assets/js/app.js`: Corrected stale coordinate handling in `clearIncidentLocation()`, `updateSimulationUI()`, and `runSimulationPreview()`.
- `tests/test_phase1_6_audit.py`: Added 6 rigorous mathematical audit unit tests.
- `docs/phase_1_6_audit_report.md`: Created complete Phase 1.6 audit report.

---

## 14. Final Readiness Assessment

The Phase 1.5 foundation has been mathematically verified and audited. All graph theoretical invariants, data structures, and edge selection decisions are supported by direct source-code inspection and empirical execution.

The codebase is in a verified, clean state and is **ready for Phase 2: OSRM Routing & Road-Measurement Engine** upon user authorization.
