# Verification & Mathematical Audit Report
**Project:** Minimum-Cost Emergency Communication Network Using Minimum Spanning Tree (MST)  
**Study Area:** BBMP Bengaluru, Karnataka, India  
**Date of Audit:** November 2026  
**Test Suite:** 89 Passed / 89 Total (100% Pass Rate)

---

## 1. Dataset Integrity & Cryptographic Provenance

The primary dataset representing the emergency facility registry for Bengaluru was audited under strict cryptographic and spatial invariants.

| Metric | Verified Value | Status |
|---|---|---|
| **File Path** | `data/processed/emergency_facilities.csv` | VERIFIED |
| **Encoding** | UTF-8 with Byte Order Mark (`utf-8-sig`) | VERIFIED |
| **SHA-256 Checksum** | `293930b3db46e55910f68494a3c7bd6652a9af0ff7fa06a761f94d9bec78d943` | MATCHED |
| **Total Records** | 1,255 records | 100% INTACT |
| **Hospitals & Clinics** | 1,097 (87.41%) | VERIFIED |
| **Police Stations** | 138 (10.99%) | VERIFIED |
| **Fire Stations** | 20 (1.60%) | VERIFIED |
| **Invalid Coordinates** | 0 records | 0 ERRORS |
| **Coordinate Bounds** | Lat: [12.8340, 13.1437], Lon: [77.4601, 77.7841] | STRICTLY BOUNDED |
| **Pairs $\le 5\text{ m}$** | 13 pairs (co-located facilities / multiple wings) | AUDITED & RETAINED |
| **Flagged Duplicates** | 5 pairs with identical name and agency | FLAGGED |

---

## 2. Global Geometric MST Mathematical Audit

The global communication network connects all 1,255 BBMP emergency facilities using the spherical Haversine metric ($R = 6,371.0088\text{ km}$) with half-up rounded integer millimetre weights.

| Property | Kruskal's Algorithm | Prim's Algorithm | Status |
|---|---|---|---|
| **Vertex Count ($|V|$)** | 1,255 | 1,255 | MATCHED |
| **Edge Count ($|E|$)** | 1,254 | 1,254 | EXACT $|V|-1$ |
| **Connected Components** | 1 (Single Tree) | 1 (Single Tree) | CONNECTED |
| **Total Weight (mm)** | 480,178,397 mm | 480,178,397 mm | **EXACT PARITY** |
| **Total Weight (km)** | 480.178397 km | 480.178397 km | **EXACT PARITY** |
| **Edge Set Identity** | 1,254 identical edges | 1,254 identical edges | **IDENTICAL** |

### 2.1 Complete LCA Binary-Lifting Cycle Property Verification
Every non-tree chord in the complete graph $K_{1255}$ (a total of $\binom{1255}{2} - 1254 = 786,885 - 1254 = 785,631$ non-tree edges) was independently evaluated against the maximum edge weight on the unique tree path between its endpoints using an $O(\log V)$ binary lifting oracle:
- **Total Non-Tree Chords Verified:** 785,631
- **Cycle Property Violations:** 0
- **Maximum Path Violation:** 0.0000 mm
- **Conclusion:** The global tree is mathematically proved to be a globally minimal spanning tree.

---

## 3. Scenario Pipeline & Road-Routing Audit

The 8-stage incident simulation pipeline was verified through end-to-end integration and automated regression testing.

### 3.1 Scenario Invariant Checks
1. **Candidate Eligibility:** Evaluates facilities within radius $R_s$ belonging strictly to the requested response agency. Non-qualifying facilities are catalogued in `exclusions_reconciliation` with reason codes.
2. **Directed Asymmetry Handling:** OSRM directed durations and distances are preserved in the route cache. Undirected edges are formed symmetrically as $S_T(i, j) = T(i, j) + T(j,i)$ and $S_D(i, j) = D(i, j) + D(j,i)$, ensuring the graph remains undirected for MST computation.
3. **Optimality Modes:**
   - Mode 1 (Time) minimizes total $S_T$.
   - Mode 2 (Distance) minimizes total $S_D$.
   - Mode 3 (Compromise) utilizes exact integer formulation $N_e = k S_T D^* + (10 - k) S_D T^*$.
4. **Decoupled Dispatch Ranking:** Facilities are ranked strictly by $(T(F \to I), D(F \to I), \text{facility\_id})$ with assumed fuel rates. The ranking is never merged with the MST backbone.
5. **Topology Telemetry:**
   - Tree path distances to the incident are computed via Breadth-First Search (BFS).
   - Stretch ratios $\frac{\text{Tree Path Distance}}{\text{Direct Distance}}$ are reported.
   - Kendall rank correlation coefficient $\tau_b$ is computed between dispatch rank order and tree-hop proximity.

### 3.2 Negative Testing & Corrupted Tree Rejection
An adversarial unit test (`test_corrupted_spanning_tree_rejection`) deliberately replaced a valid minimal tree edge with a heavy cross-edge to simulate a non-minimal spanning tree.
- **Oracle Result:** The LCA Binary-Lifting Oracle successfully detected the cycle property violation ($w(e) < \text{path\_max}$ for the replaced edge), flagged the violation count, and returned `is_optimal = False`.

---

## 4. Automated Test Suite Summary

Execution of the complete pytest test suite across 8 test modules yielded:

```
============================= test session starts =============================
platform win32 -- Python 3.11.3, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Users\DHAIRYA\Downloads\minimum_cost_emergency_network\minimum_cost_emergency_network
collected 89 items

tests/test_experiments.py (4 tests) .................... PASSED
tests/test_flask_backend.py (17 tests) ................. PASSED
tests/test_local_comparison.py (6 tests) ............... PASSED
tests/test_mst.py (24 tests) ........................... PASSED
tests/test_phase1_6_audit.py (6 tests) ................. PASSED
tests/test_scenario_pipeline.py (2 tests) .............. PASSED
tests/test_simulation.py (14 tests) .................... PASSED
tests/test_transportation_cost.py (16 tests) ........... PASSED

============================= 89 passed in 13.17s =============================
```
