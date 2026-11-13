# Deployment & Operations Guide
**Project:** Minimum-Cost Emergency Communication Network Using Minimum Spanning Tree (MST)  
**Study Area:** BBMP Bengaluru, Karnataka, India

---

## 1. Prerequisites

- **Operating System:** Windows 10/11, Ubuntu 20.04/22.04 LTS, or macOS 12+
- **Python:** Python 3.10, 3.11, or 3.12
- **Web Browser:** Google Chrome 100+, Mozilla Firefox 100+, or Microsoft Edge 100+
- **Network Access:** HTTP access to OpenStreetMap tiles (`tile.openstreetmap.org`) and OSRM routing (`router.project-osrm.org`). Alternatively, a local OSRM instance can be hosted on port 5001.

---

## 2. Quick-Start Local Installation

### Step 1: Clone and Navigate to Repository
```bash
git clone <repository_url>
cd minimum_cost_emergency_network
```

### Step 2: Configure Python Virtual Environment
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Required Dependencies
```bash
pip install -r requirements.txt
```

---

## 3. Running the Applications

### 3.1 Primary Application: Flask Web Application
The primary operational system is the Flask + HTML5/CSS3/Vanilla JS platform.

```bash
# Start Flask Server
python backend/flask_app.py
```
- **Localhost URL:** `http://127.0.0.1:5000`
- **Health Check:** `http://127.0.0.1:5000/api/health`
- **Dataset Audit:** `http://127.0.0.1:5000/api/dataset/audit`
- **Global MST:** `http://127.0.0.1:5000/api/global-mst`

### 3.2 Legacy Fallback: Streamlit Application
The original Streamlit application is preserved intact for comparative validation and academic demonstration.

```bash
streamlit run app.py --server.port 8501
```
- **Streamlit URL:** `http://127.0.0.1:8501`

---

## 4. OSRM Routing Engine Configuration

The application automatically checks for routing service availability:
1. **Local Instance (Preferred for offline/low-latency):**
   - The engine checks `http://127.0.0.1:5001/table/v1/driving/...`
   - To launch a local OSRM server for Karnataka:
     ```bash
     docker run -t -i -p 5001:5000 -v "${PWD}/data/osrm:/data" ghcr.io/project-osrm/osrm-backend osrm-routed --algorithm mld /data/karnataka-latest.osrm
     ```
2. **Public Demo Endpoint (Default fallback):**
   - If port 5001 is unavailable, the application connects to `http://router.project-osrm.org`.
3. **Persistent SQLite Route Cache:**
   - All measured pairwise routes are permanently cached in `data/cache/routes.db`. Once a route between two coordinates is computed, subsequent simulations retrieve it in sub-millisecond database queries.
4. **Offline Handling:**
   - If neither endpoint is reachable, the backend returns status `ROUTING_UNAVAILABLE` rather than substituting fake or straight-line distances.

---

## 5. Running Automated Verification & Tests

To execute the full automated verification test suite:

```bash
# Run all 89 unit and integration tests
pytest tests/ -v

# Run specific scenario pipeline tests
pytest tests/test_scenario_pipeline.py -v

# Run mathematical audit and invariant tests
pytest tests/test_phase1_6_audit.py -v
```

---

## 6. Production Deployment (WSGI)

For production deployment on Linux servers, use Gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 backend.flask_app:app
```

On Windows servers, use Waitress:

```bash
pip install waitress
waitress-serve --port=5000 backend.flask_app:app
```

