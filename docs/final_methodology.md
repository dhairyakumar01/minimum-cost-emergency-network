# FINAL MATHEMATICAL METHODOLOGY & DISCRETE OPTIMIZATION FORMULATION

**Project:** Minimum-Cost Emergency Communication Network Using Minimum Spanning Tree (MST)  
**Study Area:** Bruhat Bengaluru Mahanagara Palike (BBMP), Karnataka, India  
**Academic Focus:** Discrete Mathematics and Graph Theory (DMGT)  
**Version:** Final Release (Phase 9)  
**Date:** November 2026  

---

## 1. Project Problem Statement & Conceptual Boundaries

### 1.1 The Municipal Emergency Coordination Challenge
In a metropolitan area spanning over 700 km² with severe traffic congestion, rapid inter-agency emergency communication and efficient vehicular dispatch are paramount. The municipality oversees three primary public safety agencies:
- **Healthcare & Acute Trauma:** 1,097 hospitals, nursing homes, and clinics.
- **Law Enforcement & Public Order:** 138 police stations and traffic chowkies.
- **Fire & Disaster Rescue:** 20 Karnataka State Fire and Emergency Services (KSFES) stations.

### 1.2 Two-Layer Infrastructure Separation
A core academic requirement of this project is avoiding the conflation of telecommunication network design with vehicular transit routing. The system strictly segregates two distinct operational layers:

```
+-----------------------------------------------------------------------------------+
|                        DUAL-LAYER INFRASTRUCTURE MODEL                            |
+-----------------------------------------------------------------------------------+
| LAYER 1: COMMUNICATION BACKBONE (MINIMUM SPANNING TREE)                           |
| - Connects all 1,255 facilities via 1,254 dedicated communication links.          |
| - Metric: Pairwise great-circle Haversine distance (D_haversine).                 |
| - Topology: Acyclic Spanning Tree (|V| - 1 edges).                                |
| - Objective: Minimize municipal capital expenditure for network deployment.       |
| - Represents: Line-of-sight microwave RF / optical fiber transmission backbone.   |
| - NON-GOAL: Does NOT represent vehicle travel paths.                              |
+-----------------------------------------------------------------------------------+
| LAYER 2: VEHICULAR TRANSIT NETWORK (PHYSICAL ROAD ROUTING)                        |
| - Navigates actual urban street network of Bengaluru.                             |
| - Metric: Physical road distance (D_road) and travel duration (T_road).           |
| - Topology: Directed urban road graph with one-ways and turn restrictions.         |
| - Objective: Rapid physical vehicle dispatch from nearest station to incident.    |
| - Constraint: Physical road distance always exceeds Haversine (D_road >= D_hav).   |
| - Dispatch Rule: Strictly single-agency dispatch per simulation run.             |
+-----------------------------------------------------------------------------------+
```

### 1.3 What the System Does vs. What It Does Not Do
- **What the system does:**
  1. Computes the globally optimal minimum-cost spanning tree connecting all 1,255 municipal facilities using spherical Haversine arc lengths.
  2. Proves mathematical optimality using independent cycle-property verification across all 785,631 candidate non-tree edges via binary-lifting LCA queries.
  3. Provides an interactive incident simulation interface supporting candidate facility filtering, single-agency dispatch constraints, and multi-criteria ranking.
  4. Formally proves the mathematical equivalence between normalized distance and normalized fuel cost under single-agency operations.
- **What the system does NOT do:**
  1. It does NOT claim that the MST calculates the fastest driving route for emergency vehicles.
  2. It does NOT claim to provide real-time dynamic traffic routing (traffic signal timings, live congestion delays).
  3. It does NOT model dynamic facility bed capacity, medical specialty availability, or active fleet inventory depletion.
  4. It does NOT claim that the global Haversine MST is a certified engineering blueprint for optical fiber duct civil works.

---

## 2. Graph Theoretical Formulation

The municipal communication infrastructure is modeled as an undirected, edge-weighted complete graph:
$$G = (V, E, w)$$

### 2.1 Vertex Set ($V$)
The vertex set $V$ represents all verified active emergency facilities within the BBMP municipal boundary:
$$|V| = 1,255\text{ vertices}$$
$$V = V_{\text{hospital}} \cup V_{\text{police}} \cup V_{\text{fire}}$$
where:
- $|V_{\text{hospital}}| = 1,097$ (87.41%)
- $|V_{\text{police}}| = 138$ (11.00%)
- $|V_{\text{fire}}| = 20$ (1.59%)

### 2.2 Edge Set ($E$)
The complete graph includes an undirected edge between every distinct unordered pair of facilities:
$$E = \{(u, v) : u, v \in V, u \ne v\}$$
$$|E| = \frac{|V|(|V| - 1)}{2} = \frac{1,255 \times 1,254}{2} = 786,885\text{ candidate edges}$$

Self-loops $(u, u)$ are strictly excluded. The graph is connected, undirected, and complete ($K_{1255}$).

---

## 3. Distance Metrics & Measurement Engines

### 3.1 Spherical Haversine Geodesic Arc Metric
Edge weights in the complete graph are defined as great-circle geographic distances on a spherical Earth model:
$$w(u, v) = D_{\text{haversine}}(u, v)$$

Given geographic coordinates $(\phi_u, \lambda_u)$ and $(\phi_v, \lambda_v)$ in radians:
$$\Delta\phi = \phi_v - \phi_u, \quad \Delta\lambda = \lambda_v - \lambda_u$$
$$a = \sin^2\left(\frac{\Delta\phi}{2}\right) + \cos(\phi_u)\cos(\phi_v)\sin^2\left(\frac{\Delta\lambda}{2}\right)$$
$$D_{\text{haversine}}(u, v) = 2 R \arcsin(\min(1.0, \sqrt{a}))$$

**Calibrated Earth Radius:**
Per the International Union of Geodesy and Geophysics (IUGG) mean Earth radius standard:
$$R = 6,371.0088\text{ km}$$

**Metric Properties:**
1. *Non-negativity:* $D_{\text{haversine}}(u, v) \ge 0$ for all $u, v \in V$.
2. *Identity of Indiscernibles:* $D_{\text{haversine}}(u, v) = 0 \iff (\phi_u, \lambda_u) = (\phi_v, \lambda_v)$.
3. *Symmetry:* $D_{\text{haversine}}(u, v) = D_{\text{haversine}}(v, u)$.
4. *Triangle Inequality:* $D_{\text{haversine}}(u, v) \le D_{\text{haversine}}(u, w) + D_{\text{haversine}}(w, v)$.

### 3.2 Physical Road Routing Metrics (Layer 2)
For physical vehicular response, vehicles traverse the directed road network:
- **Fastest-Route Travel Duration ($T_{ij}$):** Computed in minutes based on street speed limits, road classifications, and turning constraints.
- **Traversed Road Distance ($D_{ij}^{\text{road}}$):** Cumulative odometer length in kilometers of the selected road trajectory.
- **Directional Asymmetry:** Unlike great-circle arcs, urban road networks exhibit directional asymmetry due to one-way streets, grade separations, and median dividers:
  $$D_{\text{road}}(u, v) \ne D_{\text{road}}(v, u)$$
- **Topological Bounding Invariant:** In Euclidean and spherical spaces, straight-line distance represents the unique geodesic lower bound:
  $$D_{\text{road}}(u, v) \ge D_{\text{haversine}}(u, v) \quad \forall u, v \in V$$
- **Undirected MST Symmetry Convention:** When evaluating undirected spanning subgraphs over road metrics, symmetric edge weights are enforced via forward/reverse directional averaging:
  $$\bar{D}_{\text{road}}(u, v) = \frac{D_{\text{road}}(u, v) + D_{\text{road}}(v, u)}{2}$$

---

## 4. Minimum Spanning Tree Mathematical Foundations

### 4.1 Spanning Tree Definition & Cayley Invariant
A spanning tree $T = (V, E_T)$ of graph $G = (V, E)$ is a connected acyclic subgraph spanning all vertices in $V$.
By Cayley's theorem and fundamental graph properties:
$$|E_T| = |V| - 1 = 1,255 - 1 = 1,254\text{ edges}$$

The Minimum Spanning Tree problem seeks a spanning tree minimizing total edge weight:
$$T^* = \arg\min_T \sum_{e \in E_T} w(e)$$

### 4.2 Prim's Algorithm (Cut-Based Formulation)
Prim's algorithm builds a single growing tree component $S \subset V$, initialized with an arbitrary seed vertex $S = \{s\}$.
At each step, it identifies the minimum-weight crossing edge across the cut $(S, V \setminus S)$:
$$e^* = \arg\min \{w(u, v) : u \in S, v \in V \setminus S\}$$

**Cut Property Theorem:**
For any cut $(S, V \setminus S)$ in connected graph $G$, the minimum-weight edge crossing the cut belongs to every Minimum Spanning Tree of $G$ (provided edge weights across the cut are distinct).

**Implementation Details:**
- **Data Structure:** Binary min-heap priority queue (`heapq`) storing crossing edges.
- **Visited Tracking:** Boolean set of visited vertices; lazy deletion skips popped elements whose destination vertex is already in $S$.
- **Time Complexity:** $O(|E| \log |V|)$ on dense graphs.
- **Deterministic Tie-Breaking:** If multiple edges have identical weight $w$, ties are broken lexicographically by the ordered tuple:
  $$(w, \text{str}(u), \text{str}(v), u, v, \dots)$$

### 4.3 Kruskal's Algorithm (Cycle-Based Formulation)
Kruskal's algorithm initializes a spanning forest where each vertex is an isolated tree.
It inspects all edges in non-decreasing order of weight:
$$w(e_1) \le w(e_2) \le \dots \le w(e_{|E|})$$
For each edge $e = (u, v)$, it adds $e$ to the forest if and only if $u$ and $v$ belong to different connected components (avoiding cycle creation).

**Cycle Property Theorem:**
For any simple cycle $C$ in graph $G$, the edge with the strictly maximum weight cannot belong to any Minimum Spanning Tree of $G$.

**Implementation Details:**
- **Edge Sorting:** Stable mergesort on `["weight_km", "u", "v"]` guaranteeing strict total ordering.
- **Disjoint Set Union (DSU):**
  - *Path Compression:* Flattens tree structures during `find(x)` queries to amortized near-constant depth.
  - *Union by Rank:* Attaches lower-rank trees under higher-rank roots to minimize tree height.
- **Time Complexity:** $O(|E| \log |E|)$ dominated by initial edge sorting; DSU operations execute in $O(|E| \alpha(|V|))$, where $\alpha$ is the inverse Ackermann function ($\alpha(1255) < 4$).

---

## 5. Emergency Simulation & Multi-Objective Optimization Modes

### 5.1 Single-Agency Dispatch Invariant
A key operational rule enforced in the system is **single-agency dispatch per simulation run**:
- When a medical trauma incident occurs, the system evaluates candidate hospitals.
- When an active armed crime occurs, the system evaluates police stations.
- When a structural fire occurs, the system evaluates fire stations.
This reflects municipal emergency response command protocols where specialized vehicle fleets are managed under unified administrative agencies.

### 5.2 Four Optimization Objectives

Let $i$ denote the incident location and $j \in V_{\text{candidate}}$ denote an eligible facility within search radius $R_s$:

1. **Mode 1: Minimum Response Time ($\min T_{ij}$)**
   $$j^* = \arg\min_{j} T_{ij}$$
   Minimizes vehicular transit duration over the street network based on urban road speed limits.

2. **Mode 2: Minimum Road Distance ($\min D_{ij}$)**
   $$j^* = \arg\min_{j} D_{ij}$$
   Minimizes physical road travel distance across Bengaluru's street grid.

3. **Mode 3: Minimum Fleet Fuel Cost ($\min C_{ij}$)**
   $$j^* = \arg\min_{j} C_{ij} \quad \text{where } C_{ij} = D_{ij} \times R_a$$
   Minimizes marginal operating fuel expenditure incurred by the responding fleet.

4. **Mode 4: Balanced Multi-Objective ($W_{ij}^{\text{balanced}}$)**
   A multi-criteria objective combining normalized travel time, road distance, and fuel cost:
   $$W_{ij}^{\text{balanced}} = 0.50 T_{ij}^{\text{norm}} + 0.25 D_{ij}^{\text{norm}} + 0.25 C_{ij}^{\text{norm}}$$

### 5.3 Normalization Formulation
To combine metrics with disparate physical units (minutes, kilometers, rupees), min-max scaling across candidate set $\mathcal{C}$ is applied:
$$X_j^{\text{norm}} = \frac{X_j - \min_{k \in \mathcal{C}} X_k}{\max_{k \in \mathcal{C}} X_k - \min_{k \in \mathcal{C}} X_k} \in [0, 1]$$
If $\max X_k = \min X_k$, $X_j^{\text{norm}} = 0.0$ by convention.

---

## 6. Transportation Operating Cost Model & Equivalence Proof

### 6.1 Direct Marginal Fuel Cost Formulation
Vehicular operating cost is modeled strictly as marginal fuel consumption over physical distance:
$$C_{ij} = D_{ij} \times R_a$$
where:
- $D_{ij}$ is the physical road distance (km).
- $R_a$ is the constant per-kilometer fuel consumption rate (₹/km) for agency $a$.

### 6.2 Evidentiary Basis for Fuel Rates ($R_a$)
- **Statutory Price Authority:** **Government of Karnataka Finance Department Notification No. FD 31 CSL 2024** (effective June 15, 2024) revised state sales tax on diesel from 14.34% to 18.44%, establishing the Bengaluru retail diesel price benchmark at **₹88.94 per liter**.
- **Agency Fleet Calibrations:** The three agency rates represent first-principles engineering fleet models derived under this statutory price benchmark:
  1. *Ambulance Fleet ($R_{\text{hospital}} = ₹12.50/\text{km}$):* Force Motors Traveller / Tata Winger 2.2L CRDe diesel ($7.11\text{ km/L}$) $\implies ₹88.94 / 7.11 \approx ₹12.50/\text{km}$.
  2. *Police Patrol ($R_{\text{police}} = ₹6.25/\text{km}$):* Mahindra Bolero B6 / Hoysala patrol diesel ($14.23\text{ km/L}$) $\implies ₹88.94 / 14.23 \approx ₹6.25/\text{km}$.
  3. *Fire Engine ($R_{\text{fire}} = ₹18.00/\text{km}$):* Ashok Leyland / Tata heavy diesel pumping appliance ($4.94\text{ km/L}$) $\implies ₹88.94 / 4.94 \approx ₹18.00/\text{km}$.

### 6.3 Mathematical Proof of Balanced Optimization Equivalence
**Theorem:** For any single-agency dispatch evaluation, normalized road distance $D^{\text{norm}}$ and normalized fuel cost $C^{\text{norm}}$ are mathematically identical, reducing the balanced optimization function to a two-parameter objective.

**Proof:**
Let candidate set $\mathcal{C}$ contain $m$ eligible facilities of agency $a$.
For each candidate $j \in \mathcal{C}$, transit fuel cost is $C_j = D_j \times R_a$, where $R_a > 0$ is an invariant scalar.

Identify the minimum and maximum costs across $\mathcal{C}$:
$$C_{\min} = \min_{j \in \mathcal{C}} (D_j \times R_a) = R_a \min_{j \in \mathcal{C}} D_j = R_a D_{\min}$$
$$C_{\max} = \max_{j \in \mathcal{C}} (D_j \times R_a) = R_a \max_{j \in \mathcal{C}} D_j = R_a D_{\max}$$

Apply min-max normalization to cost $C_j$:
$$C_j^{\text{norm}} = \frac{C_j - C_{\min}}{C_{\max} - C_{\min}} = \frac{R_a D_j - R_a D_{\min}}{R_a D_{\max} - R_a D_{\min}} = \frac{R_a (D_j - D_{\min})}{R_a (D_{\max} - D_{\min})} = \frac{D_j - D_{\min}}{D_{\max} - D_{\min}} = D_j^{\text{norm}}$$

Because $C_j^{\text{norm}} \equiv D_j^{\text{norm}}$ for every candidate facility $j$:
$$W_j^{\text{balanced}} = 0.50 T_j^{\text{norm}} + 0.25 D_j^{\text{norm}} + 0.25 C_j^{\text{norm}}$$
$$W_j^{\text{balanced}} = 0.50 T_j^{\text{norm}} + 0.25 D_j^{\text{norm}} + 0.25 D_j^{\text{norm}}$$
$$W_j^{\text{balanced}} = \mathbf{0.50 T_j^{\text{norm}} + 0.50 D_j^{\text{norm}} \quad \blacksquare}$$

**Practical Meaning:**
This reduction proves that attempting to optimize both fuel cost and road distance simultaneously in a single-agency scenario is mathematically redundant. The balanced objective is fundamentally an equal weighting between **response duration ($50\%$)** and **traversed distance ($50\%$)**.

---

## 7. Independent MST Optimality Validation (Cycle Property Certificate)

### 7.1 Objective
To provide absolute academic proof that the computed spanning tree $T^*$ is optimal without relying on self-referential algorithm outputs, an independent optimality verifier was implemented using tree Lowest Common Ancestor (LCA) queries.

### 7.2 Binary-Lifting LCA Engine
For 1,255 vertices, binary lifting precomputes ancestor jump pointers and path maxima:
$$\text{LOGN} = 12 \implies 2^{12} - 1 = 4,095\text{ depth levels}$$
- Table `up[k, i]`: Stores the $2^k$-th ancestor of vertex $i$.
- Table `max_edge[k, i]`: Stores the maximum edge weight on the path from vertex $i$ to its $2^k$-th ancestor.

**Recurrence Relations:**
$$\text{up}[k, i] = \text{up}[k - 1, \text{up}[k - 1, i]]$$
$$\text{max\_edge}[k, i] = \max(\text{max\_edge}[k - 1, i], \text{max\_edge}[k - 1, \text{up}[k - 1, i]])$$

### 7.3 Non-Tree Edge Optimality Certificate
For all $785,631$ non-tree edges $(u, v) \in E \setminus E_T$, query the maximum tree edge:
$$w_{\text{path\_max}}(u, v) = \max_{e \in P_T(u, v)} w(e)$$
Verify the cycle property inequality:
$$w(u, v) \ge w_{\text{path\_max}}(u, v) - \tau$$
where $\tau = 10^{-9}\text{ km}$ accounts for IEEE 754 floating-point precision.

**Empirical Result:**
- Evaluated non-tree edges: **785,631**
- Verified violations: **0**
- Equal-weight alternatives: **1**
- Mathematical conclusion: Tree $T^*$ is an exact, certified Minimum Spanning Tree of $K_{1255}$.

