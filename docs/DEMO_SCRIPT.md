# Demo Script: Six Screens, About 10 Minutes

Launch application:
```powershell
cd "c:\Users\DHAIRYA\Downloads\minimum_cost_emergency_network\minimum_cost_emergency_network"
python -m streamlit run app.py --server.headless true --server.port 8501
```
Use the left sidebar navigation to move between screens. All metrics displayed are dynamically calculated from actual project data.

---

## Screen 1: Dashboard (1.5 min)
- **Problem Formulation:** Connect 1,255 public safety facilities across Bengaluru into a single unified network with minimal straight-line link distance.
- **Facility Distribution:** Point to the counts: 1,255 facilities (1,097 hospitals/clinics, 138 police stations, 20 fire stations).
- **Network Properties:** 1,254 MST edges ($V - 1$), total network distance of approximately 480.1784 km, and 786,885 candidate complete graph links ($V(V-1)/2$).
- **Algorithm Performance Row:** Point to Prim execution time, Kruskal execution time, connectivity status (Connected, 1 component), and Validation status (Passed).
- **Modeling Caveat:** Reiterate that edge weights represent straight-line Haversine distances, not monetary construction costs or driving times.

---

## Screen 2: Facilities Map (1.5 min)
- **Categorical Filtering:** Toggle facility category checkboxes in the sidebar; explain that filtering changes marker visibility on the map only, never modifying the underlying graph or MST.
- **Marker Inspection:** Click any marker to view the attribute popup (Name, Category, ID, Latitude, Longitude).
- **Full-Text Fuzzy Search:** Type a query (e.g. "Victoria" or "Bowring"), select the record from the dropdown, show the highlighted marker on the map and the details table.
- **OSM Provenance Link:** Click the external link button to view the live source entity on OpenStreetMap.

---

## Screen 3: MST Network Visualization (1.5 min)
- **Algorithm Comparison:** Switch between Prim and Kruskal radio options. Show that both trees have identical edge counts (1,254) and total distance (480.1784 km).
- **Deterministic Tie-Breaking:** Point out that because alphanumeric facility IDs govern secondary tie-breaking, both algorithms converge on the exact same 1,254 edges.
- **Link Inspection:** Hover over any transmission line to view the endpoints and distance.
- **Longest Links Drawer:** Expand the "Longest 10 connections" table to show the wide geographic spans across peripheral zones (e.g., the 7.826 km link in rural north).
- **Data Export:** Click the download button to export the active MST edge list as CSV.

---

## Screen 4: Emergency Incident Simulation (2 min)
- **Simulation Concept:** Emphasize that this is an interactive geographical response simulation: the incident is evaluated externally and does not mutate the original facility graph or MST.
- **Scenario Selection:** Choose an incident type:
  - *Fire:* Primary = nearest Fire Station; Supporting = nearest Hospital, nearest Police Station.
  - *Medical Emergency:* Primary = nearest Hospital; Supporting = nearest Police Station, nearest Fire Station.
  - *Road Accident:* Primary = nearest Hospital; Supporting = nearest Police Station, nearest Fire Station.
- **Interactive Map Selection:** Click anywhere on the map or enter manual coordinates to place the incident.
- **Simulation Execution:** Click "Run Incident Simulation".
- **Inspection of Outputs:**
  - Point to the Primary Responder card (Name, Category, straight-line distance).
  - Point to the Supporting Responder cards.
  - Point to the MST Communication Paths table: shows exact tree hop counts and communication distance across the MST.
  - Show the simulation map: red pin for incident, green circle for primary responder, colored circles for supporting responders, dashed lines for dispatch spans, and thick colored lines for active MST communication paths.

---

## Screen 5: Algorithm Comparison & Validation (1.5 min)
- **Results Table:** Review the side-by-side comparison table showing identical edge counts, total distance, and validation results.
- **Runtime Comparison:** Point to the execution runtime chart with standard deviation error bars. Explain why Kruskal is faster on this dataset (vectorized C mergesort and early loop termination).
- **Distance Discrepancy:** Note the numerical gap ($5.68 \times 10^{-14}\text{ km}$), purely attributable to IEEE 754 floating-point summation ordering.
- **Validation Audit Table:** Review the 8 independent structural checks (edge count, valid IDs, no self-loops, finite positive weights, no duplicate edges, acyclicity, connectivity, and Haversine distance accuracy).
- **Data Quality Summary:** Review the 24 unnamed facilities and 142 near-proximity facility pairs ($\le 50\text{ m}$).

---

## Screen 6: Experimental Laboratory (2 min)
- **Tab 1: Scalability Experiment:**
  - Explain the methodology: evaluates subgraphs across 8 reproducible subset sizes ($N = 50, 100, 200, 400, 600, 800, 1000, 1255$) using deterministic sampling (`seed=42`).
  - Show that both Prim and Kruskal receive identical vertex sets and candidate edges for each subset.
  - Review the Plotly scaling curves:
    - *Execution Time vs. Vertices ($N$):* Shows empirical polynomial growth.
    - *Execution Time vs. Candidate Edges ($E$):* Demonstrates scaling across 1,225 to 786,885 edges.
    - *Total MST Distance vs. $N$:* Illustrates network distance expansion as facilities increase.
  - Point to the trial telemetry table and download buttons (CSV/JSON).
- **Tab 2: Controlled Graph-Density Experiment (Approach C):**
  - Explain the methodology: evaluates non-tree edge sparsification across 7 density levels ($\rho \in [0.0, 1.0]$) and 3 independent seeds on the 786,885-edge candidate graph.
  - Highlight that all 1,254 verified optimal MST edges are retained at every density level, guaranteeing connectivity and holding optimal tree distance constant at 480.1784 km.
  - Review the Plotly density curves:
    - *Execution Time vs. Density ($\rho$):* Shows Kruskal outperforming Prim once non-tree edges are introduced.
    - *Execution Time vs. Total Candidate Edges ($|E|$):* Illustrates scaling from 1,254 edges to 786,885 edges.
    - *Algorithmic Speedup Ratio vs. $\rho$:* Highlights the crossover point at $\rho = 0.0$ and asymptotic stability around ~3.1×.
  - Point to the timing methodology (single timed execution per seed graph, medians across 3 sampled graphs), standard deviation interpretation, the raw trial records expander, and CSV/JSON downloads.

---

## Likely Questions and Technical Answers
1. **Why does an MST have exactly $V - 1$ edges?**  
   Any connected graph on $V$ vertices has at least $V - 1$ edges, and any acyclic graph has at most $V - 1$ edges. A spanning tree is both connected and acyclic, forcing $|E| = V - 1$.
2. **Why do Prim and Kruskal produce identical edge sets here?**  
   When edge weights are unique, the MST is mathematically unique. When ties occur, deterministic secondary sorting on facility IDs forces both algorithms to make identical greedy choices.
3. **Why did earlier benchmarks report ~5s (Prim) and ~1.6s (Kruskal), while the scalability experiment on Windows reported ~20.9s and ~6.6s?**  
   The historical benchmark was executed on macOS Apple Silicon (ARM64) with high unified memory bandwidth running Python 3.14.7. The scalability experiment ran on an x86_64 Windows 11 machine running Python 3.11.3. The relative ratio of Prim to Kruskal remains invariant ($3.18\times$ vs $3.14\times$).
4. **Is this network fault-tolerant?**  
   No. A tree by definition contains zero cycles; every single edge is a bridge. Severing any edge partitions the network into two disconnected components.
5. **How is the emergency simulation connected to the MST?**  
   The incident location is evaluated externally via straight-line Haversine distance to find the nearest responders. Inter-facility communication between the responding facilities then travels strictly across the existing 1,254 MST edges via unique tree paths reconstructed through BFS.
