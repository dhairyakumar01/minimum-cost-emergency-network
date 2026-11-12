# Mathematical Methodology & Algorithm Specification
**Project:** Minimum-Cost Emergency Communication Network Using Minimum Spanning Tree (MST)  
**Study Area:** Bruhat Bengaluru Mahanagara Palike (BBMP), Karnataka, India  
**Academic Domain:** Discrete Mathematics and Graph Theory (DMGT)

---

## 1. Problem Formulation & Graph Theoretical Framework

Emergency infrastructure planning in a metropolitan area requires addressing two fundamentally distinct network problems:
1. **Network Backbone Topology (Layer 1):** Designing a minimum-cost, fault-resilient communication/interconnection backbone connecting critical emergency nodes (spanning all facilities or a localized cluster).
2. **First-Response Dispatch Routing (Layer 2):** Determining the optimal dispatch order of emergency vehicles from existing stations directly to an incident scene over the directed road network.

These two objectives must **never be conflated**. A Minimum Spanning Tree (MST) minimizes the aggregate edge weight required to connect all vertices in a network. In contrast, emergency dispatch minimizes point-to-point transit times from individual candidate facilities to a single incident sink.

### 1.1 Mathematical Definitions
Let the study area be represented by an undirected, weighted graph:
$$G = (V, E, w)$$
where:
- $V = \{v_0, v_1, \dots, v_n\}$ is the set of vertices.
  - In the **Global Haversine Backbone**, $V$ consists of the $N = 1,255$ registered emergency facilities in the BBMP registry ($v_i \in \{1, \dots, 1255\}$).
  - In a **Scenario Response Subgraph**, $v_0$ designates the incident origin (assigned vertex index $0$), and $v_1, \dots, v_m$ designate the $m$ eligible candidate facilities of the requested emergency agency located within search radius $R_s$.
- $E \subseteq V \times V$ is the set of edges.
- $w: E \to \mathbb{Z}^+$ is an exact integer edge-weight function defined to eliminate floating-point imprecision.

---

## 2. Global Geometric Network (Haversine MST)

### 2.1 Spherical Haversine Metric
For any two coordinates $(\phi_1, \lambda_1)$ and $(\phi_2, \lambda_2)$ expressed in radians:
$$\Delta\phi = \phi_2 - \phi_1, \quad \Delta\lambda = \lambda_2 - \lambda_1$$
$$a = \sin^2\left(\frac{\Delta\phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta\lambda}{2}\right)$$
$$c = 2 \cdot \arcsin\left(\min(1.0, \sqrt{a})\right)$$
$$d_{\text{km}} = R \cdot c$$
where the Earth radius is fixed at the IUGG mean spherical radius:
$$R = 6,371.0088 \text{ km}$$

### 2.2 Exact Integer Weight Formulation
To guarantee numerical stability, total determinism, and identical tree outputs across platforms and architectures, edge weights are mapped from kilometres to integer millimetres using half-up rounding:
$$w(e) = \left\lfloor d_{\text{km}} \times 10^6 + 0.5 \right\rfloor \in \mathbb{Z}^+$$

### 2.3 Strict Tie-Breaking Key
When multiple candidate edges have identical weights, tie-breaking must follow an immutable total order:
$$\operatorname{Key}(e) = \Big(w(e), \; \min(u, v), \; \max(u, v)\Big)$$
Because vertex IDs in the graph are distinct integers or canonical strings, this key induces a strict, unique total ordering over all possible edges in $E$.

### 2.4 Minimum Spanning Tree Invariants
For any connected component with $|V|$ vertices:
1. **Tree Size Invariant:** The spanning tree must contain exactly $|E| = |V| - 1$ edges.
2. **Acyclicity:** The selected edge set contains no cycles.
3. **Weight Parity:** Prim's algorithm and Kruskal's algorithm under strict tie-breaking must produce identical total integer weights:
   $$W(\operatorname{MST}_{\text{Kruskal}}) = W(\operatorname{MST}_{\text{Prim}})$$

### 2.5 Algorithm Implementations
- **Kruskal's Algorithm:**
  - Edges sorted by $\operatorname{Key}(e)$.
  - Disjoint Set Union (DSU) with union-by-rank and path compression.
  - Cycle Property: If $\operatorname{Find}(u) = \operatorname{Find}(v)$, the candidate edge is rejected.
- **Prim's Algorithm:**
  - Min-heap keyed on $(w, \min(u, v), \max(u, v))$.
  - Cut Property: At each step, the minimal crossing edge across the cut $(S, V \setminus S)$ is appended to the growing tree.

---

## 3. Road-Routing Infrastructure (OSRM Engine)

### 3.1 Directed Asymmetry in Real Road Networks
In urban environments like Bengaluru, road travel times and distances are inherently asymmetric due to one-way streets, grade separations, traffic islands, and U-turns:
$$T(i, j) \neq T(j, i), \quad D(i, j) \neq D(j, i)$$
where $T(i, j)$ is the driving duration from $i$ to $j$ and $D(i, j)$ is the driving distance.

### 3.2 Undirected Symmetric Edge Formulation
Graph Theory Minimum Spanning Tree algorithms require undirected edges between endpoints $\{i, j\}$. To reflect the round-trip operational reality of communication lines or response corridors, undirected edge weights are formulated as symmetric sums:
$$S_T(i, j) = T(i, j) + T(j, i) \quad (\text{measured in deciseconds})$$
$$S_D(i, j) = D(i, j) + D(j, i) \quad (\text{measured in decimetres})$$
Averaged single-direction values are reported for human interpretation:
$$T_{\text{avg}}(i, j) = \frac{S_T(i, j)}{1200} \text{ min}, \quad D_{\text{avg}}(i, j) = \frac{S_D(i, j)}{20000} \text{ km}$$

### 3.3 Road Snapping & Exclusion Criteria
Coordinates are projected onto the OpenStreetMap road network. A facility is excluded if:
- Distance to nearest road exceeds $200\text{ m}$ (`UNSNAPPED_ROAD`).
- OSRM reports null duration or unroutable geometry (`NULL_ROUTE`).
- Facility is beyond the search radius $R_s$ (`OUT_OF_RADIUS`).
- Facility belongs to a different agency (`AGENCY_MISMATCH`).

All exclusions are tracked with machine-readable reason codes and audited.

---

## 4. The Three Optimization Modes

The platform supports three mathematically distinct optimization modes.

### Mode 1: Minimum Response Time ($S_T$)
Minimizes total interconnected travel latency across the network:
$$w_T(e) = S_T(i, j) \in \mathbb{Z}^+ \quad (\text{deciseconds})$$

### Mode 2: Minimum Road Distance ($S_D$)
Minimizes physical infrastructure layout length along road centerlines:
$$w_D(e) = S_D(i, j) \in \mathbb{Z}^+ \quad (\text{decimetres})$$

### Mode 3: Compromise Multi-Objective Optimization
Balances the conflicting objectives of time and distance using a scalar parameter $k \in [0, 10]$:
$$w_{\text{comp}}(e) = k \cdot S_T(i, j) \cdot D^* + (10 - k) \cdot S_D(i, j) \cdot T^*$$
where:
- $T^* = \sum_{e \in \text{MST}_{\text{time}}} S_T(e)$ is the reference optimum under Mode 1.
- $D^* = \sum_{e \in \text{MST}_{\text{dist}}} S_D(e)$ is the reference optimum under Mode 2.
- Since $k, S_T, S_D, T^*, D^*$ are all non-negative integers, $w_{\text{comp}}(e) \in \mathbb{Z}^+$, preserving exact integer arithmetic without floating-point distortion.

#### Regret Metrics:
For any compromise tree $\mathcal{T}_k$:
$$R_T(k) = \frac{\sum_{e \in \mathcal{T}_k} S_T(e) - T^*}{T^*} \times 100\%$$
$$R_D(k) = \frac{\sum_{e \in \mathcal{T}_k} S_D(e) - D^*}{D^*} \times 100\%$$

### 4.1 Exclusion of "Minimum Cost" Mode: Proof of Redundancy
Under Karnataka Gazette FD 31 CSL 2024 diesel benchmark, transportation fuel expenditure for an agency fleet with assumed fuel rate $R_a$ (₹/km) is given by:
$$\operatorname{Cost}(i, j) = D(i, j) \times R_a$$
For any single-agency subgraph, $R_a$ is a constant scalar multiplier ($R_a > 0$). Therefore:
$$\operatorname{Cost}(e_1) < \operatorname{Cost}(e_2) \iff R_a \cdot D(e_1) < R_a \cdot D(e_2) \iff D(e_1) < D(e_2)$$
Because Kruskal's and Prim's algorithms depend exclusively on pairwise relative orderings:
$$\operatorname{Key}_{\text{Cost}}(e) \equiv \operatorname{Key}_{\text{Dist}}(e)$$
A separate "Minimum Cost" mode is mathematically identical to Mode 2 (Minimum Road Distance). Presenting it as an independent optimization mode would be academically invalid. Hence, fuel costs are reported as informative dispatch metrics, while graph optimization remains strictly tri-modal.

---

## 5. Independent Dispatch Ranking Engine

The emergency dispatch decision order is computed **independently of the MST backbone**.
For incident origin $I$ and candidate facilities $F \in \text{Eligible}$:
1. Measure direct, one-way road transit from facility to scene: $T(F \to I)$ and $D(F \to I)$.
2. Sort strictly by:
   $$\operatorname{RankKey}(F) = \Big(T(F \to I), \; D(F \to I), \; \text{facility\_id}\Big)$$
3. Compute Assumed Fuel Cost:
   $$\operatorname{Cost}_{\text{INR}} = D(F \to I) \times R_a$$
4. Compute Detour Ratio relative to Euclidean straight-line distance:
   $$\text{Detour} = \frac{D_{\text{road}}(F \to I)}{d_{\text{haversine}}(F, I)}$$

---

## 6. Mathematical Validation Oracle

To rigorously prove tree optimality, the engine incorporates an independent validation suite based on Lowest Common Ancestor (LCA) binary lifting.

### 6.1 Cycle Property Theorem
**Theorem:** For any spanning tree $\mathcal{T}$ of connected graph $G = (V, E)$, $\mathcal{T}$ is a Minimum Spanning Tree if and only if for every non-tree edge (chord) $e = (u, v) \notin \mathcal{T}$:
$$w(e) \ge \max_{e' \in \operatorname{Path}_{\mathcal{T}}(u, v)} w(e')$$

### 6.2 LCA Binary-Lifting Implementation
1. Root tree $\mathcal{T}$ arbitrarily at vertex $0$.
2. Compute depths and binary lifting tables for $2^k$-th ancestors:
   $$\operatorname{up}[v][k] = \operatorname{up}\Big[\operatorname{up}[v][k-1]\Big][k-1]$$
   $$\operatorname{max\_wt}[v][k] = \max\Big(\operatorname{max\_wt}[v][k-1], \; \operatorname{max\_wt}[\operatorname{up}[v][k-1]][k-1]\Big)$$
3. For every chord $(u, v) \notin \mathcal{T}$, determine path maximum in $O(\log V)$ operations:
   $$M = \operatorname{QueryMaxPath}(u, v)$$
4. Assert:
   $$w(u, v) - M \ge 0$$
   Any negative difference indicates a cycle property violation and invalidates the tree.
