# DATASET DOCUMENTATION & PROVENANCE AUDIT

**Project:** Minimum-Cost Emergency Communication Network Using Minimum Spanning Tree (MST)  
**Study Area:** Bruhat Bengaluru Mahanagara Palike (BBMP), Karnataka, India  
**Dataset File:** `data/processed/emergency_facilities.csv`  
**Record Count:** 1,255 Verified Emergency Facilities  
**Format:** UTF-8-SIG CSV (Comma-Separated Values with Byte Order Mark handling)  

---

## 1. Dataset Origin & Provenance

### 1.1 Source Attribution
The emergency facility dataset was extracted from **OpenStreetMap (OSM)** geographic data exports corresponding to the administrative boundary of the **Bruhat Bengaluru Mahanagara Palike (BBMP)** metropolitan corporation.

- **Primary Source:** OpenStreetMap contributors (Open Database License - ODbL).
- **Extraction Scope:** Emergency public safety and acute healthcare infrastructure within the BBMP municipal jurisdiction and immediate contiguous urban growth corridors (Electronic City, Whitefield, Yelahanka, Kengeri).
- **Raw Export Layers:**
  - `hospitals_raw.geojson`: Features tagged `amenity=hospital`, `amenity=clinic`, `healthcare=hospital`.
  - `police_raw.geojson`: Features tagged `amenity=police`, `office=government` + `police=*`.
  - `fire_stations_raw.geojson`: Features tagged `amenity=fire_station`.

---

## 2. Facility Agency Distribution

The dataset comprises exactly 1,255 emergency response facilities classified into three public safety agencies:

```
+-----------------------------------------------------------------------------------+
|                        FACILITY AGENCY DISTRIBUTION IN BBMP                       |
+-------------------+-----------------+-----------------------+---------------------+
| Agency Category   | Record Count    | Percentage of Fleet   | Representative Role |
+-------------------+-----------------+-----------------------+---------------------+
| hospital          | 1,097           | 87.41%                | Trauma & acute care |
| police_station    | 138             | 11.00%                | Law & order patrol  |
| fire_station      | 20              | 1.59%                 | KSFES fire & rescue |
+-------------------+-----------------+-----------------------+---------------------+
| TOTAL             | 1,255           | 100.00%               | Full Graph K_1255   |
+-------------------+-----------------+-----------------------+---------------------+
```

### Agency Normalization
In the Flask backend (`backend/config.py` and `backend/services/data_service.py`), agency identifiers are canonicalized:
- `hospital` $\leftarrow$ `["hospital", "hospitals", "clinic", "clinics", "ambulance"]`
- `police_station` $\leftarrow$ `["police_station", "police", "law_enforcement"]`
- `fire_station` $\leftarrow$ `["fire_station", "fire", "rescue"]`

---

## 3. Coordinate Quality & Boundary Validation

All 1,255 facility records were evaluated against geographic coordinate validation rules (`src/mst_network.py::load_facilities`):

1. **Missing Coordinate Check:**
   - Latitudes missing / `NaN`: **0**
   - Longitudes missing / `NaN`: **0**
2. **Global Coordinate Boundary Check:**
   - $\text{Latitude} \in [-90.0, 90.0]$: 100% compliant.
   - $\text{Longitude} \in [-180.0, 180.0]$: 100% compliant.
3. **Bengaluru Regional Bounding Box:**
   - Minimum Latitude: $12.7845^\circ\text{ N}$
   - Maximum Latitude: $13.2140^\circ\text{ N}$
   - Minimum Longitude: $77.4120^\circ\text{ E}$
   - Maximum Longitude: $77.7890^\circ\text{ E}$
   - All 1,255 facilities reside strictly within the geographic bounds of the greater Bengaluru urban agglomeration.
4. **Primary Key Uniqueness:**
   - Total records: 1,255
   - Unique `facility_id` values: 1,255 (Zero primary key collisions).
   - Format: OpenStreetMap identifiers (`node/{id}`, `way/{id}`, `relation/{id}`).

---

## 4. Duplicate Coordinate Investigation

During the mathematical audit of the complete graph's 786,885 edges, exactly **one** pairwise edge exhibited an edge weight of `0.000000 km`:

### 4.1 Record Breakdown
- **Facility 1:**
  - ID: `way/1544830710`
  - Name: `SPS Surgicals`
  - Type: `hospital`
  - Latitude: `12.9541576° N`
  - Longitude: `77.6608368° E`
- **Facility 2:**
  - ID: `way/1544831540`
  - Name: `""` (Unnamed healthcare geometry in OpenStreetMap)
  - Type: `hospital`
  - Latitude: `12.9541576° N`
  - Longitude: `77.6608368° E`

### 4.2 Investigation Assessment
1. **Identical Centroids:** Both features share exact coordinates across all 7 decimal places.
2. **OSM Geometry Artifact:** In OpenStreetMap, these represent two distinct polygon features tagged with healthcare properties representing co-located rooms or administrative subdivisions within the same physical medical complex.
3. **Academic Integrity Decision:** Per strict project audit rules, these records were **NOT silently merged or deleted**. Deleting one record would reduce the vertex count from 1,255 to 1,254 and alter the canonical dataset. Retaining them preserves dataset provenance while both Prim and Kruskal handle the zero-weight connection with zero added tree cost and zero cycle violations.

---

## 5. Dataset Limitations

1. **Static Data Snapshot:**
   The facility catalog represents a discrete snapshot of OpenStreetMap data. Newly inaugurated Primary Health Centres (PHCs) or decommissioned private nursing homes post-dating the snapshot are not reflected.
2. **Lack of Clinical & Operational Capacity Attributes:**
   OSM data contains facility locations and names, but omits:
   - Bed counts (ICU beds, oxygen-supported beds, general ward capacity).
   - Medical specialty designations (cardiac cath-labs, burn units, Level-1 trauma surgical suites).
   - Emergency dispatch equipment (snorkel ladders, hydraulic extrication shears, hazardous materials containment).
3. **Stationary Representation of Mobile Patrols:**
   Police Hoysala patrol vehicles are assigned to stationary police station vertices. The dataset does not incorporate real-time GPS telemetry from mobile cruisers on active patrol.
4. **Centroid Approximation:**
   Large hospital campuses (e.g., Victoria Hospital, NIMHANS, Manipal Hospital) are represented by a single geographic centroid coordinate rather than individual building gates or emergency ambulance bays.
