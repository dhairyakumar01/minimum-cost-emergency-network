# COMPREHENSIVE LIMITATIONS & ACADEMIC BOUNDARIES

**Project:** Minimum-Cost Emergency Communication Network Using Minimum Spanning Tree (MST)  
**Study Area:** Bruhat Bengaluru Mahanagara Palike (BBMP), Karnataka, India  
**Policy:** Strict Transparency & Multi-Disciplinary Limitation Disclosure  

---

## 1. Executive Statement

In academic research and engineering demonstrations, clearly delineating what a system **cannot** do is as important as presenting its capabilities. 

This project implements a discrete optimization model for emergency infrastructure communication and logistics dispatch. It does **not** purport to be an operational, real-time emergency dispatching CAD (Computer-Aided Dispatch) system. 

The limitations documented below represent inherent methodological boundaries.

---

## 2. Telecommunication & Graph-Theoretic Limitations (Layer 1)

### 2.1 Global Haversine MST Is a Conceptual Model, Not a Construction Blueprint
- The global spanning tree connects all 1,255 facilities with 1,254 straight-line great-circle links minimizing cumulative geographic distance (480.1784 km).
- **Limitation:** In physical civil engineering, fiber-optic telecommunication cables cannot be deployed in straight line-of-sight arcs. They must follow municipal road rights-of-way, bridge ducts, and utility easements, avoiding subterranean metro tunnels, water bodies, and private property.
- Therefore, the global MST represents a **theoretical lower bound on inter-facility connectivity**, not an executable civil works trenching plan.

### 2.2 Complete Lack of Topological Redundancy (Zero Cycle Invariant)
- By definition, an MST is an acyclic tree with exactly $|V| - 1$ edges and vertex connectivity $k = 1$.
- **Limitation:** In critical emergency communications, high survivability requires redundant ring or mesh topologies (such as 2-connected or biconnected graphs). In our MST model, severing any single communication edge partitions the entire metropolitan network into two mutually unreachable components.

### 2.3 Two-Dimensional Spherical Elevation Simplification
- Great-circle distances are computed using spherical trigonometry with IUGG Earth radius $R = 6,371.0088\text{ km}$.
- **Limitation:** Bengaluru sits on the Deccan Plateau with undulating terrain ranging from ~850 meters to ~960 meters above Mean Sea Level (MSL). Topographical relief and elevation variations are not modeled in pairwise link lengths.

---

## 3. Physical Road Routing & Vehicular Dispatch Limitations (Layer 2)

### 3.1 No Live Dynamic Traffic Guarantee
- Road transit durations ($T_{\text{road}}$) are estimated using OpenStreetMap road classification speed limits.
- **Limitation:** Bengaluru experiences severe, time-varying urban traffic congestion (e.g., peak-hour chokepoints along Outer Ring Road, Silk Board, Tin Factory, and Hebbal Flyover). The system does not ingest live GPS probe feeds (such as Google Maps Traffic or TomTom APIs); estimated durations represent free-flow conditions.

### 3.2 Routing Profile Restrictions
- The default OSRM driving profile models passenger automobile movements.
- **Limitation:** Emergency response vehicles operate under distinct emergency exemptions (sirens, flashing beacons, priority traffic signal overrides, contraflow on divided corridors). Conversely, heavy fire tenders cannot navigate narrow, unpaved lanes in historic Bengaluru areas (Chickpet, Cottonpet) where a private car might pass.

### 3.3 MST Paths Are NOT Vehicular Response Routes
- In the simulation interface, telemetry coordination paths can be traced across the MST backbone.
- **Limitation:** Under no circumstances should an emergency ambulance or fire engine follow an MST path. Spanning tree edges represent telecommunication links; vehicles must strictly navigate the physical surface street network.

---

## 4. Operational & Fleet Management Limitations

### 4.1 Infinite Fleet Capacity & Vehicle Availability Assumption
- When an incident occurs, the dispatch ranking identifies the nearest response stations.
- **Limitation:** The model assumes that the nearest facility always possesses an idle, fully crewed emergency vehicle ready for immediate rollout. In real-world municipal operations, vehicles may be actively deployed on prior calls, undergoing mechanical overhaul, or constrained by shift turnover.

### 4.2 Facility Clinical Specialties & Equipment Tiers Not Modeled
- All healthcare facilities are modeled as homogeneous medical response nodes.
- **Limitation:** An acute neuro-trauma patient or burn victim requires Level-1 tertiary trauma facilities (e.g., NIMHANS or Victoria Hospital), not an outpatient polyclinic or cosmetic dermatology center. The dataset does not incorporate hospital clinical capability classifications.

### 4.3 Fuel-Only Cost Assumption
- Vehicular operating expenditure is modeled strictly as:
  $$C_{ij} = D_{ij} \times R_a$$
  where $R_a$ reflects marginal fuel consumption per kilometer (Ambulance ₹12.50/km, Police ₹6.25/km, Fire ₹18.00/km) under statutory diesel benchmark ₹88.94/L (GOK Notification No. FD 31 CSL 2024).
- **Limitation:** This formulation excludes vehicle capital depreciation, specialized on-board medical equipment wear (defibrillators, oxygen regulators), paramedical crew salaries, insurance, and institutional dispatch center overhead.

---

## 5. Summary Matrix of Limitations

```
+-----------------------------------------------------------------------------------+
|                        RESEARCH LIMITATION SUMMARY MATRIX                         |
+--------------------+---------------------------+----------------------------------+
| Domain             | Modeled in System         | Real-World Unmodeled Factor      |
+--------------------+---------------------------+----------------------------------+
| Network Topology   | Global Acyclic MST        | Ring / Mesh Path Redundancy      |
| Transmission Media | Great-Circle Haversine    | Municipal Road Rights-of-Way     |
| Traffic Conditions | Free-Flow Road Speeds     | Live Urban Congestion & Bottlenecks|
| Vehicle Routing    | Physical Street Network   | Emergency Signal Priority / Width|
| Facility Capacity  | Geographic Coordinates    | ICU Beds, Trauma Centers, Crew   |
| Fleet Logistics    | Infinite Availability     | Concurrent Calls & Fleet Depletion|
| Journey Cost       | Marginal Diesel Rate      | Capital, Medical Staff & Overhead|
+--------------------+---------------------------+----------------------------------+
```

