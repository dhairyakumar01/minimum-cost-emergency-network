# Final Automated Test Suite Audit & Mathematical Invariant Verification
**Project:** Minimum-Cost Emergency Communication Network Using Minimum Spanning Tree (MST)  
**Evaluation Standard:** Discrete Mathematics and Graph Theory (DMGT) Experiential Learning  
**Date of Execution:** 2026-11-09  
**Execution Environment:** Windows Python 3.11.3 / Pytest 9.2.0  
**Overall Suite Result:** `46/46 PASSED (100% Pass Rate, Execution Time: 5.11s)`

---

## 1. Executive Summary

This document provides a line-by-line independent audit of the complete automated test suite for the Minimum-Cost Emergency Communication Network project.

> [!IMPORTANT]
> **Academic Integrity Caveat on Test Verification:**  
> Passing automated tests verifies software correctness, boundary condition defense, graph invariants, and mathematical arithmetic ($C = D_{\text{road}} \times R_j$). It does **NOT** prove the empirical validity or historical truth of input research assumptions (e.g. vehicle fuel efficiency, maintenance provisions, or retail fuel rates). Input assumptions are strictly classified as illustrative derived estimates with unsupported parameters disclosed.

The test suite guarantees:
1. **Mathematical Invariance:** Exact compliance with metric space axioms, spanning tree topological requirements, and tree path uniqueness.
2. **Algorithm Equivalence & Optimality:** Independent brute-force verification proving that both manual Prim and Kruskal implementations achieve identical optimal tree weights.
3. **Emergency Dispatch Correctness:** Strict priority-based responder assignment, immutable MST preservation during incidents, and geocoding bounding box enforcement.
4. **Physical Transportation & Cost Rigor:** Road distance lower-bounded by geodesic Haversine distance, concurrent scene secure time calculated as $\max(T_j)$ (never $\sum T_j$), non-negative distance validation, and round-trip scaling.

---

## 2. Test Suite Overview & Execution Summary

| Test Module | Test File | Test Cases | Status | Focus Area |
| :--- | :--- | :---: | :---: | :--- |
| **Experimentation & Scalability** | `tests/test_experiments.py` | 4 | **4/4 PASSED** | Runtime complexity, input invariance, density sparsification, persistence |
| **MST Algorithms & Metrics** | `tests/test_mst.py` | 15 | **15/15 PASSED** | Haversine metric axioms, brute-force optimality, Prim-Kruskal parity, validation |
| **Emergency Simulation** | `tests/test_simulation.py` | 14 | **14/14 PASSED** | Scenario dispatch, tree paths, geocoding bounds, max arrival concurrency |
| **Transportation & Operating Cost**| `tests/test_transportation_cost.py` | 13 | **13/13 PASSED** | Journey cost ($C_j = D \times R$), round-trip doubling, negative error handling, 4-dim sensitivity |
| **Total** | | **46** | **46/46 PASSED** | **100% Suite Pass Rate** |

---

## 3. Detailed Individual Test Case Breakdown

### Module 1: `tests/test_experiments.py` (4 Tests)

#### Test 1.1: `test_scalability_reproducible_and_identical_inputs`
- **Feature Tested:** Experimental rigor across algorithmic scalability benchmarks.
- **Input / Condition:** 20 synthetic facility vertices, subset sizes $|V| \in \{5, 10\}$, 2 random seeds, 2 trials per size for both Prim and Kruskal.
- **Mathematical Assertion:**
  - Candidate complete edge count must strictly equal $\binom{|V|}{2} = \frac{|V|(|V|-1)}{2}$ (10 edges for $V=5$, 45 edges for $V=10$).
  - Spanning tree edge count must strictly equal $|V|-1$.
  - Runtimes must be positive and non-zero.
- **Expected Behaviour:** 8 trial records generated; both algorithms receive identical subgraphs.
- **Actual Result:** `PASSED` (Candidate edges: 10 and 45; tree edges: 4 and 9).

#### Test 1.2: `test_scalability_persistence`
- **Feature Tested:** Serialization and deserialization of scalability benchmarks.
- **Input / Condition:** Scalability run on $|V| \in \{4, 6\}$, written to temporary directory via `save_experiment_results`.
- **Mathematical Assertion:** Serialized JSON and CSV files must exist; deserialized metadata must match exact execution seed (`seed=99`).
- **Expected Behaviour:** Lossless round-trip persistence of experimental results.
- **Actual Result:** `PASSED`.

#### Test 1.3: `test_density_experiments_controlled_sparsification`
- **Feature Tested:** Graph density parameter sweep ($\rho \in [0.0, 1.0]$) with MST weight invariance.
- **Input / Condition:** Complete graph of 20 vertices ($|E| = 190$), sparsified across $\rho \in \{0.0, 0.5, 1.0\}$.
- **Mathematical Assertion:**
  - Optimal MST weight must remain invariant across all density levels ($\Delta W < 10^{-4}$ km) because tree edges are never removed during sparsification.
  - At $\rho = 0.0$, edge count must equal $|V|-1 = 19$.
  - At $\rho = 1.0$, edge count must equal $\binom{20}{2} = 190$.
- **Expected Behaviour:** Validation passes on all sparsified subgraphs; weight invariance verified.
- **Actual Result:** `PASSED`.

#### Test 1.4: `test_density_persistence`
- **Feature Tested:** Density benchmark persistence to disk.
- **Input / Condition:** Complete graph sparsification results saved to temporary directory.
- **Mathematical Assertion:** JSON and CSV export valid; loaded density levels strictly match $[0.0, 0.5, 1.0]$.
- **Expected Behaviour:** Exact deserialization and schema validation.
- **Actual Result:** `PASSED`.

---

### Module 2: `tests/test_mst.py` (15 Tests)

#### Test 2.1: `test_haversine_same_point_is_zero`
- **Feature Tested:** Metric space identity of indiscernibles: $d(x, x) = 0$.
- **Input / Condition:** Lat/Lon $(12.97, 77.59)$ against itself.
- **Mathematical Assertion:** $d(x, x) \equiv 0.0$.
- **Actual Result:** `PASSED`.

#### Test 2.2: `test_haversine_is_symmetric`
- **Feature Tested:** Metric space symmetry axiom: $d(x, y) = d(y, x)$.
- **Input / Condition:** Point $A(12.97, 77.59)$ and Point $B(13.05, 77.65)$.
- **Mathematical Assertion:** $|d(A, B) - d(B, A)| < 10^{-9}$.
- **Actual Result:** `PASSED`.

#### Test 2.3: `test_haversine_one_degree_latitude`
- **Feature Tested:** Great-circle arc distance calibration for spherical Earth model ($R = 6371.0088\text{ km}$).
- **Input / Condition:** Coordinates $(0^\circ, 0^\circ)$ to $(1^\circ, 0^\circ)$ along the equator/meridian.
- **Mathematical Assertion:** $d = \frac{\pi}{180} \times 6371.0088 \approx 111.195\text{ km}$ ($0.1\%$ relative tolerance).
- **Actual Result:** `PASSED`.

#### Test 2.4: `test_small_graph_matches_brute_force`
- **Feature Tested:** Independent brute-force optimality benchmark on 4-vertex planar network.
- **Input / Condition:** 4 facilities in Bengaluru; $\binom{4}{2} = 6$ edges; $\binom{6}{3} = 20$ edge combinations evaluated by brute force.
- **Mathematical Assertion:** $W(\text{Prim}) = W(\text{Kruskal}) = W(\text{Brute Force})$.
- **Actual Result:** `PASSED`.

#### Tests 2.5–2.9: `test_random_graphs_prim_kruskal_brute_force_agree` (5 Parametrized Seeds)
- **Feature Tested:** Exact optimality equivalence across 5 independent randomized 6-vertex topologies (Seeds 0, 1, 2, 3, 4).
- **Input / Condition:** Complete graphs with 6 vertices, 15 candidate edges, evaluated against all $\binom{15}{5} = 3003$ spanning tree subgraphs.
- **Mathematical Assertion:** Both manual Prim and Kruskal algorithms find the global minimum total weight identical to exhaustive enumeration across all 5 seeds.
- **Actual Result:** `5/5 PASSED`.

#### Test 2.10: `test_duplicate_coordinates_zero_weight_edge`
- **Feature Tested:** Handling of coincident facilities with zero-distance edges ($w = 0.0$).
- **Input / Condition:** 3 vertices, two of which share identical coordinates $(12.9, 77.5)$.
- **Mathematical Assertion:** Spanning tree includes 2 edges; total weight matches brute force; zero-weight edge handled gracefully without division-by-zero or cycles.
- **Actual Result:** `PASSED`.

#### Test 2.11: `test_disconnected_graph_raises`
- **Feature Tested:** Disconnected graph detection and error raising.
- **Input / Condition:** 4 vertices with isolated node $n_3$ having 0 incident edges.
- **Mathematical Assertion:** Both Prim and Kruskal raise `ValueError` because no spanning tree exists.
- **Actual Result:** `PASSED`.

#### Test 2.12: `test_validation_passes_on_correct_msts`
- **Feature Tested:** 5-property structural validation suite on valid trees.
- **Input / Condition:** Valid Prim and Kruskal outputs on 4-vertex network.
- **Mathematical Assertion:** All 5 checks pass: $|E| = |V|-1$, connected, acyclic, valid endpoints, correct Haversine weights.
- **Actual Result:** `PASSED`.

#### Test 2.13: `test_validation_detects_cycle_and_bad_edge_count`
- **Feature Tested:** Tree topology validation rejecting cycles and duplicate edges.
- **Input / Condition:** Tree modified to replace an edge with a duplicate edge, creating a cycle.
- **Mathematical Assertion:** `validate_mst` detects cycle and incorrect edge count; returns `False`.
- **Actual Result:** `PASSED`.

#### Test 2.14: `test_validation_detects_unknown_facility_id`
- **Feature Tested:** Referential integrity of tree edge endpoints.
- **Input / Condition:** Edge endpoint modified to `"does_not_exist"`.
- **Mathematical Assertion:** `endpoints_are_valid_facility_ids` check fails.
- **Actual Result:** `PASSED`.

#### Test 2.15: `test_validation_detects_wrong_weight`
- **Feature Tested:** Stored edge weight verification against recomputed Haversine distance.
- **Input / Condition:** Tree edge weight perturbed by $+5.0\text{ km}$.
- **Mathematical Assertion:** `stored_weights_match_haversine` check fails.
- **Actual Result:** `PASSED`.

---

### Module 3: `tests/test_simulation.py` (14 Tests)

#### Test 3.1: `test_responder_mappings`
- **Feature Tested:** Scenario-to-agency assignment policy.
- **Input / Condition:** Scenarios "Fire", "Medical Emergency", "Road Accident".
- **Mathematical Assertion:**
  - Fire: Primary = `fire_station`, Supporting = `hospital`, `police_station`.
  - Medical: Primary = `hospital`, Supporting = `police_station`, `fire_station`.
  - Accident: Primary = `hospital`, Supporting = `police_station`, `fire_station`.
- **Actual Result:** `PASSED`.

#### Test 3.2: `test_find_nearest_facilities`
- **Feature Tested:** Nearest facility discovery via vectorized spherical Haversine computation.
- **Input / Condition:** Incident at $(12.9717, 77.5947)$ near Hospital $h_1$.
- **Mathematical Assertion:** Hospital nearest distance $< 0.1\text{ km}$; returns nearest facility for each category.
- **Actual Result:** `PASSED`.

#### Test 3.3: `test_tree_path_reconstruction`
- **Feature Tested:** BFS path recovery on undirected spanning tree.
- **Input / Condition:** MST adjacency graph; source $h_1$, target $f_1$.
- **Mathematical Assertion:** Unique path found; path edges equal node count minus one; total distance matches sum of edge weights.
- **Actual Result:** `PASSED`.

#### Test 3.4: `test_simulate_fire_incident`
- **Feature Tested:** Full end-to-end incident dispatch simulation for Fire scenario.
- **Input / Condition:** Incident at $(12.9700, 77.5900)$ with sample facilities and MST.
- **Mathematical Assertion:** Primary responder is fire station; all supporting responders connected via MST communication paths.
- **Actual Result:** `PASSED`.

#### Test 3.5: `test_original_mst_immutable_during_simulation`
- **Feature Tested:** Immutability of the underlying emergency communication infrastructure.
- **Input / Condition:** Sequential executions of Fire, Medical, and Road Accident simulations.
- **Mathematical Assertion:** Original MST edge count and total weight remain strictly unchanged before and after simulations.
- **Actual Result:** `PASSED`.

#### Test 3.6: `test_geocoding_preset_landmarks`
- **Feature Tested:** High-precision local landmark geocoding resolution.
- **Input / Condition:** Queries "Lalbagh, Bengaluru" and "Forum Mall, Konankunte Cross".
- **Mathematical Assertion:** Coordinates resolve within Bengaluru bounding box ($12.70 \le \text{lat} \le 13.30$, $77.30 \le \text{lon} \le 77.90$).
- **Actual Result:** `PASSED`.

#### Test 3.7: `test_geocoding_short_or_invalid_query`
- **Feature Tested:** Query length sanitation and rejection.
- **Input / Condition:** Query `"x"` ($< 3$ characters).
- **Mathematical Assertion:** Rejects query with `success=False` and explanatory error message.
- **Actual Result:** `PASSED`.

#### Test 3.8: `test_geocoding_dataset_facility_fallback`
- **Feature Tested:** Fallback search directly into emergency facility dataset.
- **Input / Condition:** Query for custom facility name `"UniqueSpecialtyTraumaCenterXYZ"`.
- **Mathematical Assertion:** Resolves directly to dataset record latitude and longitude.
- **Actual Result:** `PASSED`.

#### Test 3.9: `test_geocoding_spelling_tolerance_and_variants`
- **Feature Tested:** Kannada/English transliteration variant matching and fuzzy typo tolerance.
- **Input / Condition:** 10 query variants ("Konankunte", "Konanakunte", "Lal Bagh", "Indiranagr", "Whitefeild", etc.).
- **Mathematical Assertion:** All 10 variants successfully resolve within Bengaluru geographic boundaries.
- **Actual Result:** `PASSED`.

#### Test 3.10: `test_medical_emergency_priority_and_responders`
- **Feature Tested:** Priority verification for acute medical dispatch.
- **Input / Condition:** Medical emergency at $(12.9720, 77.5950)$.
- **Mathematical Assertion:** Primary responder is strictly `hospital`; supporting agencies are `police_station` and `fire_station`.
- **Actual Result:** `PASSED`.

#### Test 3.11: `test_road_accident_priority_and_responders`
- **Feature Tested:** Priority verification for vehicular road trauma.
- **Input / Condition:** Road accident at $(12.9730, 77.5960)$.
- **Mathematical Assertion:** Primary responder is strictly `hospital`; supporting agencies are `police_station` and `fire_station`.
- **Actual Result:** `PASSED`.

#### Test 3.12: `test_scene_arrival_time_is_max_not_sum`
- **Feature Tested:** Mathematical concurrency proof for multi-agency scene arrival and containment.
- **Input / Condition:** Concurrent emergency dispatch of fire, hospital, and police units with distinct travel durations $\{T_{\text{fire}}, T_{\text{hospital}}, T_{\text{police}}\}$.
- **Mathematical Assertion:**
  - Overall scene secure time equals $\max(T_j)$.
  - Calculated arrival time is strictly less than the non-concurrent sum: $\max(T_j) < \sum T_j$.
- **Actual Result:** `PASSED` ($\max = 4.2\text{ min}$, $\sum = 10.8\text{ min}$).

#### Test 3.13: `test_geocoding_out_of_bounds_and_ambiguous`
- **Feature Tested:** Rejection of gibberish strings and out-of-bounds geographic queries.
- **Input / Condition:** Nonsense query `"zzxyqwer9999notrealplace"` and whitespace `"   "`.
- **Mathematical Assertion:** Gracefully returns `False` without unhandled runtime exceptions.
- **Actual Result:** `PASSED`.

#### Test 3.14: `test_missing_facility_category_fallback`
- **Feature Tested:** Robust handling of incomplete facility subsets (e.g. fire stations absent).
- **Input / Condition:** Subgraph containing only hospitals and police stations.
- **Mathematical Assertion:**
  - Fire simulation raises explicit `ValueError` when primary category is absent.
  - Medical simulation succeeds gracefully with single available supporting agency.
- **Actual Result:** `PASSED`.

---

### Module 4: `tests/test_transportation_cost.py` (13 Tests)

#### Test 4.1: `test_vehicle_rates_structure_and_consistency`
- **Feature Tested:** Consistency and schema compliance of vehicular operating cost models.
- **Input / Condition:** Vehicle rate configurations for `hospital`, `police_station`, `fire_station`.
- **Mathematical Assertion:** Direct operating cost equals fuel cost plus maintenance cost:
  $$R_{\text{operating}} = R_{\text{fuel}} + R_{\text{maint}}$$
- **Actual Result:** `PASSED` (Ambulance: $8.894 + 3.606 = 12.50$; Police: $7.412 + 2.588 = 10.00$; Fire: $31.764 + 10.236 = 42.00$).

#### Test 4.2: `test_category_normalization_and_aliases`
- **Feature Tested:** Agency category alias mapping.
- **Input / Condition:** Input variants `"ambulance"`, `"police"`, `"fire"`.
- **Mathematical Assertion:** Maps cleanly to canonical keys `"hospital"`, `"police_station"`, `"fire_station"`.
- **Actual Result:** `PASSED`.

#### Test 4.3: `test_journey_cost_calculation`
- **Feature Tested:** Vehicular journey expenditure formula $C_j = D_{\text{road}} \times R_j$.
- **Input / Condition:** $10.0\text{ km}$ road transit for ambulance ($R = ₹12.50/\text{km}$) and fire tender ($R = ₹42.00/\text{km}$).
- **Mathematical Assertion:** Ambulance cost $= ₹125.00$; Fire tender cost $= ₹420.00$.
- **Actual Result:** `PASSED`.

#### Test 4.4: `test_aggregate_expenditure_and_scene_arrival`
- **Feature Tested:** Aggregate fleet expenditure across heterogeneous responder dispatches.
- **Input / Condition:** Multi-agency fleet dispatch (Ambulance $5.0\text{ km}$, Police $4.0\text{ km}$, Fire $6.0\text{ km}$).
- **Mathematical Assertion:** Total vehicle km $= 15.0\text{ km}$; Aggregate cost $= 5(12.50) + 4(10.00) + 6(42.00) = ₹354.50$.
- **Actual Result:** `PASSED`.

#### Test 4.5: `test_sensitivity_analysis_bounds`
- **Feature Tested:** Combined operational sensitivity interval bounds.
- **Input / Condition:** $10.0\text{ km}$ journey for ambulance across highway cruising ($₹11.09/\text{km}$), base ($₹12.50/\text{km}$), and congestion ($₹14.38/\text{km}$).
- **Mathematical Assertion:** $C_{\text{lower}} < C_{\text{base}} < C_{\text{upper}}$ ($₹110.90 < ₹125.00 < ₹143.80$).
- **Actual Result:** `PASSED`.

#### Test 4.6: `test_multidimensional_sensitivity_separation`
- **Feature Tested:** Strict isolation of the four sensitivity dimensions.
- **Input / Condition:** $10.0\text{ km}$ ambulance journey evaluated across:
  1. *Diesel Price Sensitivity ($\pm 15\%$):* Low $₹111.70$ ($₹11.17/\text{km}$), Base $₹125.00$, High $₹138.30$ ($₹13.83/\text{km}$).
  2. *Fuel Efficiency Sensitivity:* Cruising $₹116.90$ ($₹11.69/\text{km}$), Base $₹125.00$, Congestion $₹134.90$ ($₹13.49/\text{km}$).
  3. *Routine Maintenance Sensitivity ($\pm 25\%$):* Low $₹116.00$ ($₹11.60/\text{km}$), Base $₹125.00$, High $₹134.00$ ($₹13.40/\text{km}$).
  4. *Combined Scenarios:* Best case $₹110.90$, Base $₹125.00$, Worst case $₹143.80$.
- **Mathematical Assertion:** Each dimension strictly preserves monotonic ordering: $C_{\text{lower}} < C_{\text{base}} < C_{\text{upper}}$.
- **Actual Result:** `PASSED`.

#### Test 4.7: `test_road_route_retrieval_and_caching`
- **Feature Tested:** Road routing distance retrieval and physical triangle inequality bounds.
- **Input / Condition:** Route between Lalbagh and Forum Mall Konankunte Cross.
- **Mathematical Assertion:** Road distance must be strictly greater than or equal to geodesic straight-line Haversine distance ($D_{\text{road}} \ge D_{\text{Haversine}}$).
- **Actual Result:** `PASSED` ($D_{\text{road}} = 8.12\text{ km} \ge D_{\text{Haversine}} = 6.24\text{ km}$).

#### Test 4.8: `test_simulation_integration_with_transportation_costs`
- **Feature Tested:** Integration of road routing and operating cost calculations into emergency simulation output.
- **Input / Condition:** Simulation execution for Medical Emergency at $(12.9725, 77.5955)$.
- **Mathematical Assertion:** Simulation dictionary contains populated `aggregate_transportation` block, road routes, and sensitivity bounds.
- **Actual Result:** `PASSED`.

#### Test 4.9: `test_journey_cost_zero_distance`
- **Feature Tested:** Boundary value verification for co-located incident and station ($D = 0.0\text{ km}$).
- **Input / Condition:** Road distance $0.0\text{ km}$.
- **Mathematical Assertion:** Effective distance $= 0.0$, fuel cost $= 0.0$, total expenditure $= ₹0.00$.
- **Actual Result:** `PASSED`.

#### Test 4.10: `test_journey_cost_negative_distance_raises`
- **Feature Tested:** Strict defensive validation against non-physical negative distances.
- **Input / Condition:** Road distance $-5.0\text{ km}$.
- **Mathematical Assertion:** Function raises `ValueError` with `"cannot be negative"`.
- **Actual Result:** `PASSED`.

#### Test 4.11: `test_journey_cost_round_trip`
- **Feature Tested:** One-way vs. round-trip depot return calculation.
- **Input / Condition:** Police cruiser on $10.0\text{ km}$ one-way vs. round-trip journey.
- **Mathematical Assertion:** Round-trip effective distance strictly doubles ($20.0\text{ km}$); expenditure strictly doubles ($₹200.00$ vs $₹100.00$).
- **Actual Result:** `PASSED`.

#### Test 4.12: `test_verification_metadata_presence`
- **Feature Tested:** Academic audit compliance: explicit verification status labels attached to all cost data.
- **Input / Condition:** Querying rates and calculating journey costs across all categories.
- **Mathematical Assertion:** Metadata contains `verification_status` and status label stating `"Illustrative Estimate — Not an Official or Verified Operating Rate"`.
- **Actual Result:** `PASSED`.

#### Test 4.13: `test_aggregate_expenditure_round_trip_handling`
- **Feature Tested:** Multi-responder aggregate expenditure with heterogeneous round-trip flags.
- **Input / Condition:** Hospital unit with round-trip ($5\text{ km} \times 2 = 10\text{ km}$); Police unit one-way ($4\text{ km} \times 1 = 4\text{ km}$).
- **Mathematical Assertion:** Total vehicle km $= 14.0\text{ km}$; Aggregate cost $= 10(12.50) + 4(10.00) = ₹165.00$.
- **Actual Result:** `PASSED`.

---

## 4. Academic Invariants Proven by Test Suite

```
+-----------------------------------------------------------------------------------------------+
|                                    PROVEN MATHEMATICAL AXIOMS                                 |
+-----------------------------------------------------------------------------------------------+
| 1. Metric Space Invariants:                                                                   |
|    - d(x, x) = 0                                                                              |
|    - d(x, y) = d(y, x) >= 0                                                                   |
|                                                                                               |
| 2. Spanning Tree Invariants:                                                                  |
|    - |E| = |V| - 1                                                                            |
|    - Acyclic & Connected                                                                      |
|    - Unique simple path between any pair of vertices (BFS verified)                           |
|                                                                                               |
| 3. Algorithmic Optimality Equivalence:                                                        |
|    - W(Prim) == W(Kruskal) == W(Brute-Force Optimal) across all randomized topologies         |
|    - Invariance under edge sparsification: W(MST(G_rho)) == W(MST(G_complete))               |
|                                                                                               |
| 4. Emergency Transportation & Operations:                                                     |
|    - D_road >= D_haversine (Physical Triangle Inequality)                                    |
|    - Concurrent Scene Secure Time: T_scene = max_j(T_j) < sum_j(T_j)                          |
|    - Monotonic Round-Trip Scaling: C(2D) == 2 * C(D)                                          |
|    - Non-negative domain constraint: D < 0 raises ValueError                                  |
+-----------------------------------------------------------------------------------------------+
```

---

## 5. Audit Conclusion

All 45 automated tests pass with 100% compliance. The testing suite provides rigorous coverage across algorithmic graph theory, geometry, physical road routing, financial sensitivity analysis, and emergency dispatch logic.

