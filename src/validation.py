"""Independent validation of an MST result against the facility table.

These checks look only at the output edge list and the facility coordinates,
not at how Prim or Kruskal produced the tree.
"""
import numpy as np

from src.mst_network import haversine_km


def validate_mst(nodes, mst, tol=1e-6):
    """Return a dict of check name -> bool for one MST edge table."""
    ids = set(nodes.facility_id)
    n = len(ids)
    checks = {}

    us = mst["u"].tolist()
    vs = mst["v"].tolist()

    checks["edge_count_is_V_minus_1"] = len(mst) == max(0, n - 1)

    endpoints_valid = all(x in ids for x in us + vs)
    checks["endpoints_are_valid_facility_ids"] = endpoints_valid

    checks["no_self_loops"] = all(a != b for a, b in zip(us, vs))

    w = mst["weight_km"].to_numpy(dtype=float)
    checks["weights_finite_and_nonnegative"] = bool(
        np.isfinite(w).all() and (w >= 0).all()
    )

    checks["no_duplicate_edges"] = (
        len({frozenset((a, b)) for a, b in zip(us, vs)}) == len(mst)
    )

    if endpoints_valid:
        parent = {x: x for x in ids}

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        acyclic = True
        for a, b in zip(us, vs):
            ra, rb = find(a), find(b)
            if ra == rb:
                acyclic = False
            else:
                parent[rb] = ra

        components = len({find(x) for x in ids})
        checks["acyclic"] = acyclic
        checks["connected_and_spans_all_facilities"] = components == 1

        coords = nodes.set_index("facility_id")[["latitude", "longitude"]]
        recomputed = np.array(
            [
                haversine_km(
                    coords.at[a, "latitude"], coords.at[a, "longitude"],
                    coords.at[b, "latitude"], coords.at[b, "longitude"],
                )
                for a, b in zip(us, vs)
            ]
        )
        checks["stored_weights_match_haversine"] = bool(
            np.allclose(recomputed, w, atol=tol)
        )
    else:
        checks["acyclic"] = False
        checks["connected_and_spans_all_facilities"] = False
        checks["stored_weights_match_haversine"] = False

    return checks
