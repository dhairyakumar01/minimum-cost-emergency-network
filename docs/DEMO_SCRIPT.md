# Demo Script: four screens, about 8 minutes

Launch: `cd ~/Desktop/minimum_cost_emergency_network && python -m streamlit run app.py`
Use the left sidebar to move between screens. Numbers below are from your recorded runs; read them off the screen as you go.

## Screen 1: Dashboard (1 to 1.5 min)
- Read the problem statement: connect every facility in one network with the smallest total length.
- Point to the counts: 1,255 facilities (1,097 hospitals, 138 police stations, 20 fire stations).
- Point to 1,254 MST edges and about 480.18 km total. Say why: a spanning tree on 1,255 vertices has 1,255 - 1 = 1,254 edges.
- Point to 786,885 candidate edges: 1,255 x 1,254 / 2 possible pairs.
- Read the yellow box: weights are straight-line distances, not cost, road distance or response time.

## Screen 2: Facilities Map (1.5 min)
- Untick two facility types, then re-tick them. Say: filters change only which markers are shown, never the MST.
- Click a marker to show the popup (name, type, ID, coordinates).
- Type a name in the search box, pick a match, show the highlighted marker and the details table.

## Screen 3: MST Network (2 min)
- Select Prim. Show 1,254 edges, total distance, median runtime, 0 unmatched IDs.
- Say: every edge endpoint was matched to a facility by ID, and each stored length was recomputed from the coordinates (see the ID check line under the metrics).
- Select Kruskal. Same totals, different-looking tree. Say: an MST is not unique when edge lengths tie; the total is the same.
- Hover a line to show the two facilities and the distance. Open "Longest 10 connections".

## Screen 4: Comparison and Validation (2 min)
- Show the results table: equal edge counts and equal totals (difference is rounding).
- Show "Edges in both MSTs" and explain it.
- Show the runtime chart. Say: median of repeated runs on one machine, specific to these implementations.
- Open the validation table: eight independent checks, all passing for both algorithms.
- Finish with the Limitations section.

## Likely questions (answers use only this project's results)
1. **Why does an MST have V - 1 edges?** It must connect all V vertices (at least V - 1 edges) and contain no cycle (at most V - 1 edges).
2. **Why do both algorithms give the same total?** Every MST has the same minimum total weight. The trees themselves can differ when edge lengths tie.
3. **Why is Kruskal faster here?** In this implementation and on this machine, Kruskal's median was lower. The likely reason is how the Prim code stores the graph, but that was not profiled, so it is not claimed as a finding.
4. **Is this the real cost of building the network?** No. Weights are Haversine straight-line kilometres.
5. **Does the MST give the fastest route for an ambulance?** No. It gives no shortest paths, no redundancy and no fault tolerance.
6. **How do you know the output is a valid MST?** Eight independent checks on each output (edge count, valid IDs, no self-loops or duplicate edges, finite non-negative weights, acyclic, connected and spanning, weights match recomputed Haversine), plus automated tests including a brute-force comparison on small graphs.
7. **What is the Haversine formula for?** Great-circle distance between two latitude/longitude points on a sphere of radius 6,371.0088 km.
8. **Where does the data come from?** OpenStreetMap-derived GeoJSON exports. Accuracy and completeness are not independently verified.
9. **Are there duplicate facilities?** Some facility pairs are very close together (see the data-quality numbers on Screen 4). The data cannot show whether they are duplicates, so nothing was removed.
10. **What would you improve next?** Road-network distances, a deduplication sensitivity run, and resilience (extra links so one failure does not disconnect the network).
