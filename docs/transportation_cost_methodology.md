# Research Methodology & Transportation Cost Audit for Emergency Responders in Bengaluru

**Project:** Minimum-Cost Emergency Communication Network Using Minimum Spanning Tree (MST)  
**Academic Focus:** Discrete Mathematics and Graph Theory (DMGT) Experiential Learning  
**Geographical Scope:** Bengaluru Metropolitan Area, Karnataka, India  
**Audit Date:** November 2026  
**Audit Standard:** Strict Academic Integrity & Multi-Tier Evidence Classification  

---

## 1. Executive Summary & Research Scope

This document provides the formal audit and methodology for evaluating vehicular transportation expenditures associated with emergency response logistics in the Bengaluru metropolitan area.

### Core Conceptual Distinctions (Preserving the Five-Layer Separation)
In an academic graph theory and network optimization evaluation, distinct physical and operational metrics must never be conflated:

1. **Spherical Haversine Distance ($D_{\text{haversine}}$):** Straight-line great-circle distance between two coordinates on the WGS-84 sphere ($R = 6,371.0088\text{ km}$). Used solely as edge candidate weights to construct the complete theoretical graph $K_{1255}$ and solve the Minimum Spanning Tree problem.
2. **MST Geographical Edge Weight ($w_{uv}$):** The pairwise great-circle distance between facility vertices $u$ and $v$ selected by Prim's or Kruskal's algorithm. It functions as a **conceptual mathematical communication-backbone model** representing the minimum theoretical span required to interconnect all facilities. It does **not** represent physically installed or trenched telecommunication infrastructure.
3. **MST Tree Path Distance ($D_{\text{tree}}$):** The unique simple path length across the tree graph between two facility vertices, representing the multi-hop conceptual coordination distance for inter-agency telemetry signals.
4. **Physical Road Distance ($D_{\text{road}}$):** The actual vehicular driving distance over the physical urban street grid of Bengaluru, obtained via OpenStreetMap (OSRM) street routing.
5. **Estimated Travel Duration ($T_{\text{travel}}$):** The estimated vehicular journey transit time over the road network based on street classifications, turn restrictions, and urban driving speed profiles.
6. **Transportation Expenditure ($C_j$):** The direct vehicular operating expenditure incurred when dispatching emergency vehicle category $j$ over physical road distance $D_{\text{road}}$.

### Scope Boundaries: What Is Included vs Excluded
- **Included in Operating Estimates:** Marginal fuel consumption per kilometer and estimated routine fleet mechanical maintenance provision (lubricants, filters, tires, brake wear).
- **Excluded:** Road construction, fiber-optic cable trenching, telecommunication transceiver procurement, hospital capital construction, medical equipment capital cost, patient medical fees, and permanent staff payroll.
- **Consumer Tariff vs Internal Fleet Operating Cost:** Regulated commercial ambulance fares represent private market consumer prices inclusive of equipment, medical staffing, PPE kits, and operator profit. These are rigorously segregated from direct state fleet operating costs.

---

## 2. Multi-Tier Evidence Audit of Transportation Figures

To maintain academic defensibility, all cost figures are categorized into four distinct evidentiary tiers:
1. **Verified Statutory Orders:** Primary government orders directly verified from accessible gazette notifications.
2. **Secondary-Source Reported Statutory Ceilings:** Authentic government regulations reported in reliable secondary investigative media, where the scanned circular PDF itself is not hosted on an open-access public URL.
3. **Illustrative Engineering Derived Estimates:** First-principles mathematical models combining real-world fuel benchmarks with representative engineering assumptions.
4. **Unsupported Inputs Disclosed:** Specific variables that are engineering approximations rather than audited operational data.

```
+-------------------------------------------------------------------------------------------------------+
|                                  EVIDENTIARY AUDIT CLASSIFICATION MATRIX                              |
+-------------------+-----------------+----------------------------------------+------------------------+
| Rate Figure       | Vehicle Profile | Evidentiary Tier                       | Primary / Secondary Ref|
+-------------------+-----------------+----------------------------------------+------------------------+
| ₹120.00 / km      | Ambulance       | Secondary-Source Reported Tariff Cap   | The Hindu / TOI (2021) |
| ₹12.50 / km       | Ambulance (108) | Illustrative Engineering Estimate      | First-Principles Model |
| ₹10.00 / km       | Police Hoysala  | Illustrative Engineering Estimate      | First-Principles Model |
| ₹42.00 / km       | Fire Tender     | Illustrative Engineering Estimate      | First-Principles Model |
+-------------------+-----------------+----------------------------------------+------------------------+
```

---

### Audit Item 1: Private Ambulance Tariff Ceiling (₹120.00 / km)
1. **Does the cited figure genuinely exist?** Yes.
2. **Primary vs. Secondary Classification:** **Secondary-Source Reported Statutory Tariff Cap**. While an official Government Order was promulgated in May 2021 under the *Karnataka Epidemic Diseases Ordinance / Act, 2020*, the signed circular PDF is not hosted on an open-access government portal in our environment; hence, evidence is established via secondary investigative reports (*The Hindu*, *Bangalore Mirror / Times of India*, *The Canara Post*).
3. **Exact Document Title:** Notification on Maximum Fare Ceiling for Private Ambulance Services during Public Health Emergency.
4. **Issuing Organization:** Government of Karnataka, Department of Health and Family Welfare & Transport Department.
5. **Publication Date:** May 2021.
6. **Exact Section / Clause Supporting the Figure:** Mandates capped fares for Patient Transport Ambulances (PTA) and Basic Life Support (BLS) Ambulances:
   - Base fare: **₹1,500** for first 10 km (PTA) / **₹2,000** for first 10 km (BLS).
   - Additional distance: **₹120.00 per kilometer** for each subsequent kilometer beyond 10 km.
   - Waiting charges: ₹200 to ₹250 per hour.
7. **Secondary Source References:**
   - [The Hindu Report: Karnataka caps ambulance rates](https://thehindu.com/news/national/karnataka/karnataka-caps-ambulance-rates/article34925828.ece)
   - [Times of India / Bangalore Mirror: State caps ambulance fares](https://bangaloremirror.indiatimes.com/bangalore/others/state-caps-ambulance-fares/articleshow/82437812.cms)
   - [The Canara Post: Karnataka Government caps ambulance fares](https://thecanarapost.com/karnataka-government-caps-ambulance-fares-check-rates-here/)
8. **Cost Components Included:** Vehicle capital depreciation, fuel, driver wage, PPE kits, sanitization, basic oxygen administration apparatus, operator overhead, and commercial profit margin.
9. **Geographic Relevance:** Karnataka State, including the entire Bengaluru metropolitan area.
10. **Financial Classification:** **Regulated Maximum Consumer Tariff Cap for Private Ambulances**. It is NOT the government's internal fleet vehicle running cost.
- **Verification Status:** `SECONDARY_SOURCE_REPORTED_STATUTORY_TARIFF_CAP`

---

### Audit Item 2: Public Ambulance Operating Expenditure (₹12.50 / km)
1. **Does the cited source genuinely exist as a statutory per-km order?** No statutory Gazette notification fixes an internal per-km operating fee of ₹12.50.
2. **Primary Source Assessment:** The Karnataka State Government directly funds the 108 "Arogya Kavacha" ambulance fleet through departmental line-item allocations (bulk diesel indents, institutional maintenance contracts, and salaried staff payroll) rather than paying a statutory per-km contractor fee.
3. **Exact Document Title:** N/A.
4. **Issuing Organization:** National Health Mission (NHM) Karnataka / Directorate of Health & Family Welfare Services.
5. **Cost Components Included in Derived Estimate:** Direct marginal mechanical operating costs (fuel + routine scheduled maintenance).
6. **Disclosure of Unsupported Inputs:** Fuel efficiency ($10.0\text{ km/L}$) and routine maintenance allowance ($₹3.606/\text{km}$) are illustrative engineering modeling assumptions; they are **not** extracted from official departmental audit reports.
7. **Financial Classification:** **Illustrative Engineering Derived Estimate**.
- **Verification Status:** `Not established from verified evidence` as an official statutory rate. Classified as `Illustrative Estimate — Not an Official or Verified Operating Rate`.

---

### Audit Item 3: Police Patrol Vehicle Operating Expenditure (₹10.00 / km)
1. **Does the cited source genuinely exist as a statutory per-km order?** No. Police patrolling is a non-commercial sovereign public duty.
2. **Primary Source Assessment:** Karnataka Police Motor Transport (KPMT) Wing maintains Hoysala patrol vehicles through departmental police garages, government fuel vouchers, and state budget allocations.
3. **Exact Document Title:** N/A.
4. **Issuing Organization:** Karnataka State Police / Bengaluru City Police (BCP).
5. **Cost Components Included in Derived Estimate:** Marginal fuel consumption + routine garage maintenance provision.
6. **Disclosure of Unsupported Inputs:** Fuel efficiency ($12.0\text{ km/L}$) and maintenance provision ($₹2.588/\text{km}$) are illustrative engineering modeling assumptions.
7. **Financial Classification:** **Illustrative Engineering Derived Estimate**.
- **Verification Status:** `Not established from verified evidence` as an official statutory rate. Classified as `Illustrative Estimate — Not an Official or Verified Operating Rate`.

---

### Audit Item 4: Heavy Fire Engine Operating Expenditure (₹42.00 / km)
1. **Does the cited source genuinely exist as a statutory per-km order?** No. Fire services are funded through state budget grants.
2. **Primary Source Assessment:** KSFES tenders specify heavy chassis procurement (Ashok Leyland 16T / Tata 16T), water tank fabrication (4,500L), and high-pressure centrifugal PTO pump specifications. No per-km transport tariff is charged to citizens or contracted.
3. **Exact Document Title:** N/A.
4. **Issuing Organization:** Karnataka State Fire & Emergency Services (KSFES).
5. **Cost Components Included in Derived Estimate:** High diesel consumption (2.8 km/L) + heavy chassis maintenance and PTO pump wear provision.
6. **Disclosure of Unsupported Inputs:** Fuel efficiency ($2.8\text{ km/L}$) and heavy maintenance provision ($₹10.236/\text{km}$) are illustrative engineering modeling assumptions.
7. **Financial Classification:** **Illustrative Engineering Derived Estimate**.
- **Verification Status:** `Not established from verified evidence` as an official statutory rate. Classified as `Illustrative Estimate — Not an Official or Verified Operating Rate`.

---

## 3. Engineering Derivation & Diesel Benchmark Analysis

### Establishing the Retail Diesel Benchmark (₹88.94 / Liter)
A critical discrepancy identified during audit involved conflicting references to ₹88.94/L and ₹102.86/L. Investigation of Karnataka state tax revisions establishes:

- **Source:** Government of Karnataka, Finance Department Notification (effective **June 15, 2024**).
- **Policy Action:** The state government increased the sales tax on diesel from 14.34% to 18.44%, and on petrol from 25.92% to 29.84%.
- **Price Effect in Bengaluru:**
  - **High-Speed Diesel:** Revised to **₹88.94 / Liter** (the benchmark used across our mathematical model, JSON database, Python implementation, and test suite).
  - **Petrol:** Revised concurrently to **₹102.86 / Liter**.
- **Resolution:** Earlier drafts mistakenly referenced the petrol price figure (₹102.86) in narrative descriptions of diesel. All models, code, tests, and documentation are now rigorously harmonized to the verified diesel benchmark of **₹88.94 / Liter**.

### Engineering Derivation Formula
For vehicle category $j$:
\[
R_j = R_{\text{fuel}} + R_{\text{maint}} = \left( \frac{P_{\text{diesel}}}{\eta_j} \right) + R_{\text{maint}}
\]
Where:
- $P_{\text{diesel}} = ₹88.94 \text{ / Liter}$ (Retail High-Speed Diesel in Bengaluru benchmark, June 2024 tax notification).
- $\eta_j$ = Representative urban fuel efficiency in stop-and-go Bengaluru emergency driving conditions.
- $R_{\text{maint}}$ = Estimated routine per-kilometer maintenance provision (lubricants, filters, tires, brake pads).

### Baseline Parameter Breakdown

| Vehicle Category | Representative Model | Urban Fuel Economy ($\eta$) | Fuel Cost ($R_{\text{fuel}}$) | Maintenance Provision ($R_{\text{maint}}$) | Illustrative Direct Operating Rate ($R_j$) | Status Classification |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **Ambulance** | Force Traveller / Tata Winger 2.2L Diesel | 10.0 km/L | ₹8.894 / km | ₹3.606 / km | **₹12.50 / km** | *Illustrative Estimate — Unsupported Inputs Disclosed* |
| **Police Patrol** | Mahindra Bolero B6 / Maruti Ertiga 1.5L Diesel | 12.0 km/L | ₹7.412 / km | ₹2.588 / km | **₹10.00 / km** | *Illustrative Estimate — Unsupported Inputs Disclosed* |
| **Fire Engine** | Ashok Leyland 16T Heavy Water Tender (4,500L) | 2.8 km/L | ₹31.764 / km | ₹10.236 / km | **₹42.00 / km** | *Illustrative Estimate — Unsupported Inputs Disclosed* |

---

## 4. Multi-Dimensional Sensitivity Analysis

To avoid conflating distinct operating variables, sensitivity analysis is explicitly decomposed into four isolated experimental dimensions:

### Dimension 1: Retail Diesel Price Sensitivity ($\pm 15\%$)
*Holding fuel efficiency ($\eta$) and maintenance provision ($R_{\text{maint}}$) constant at base values.*
- **Low Diesel Price (-15%):** $P_{\text{diesel}} = ₹75.60 \text{ / L}$
- **Base Diesel Price:** $P_{\text{diesel}} = ₹88.94 \text{ / L}$
- **High Diesel Price (+15%):** $P_{\text{diesel}} = ₹102.28 \text{ / L}$

| Vehicle Category | Low Diesel (-15%) | Base Diesel (₹88.94/L) | High Diesel (+15%) | Experimental Condition |
| :--- | :---: | :---: | :---: | :--- |
| **Ambulance** | **₹11.17 / km** | **₹12.50 / km** | **₹13.83 / km** | $(75.60/10.0)+3.61$ to $(102.28/10.0)+3.61$ |
| **Police Patrol** | **₹8.89 / km** | **₹10.00 / km** | **₹11.11 / km** | $(75.60/12.0)+2.59$ to $(102.28/12.0)+2.59$ |
| **Fire Engine** | **₹37.24 / km** | **₹42.00 / km** | **₹46.76 / km** | $(75.60/2.8)+10.24$ to $(102.28/2.8)+10.24$ |

---

### Dimension 2: Urban Fuel Efficiency Sensitivity (Congestion vs. Cruising)
*Holding diesel price ($₹88.94\text{ / L}$) and maintenance provision constant at base values.*
- **Cruising / Open Corridor:** Higher efficiency under free-flow conditions.
- **Base Urban Traffic:** Normal Bengaluru stop-and-go conditions.
- **Severe Congestion:** Heavy traffic delays and prolonged idling.

| Vehicle Category | Cruising Efficiency | Base Urban | Severe Congestion | Efficiency Range ($\eta$) |
| :--- | :---: | :---: | :---: | :--- |
| **Ambulance** | **₹11.69 / km** | **₹12.50 / km** | **₹13.49 / km** | $11.0\text{ km/L}$ (cruising) to $9.0\text{ km/L}$ (congestion) |
| **Police Patrol** | **₹9.18 / km** | **₹10.00 / km** | **₹11.06 / km** | $13.5\text{ km/L}$ (highway) to $10.5\text{ km/L}$ (gridlock) |
| **Fire Engine** | **₹35.65 / km** | **₹42.00 / km** | **₹50.66 / km** | $3.5\text{ km/L}$ (corridor) to $2.2\text{ km/L}$ (idling/pumping) |

---

### Dimension 3: Routine Maintenance Cost Provision Sensitivity ($\pm 25\%$)
*Holding diesel price ($₹88.94\text{ / L}$) and fuel efficiency constant at base values.*
- Reflects variation in vehicle fleet age, severe road surface wear, and component replacement costs.

| Vehicle Category | Low Maintenance (-25%) | Base Maintenance | High Maintenance (+25%) | Maintenance Range ($R_{\text{maint}}$) |
| :--- | :---: | :---: | :---: | :--- |
| **Ambulance** | **₹11.60 / km** | **₹12.50 / km** | **₹13.40 / km** | $₹2.70/\text{km}$ to $₹4.51/\text{km}$ |
| **Police Patrol** | **₹9.35 / km** | **₹10.00 / km** | **₹10.65 / km** | $₹1.94/\text{km}$ to $₹3.24/\text{km}$ |
| **Fire Engine** | **₹39.44 / km** | **₹42.00 / km** | **₹44.56 / km** | $₹7.68/\text{km}$ to $₹12.80/\text{km}$ |

---

### Dimension 4: Combined Operating Condition Scenarios
*Compound scenarios reflecting simultaneous shifts across operating conditions:*
- **Best Case (Highway Cruising):** Free-flow corridor, improved efficiency, and reduced mechanical wear.
- **Base Case:** Standard urban driving in Bengaluru.
- **Worst Case (Severe Congestion & Prolonged Idling):** Severe traffic delays, reduced efficiency, and heightened mechanical stress.

| Vehicle Category | Lower Bound (Best Case) | Base Case Rate | Upper Bound (Worst Case) | Scenario Assumptions |
| :--- | :---: | :---: | :---: | :--- |
| **Ambulance** | **₹11.09 / km** | **₹12.50 / km** | **₹14.38 / km** | $\eta=11.0, M=3.00$ vs $\eta=9.0, M=4.50$ |
| **Police Patrol** | **₹8.79 / km** | **₹10.00 / km** | **₹11.47 / km** | $\eta=13.5, M=2.20$ vs $\eta=10.5, M=3.00$ |
| **Fire Engine** | **₹33.91 / km** | **₹42.00 / km** | **₹52.43 / km** | $\eta=3.5, M=8.50$ vs $\eta=2.2, M=12.00$ |

---

## 5. Mathematical Model of Transportation Expenditure

### Individual Journey Expenditure (One-Way vs Round-Trip)
For an emergency dispatch from responding facility $i$ to incident location $k$:
\[
C_{i, j} = D_{\text{road}}(i, k) \times (1 + \mathbb{I}_{\text{round\_trip}}) \times R_j
\]
Where:
- $D_{\text{road}}(i, k)$ is the physical road distance returned by the OpenStreetMap (OSRM) driving profile.
- $\mathbb{I}_{\text{round\_trip}} = 1$ if vehicle return to base station is included, and $0$ for one-way scene transit.
- $R_j$ is the vehicle operating rate per kilometer.

### Multi-Agency Concurrent Dispatch Expenditure
For an incident requiring multiple responding agencies $\mathcal{S}$ (e.g. Hospital + Police + Fire Station):
\[
C_{\text{total}} = \sum_{j \in \mathcal{S}} C_{i_j, j} = \sum_{j \in \mathcal{S}} \left( D_{\text{road}}(i_j, k) \times (1 + \mathbb{I}_{\text{round\_trip}}) \times R_j \right)
\]

### Physical Reality of Concurrent Arrival (No Time Summation)
Because responding units depart simultaneously from their respective stations upon alarm confirmation:
\[
T_{\text{scene\_secure}} = \max_{j \in \mathcal{S}} T_{i_j, k}
\]
*(Summing transit times across concurrent trips, i.e., $\sum T_j$, is physically false and strictly rejected).*

---

## 6. Explicitly Rejected Claims & Summary of Evidence

1. **Rejected Claim:** *The ₹120.00/km rate represents internal government fleet operating cost.*  
   **Audit Finding:** False. The ₹120.00/km figure is a secondary-source reported statutory ceiling on private commercial ambulance tariffs, inclusive of private capital, equipment, and profit margins.
2. **Rejected Claim:** *₹12.50/km, ₹10.00/km, and ₹42.00/km are statutory rates published in the Karnataka Government Gazette.*  
   **Audit Finding:** False. No gazette order establishes these per-km rates. They are illustrative engineering estimates derived from fuel consumption benchmarks.
3. **Rejected Claim:** *The MST communication links represent physical telecommunication lines.*  
   **Audit Finding:** False. The MST is a conceptual mathematical communication-backbone model using great-circle Haversine weights; it does not model trenching or physical fiber-optic cables.
