"""Data service for loading, caching, and querying emergency network datasets."""
import csv
import threading
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from backend.config import Config


class DataService:
    """Thread-safe cached data service for emergency facilities and precomputed MSTs."""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self._lock = threading.RLock()
        self._facilities: Optional[List[Dict[str, Any]]] = None
        self._facilities_by_id: Optional[Dict[str, Dict[str, Any]]] = None
        self._facilities_by_agency: Optional[Dict[str, List[Dict[str, Any]]]] = None
        self._global_mst_cache: Dict[str, Dict[str, Any]] = {}

    def normalize_agency(self, agency_str: Optional[str]) -> Optional[str]:
        """Normalize an agency query string to its canonical key."""
        if not agency_str:
            return None
        cleaned = agency_str.strip().lower().replace(" ", "_").replace("-", "_")
        canonical = self.config.AGENCY_ALIASES.get(cleaned)
        if not canonical:
            supported = sorted(list(self.config.AGENCY_CANONICAL.keys()))
            raise ValueError(
                f"Unsupported agency filter '{agency_str}'. Supported agencies: {', '.join(supported)}"
            )
        return canonical

    def load_facilities(self, force_reload: bool = False) -> List[Dict[str, Any]]:
        """Load and cache verified facilities from CSV.
        
        Only reads essential columns into a lightweight memory structure.
        """
        with self._lock:
            if self._facilities is not None and not force_reload:
                return self._facilities

            csv_path = self.config.FACILITIES_CSV
            if not csv_path.exists():
                raise FileNotFoundError(f"Facilities dataset not found at {csv_path}")

            facilities = []
            by_id = {}
            by_agency = {k: [] for k in self.config.AGENCY_CANONICAL.keys()}

            with open(csv_path, mode="r", encoding="utf-8-sig", errors="replace") as f:
                reader = csv.DictReader(f)
                clean_fields = {fn.strip().lstrip("\ufeff") for fn in (reader.fieldnames or [])}
                required = {"facility_id", "facility_name", "facility_type", "latitude", "longitude"}
                if not required.issubset(clean_fields):
                    missing = required - clean_fields
                    raise ValueError(f"Facilities CSV missing required fields: {sorted(missing)}")

                for row in reader:
                    f_id = row["facility_id"].strip()
                    f_name = row["facility_name"].strip() or f_id
                    f_type = row["facility_type"].strip()
                    
                    try:
                        lat = float(row["latitude"])
                        lon = float(row["longitude"])
                    except (ValueError, TypeError):
                        continue  # Skip unparseable coordinates safely

                    # Ensure coordinates are within valid geographic bounds
                    if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
                        continue

                    canonical_agency = self.config.AGENCY_ALIASES.get(f_type.lower(), "hospital")
                    agency_label = self.config.AGENCY_CANONICAL.get(canonical_agency, "Emergency Facility")

                    fac_obj = {
                        "facility_id": f_id,
                        "facility_name": f_name,
                        "agency": canonical_agency,
                        "agency_label": agency_label,
                        "latitude": round(lat, 6),
                        "longitude": round(lon, 6),
                    }
                    facilities.append(fac_obj)
                    by_id[f_id] = fac_obj
                    if canonical_agency in by_agency:
                        by_agency[canonical_agency].append(fac_obj)

            self._facilities = facilities
            self._facilities_by_id = by_id
            self._facilities_by_agency = by_agency
            return self._facilities

    def get_facilities(
        self,
        agency: Optional[str] = None,
        search: Optional[str] = None,
        page: Optional[int] = None,
        per_page: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Query facilities with optional agency filter, substring search, and pagination."""
        facilities = self.load_facilities()
        canonical_agency = self.normalize_agency(agency) if agency else None

        # Filter by agency using pre-indexed agency buckets for maximum performance
        if canonical_agency:
            filtered = self._facilities_by_agency.get(canonical_agency, [])
        else:
            filtered = facilities

        # Optional substring search (case-insensitive on name or ID)
        if search:
            q = search.strip().lower()
            filtered = [
                f for f in filtered
                if q in f["facility_name"].lower() or q in f["facility_id"].lower()
            ]

        total_matching = len(filtered)

        # Optional pagination
        if page is not None and per_page is not None:
            page = max(1, page)
            per_page = max(1, min(per_page, 2000))
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            paged_items = filtered[start_idx:end_idx]
            is_paginated = True
        else:
            paged_items = filtered
            is_paginated = False
            page = 1
            per_page = total_matching

        return {
            "total": total_matching,
            "count": len(paged_items),
            "page": page if is_paginated else None,
            "per_page": per_page if is_paginated else None,
            "agency_filter": canonical_agency,
            "search_query": search,
            "facilities": paged_items,
        }

    def get_facility_by_id(self, facility_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single facility record by ID."""
        self.load_facilities()
        return self._facilities_by_id.get(str(facility_id).strip())

    def get_health_status(self) -> Dict[str, Any]:
        """Return application health and dataset readiness metrics without computing graph."""
        csv_exists = self.config.FACILITIES_CSV.exists()
        fac_count = 0
        agency_breakdown = {}

        if csv_exists:
            try:
                facs = self.load_facilities()
                fac_count = len(facs)
                for k, v in (self._facilities_by_agency or {}).items():
                    agency_breakdown[k] = len(v)
            except Exception:
                csv_exists = False

        return {
            "status": "healthy" if csv_exists and fac_count > 0 else "degraded",
            "version": self.config.VERSION,
            "dataset_available": csv_exists,
            "facilities_count": fac_count,
            "agency_breakdown": agency_breakdown,
            "ready": csv_exists and fac_count > 0,
            "environment": self.config.ENV,
        }

    def get_global_mst(self, algo: str = "kruskal") -> Dict[str, Any]:
        """Load and return the precomputed global MST from validated results.
        
        Guarantees that no 786,885-edge candidate graph is generated or recalculated.
        """
        algo_norm = algo.strip().lower()
        if algo_norm not in ("kruskal", "prim"):
            raise ValueError(f"Invalid algorithm '{algo}'. Supported: 'kruskal', 'prim'")

        with self._lock:
            if algo_norm in self._global_mst_cache:
                return self._global_mst_cache[algo_norm]

            csv_path = (
                self.config.KRUSKAL_MST_CSV
                if algo_norm == "kruskal"
                else self.config.PRIM_MST_CSV
            )

            if not csv_path.exists():
                raise FileNotFoundError(
                    f"Validated {algo.capitalize()} MST result file not found at {csv_path}"
                )

            # Ensure facility data is cached for lookup and vertex count
            facs = self.load_facilities()

            edges = []
            total_weight = 0.0

            with open(csv_path, mode="r", encoding="utf-8-sig", errors="replace") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    w = float(r.get("weight_km", 0.0))
                    total_weight += w
                    u_id = r.get("u")
                    v_id = r.get("v")
                    u_fac = self._facilities_by_id.get(u_id)
                    v_fac = self._facilities_by_id.get(v_id)
                    edges.append({
                        "u": u_id,
                        "v": v_id,
                        "u_name": r.get("u_name"),
                        "v_name": r.get("v_name"),
                        "u_type": r.get("u_type"),
                        "v_type": r.get("v_type"),
                        "weight_km": round(w, 4),
                        "u_lat": u_fac["latitude"] if u_fac else None,
                        "u_lon": u_fac["longitude"] if u_fac else None,
                        "v_lat": v_fac["latitude"] if v_fac else None,
                        "v_lon": v_fac["longitude"] if v_fac else None,
                    })

            mst_result = {
                "algorithm": "Kruskal" if algo_norm == "kruskal" else "Prim",
                "vertex_count": len(facs),
                "edge_count": len(edges),
                "total_weight_km": round(total_weight, 4),
                "weight_unit": "km",
                "distance_metric": "Spherical Haversine",
                "edges": edges,
            }

            self._global_mst_cache[algo_norm] = mst_result
            return mst_result


# Singleton instance
data_service = DataService()
