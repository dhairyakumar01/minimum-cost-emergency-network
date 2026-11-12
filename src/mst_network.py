"""MST algorithms for facility locations; edge weights are Haversine km."""
import math, heapq
from itertools import combinations
import pandas as pd
EARTH_KM = 6371.0088
REQUIRED = {'facility_id','facility_name','facility_type','latitude','longitude'}

def haversine_km(lat1, lon1, lat2, lon2):
    p1,p2=math.radians(lat1),math.radians(lat2)
    dp=math.radians(lat2-lat1); dl=math.radians(lon2-lon1)
    a=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*EARTH_KM*math.asin(min(1,math.sqrt(a)))

def load_facilities(path):
    df=pd.read_csv(path)
    missing=REQUIRED-set(df.columns)
    if missing: raise ValueError(f'Missing columns: {sorted(missing)}')
    for c in ['latitude','longitude']: df[c]=pd.to_numeric(df[c],errors='coerce')
    if df[['latitude','longitude']].isna().any().any(): raise ValueError('Missing or invalid coordinates; review data first.')
    if (~df.latitude.between(-90,90)).any() or (~df.longitude.between(-180,180)).any(): raise ValueError('Out-of-range coordinates found.')
    if df.facility_id.duplicated().any(): raise ValueError('Duplicate facility IDs found.')
    return df.reset_index(drop=True)

def build_complete_edges(nodes):
    rows=[]; r=nodes.to_dict('records')
    for i,j in combinations(range(len(r)),2):
        a,b=r[i],r[j]
        rows.append({'u':a['facility_id'],'v':b['facility_id'],'u_name':a['facility_name'],'v_name':b['facility_name'],'u_type':a['facility_type'],'v_type':b['facility_type'],'weight_km':haversine_km(a['latitude'],a['longitude'],b['latitude'],b['longitude'])})
    return pd.DataFrame(rows,columns=['u','v','u_name','v_name','u_type','v_type','weight_km'])

from collections import deque


def find_tree_path(adj, start, target):
    """Find unique path between start and target in a tree adjacency dict.
    
    Returns (path_nodes, max_edge_weight, list_of_path_edges) or (None, 0.0, []).
    """
    if start == target:
        return [start], 0.0, []
    queue = deque([[start]])
    visited = {start}
    while queue:
        path = queue.popleft()
        curr = path[-1]
        if curr == target:
            max_w = 0.0
            edges_on_path = []
            for i in range(len(path) - 1):
                a, b = path[i], path[i + 1]
                for nbr, w, *_ in adj.get(a, []):
                    if nbr == b:
                        edges_on_path.append((a, b, w))
                        max_w = max(max_w, w)
                        break
            return path, max_w, edges_on_path
        for nbr, w, *_ in adj.get(curr, []):
            if nbr not in visited:
                visited.add(nbr)
                queue.append(path + [nbr])
    return None, 0.0, []


def prim_mst(nodes, edges, track_decisions=False):
    ids = nodes.facility_id.tolist()
    if not ids:
        return (pd.DataFrame(), 0.0, []) if track_decisions else (pd.DataFrame(), 0.0)
    adj = {x: [] for x in ids}
    for e in edges.itertuples(index=False):
        adj[e.u].append((e.weight_km, e.u, e.v, e.u_name, e.v_name, e.u_type, e.v_type))
        adj[e.v].append((e.weight_km, e.v, e.u, e.v_name, e.u_name, e.v_type, e.u_type))
    visited = {ids[0]}
    heap = []
    chosen = []
    decisions = []

    def push(node):
        for w, s, t, sn, tn, st, tt in adj[node]:
            if t not in visited:
                heapq.heappush(heap, (w, str(s), str(t), s, t, sn, tn, st, tt))

    push(ids[0])
    while heap and len(visited) < len(ids):
        w, _, __, s, t, sn, tn, st, tt = heapq.heappop(heap)
        if t in visited:
            continue
        iter_num = len(chosen) + 1
        cut_visited = len(visited)
        if track_decisions:
            decisions.append({
                "iteration": iter_num,
                "u": s, "v": t,
                "u_name": sn, "v_name": tn,
                "u_type": st, "v_type": tt,
                "weight_km": float(w),
                "cut_visited": cut_visited,
                "cut_unvisited": len(ids) - cut_visited,
                "heap_candidates_count": len(heap) + 1,
                "reason": (
                    f"Iteration #{iter_num}: Minimum-weight eligible link ({w:.4f} km) crossing "
                    f"the tree boundary ({cut_visited} spanned, {len(ids) - cut_visited} unvisited)."
                ),
            })
        visited.add(t)
        chosen.append((s, t, sn, tn, st, tt, w))
        push(t)

    if len(visited) != len(ids):
        raise ValueError("Graph is disconnected.")
    out = pd.DataFrame(chosen, columns=["u", "v", "u_name", "v_name", "u_type", "v_type", "weight_km"])
    if track_decisions:
        return out, float(out.weight_km.sum()), decisions
    return out, float(out.weight_km.sum())


def kruskal_mst(nodes, edges, track_decisions=False):
    parent = {x: x for x in nodes.facility_id}
    rank = {x: 0 for x in parent}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra == rb:
            return False, ra, rb
        if rank[ra] < rank[rb]:
            ra, rb = rb, ra
        parent[rb] = ra
        if rank[ra] == rank[rb]:
            rank[ra] += 1
        return True, ra, rb

    chosen = []
    target = max(0, len(nodes) - 1)
    accepted_decisions = []
    rejected_decisions = []
    tree_adj = {x: [] for x in nodes.facility_id}

    sorted_edges = edges.sort_values(["weight_km", "u", "v"], kind="mergesort")
    for rank_idx, e in enumerate(sorted_edges.itertuples(index=False), 1):
        merged, ca, cb = union(e.u, e.v)
        if merged:
            chosen.append((e.u, e.v, e.u_name, e.v_name, e.u_type, e.v_type, e.weight_km))
            tree_adj[e.u].append((e.v, e.weight_km, e.v_name))
            tree_adj[e.v].append((e.u, e.weight_km, e.u_name))
            if track_decisions:
                accepted_decisions.append({
                    "rank": rank_idx,
                    "step": len(chosen),
                    "u": e.u, "v": e.v,
                    "u_name": e.u_name, "v_name": e.v_name,
                    "weight_km": float(e.weight_km),
                    "comp_u": ca, "comp_v": cb,
                    "reason": (
                        f"Rank #{rank_idx}: Accepted ({float(e.weight_km):.4f} km). "
                        f"Endpoints in separate components ({ca} ≠ {cb}). Merged components."
                    ),
                })
            if len(chosen) == target and not track_decisions:
                break
        else:
            if track_decisions:
                path, max_w, _ = find_tree_path(tree_adj, e.u, e.v)
                rejected_decisions.append({
                    "rank": rank_idx,
                    "u": e.u, "v": e.v,
                    "u_name": e.u_name, "v_name": e.v_name,
                    "weight_km": float(e.weight_km),
                    "comp": ca,
                    "cycle_path": path,
                    "path_max_w": max_w,
                    "reason": (
                        f"Rank #{rank_idx}: Rejected ({float(e.weight_km):.4f} km). "
                        f"Endpoints already connected in component {ca}. "
                        f"Adding link forms cycle with path of length {len(path) - 1 if path else 0} "
                        f"(max link on path: {max_w:.4f} km ≤ {float(e.weight_km):.4f} km)."
                    ),
                })

    if len(chosen) != target:
        raise ValueError("Could not construct spanning tree.")
    out = pd.DataFrame(chosen, columns=["u", "v", "u_name", "v_name", "u_type", "v_type", "weight_km"])
    if track_decisions:
        return out, float(out.weight_km.sum()), {"accepted": accepted_decisions, "rejected": rejected_decisions}
    return out, float(out.weight_km.sum())
