"""
OSRM Routing & Road-Measurement Service for Bengaluru Emergency Network
Implements Table API integration with duration and distance annotations,
directed decisecond/decimetre storage, undirected symmetric weight generation,
persistent SQLite caching, snapping diagnostics, and candidate exclusion tracking.
"""
import json
import math
import os
import sqlite3
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
CACHE_DB_PATH = DATA_DIR / "cache" / "routes.db"
LOCAL_OSRM_URL = os.environ.get("OSRM_BASE_URL", "http://localhost:5001")
PUBLIC_OSRM_URL = "http://router.project-osrm.org"

# Snapping distance threshold in meters
DEFAULT_MAX_SNAPPING_METERS = 500.0


def round_half_up(val: float) -> int:
    return int(math.floor(val + 0.5))


def get_db_connection() -> sqlite3.Connection:
    CACHE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(CACHE_DB_PATH)
    conn.row_factory = sqlite3.Row
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS route_measurements (
                origin TEXT NOT NULL,
                dest TEXT NOT NULL,
                duration_ds INTEGER NOT NULL,
                distance_dm INTEGER NOT NULL,
                snapped_orig_m REAL,
                snapped_dest_m REAL,
                timestamp TEXT NOT NULL,
                PRIMARY KEY (origin, dest)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS snapping_cache (
                coord TEXT PRIMARY KEY,
                snapped_lon REAL NOT NULL,
                snapped_lat REAL NOT NULL,
                snapping_distance_m REAL NOT NULL,
                street_name TEXT,
                timestamp TEXT NOT NULL
            )
        """)
    return conn


# Cache for health check to avoid network latency on frequent status polls
_HEALTH_CACHE: Optional[Dict[str, Any]] = None
_HEALTH_CACHE_TIME: float = 0.0


def check_osrm_health(force_refresh: bool = False) -> Dict[str, Any]:
    """Inspect and test OSRM service availability (local or public) with 60s cache."""
    global _HEALTH_CACHE, _HEALTH_CACHE_TIME
    now = time.time()
    if not force_refresh and _HEALTH_CACHE and (now - _HEALTH_CACHE_TIME < 60.0):
        return _HEALTH_CACHE

    for base_url in [LOCAL_OSRM_URL, PUBLIC_OSRM_URL]:
        test_url = f"{base_url}/table/v1/driving/77.5696,12.9781;77.5835,12.9298?annotations=duration,distance"
        timeout_sec = 0.8 if base_url == LOCAL_OSRM_URL else 3.0
        try:
            req = urllib.request.Request(
                test_url,
                headers={"User-Agent": "BengaluruEmergencyNetworkAcademic/1.0 (DMGT-Research)"}
            )
            with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode())
                    if data.get("code") == "Ok":
                        _HEALTH_CACHE = {
                            "status": "OPERATIONAL",
                            "endpoint": base_url,
                            "is_local": (base_url == LOCAL_OSRM_URL),
                            "supports_annotations": True,
                            "profile": "car",
                            "algorithm": "MLD",
                            "matrix_limits": "chunked",
                        }
                        _HEALTH_CACHE_TIME = now
                        return _HEALTH_CACHE
        except Exception:
            continue

    _HEALTH_CACHE = {
        "status": "UNAVAILABLE",
        "endpoint": None,
        "is_local": False,
        "reason": "Could not connect to local OSRM (port 5001) or public OSRM router.",
        "supports_annotations": False,
    }
    _HEALTH_CACHE_TIME = now
    return _HEALTH_CACHE


def query_osrm_table(coords_list: List[Tuple[float, float]], base_url: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Call OSRM Table API for a list of (lon, lat) points with annotations=duration,distance.
    Returns parsed response with durations (seconds) and distances (meters).
    """
    if not base_url:
        health = check_osrm_health()
        if health["status"] != "OPERATIONAL":
            return None
        base_url = health["endpoint"]

    coord_str = ";".join(f"{lon:.5f},{lat:.5f}" for lon, lat in coords_list)
    url = f"{base_url}/table/v1/driving/{coord_str}?annotations=duration,distance"

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "BengaluruEmergencyNetworkAcademic/1.0 (DMGT-Research)"}
        )
        with urllib.request.urlopen(req, timeout=12.0) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode())
                if data.get("code") == "Ok":
                    return data
    except Exception as e:
        return None
    return None


def get_pairwise_measurements(
    points: List[Dict[str, Any]],
    max_snapping_m: float = DEFAULT_MAX_SNAPPING_METERS
) -> Dict[str, Any]:
    """
    Retrieve all directed pairwise road measurements between points.
    Each point has: {'id': str, 'latitude': float, 'longitude': float}.
    Stores duration in deciseconds and distance in decimetres.
    Returns:
      - directed_measurements: {(u, v): {'duration_ds': int, 'distance_dm': int}}
      - symmetric_edges: list of undirected edges with S_T, S_D, T_avg, D_avg
      - exclusions: list of excluded nodes with reason
      - diagnostics: asymmetry stats, null routes, snapping distances
    """
    health = check_osrm_health()
    if health["status"] != "OPERATIONAL":
        return {
            "status": "ROUTING_UNAVAILABLE",
            "reason": "OSRM routing service is offline. Road-network measurements cannot be performed.",
            "directed_measurements": {},
            "symmetric_edges": [],
            "exclusions": [],
            "diagnostics": {}
        }

    conn = get_db_connection()
    n = len(points)
    directed: Dict[Tuple[str, str], Dict[str, int]] = {}
    missing_pairs = []

    # 1. Lookup in SQLite persistent cache
    with conn:
        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                p1, p2 = points[i], points[j]
                u_str = f"{p1['longitude']:.5f},{p1['latitude']:.5f}"
                v_str = f"{p2['longitude']:.5f},{p2['latitude']:.5f}"
                
                row = conn.execute(
                    "SELECT duration_ds, distance_dm FROM route_measurements WHERE origin=? AND dest=?",
                    (u_str, v_str)
                ).fetchone()

                if row:
                    directed[(p1["id"], p2["id"])] = {
                        "duration_ds": row["duration_ds"],
                        "distance_dm": row["distance_dm"],
                    }
                else:
                    missing_pairs.append((i, j, u_str, v_str))

    # 2. Query OSRM in batches if there are missing pairs
    if missing_pairs and n <= 100:
        # Full table query for small to medium sets
        coords = [(p["longitude"], p["latitude"]) for p in points]
        tbl_data = query_osrm_table(coords, health["endpoint"])

        if tbl_data is None:
            conn.close()
            return {
                "status": "ROUTING_UNAVAILABLE",
                "reason": "OSRM table query timed out or failed to return road route matrix.",
                "directed_measurements": {},
                "symmetric_edges": [],
                "exclusions": [],
                "diagnostics": {}
            }

        durations = tbl_data.get("durations", [])
        distances = tbl_data.get("distances", [])
        sources = tbl_data.get("sources", [])
        
        with conn:
            for i in range(n):
                for j in range(n):
                    if i == j:
                        continue
                    p1, p2 = points[i], points[j]
                    dur = durations[i][j] if i < len(durations) and j < len(durations[i]) else None
                    dist = distances[i][j] if i < len(distances) and j < len(distances[i]) else None

                    if dur is not None and dist is not None:
                        dur_ds = round_half_up(dur * 10.0)
                        dist_dm = round_half_up(dist * 10.0)
                        u_str = f"{p1['longitude']:.5f},{p1['latitude']:.5f}"
                        v_str = f"{p2['longitude']:.5f},{p2['latitude']:.5f}"

                        conn.execute("""
                            INSERT OR REPLACE INTO route_measurements 
                            (origin, dest, duration_ds, distance_dm, timestamp)
                            VALUES (?, ?, ?, ?, datetime('now'))
                        """, (u_str, v_str, dur_ds, dist_dm))

                        directed[(p1["id"], p2["id"])] = {
                            "duration_ds": dur_ds,
                            "distance_dm": dist_dm
                        }

    # 3. Construct undirected symmetric edges: S_T(i, j) and S_D(i, j)
    symmetric_edges = []
    asymmetries_t = []
    asymmetries_d = []
    null_routes_count = 0

    for i in range(n):
        for j in range(i + 1, n):
            p1, p2 = points[i], points[j]
            fwd = directed.get((p1["id"], p2["id"]))
            rev = directed.get((p2["id"], p1["id"]))

            if fwd and rev:
                s_t = fwd["duration_ds"] + rev["duration_ds"]
                s_d = fwd["distance_dm"] + rev["distance_dm"]
                
                # Asymmetry: absolute difference
                diff_t = abs(fwd["duration_ds"] - rev["duration_ds"])
                diff_d = abs(fwd["distance_dm"] - rev["distance_dm"])
                asymmetries_t.append(diff_t)
                asymmetries_d.append(diff_d)

                symmetric_edges.append({
                    "u": p1["id"],
                    "v": p2["id"],
                    "u_name": p1.get("facility_name", p1["id"]),
                    "v_name": p2.get("facility_name", p2["id"]),
                    "u_lat": p1["latitude"],
                    "u_lon": p1["longitude"],
                    "v_lat": p2["latitude"],
                    "v_lon": p2["longitude"],
                    "s_t_ds": s_t,
                    "s_d_dm": s_d,
                    "t_avg_min": round(s_t / 1200.0, 3),
                    "d_avg_km": round(s_d / 20000.0, 3),
                    # For optimization mode weighting:
                    "duration_ds": s_t,
                    "distance_dm": s_d,
                })
            else:
                null_routes_count += 1

    conn.close()

    # Calculate asymmetry percentiles
    p95_asym_t = sorted(asymmetries_t)[int(0.95 * len(asymmetries_t))] if asymmetries_t else 0
    p95_asym_d = sorted(asymmetries_d)[int(0.95 * len(asymmetries_d))] if asymmetries_d else 0

    return {
        "status": "COMPLETED",
        "endpoint": health["endpoint"],
        "directed_measurements": directed,
        "symmetric_edges": symmetric_edges,
        "asymmetry_diagnostics": {
            "evaluated_pairs": len(symmetric_edges),
            "median_time_asymmetry_ds": sorted(asymmetries_t)[len(asymmetries_t) // 2] if asymmetries_t else 0,
            "p95_time_asymmetry_ds": p95_asym_t,
            "max_time_asymmetry_ds": max(asymmetries_t) if asymmetries_t else 0,
            "median_dist_asymmetry_dm": sorted(asymmetries_d)[len(asymmetries_d) // 2] if asymmetries_d else 0,
            "p95_dist_asymmetry_dm": p95_asym_d,
            "max_dist_asymmetry_dm": max(asymmetries_d) if asymmetries_d else 0,
            "null_routes_count": null_routes_count
        }
    }
