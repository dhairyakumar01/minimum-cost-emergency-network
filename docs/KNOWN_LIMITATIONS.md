# Known Limitations & Academic Scope
**Project:** Minimum-Cost Emergency Communication Network Using Minimum Spanning Tree (MST)  
**Study Area:** BBMP Bengaluru, Karnataka, India

---

## 1. Scope & Domain Boundaries

### 1.1 Study Area Boundaries
The platform's spatial scope is strictly bounded to the administrative perimeter of the Bruhat Bengaluru Mahanagara Palike (BBMP) municipal corporation:
- Latitude: $[12.8340^\circ \text{N}, \; 13.1437^\circ \text{N}]$
- Longitude: $[77.4601^\circ \text{E}, \; 77.7841^\circ \text{E}]$

Incidents placed outside this bounding box are rejected during Stage 1 validation. Facilities in neighboring districts (e.g., Bengaluru Rural, Ramanagara, Hosur) are not included in the dataset.

### 1.2 Distinction Between Network Design and Vehicle Dispatch
- **What MST Does:** Constructs a minimum-weight connected communication/interconnection backbone across facilities.
- **What MST Does NOT Do:** It does not route an emergency vehicle through intermediate tree edges. Emergency dispatch always occurs directly from the dispatch station to the incident scene over the shortest path on the road network.

---

## 2. Road Routing & Traffic Assumptions

### 2.1 Static vs Dynamic Traffic Conditions
- Travel times reported by the OSRM engine reflect typical driving speeds derived from OpenStreetMap road classifications (motorway, trunk, primary, secondary, residential) and standard speed limits.
- The system does **not incorporate real-time dynamic traffic sensor data** (e.g., live congestion spikes during peak rush hours on Outer Ring Road, Silk Board, or Whitefield).

### 2.2 OSRM Demonstration Server Rate & Size Limits
- When using the public demonstration server (`router.project-osrm.org`), table queries are subject to community rate limits and maximum URL lengths (~100 coordinates).
- To preserve sub-2-second response times, candidate facility graphs are capped at the nearest 25-50 facilities. Candidates beyond this threshold are excluded with the reason code `COMPUTATIONAL_LIMIT` and recorded in the audit log.
- For high-volume or enterprise deployments, hosting a local OSRM Docker instance (port 5001) removes all network rate limitations.

---

## 3. Fleet & Cost Model Constraints

### 3.1 Linear Single-Agency Fuel Formulation
- Assumed fuel rates (₹12.50/km for Ambulances, ₹6.25/km for Police Patrols, ₹18.00/km for Fire Appliances) are fixed linear approximations based on Karnataka Gazette FD 31 CSL 2024 diesel price benchmarks (₹88.94/L).
- The model does not account for vehicle age, engine displacement, idling in traffic, or specialized on-board medical power consumption.
- Because fuel costs are linear in road distance, "Minimum Cost" optimization is mathematically isomorphic to Mode 2 (Minimum Road Distance) and is therefore excluded as an independent optimization mode.

---

## 4. Facility Registry & Data Freshness

### 4.1 Registry Coverage
- The catalog contains 1,255 facilities (1,097 hospitals/clinics, 138 police stations, 20 fire stations) sourced from open municipal registries.
- Small private clinics or temporary police outposts not recorded in the official dataset are not reflected in the network.
- 13 facility pairs are located within 5 metres of each other (representing co-located clinics, campus multi-specialty buildings, or sub-stations). These are treated as distinct vertices with small positive or zero-distance edges, correctly handled by the mathematical engine.

