"""Interactive Local Comparison Graph and Side-by-Side Prim vs Kruskal Evaluation.

Constructs an explicitly identified temporary comparison graph for an emergency incident:
- Temporary incident vertex (placed as root at index 0).
- Nearby emergency facilities selected via configurable geographic radius.
- Guaranteed inclusion of nearest hospital, police station, and fire station.
- Identical complete edge generation via Haversine distance.
- Independent execution of manual Prim and manual Kruskal algorithms.
- Validation, timing, and cycle-rejection tracking.
"""
import time
import math
from typing import Dict, Any, Tuple
import pandas as pd
import numpy as np

from src.mst_network import haversine_km, build_complete_edges, prim_mst, kruskal_mst


def build_local_comparison_graph(
    incident_lat: float,
    incident_lon: float,
    fac_df: pd.DataFrame,
    radius_km: float = 5.0,
    max_facilities: int = 30,
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """Construct an explicitly identified temporary comparison graph for the selected incident.
    
    Returns:
        local_nodes: DataFrame with Incident at index 0 followed by nearby facilities.
        candidate_edges: Complete graph edges between all local nodes.
        meta: Metadata dictionary describing selection rules and counts.
    """
    df = fac_df.copy()
    
    # Calculate distance from incident to every facility in dataset
    lats = df["latitude"].to_numpy(dtype=float)
    lons = df["longitude"].to_numpy(dtype=float)
    
    dlat = np.radians(lats - incident_lat)
    dlon = np.radians(lons - incident_lon)
    a = np.sin(dlat / 2.0) ** 2 + np.cos(np.radians(incident_lat)) * np.cos(np.radians(lats)) * np.sin(dlon / 2.0) ** 2
    c = 2.0 * np.arcsin(np.sqrt(np.clip(a, 0.0, 1.0)))
    df["dist_to_incident_km"] = 6371.0088 * c
    
    # 1. Nearby facilities within radius
    within_radius = df[df["dist_to_incident_km"] <= radius_km].sort_values("dist_to_incident_km")
    
    # 2. Ensure multi-agency representation (guarantee at least nearest hospital, police station, and fire station)
    nearest_hosp = df[df["facility_type"] == "hospital"].sort_values("dist_to_incident_km").head(3)
    nearest_pol = df[df["facility_type"] == "police_station"].sort_values("dist_to_incident_km").head(2)
    nearest_fire = df[df["facility_type"] == "fire_station"].sort_values("dist_to_incident_km").head(2)
    
    # Strictly mandatory units for multi-agency representation
    mandatory = pd.concat([nearest_hosp.head(1), nearest_pol.head(1), nearest_fire.head(1)]).drop_duplicates(subset=["facility_id"])
    mandatory_ids = set(mandatory["facility_id"])

    combined = pd.concat([within_radius, nearest_hosp, nearest_pol, nearest_fire]).drop_duplicates(subset=["facility_id"])
    
    # Cap total facilities if radius is very dense to maintain instant visual clarity, while preserving mandatory multi-agency units
    if len(combined) > max_facilities:
        remaining_budget = max(0, max_facilities - len(mandatory))
        others = combined[~combined["facility_id"].isin(mandatory_ids)].sort_values("dist_to_incident_km").head(remaining_budget)
        combined = pd.concat([mandatory, others])
        
    selected_facs = combined.sort_values("dist_to_incident_km").reset_index(drop=True)
    
    # 3. Create temporary incident vertex at index 0 (Root for Prim's algorithm)
    incident_vertex = pd.DataFrame([{
        "facility_id": "INCIDENT_LOCATION",
        "facility_name": "Emergency Incident Location",
        "facility_type": "incident",
        "latitude": float(incident_lat),
        "longitude": float(incident_lon),
        "dist_to_incident_km": 0.0,
    }])
    
    local_nodes = pd.concat([incident_vertex, selected_facs], ignore_index=True)
    
    # 4. Generate identical complete candidate graph edges
    candidate_edges = build_complete_edges(local_nodes)
    
    meta = {
        "radius_km": radius_km,
        "selection_rule": f"Facilities within {radius_km:.1f} km radius (with guaranteed nearest hospital, police, and fire station included)",
        "incident_coordinates": (incident_lat, incident_lon),
        "total_vertices": len(local_nodes),
        "facility_vertices": len(selected_facs),
        "hospitals_count": int((selected_facs["facility_type"] == "hospital").sum()),
        "police_count": int((selected_facs["facility_type"] == "police_station").sum()),
        "fire_count": int((selected_facs["facility_type"] == "fire_station").sum()),
        "candidate_edges_count": len(candidate_edges),
    }
    
    return local_nodes, candidate_edges, meta


def run_local_mst_comparison(
    local_nodes: pd.DataFrame,
    candidate_edges: pd.DataFrame,
) -> Dict[str, Any]:
    """Execute manual Prim and manual Kruskal on the exact same temporary comparison graph.
    
    Prim starts from the temporary incident location (index 0).
    Measures timing with high-precision perf_counter.
    Tracks rejected cycle-forming edges in Kruskal.
    """
    v_count = len(local_nodes)
    target_edges = v_count - 1
    
    # Execute Prim's algorithm with decision tracking (starts from local_nodes.facility_id[0] = 'INCIDENT_LOCATION')
    t0 = time.perf_counter()
    prim_tree, prim_weight, prim_decisions = prim_mst(local_nodes, candidate_edges, track_decisions=True)
    prim_time_sec = time.perf_counter() - t0
    
    # Execute Kruskal's algorithm on the exact same candidate edge list with decision tracking
    t0 = time.perf_counter()
    kruskal_tree, kruskal_weight, kruskal_decisions = kruskal_mst(local_nodes, candidate_edges, track_decisions=True)
    kruskal_time_sec = time.perf_counter() - t0
    
    # Identify rejected cycle-forming edges in Kruskal
    rejected_edges = kruskal_decisions.get("rejected", [])
    if not rejected_edges:
        # Fallback if no decisions recorded
        kruskal_edge_keys = set()
        for r in kruskal_tree.itertuples():
            kruskal_edge_keys.add((min(str(r.u), str(r.v)), max(str(r.u), str(r.v))))
        for r in candidate_edges.itertuples():
            k = (min(str(r.u), str(r.v)), max(str(r.u), str(r.v)))
            if k not in kruskal_edge_keys:
                rejected_edges.append({
                    "u": r.u,
                    "v": r.v,
                    "u_name": r.u_name,
                    "v_name": r.v_name,
                    "weight_km": float(r.weight_km),
                    "reason": f"Rejected: Adding edge would close a cycle in Kruskal's spanning forest.",
                })
    rejected_df = pd.DataFrame(rejected_edges)
    
    # Check topological edge set equality
    prim_edge_keys = set()
    for r in prim_tree.itertuples():
        prim_edge_keys.add((min(str(r.u), str(r.v)), max(str(r.u), str(r.v))))
        
    kruskal_edge_keys = set()
    for r in kruskal_tree.itertuples():
        kruskal_edge_keys.add((min(str(r.u), str(r.v)), max(str(r.u), str(r.v))))
        
    edge_sets_identical = (prim_edge_keys == kruskal_edge_keys)
    differing_edges_count = len(prim_edge_keys.symmetric_difference(kruskal_edge_keys))
    
    # Independent validation
    prim_valid = (len(prim_tree) == target_edges and prim_weight > 0.0)
    kruskal_valid = (len(kruskal_tree) == target_edges and kruskal_weight > 0.0)
    weight_agree = math.isclose(prim_weight, kruskal_weight, rel_tol=1e-7, abs_tol=1e-5)
    
    return {
        "v_count": v_count,
        "target_edges": target_edges,
        "candidate_edges_count": len(candidate_edges),
        "prim": {
            "tree": prim_tree,
            "total_weight_km": prim_weight,
            "execution_time_sec": prim_time_sec,
            "execution_time_ms": prim_time_sec * 1000.0,
            "is_valid": prim_valid,
            "root_vertex": str(local_nodes.iloc[0]["facility_name"]),
            "decisions": prim_decisions,
        },
        "kruskal": {
            "tree": kruskal_tree,
            "total_weight_km": kruskal_weight,
            "execution_time_sec": kruskal_time_sec,
            "execution_time_ms": kruskal_time_sec * 1000.0,
            "is_valid": kruskal_valid,
            "rejected_edges_df": rejected_df,
            "rejected_count": len(rejected_df),
            "accepted_decisions": kruskal_decisions.get("accepted", []),
            "rejected_decisions": kruskal_decisions.get("rejected", []),
        },
        "comparison": {
            "edge_sets_identical": edge_sets_identical,
            "differing_edges_count": differing_edges_count,
            "weight_difference_km": abs(prim_weight - kruskal_weight),
            "weights_agree": weight_agree,
            "faster_algorithm": "Prim" if prim_time_sec < kruskal_time_sec else "Kruskal",
            "speedup_ratio": max(prim_time_sec, kruskal_time_sec) / max(1e-9, min(prim_time_sec, kruskal_time_sec)),
        },
    }
