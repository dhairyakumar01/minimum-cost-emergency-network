"""Emergency Incident Simulation Module.

Calculates nearest facilities for an incident, assigns primary and supporting responders,
and reconstructs the unique communication paths across the Minimum Spanning Tree.

Constraints:
- Incident point is NOT added to the facility graph or MST.
- Original MST is immutable.
- Incident-to-facility distances are straight-line Haversine km.
- Inter-facility communication uses only existing MST edges.
"""
from collections import deque
import numpy as np
import pandas as pd

from src.mst_network import haversine_km
from src.transportation_cost import (
    get_road_route,
    calculate_journey_cost,
    calculate_aggregate_expenditure,
    get_sensitivity_expenditures,
)

SCENARIOS = {
    "Medical Emergency": {
        "primary_type": "hospital",
        "supporting_types": ["police_station", "fire_station"],
        "description": "Acute medical emergency requiring primary hospital triage, supported by police corridor clearance and fire rescue.",
    },
    "Fire Emergency": {
        "primary_type": "fire_station",
        "supporting_types": ["hospital", "police_station"],
        "description": "Structure or urban fire requiring primary fire suppression, supported by trauma care and perimeter police control.",
    },
    "Road Accident": {
        "primary_type": "hospital",
        "supporting_types": ["police_station", "fire_station"],
        "description": "Vehicular collision requiring primary trauma care, supported by traffic police and fire extrication rescue.",
    },
    "Public Safety": {
        "primary_type": "police_station",
        "supporting_types": ["hospital", "fire_station"],
        "description": "Law enforcement and public safety incident requiring primary police intervention, supported by emergency medical triage.",
    },
}
# Backward-compatibility and UI aliases
SCENARIOS["Fire"] = SCENARIOS["Fire Emergency"]
SCENARIOS["Police"] = SCENARIOS["Public Safety"]
SCENARIOS["Traffic"] = SCENARIOS["Road Accident"]
SCENARIOS["Road Traffic Accident"] = SCENARIOS["Road Accident"]
SCENARIOS["Structural Fire / HazMat"] = SCENARIOS["Fire Emergency"]
SCENARIOS["Public Safety / Crime"] = SCENARIOS["Public Safety"]


def find_nearest_facilities(incident_lat: float, incident_lon: float, facilities: pd.DataFrame) -> dict:
    """Find the nearest facility of each category (hospital, police_station, fire_station) to the incident.
    
    Returns a dict mapping category to (facility_series, distance_km).
    """
    fac = facilities.copy()
    lats = fac["latitude"].to_numpy(dtype=float)
    lons = fac["longitude"].to_numpy(dtype=float)
    
    # Compute Haversine distance to all facilities
    p1, p2 = np.radians(incident_lat), np.radians(lats)
    dp = p2 - p1
    dl = np.radians(lons - incident_lon)
    a = np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    fac["incident_distance_km"] = 2 * 6371.0088 * np.arcsin(np.minimum(1.0, np.sqrt(a)))
    
    result = {}
    for cat in ["hospital", "police_station", "fire_station"]:
        sub = fac[fac["facility_type"] == cat]
        if sub.empty:
            result[cat] = None
        else:
            nearest_idx = sub["incident_distance_km"].idxmin()
            row = sub.loc[nearest_idx].to_dict()
            result[cat] = {
                "facility": row,
                "distance_km": float(row["incident_distance_km"]),
            }
    return result


def build_mst_adjacency(mst_edges: pd.DataFrame) -> dict:
    """Build an undirected adjacency list from MST edges.
    
    adj[u] = [(v, weight_km), ...]
    """
    adj = {}
    for row in mst_edges.itertuples(index=False):
        u, v, w = str(row.u), str(row.v), float(row.weight_km)
        adj.setdefault(u, []).append((v, w))
        adj.setdefault(v, []).append((u, w))
    return adj


def find_tree_path(adj: dict, start_node: str, end_node: str) -> dict:
    """Find the unique simple path between two nodes in a tree using Breadth-First Search.
    
    Returns dict with 'found', 'nodes', 'edges', 'total_distance_km'.
    """
    start = str(start_node)
    target = str(end_node)
    
    if start == target:
        return {
            "found": True,
            "nodes": [start],
            "edges": [],
            "total_distance_km": 0.0,
            "hop_count": 0,
        }
        
    if start not in adj or target not in adj:
        return {
            "found": False,
            "nodes": [],
            "edges": [],
            "total_distance_km": float("inf"),
            "hop_count": 0,
        }
        
    queue = deque([start])
    parent = {start: None}
    edge_to_parent = {}
    
    while queue:
        curr = queue.popleft()
        if curr == target:
            break
        for neighbor, weight in adj.get(curr, []):
            if neighbor not in parent:
                parent[neighbor] = curr
                edge_to_parent[neighbor] = (curr, neighbor, weight)
                queue.append(neighbor)
                
    if target not in parent:
        return {
            "found": False,
            "nodes": [],
            "edges": [],
            "total_distance_km": float("inf"),
            "hop_count": 0,
        }
        
    # Reconstruct path
    curr = target
    path_nodes = []
    path_edges = []
    total_km = 0.0
    
    while curr is not None:
        path_nodes.append(curr)
        if curr in edge_to_parent:
            edge = edge_to_parent[curr]
            path_edges.append(edge)
            total_km += edge[2]
        curr = parent[curr]
        
    path_nodes.reverse()
    path_edges.reverse()
    
    return {
        "found": True,
        "nodes": path_nodes,
        "edges": path_edges,
        "total_distance_km": float(total_km),
        "hop_count": len(path_edges),
    }


def simulate_emergency_incident(
    incident_type: str,
    incident_lat: float,
    incident_lon: float,
    facilities: pd.DataFrame,
    mst_edges: pd.DataFrame,
) -> dict:
    """Execute end-to-end emergency incident simulation.
    
    1. Identifies nearest facility of each type.
    2. Classifies primary and supporting responders based on scenario.
    3. Reconstructs MST communication paths between responding facilities.
    """
    if incident_type not in SCENARIOS:
        raise ValueError(f"Unknown incident type '{incident_type}'. Valid types: {list(SCENARIOS.keys())}")
        
    scenario = SCENARIOS[incident_type]
    nearest = find_nearest_facilities(incident_lat, incident_lon, facilities)
    
    primary_cat = scenario["primary_type"]
    primary_info = nearest.get(primary_cat)
    if not primary_info:
        raise ValueError(f"No facility found for primary responder category '{primary_cat}'")
        
    supporting_info = []
    for scat in scenario["supporting_types"]:
        s_info = nearest.get(scat)
        if s_info:
            supporting_info.append(s_info)
            
    # Build tree adjacency for path reconstruction
    adj = build_mst_adjacency(mst_edges)
    
    # Reconstruct communication paths from Primary to each Supporting responder
    primary_id = str(primary_info["facility"]["facility_id"])
    paths = []
    total_mst_comms_km = 0.0
    all_connected = True
    
    for supp in supporting_info:
        supp_id = str(supp["facility"]["facility_id"])
        path_res = find_tree_path(adj, primary_id, supp_id)
        if not path_res["found"]:
            all_connected = False
        else:
            total_mst_comms_km += path_res["total_distance_km"]
        paths.append({
            "from_id": primary_id,
            "to_id": supp_id,
            "from_name": primary_info["facility"]["facility_name"],
            "to_name": supp["facility"]["facility_name"],
            "from_type": primary_info["facility"]["facility_type"],
            "to_type": supp["facility"]["facility_type"],
            "path_result": path_res,
        })
        
    # Also compute path between the two supporting responders to verify tri-agency coordination
    inter_support_path = None
    if len(supporting_info) >= 2:
        s1_id = str(supporting_info[0]["facility"]["facility_id"])
        s2_id = str(supporting_info[1]["facility"]["facility_id"])
        inter_support_path = find_tree_path(adj, s1_id, s2_id)
        
    # Calculate physical road transit and research-backed transportation expenditure
    all_responders = [primary_info] + supporting_info
    responder_journeys = []
    max_arrival_min = 0.0
    for resp in all_responders:
        f_lat = float(resp["facility"]["latitude"])
        f_lon = float(resp["facility"]["longitude"])
        cat = resp["facility"]["facility_type"]
        route = get_road_route(f_lat, f_lon, float(incident_lat), float(incident_lon))
        cost_details = calculate_journey_cost(cat, route["road_distance_km"])
        sens = get_sensitivity_expenditures(cat, route["road_distance_km"])
        resp["road_route"] = route
        resp["cost_details"] = cost_details
        resp["sensitivity"] = sens
        responder_journeys.append({
            "category": cat,
            "road_distance_km": route["road_distance_km"],
            "facility_id": resp["facility"]["facility_id"],
            "facility_name": resp["facility"]["facility_name"],
        })
        if route["travel_time_minutes"] > max_arrival_min:
            max_arrival_min = route["travel_time_minutes"]

    aggregate_cost = calculate_aggregate_expenditure(responder_journeys)
    aggregate_cost["scene_secure_minutes"] = max_arrival_min
    aggregate_cost["scene_arrival_time_minutes"] = max_arrival_min

    return {
        "incident_type": incident_type,
        "incident_coordinates": (float(incident_lat), float(incident_lon)),
        "scenario_description": scenario["description"],
        "nearest_facilities": nearest,
        "primary_responder": primary_info,
        "supporting_responders": supporting_info,
        "communication_paths": paths,
        "inter_supporting_path": inter_support_path,
        "total_mst_communication_distance_km": float(total_mst_comms_km),
        "all_connected": all_connected,
        "aggregate_transportation": aggregate_cost,
    }

