"""
Comprehensive Graph Theory & Minimum Spanning Tree Engine
Implements deterministic Prim's and Kruskal's algorithms, integer weight representations,
Disjoint Set Union (DSU) with union-by-rank and path compression, LCA binary-lifting
cycle-property validation, and compromise multi-objective optimization.
"""
import heapq
import math
from typing import Dict, Any, List, Tuple, Optional, Set


def round_half_up(val: float) -> int:
    """Deterministic round half up to nearest integer."""
    return int(math.floor(val + 0.5))


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Spherical Haversine distance in kilometers (R = 6,371.0088 km)."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = phi2 - phi1
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2.0) ** 2
    # Clamp a into [0, 1] to guard against floating-point inaccuracies
    a_clamped = min(1.0, max(0.0, a))
    return 2.0 * 6371.0088 * math.asin(math.sqrt(a_clamped))


def haversine_integer_mm(lat1: float, lon1: float, lat2: float, lon2: float) -> int:
    """Compute Haversine distance as integer millimetres."""
    d_km = haversine_km(lat1, lon1, lat2, lon2)
    return round_half_up(d_km * 1_000_000.0)


def canonical_edge_endpoints(u: Any, v: Any) -> Tuple[Any, Any]:
    """Return endpoints ordered as (min(u, v), max(u, v))."""
    u_str, v_str = str(u), str(v)
    return (u, v) if u_str <= v_str else (v, u)


def make_edge_key(weight: int, u: Any, v: Any) -> Tuple[int, Any, Any]:
    """Strict total edge ordering key: (weight, min(u, v), max(u, v))."""
    c_u, c_v = canonical_edge_endpoints(u, v)
    return (int(weight), str(c_u), str(c_v))


class DisjointSetUnion:
    """Disjoint Set Union with Union by Rank and Path Compression."""
    def __init__(self, elements: List[Any]):
        self.parent = {x: x for x in elements}
        self.rank = {x: 0 for x in elements}
        self.num_components = len(elements)
        self.find_ops = 0
        self.union_ops = 0

    def find(self, x: Any) -> Any:
        self.find_ops += 1
        path = []
        curr = x
        while self.parent[curr] != curr:
            path.append(curr)
            curr = self.parent[curr]
        # Path compression
        for node in path:
            self.parent[node] = curr
        return curr

    def union(self, x: Any, y: Any) -> bool:
        self.union_ops += 1
        root_x = self.find(x)
        root_y = self.find(y)
        if root_x == root_y:
            return False

        if self.rank[root_x] < self.rank[root_y]:
            root_x, root_y = root_y, root_x
        self.parent[root_y] = root_x
        if self.rank[root_x] == self.rank[root_y]:
            self.rank[root_x] += 1
        self.num_components -= 1
        return True

    def connected(self, x: Any, y: Any) -> bool:
        return self.find(x) == self.find(y)

    def get_components(self) -> Dict[Any, List[Any]]:
        groups = {}
        for x in self.parent:
            root = self.find(x)
            groups.setdefault(root, []).append(x)
        return groups


def kruskal_mst(
    vertices: List[Any],
    edges: List[Dict[str, Any]],
    weight_key: str = "weight",
    track_trace: bool = False
) -> Dict[str, Any]:
    """
    Kruskal's Algorithm using manual edge sorting and DSU.
    Accepts vertices and edges with weight attribute.
    Returns MST (or Minimum Spanning Forest if disconnected) and telemetry.
    """
    dsu = DisjointSetUnion(vertices)
    
    # Construct normalized edge list with strict ordering keys
    normalized_edges = []
    for e in edges:
        u, v = e["u"], e["v"]
        w = int(e[weight_key])
        key = make_edge_key(w, u, v)
        normalized_edges.append({
            "key": key,
            "weight": w,
            "u": u,
            "v": v,
            "data": e
        })

    # Sort strictly by (weight, min(u, v), max(u, v))
    normalized_edges.sort(key=lambda item: item["key"])

    mst_edges = []
    total_weight = 0
    trace = [] if track_trace else None

    for rank_idx, edge_item in enumerate(normalized_edges, start=1):
        u, v, w = edge_item["u"], edge_item["v"], edge_item["weight"]
        root_u = dsu.find(u)
        root_v = dsu.find(v)
        
        if root_u != root_v:
            dsu.union(u, v)
            mst_edges.append(edge_item["data"])
            total_weight += w
            if track_trace:
                trace.append({
                    "step": len(mst_edges),
                    "rank": rank_idx,
                    "action": "ACCEPT",
                    "u": u,
                    "v": v,
                    "weight": w,
                    "edge_key": edge_item["key"],
                    "comp_u": str(root_u),
                    "comp_v": str(root_v),
                    "running_total": total_weight,
                    "dsu_components_remaining": dsu.num_components,
                    "dsu_find_ops": dsu.find_ops,
                    "dsu_union_ops": dsu.union_ops,
                    "reason": f"Rank #{rank_idx}: Minimum available link connecting disjoint components ({root_u} ≠ {root_v})."
                })
        else:
            if track_trace:
                trace.append({
                    "rank": rank_idx,
                    "action": "REJECT",
                    "u": u,
                    "v": v,
                    "weight": w,
                    "edge_key": edge_item["key"],
                    "comp": str(root_u),
                    "running_total": total_weight,
                    "dsu_find_ops": dsu.find_ops,
                    "dsu_union_ops": dsu.union_ops,
                    "reason": f"Rank #{rank_idx}: Cycle chord rejected. Endpoints already connected in component {root_u}."
                })

    components = dsu.get_components()
    is_connected = len(components) <= 1
    expected_edges = max(0, len(vertices) - len(components))

    return {
        "algorithm": "kruskal",
        "mst_edges": mst_edges,
        "edges": mst_edges,
        "edge_count": len(mst_edges),
        "expected_edge_count": expected_edges,
        "total_integer_weight": total_weight,
        "is_connected": is_connected,
        "num_components": len(components),
        "components": components,
        "dsu_ops": {"find": dsu.find_ops, "union": dsu.union_ops},
        "trace": trace
    }


def prim_mst(
    vertices: List[Any],
    edges: List[Dict[str, Any]],
    weight_key: str = "weight",
    start_vertex: Optional[Any] = None,
    track_trace: bool = False
) -> Dict[str, Any]:
    """
    Prim's Algorithm using Python heapq with lazy deletion and deterministic tie-breaking.
    If graph is disconnected, runs within the start vertex component (or across all components).
    """
    if not vertices:
        return {
            "algorithm": "prim",
            "mst_edges": [],
            "edge_count": 0,
            "total_integer_weight": 0,
            "is_connected": True,
            "num_components": 0,
            "components": {},
            "trace": [] if track_trace else None
        }

    # Deterministic start vertex selection
    sorted_vertices = sorted(vertices, key=lambda x: str(x))
    start_v = start_vertex if start_vertex in vertices else sorted_vertices[0]

    # Build adjacency list
    adj = {v: [] for v in vertices}
    for e in edges:
        u, v = e["u"], e["v"]
        w = int(e[weight_key])
        adj[u].append((w, u, v, e))
        adj[v].append((w, v, u, e))

    visited: Set[Any] = set()
    mst_edges = []
    total_weight = 0
    trace = [] if track_trace else None
    heap_ops = 0

    # Handle multiple connected components deterministically
    components = {}
    component_idx = 0

    for current_start in sorted_vertices:
        if current_start in visited:
            continue

        component_idx += 1
        comp_members = []
        visited.add(current_start)
        comp_members.append(current_start)

        # Min-heap ordered strictly by (weight, min(u, v), max(u, v), u, v, edge_data)
        min_heap = []

        def push_edges(node):
            nonlocal heap_ops
            for w, s, t, edge_data in adj[node]:
                if t not in visited:
                    c_u, c_v = canonical_edge_endpoints(s, t)
                    heapq.heappush(min_heap, (w, str(c_u), str(c_v), s, t, edge_data))
                    heap_ops += 1

        push_edges(current_start)

        while min_heap:
            w, cu_str, cv_str, s, t, edge_data = heapq.heappop(min_heap)
            heap_ops += 1
            if t in visited:
                continue

            visited.add(t)
            comp_members.append(t)
            mst_edges.append(edge_data)
            total_weight += w

            if track_trace:
                trace.append({
                    "step": len(mst_edges),
                    "action": "ACCEPT",
                    "u": s,
                    "v": t,
                    "weight": w,
                    "edge_key": (w, cu_str, cv_str),
                    "cut_visited_count": len(visited),
                    "heap_size": len(min_heap),
                    "heap_ops": heap_ops,
                    "running_total": total_weight,
                    "reason": f"Step #{len(mst_edges)}: Minimal crossing edge ({w}) from tree cut to unvisited vertex {t}."
                })

            push_edges(t)

        components[f"component_{component_idx}"] = comp_members

    is_connected = len(components) <= 1
    expected_edges = max(0, len(vertices) - len(components))

    return {
        "algorithm": "prim",
        "mst_edges": mst_edges,
        "edges": mst_edges,
        "edge_count": len(mst_edges),
        "expected_edge_count": expected_edges,
        "total_integer_weight": total_weight,
        "is_connected": is_connected,
        "num_components": len(components),
        "components": components,
        "heap_ops": heap_ops,
        "trace": trace
    }


class LCABinaryLiftingOracle:
    """
    Independent LCA Binary Lifting Oracle.
    Preprocesses spanning tree in O(V log V) to answer max-edge queries along
    any tree path in O(log V) time, strictly using (weight, min(u, v), max(u, v)) keys.
    """
    def __init__(self, vertices: List[Any], tree_edges: List[Dict[str, Any]], weight_key: str = "weight"):
        self.vertices = sorted(vertices, key=lambda x: str(x))
        self.n = len(self.vertices)
        self.v_to_idx = {v: i for i, v in enumerate(self.vertices)}
        self.weight_key = weight_key

        self.adj = [[] for _ in range(self.n)]
        for e in tree_edges:
            u_idx = self.v_to_idx.get(e["u"])
            v_idx = self.v_to_idx.get(e["v"])
            if u_idx is not None and v_idx is not None:
                w = int(e[weight_key])
                key = make_edge_key(w, e["u"], e["v"])
                self.adj[u_idx].append((v_idx, key))
                self.adj[v_idx].append((u_idx, key))

        # Max depth
        self.max_log = max(1, math.ceil(math.log2(max(2, self.n))) + 1)
        self.up = [[-1] * self.max_log for _ in range(self.n)]
        self.max_key = [[(-1, "", "")] * self.max_log for _ in range(self.n)]
        self.depth = [-1] * self.n

        # Preprocess each tree component (forest)
        for i in range(self.n):
            if self.depth[i] == -1:
                self._dfs(i, -1, 0, (-1, "", ""))

    def _dfs(self, u: int, p: int, d: int, edge_key_to_p: Tuple[int, Any, Any]):
        self.depth[u] = d
        self.up[u][0] = p
        self.max_key[u][0] = edge_key_to_p

        for j in range(1, self.max_log):
            anc = self.up[u][j - 1]
            if anc != -1:
                self.up[u][j] = self.up[anc][j - 1]
                self.max_key[u][j] = max(self.max_key[u][j - 1], self.max_key[anc][j - 1])
            else:
                self.up[u][j] = -1
                self.max_key[u][j] = self.max_key[u][j - 1]

        for v, k in self.adj[u]:
            if v != p:
                self._dfs(v, u, d + 1, k)

    def query_max_key_on_path(self, u_val: Any, v_val: Any) -> Tuple[bool, Tuple[int, Any, Any]]:
        """Return (path_exists, max_edge_key) on tree path between u and v."""
        u = self.v_to_idx.get(u_val)
        v = self.v_to_idx.get(v_val)
        if u is None or v is None:
            return False, (-1, "", "")

        # Check if in same component
        root_u = u
        for j in range(self.max_log - 1, -1, -1):
            if self.up[root_u][j] != -1:
                root_u = self.up[root_u][j]

        root_v = v
        for j in range(self.max_log - 1, -1, -1):
            if self.up[root_v][j] != -1:
                root_v = self.up[root_v][j]

        if root_u != root_v:
            return False, (-1, "", "")

        if self.depth[u] < self.depth[v]:
            u, v = v, u

        res_key = (-1, "", "")
        diff = self.depth[u] - self.depth[v]
        for j in range(self.max_log):
            if (diff >> j) & 1:
                res_key = max(res_key, self.max_key[u][j])
                u = self.up[u][j]

        if u == v:
            return True, res_key

        for j in range(self.max_log - 1, -1, -1):
            if self.up[u][j] != self.up[v][j]:
                res_key = max(res_key, self.max_key[u][j], self.max_key[v][j])
                u = self.up[u][j]
                v = self.up[v][j]

        res_key = max(res_key, self.max_key[u][0], self.max_key[v][0])
        return True, res_key

    def verify_cycle_property(self, candidate_edges: List[Dict[str, Any]], tree_edges: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Verify cycle property on all non-tree chords."""
        tree_set = {canonical_edge_endpoints(e["u"], e["v"]) for e in tree_edges}
        violations = []
        chords_tested = 0

        for e in candidate_edges:
            pair = canonical_edge_endpoints(e["u"], e["v"])
            if pair in tree_set:
                continue

            chords_tested += 1
            w = int(e[self.weight_key])
            chord_key = make_edge_key(w, e["u"], e["v"])
            has_path, max_tree_key = self.query_max_key_on_path(e["u"], e["v"])

            if has_path:
                # Cycle property requirement: chord_key >= max_tree_key
                if chord_key < max_tree_key:
                    violations.append({
                        "chord": pair,
                        "chord_key": chord_key,
                        "max_tree_key": max_tree_key,
                        "discrepancy": max_tree_key[0] - chord_key[0]
                    })

        max_viol = max((v["discrepancy"] for v in violations), default=0)
        return {
            "chords_tested": chords_tested,
            "violations_count": len(violations),
            "max_violation": max_viol,
            "is_optimal": len(violations) == 0,
            "violations": violations
        }


def validate_mst_structural(vertices: List[Any], tree_edges: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Validate structural tree invariants: coverage, edge count, acyclicity, connectivity."""
    dsu = DisjointSetUnion(vertices)
    has_cycle = False
    
    for e in tree_edges:
        u, v = e["u"], e["v"]
        if not dsu.union(u, v):
            has_cycle = True

    components = dsu.get_components()
    expected_edges = max(0, len(vertices) - len(components))
    is_valid_tree = (not has_cycle) and (len(tree_edges) == expected_edges)

    return {
        "is_valid_tree": is_valid_tree,
        "vertex_count": len(vertices),
        "edge_count": len(tree_edges),
        "expected_edge_count": expected_edges,
        "has_cycle": has_cycle,
        "num_components": len(components),
        "components": components
    }


def compute_compromise_tradeoff_sweep(
    vertices: List[Any],
    candidate_edges: List[Dict[str, Any]],
    time_weight_key: str = "duration_ds",
    dist_weight_key: str = "distance_dm"
) -> Dict[str, Any]:
    """
    Compromise Multi-Objective Optimization Mode.
    1. Computes T* = time-optimal MST total
    2. Computes D* = distance-optimal MST total
    3. For k in 0..10:
       N_e = k * S_T(e) * D* + (10 - k) * S_D(e) * T*
       Runs Kruskal with exact integer arithmetic
       Calculates Regrets: R_T = (T_tree / T*) - 1, R_D = (D_tree / D*) - 1
    """
    # 1. Pure Time MST
    res_time = kruskal_mst(vertices, candidate_edges, weight_key=time_weight_key)
    t_star = res_time["total_integer_weight"]

    # 2. Pure Distance MST
    res_dist = kruskal_mst(vertices, candidate_edges, weight_key=dist_weight_key)
    d_star = res_dist["total_integer_weight"]

    if t_star <= 0 or d_star <= 0:
        return {
            "status": "UNAVAILABLE",
            "reason": f"Reference optimum totals non-positive: T*={t_star}, D*={d_star}",
            "t_star": t_star,
            "d_star": d_star,
            "tradeoff_points": []
        }

    points = []
    # Test if pure objective trees coincide
    time_edge_set = {canonical_edge_endpoints(e["u"], e["v"]) for e in res_time["mst_edges"]}
    dist_edge_set = {canonical_edge_endpoints(e["u"], e["v"]) for e in res_dist["mst_edges"]}
    coincide = (time_edge_set == dist_edge_set)

    for k in range(11):
        lambda_val = k / 10.0
        # Compute exact integer composite weight
        compromise_edges = []
        for e in candidate_edges:
            s_t = int(e[time_weight_key])
            s_d = int(e[dist_weight_key])
            n_e = k * s_t * d_star + (10 - k) * s_d * t_star
            e_copy = dict(e)
            e_copy["compromise_weight"] = n_e
            compromise_edges.append(e_copy)

        res_comp = kruskal_mst(vertices, compromise_edges, weight_key="compromise_weight")
        
        # Calculate actual time and distance sum of this compromise tree
        tree_t = sum(int(e[time_weight_key]) for e in res_comp["mst_edges"])
        tree_d = sum(int(e[dist_weight_key]) for e in res_comp["mst_edges"])

        regret_t_pct = ((tree_t / t_star) - 1.0) * 100.0
        regret_d_pct = ((tree_d / d_star) - 1.0) * 100.0

        points.append({
            "k": k,
            "lambda": lambda_val,
            "tree_time_ds": tree_t,
            "tree_time_min": round(tree_t / 1200.0, 2),
            "tree_dist_dm": tree_d,
            "tree_dist_km": round(tree_d / 20000.0, 2),
            "regret_time_pct": round(max(0.0, regret_t_pct), 2),
            "regret_dist_pct": round(max(0.0, regret_d_pct), 2),
            "edge_count": len(res_comp["mst_edges"]),
            "edges": res_comp["mst_edges"]
        })

    return {
        "status": "COMPUTED",
        "t_star_ds": t_star,
        "t_star_min": round(t_star / 1200.0, 2),
        "d_star_dm": d_star,
        "d_star_km": round(d_star / 20000.0, 2),
        "pure_objectives_coincide": coincide,
        "tradeoff_points": points
    }

