import sys
import os
import sqlite3
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.services.scenario_service import DB_PATH

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute("SELECT scenario_id, incident_lat, incident_lon, agency, radius_km, result_json FROM scenarios WHERE agency='police' ORDER BY created_at DESC LIMIT 3")
for row in cur.fetchall():
    res = json.loads(row[5])
    summ = res.get("summary", {})
    net = res.get("network_mst", {})
    print("=" * 60)
    print(f"Scenario ID: {row[0]}")
    print(f"Agency: {row[3]}, Coordinates: ({row[1]}, {row[2]}), Radius: {row[4]} km")
    print(f"Candidates (Facilities): {summ.get('total_candidates_in_radius')}")
    print(f"Graph Vertices |V|: {summ.get('graph_vertices_count')}")
    print(f"Tree Edges |E|: {summ.get('tree_edge_count')}")
    print(f"Components C: {summ.get('num_components')}")
    print(f"Road Geometries: {net.get('road_geometries_count')}")
    print(f"Cayley Invariant: |E| == |V| - C -> {summ.get('tree_edge_count')} == {summ.get('graph_vertices_count')} - {summ.get('num_components')} -> {summ.get('tree_edge_count') == summ.get('graph_vertices_count') - summ.get('num_components')}")
    
    # Detail vertex list and edges
    edges = net.get("edges", [])
    print(f"Sample First 5 Edges:")
    for e in edges[:5]:
        print(f"  {e['u']} <--> {e['v']} | S_T: {e.get('duration_ds')} ds, S_D: {e.get('distance_dm')} dm, Road Route: {e.get('is_road_route')}")
    
    incident_links = [e for e in edges if e["u"] == "incident_0" or e["v"] == "incident_0"]
    print(f"Incident origin links in MST: {len(incident_links)}")
    for e in incident_links:
        print(f"  Incident linked to: {e['v'] if e['u'] == 'incident_0' else e['u']}")

conn.close()
