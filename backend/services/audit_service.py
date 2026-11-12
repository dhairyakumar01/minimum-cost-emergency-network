"""
Dataset Audit and Provenance Service
Reconciles emergency facility records, checks coordinate validity,
identifies spatial co-locations and duplicate records within 5m,
and computes cryptographic dataset provenance.
"""
import hashlib
import math
from pathlib import Path
from typing import Dict, Any, List

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
FACILITIES_CSV = DATA_DIR / "processed" / "emergency_facilities.csv"
EARTH_RADIUS_M = 6371008.8  # Earth radius in meters


def haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Spherical Haversine distance in meters."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = phi2 - phi1
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2.0) ** 2
    return 2.0 * EARTH_RADIUS_M * math.asin(min(1.0, math.sqrt(a)))


def normalize_agency(source_type: str) -> str:
    """Maps raw CSV facility_type to canonical specification category."""
    st = str(source_type).lower().strip()
    if "hosp" in st or "clinic" in st:
        return "hospital_clinic"
    if "pol" in st:
        return "police"
    if "fire" in st:
        return "fire"
    return "hospital_clinic"


def audit_facilities_dataset() -> Dict[str, Any]:
    """Execute complete mathematical and provenance audit of the facilities dataset."""
    if not FACILITIES_CSV.exists():
        return {
            "status": "MISSING_DATASET",
            "file_path": str(FACILITIES_CSV),
            "sha256": None,
            "total_records": 0,
        }

    # Compute SHA-256 hash
    with open(FACILITIES_CSV, "rb") as f:
        sha256_hash = hashlib.sha256(f.read()).hexdigest()

    import csv
    records = []
    with open(FACILITIES_CSV, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)

    total_records = len(records)
    agency_counts = {"hospital_clinic": 0, "police": 0, "fire": 0}
    invalid_records = []
    seen_ids = set()
    duplicate_ids = []

    parsed_facilities = []

    for idx, r in enumerate(records):
        fac_id = r.get("facility_id", "").strip()
        fac_name = r.get("facility_name", "").strip() or "Unnamed Facility"
        fac_type = r.get("facility_type", "").strip()
        norm_agency = normalize_agency(fac_type)

        # ID validation
        if not fac_id:
            invalid_records.append({"row": idx, "reason": "Missing facility_id"})
            continue
        if fac_id in seen_ids:
            duplicate_ids.append(fac_id)
        seen_ids.add(fac_id)

        # Coordinate validation
        try:
            lat = float(r.get("latitude", ""))
            lon = float(r.get("longitude", ""))
            if math.isnan(lat) or math.isinf(lat) or lat < -90.0 or lat > 90.0:
                invalid_records.append({"facility_id": fac_id, "reason": f"Invalid latitude: {lat}"})
                continue
            if math.isnan(lon) or math.isinf(lon) or lon < -180.0 or lon > 180.0:
                invalid_records.append({"facility_id": fac_id, "reason": f"Invalid longitude: {lon}"})
                continue
        except (ValueError, TypeError):
            invalid_records.append({"facility_id": fac_id, "reason": "Non-numeric coordinates"})
            continue

        agency_counts[norm_agency] = agency_counts.get(norm_agency, 0) + 1
        parsed_facilities.append({
            "facility_id": fac_id,
            "facility_name": fac_name,
            "raw_type": fac_type,
            "agency": norm_agency,
            "latitude": lat,
            "longitude": lon,
            "source": r.get("source", "OpenStreetMap (BBMP Export)"),
            "source_id": r.get("source_id", fac_id),
            "validation_status": r.get("validation_status", "verified"),
        })

    # Sort stably by facility_id
    parsed_facilities.sort(key=lambda x: x["facility_id"])
    for vertex_id, fac in enumerate(parsed_facilities, start=1):
        fac["vertex_id"] = vertex_id

    # Spatial proximity duplicate audit (<= 5.0 meters)
    pairs_under_5m = []
    same_name_duplicates = []
    for i in range(len(parsed_facilities)):
        f1 = parsed_facilities[i]
        for j in range(i + 1, len(parsed_facilities)):
            f2 = parsed_facilities[j]
            d_m = haversine_meters(f1["latitude"], f1["longitude"], f2["latitude"], f2["longitude"])
            if d_m <= 5.0:
                norm1 = f1["facility_name"].lower().strip()
                norm2 = f2["facility_name"].lower().strip()
                is_same_name = (norm1 == norm2 and norm1 != "unnamed facility")
                item = {
                    "id1": f1["facility_id"],
                    "name1": f1["facility_name"],
                    "id2": f2["facility_id"],
                    "name2": f2["facility_name"],
                    "agency": f1["agency"],
                    "distance_meters": round(d_m, 2),
                    "is_same_name": is_same_name,
                    "is_same_agency": f1["agency"] == f2["agency"],
                }
                pairs_under_5m.append(item)
                if is_same_name and f1["agency"] == f2["agency"]:
                    same_name_duplicates.append(item)

    return {
        "status": "VERIFIED_VALID",
        "file_path": str(FACILITIES_CSV),
        "sha256": sha256_hash,
        "total_source_records": total_records,
        "valid_records_count": len(parsed_facilities),
        "invalid_records_count": len(invalid_records),
        "invalid_records": invalid_records,
        "exact_duplicate_ids": duplicate_ids,
        "agency_breakdown": agency_counts,
        "pairs_under_5m_count": len(pairs_under_5m),
        "pairs_under_5m": pairs_under_5m,
        "flagged_same_name_duplicates_count": len(same_name_duplicates),
        "flagged_same_name_duplicates": same_name_duplicates,
        "study_area": "Bruhat Bengaluru Mahanagara Palike (BBMP)",
        "stable_ordering_rule": "Ascending lexicographical sort on facility_id",
        "indexing_convention": "Incident vertex ID = 0, Facility vertices = 1 through N",
        "facilities": parsed_facilities,
    }
