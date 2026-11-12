"""Configuration settings for the Emergency Network Flask application."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Config:
    VERSION = "1.0.0"
    APP_NAME = "Bengaluru Emergency Communication Network"
    ENV = os.getenv("FLASK_ENV", "production")
    DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"
    PORT = int(os.getenv("PORT", "5000"))
    HOST = os.getenv("HOST", "0.0.0.0")

    # Storage paths
    DATA_DIR = BASE_DIR / "data"
    PROCESSED_DATA_DIR = DATA_DIR / "processed"
    RESULTS_DIR = BASE_DIR / "results"
    FRONTEND_DIR = BASE_DIR / "frontend"
    CACHE_DIR = DATA_DIR / "cache"

    # Dataset file paths
    FACILITIES_CSV = PROCESSED_DATA_DIR / "emergency_facilities.csv"
    KRUSKAL_MST_CSV = RESULTS_DIR / "kruskal_mst_edges.csv"
    PRIM_MST_CSV = RESULTS_DIR / "prim_mst_edges.csv"
    ROUTES_CACHE_FILE = CACHE_DIR / "routes_cache.json"

    # Supported emergency agencies and user-friendly aliases
    AGENCY_CANONICAL = {
        "hospital": "Hospital / Clinic",
        "police_station": "Police Station",
        "fire_station": "Fire Station",
    }

    AGENCY_ALIASES = {
        "hospital": "hospital",
        "hospitals": "hospital",
        "clinic": "hospital",
        "clinics": "hospital",
        "ambulance": "hospital",
        "medical": "hospital",
        "police": "police_station",
        "police_station": "police_station",
        "police_stations": "police_station",
        "cops": "police_station",
        "fire": "fire_station",
        "fire_station": "fire_station",
        "fire_stations": "fire_station",
        "firefighting": "fire_station",
    }

