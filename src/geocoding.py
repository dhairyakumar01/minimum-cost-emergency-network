"""Geocoding Service for Bengaluru Emergency Network.

Resolves arbitrary location queries using OpenStreetMap Nominatim with:
- Strict rate-limiting (>= 1.0 second between network requests).
- Custom identifiable User-Agent conforming to Nominatim Usage Policy.
- In-memory result caching.
- Greater Bengaluru bounding box validation (12.7°N - 13.3°N, 77.3°E - 77.9°E).
- Spelling / transliteration variant handling (e.g., Konankunte vs Konanakunte).
- Local landmark and facility dataset fallbacks.
"""
import difflib
import json
import re
import time
import urllib.parse
import urllib.request
from typing import Dict, Optional, Tuple

USER_AGENT = "BengaluruEmergencyNetworkMST_AcademicProject/1.0 (academic_evaluation@emergency-mst.edu)"
BENGALURU_VIEWBOX = "77.3,13.2,77.9,12.7"  # left, top, right, bottom
LAT_BOUNDS = (12.70, 13.30)
LON_BOUNDS = (77.30, 77.90)

# Global in-memory cache for resolved locations
_GEOCODE_CACHE: Dict[str, dict] = {}
_LAST_REQUEST_TIME: float = 0.0

# Verified local landmark coordinate reference
KNOWN_LANDMARKS = {
    "forum mall, konankunte cross": (12.89060, 77.57500, "Forum Mall, Konankunte Cross (South Bengaluru)"),
    "konankunte cross": (12.88894, 77.56270, "Konanakunte Cross, Kanakapura Road, Bengaluru"),
    "konanakunte cross": (12.88894, 77.56270, "Konanakunte Cross, Kanakapura Road, Bengaluru"),
    "konankunte": (12.88894, 77.56270, "Konanakunte Cross, Kanakapura Road, Bengaluru"),
    "konanakunte": (12.88894, 77.56270, "Konanakunte Cross, Kanakapura Road, Bengaluru"),
    "majestic bus station": (12.97818, 77.57218, "Kempegowda Bus Station (Majestic), Bengaluru"),
    "majestic": (12.97818, 77.57218, "Kempegowda Bus Station (Majestic), Bengaluru"),
    "lalbagh": (12.94653, 77.58004, "Lalbagh Botanical Garden, Bengaluru"),
    "lal bagh": (12.94653, 77.58004, "Lalbagh Botanical Garden, Bengaluru"),
    "indiranagar": (12.97329, 77.64047, "Indiranagar 100 Feet Road, Bengaluru"),
    "whitefield": (12.99574, 77.75795, "Whitefield (Kadugodi / ITPL Corridor), Bengaluru"),
    "electronic city": (12.84520, 77.66020, "Electronic City Phase 1, Bengaluru"),
    "silk institute": (12.86240, 77.53120, "Silk Institute Metro Station, Kanakapura Road, Bengaluru"),
    "silk institute metro": (12.86240, 77.53120, "Silk Institute Metro Station, Kanakapura Road, Bengaluru"),
    "jayanagar metro": (12.92980, 77.58010, "Jayanagar Metro Station (Green Line), Bengaluru"),
    "jayanagar": (12.92980, 77.58010, "Jayanagar 4th Block, Bengaluru"),
    "koramangala": (12.93520, 77.62450, "Koramangala Sony World Junction, Bengaluru"),
    "banashankari metro": (12.91550, 77.57360, "Banashankari Metro Station & Bus Terminal, Bengaluru"),
    "banashankari": (12.91550, 77.57360, "Banashankari Bus Terminal & Metro, Bengaluru"),
    "mg road metro": (12.97560, 77.60660, "Mahatma Gandhi Road (MG Road Metro), Bengaluru"),
    "mg road": (12.97560, 77.60660, "Mahatma Gandhi Road (MG Road), Bengaluru"),
    "rajajinagar metro": (12.99820, 77.55300, "Rajajinagar Metro Station, Bengaluru"),
    "rajajinagar": (12.99820, 77.55300, "Rajajinagar 1st Block, Bengaluru"),
    "yeshwanthpur metro": (13.02220, 77.54940, "Yeshwanthpur Metro Station & Railway Terminal, Bengaluru"),
    "yeshwanthpur": (13.02220, 77.54940, "Yeshwanthpur Railway Station, Bengaluru"),
    "malleshwaram": (13.00310, 77.56430, "Malleshwaram 8th Cross, Bengaluru"),
    "btm layout": (12.91660, 77.61010, "BTM Layout 2nd Stage, Bengaluru"),
    "hsr layout": (12.91210, 77.64460, "HSR Layout Sector 1, Bengaluru"),
    "peenya": (13.03290, 77.51420, "Peenya Industrial Area, Bengaluru"),
    "hebbal": (13.03580, 77.59700, "Hebbal Flyover Junction, Bengaluru"),
    "yelahanka": (13.10070, 77.59630, "Yelahanka Old Town, Bengaluru"),
}

GENERIC_TERMS = {
    "metro", "station", "road", "cross", "circle", "junction", "layout",
    "block", "halli", "nagar", "park", "garden", "mall", "hospital", "clinic"
}


def _rate_limited_nominatim_query(q_str: str) -> Optional[dict]:
    """Execute rate-limited request to OpenStreetMap Nominatim."""
    global _LAST_REQUEST_TIME
    
    elapsed = time.time() - _LAST_REQUEST_TIME
    if elapsed < 1.05:
        time.sleep(1.05 - elapsed)
        
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode({
        "q": q_str,
        "format": "json",
        "limit": 1,
        "countrycodes": "in",
        "viewbox": BENGALURU_VIEWBOX,
        "bounded": 0,
    })
    
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            _LAST_REQUEST_TIME = time.time()
            data = json.loads(resp.read().decode())
            if data and len(data) > 0:
                first = data[0]
                lat = float(first["lat"])
                lon = float(first["lon"])
                if LAT_BOUNDS[0] <= lat <= LAT_BOUNDS[1] and LON_BOUNDS[0] <= lon <= LON_BOUNDS[1]:
                    return {
                        "display_name": first["display_name"],
                        "latitude": lat,
                        "longitude": lon,
                        "source": f"OpenStreetMap Nominatim (Query: '{q_str}')",
                    }
    except Exception:
        _LAST_REQUEST_TIME = time.time()
        return None
    return None


def geocode_bengaluru_location(query: str, facilities_df=None) -> Tuple[bool, Optional[dict], str]:
    """Resolve an arbitrary user query string into geographical coordinates in Bengaluru.
    
    Returns:
        (success: bool, result_dict: Optional[dict], message: str)
    """
    clean_q = " ".join(query.strip().split())
    if not clean_q or len(clean_q) < 3:
        return False, None, "Query too short. Please enter a valid location or landmark name."
        
    cache_key = clean_q.lower()
    if cache_key in _GEOCODE_CACHE:
        return True, _GEOCODE_CACHE[cache_key], "Resolved from session cache."
        
    # 1. Check known landmark dictionary (exact, compact, or fuzzy spelling tolerance)
    q_compact = re.sub(r"[^a-z0-9]", "", cache_key)
    best_landmark = None
    best_score = 0.0

    for k_name, (k_lat, k_lon, k_disp) in KNOWN_LANDMARKS.items():
        k_compact = re.sub(r"[^a-z0-9]", "", k_name)
        if k_name in cache_key or cache_key in k_name or k_compact == q_compact or (len(q_compact) >= 5 and (q_compact in k_compact or k_compact in q_compact)):
            best_landmark = (k_lat, k_lon, k_disp)
            best_score = 1.0
            break
        # Token-level fuzzy match for minor spelling typos (e.g., Indiranagr, Whitefeild)
        # Exclude generic words (e.g. 'metro', 'station', 'road') from matching alone
        for q_tok in re.split(r"\W+", cache_key):
            if len(q_tok) >= 4 and q_tok not in GENERIC_TERMS:
                for k_tok in re.split(r"\W+", k_name):
                    if len(k_tok) >= 4 and k_tok not in GENERIC_TERMS:
                        ratio = difflib.SequenceMatcher(None, q_tok, k_tok).ratio()
                        if ratio > best_score and ratio >= 0.82:
                            best_score = ratio
                            best_landmark = (k_lat, k_lon, k_disp)

    if best_landmark and best_score >= 0.82:
        res = {
            "display_name": best_landmark[2],
            "latitude": best_landmark[0],
            "longitude": best_landmark[1],
            "source": "Verified Bengaluru Landmark Registry",
        }
        _GEOCODE_CACHE[cache_key] = res
        return True, res, "Resolved from verified landmark registry."
            
    # 2. Build candidate queries for Nominatim
    candidates = [clean_q]
    q_lower = clean_q.lower()
    if "bengaluru" not in q_lower and "bangalore" not in q_lower:
        candidates.append(f"{clean_q}, Bengaluru")
        
    # Handle common Kannada / English transliteration spelling variations
    if "konankunte" in q_lower:
        variant = re.sub(r"konankunte", "konanakunte", clean_q, flags=re.IGNORECASE)
        candidates.append(variant + (", Bengaluru" if "bengaluru" not in variant.lower() else ""))
        candidates.append("Konanakunte Cross, Bengaluru")
        
    for cand in candidates:
        nom_res = _rate_limited_nominatim_query(cand)
        if nom_res:
            _GEOCODE_CACHE[cache_key] = nom_res
            return True, nom_res, "Successfully resolved via OpenStreetMap Nominatim."
            
    # 3. Fallback: Search dataset facilities if DataFrame provided
    if facilities_df is not None and not facilities_df.empty:
        q_norm = re.sub(r"[^\w\s]", " ", q_lower)
        q_tokens = [t for t in q_norm.split() if len(t) >= 3]
        if q_tokens:
            for _, row in facilities_df.iterrows():
                fname = str(row["facility_name"]).lower()
                if all(t in fname for t in q_tokens):
                    res = {
                        "display_name": f"{row['facility_name']} (Facility ID: {row['facility_id']})",
                        "latitude": float(row["latitude"]),
                        "longitude": float(row["longitude"]),
                        "source": "Bengaluru Emergency Facility Dataset Record",
                    }
                    _GEOCODE_CACHE[cache_key] = res
                    return True, res, "Resolved from emergency facility registry."

    return False, None, f"Could not resolve '{clean_q}' to coordinates within Bengaluru. Please check spelling or refine with map click."

