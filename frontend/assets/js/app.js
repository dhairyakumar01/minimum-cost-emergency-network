/**
 * Main Application Module — Bengaluru Emergency Network
 * Handles UI interactions, Leaflet maps, clustering, incident placement,
 * global MST schematic rendering, and emergency response simulation setup.
 */

(function () {
  const EARTH_KM = 6371.0088;

  const AGENCY_COLORS = {
    "hospital": "#dc2626",
    "police_station": "#2563eb",
    "fire_station": "#ea580c",
  };

  const AGENCY_LABELS = {
    "hospital": "Hospital / Clinic",
    "police_station": "Police Station",
    "fire_station": "Fire Station",
  };

  const AGENCY_RATES = {
    "hospital": { rate: 12.50, vehicle: "Ambulance (BLS/ALS)", speedKmh: 42.0 },
    "police_station": { rate: 6.25, vehicle: "Police Patrol (Hoysala)", speedKmh: 48.0 },
    "fire_station": { rate: 18.00, vehicle: "Fire Engine Appliance", speedKmh: 35.0 },
  };

  // Global Application State
  const State = {
    facilities: [],
    facilitiesById: {},
    currentAgencyFilter: "all",
    activeSearchTerm: "",
    selectedFacility: null,
    
    // Incident State
    incident: {
      lat: 12.9781,
      lon: 77.5696,
      label: "Majestic (KSR Railway Station)",
      isSet: true,
    },
    incidentSelectMode: false,
    
    // Simulation State
    simCategory: "medical",
    simAgency: "hospital",
    simRadiusKm: 5.0,
    simMode: "time",
    
    // MST State
    mstAlgorithm: "kruskal",
    mstCache: { kruskal: null, prim: null },
    mstSelectedEdge: null,
  };

  // Leaflet Map Instances
  let facMap = null;
  let facMarkersLayer = null;
  let incidentMarker = null;

  let mstMap = null;
  let mstEdgesLayer = null;
  let mstNodesLayer = null;

  /**
   * Spherical Haversine calculation matching backend and DMGT formulation.
   */
  function haversineKm(lat1, lon1, lat2, lon2) {
    const toRad = (x) => (x * Math.PI) / 180.0;
    const p1 = toRad(lat1);
    const p2 = toRad(lat2);
    const dp = toRad(lat2 - lat1);
    const dl = toRad(lon2 - lon1);
    const a =
      Math.sin(dp / 2.0) ** 2 +
      Math.cos(p1) * Math.cos(p2) * Math.sin(dl / 2.0) ** 2;
    return 2.0 * EARTH_KM * Math.asin(Math.min(1.0, Math.sqrt(a)));
  }

  // --------------------------------------------------------------------------
  // Lifecycle Initialization
  // --------------------------------------------------------------------------

  document.addEventListener("DOMContentLoaded", () => {
    Navigation.init();
    initApp();

    // Map invalidation on navigation
    Navigation.onNavigate((sectionId) => {
      if (sectionId === "facilities-map") {
        setTimeout(() => {
          if (!facMap) {
            initFacilitiesMap();
          } else {
            facMap.invalidateSize();
          }
        }, 120);
      } else if (sectionId === "mst-network") {
        setTimeout(() => {
          if (!mstMap) {
            initMstMap();
          } else {
            mstMap.invalidateSize();
          }
        }, 120);
      } else if (sectionId === "simulation") {
        updateSimulationUI();
      }
    });

    bindFacilitiesMapEvents();
    bindMstEvents();
  });

  /**
   * Load health and facility catalog from backend.
   */
  async function initApp() {
    showLoader("Connecting to backend...", "Fetching system health and facility records");
    hideErrorBanner();

    try {
      const [health, facData] = await Promise.all([
        API.getHealth(),
        API.getFacilities(),
      ]);

      State.facilities = facData.facilities || [];
      State.facilitiesById = {};
      State.facilities.forEach((f) => {
        State.facilitiesById[f.facility_id] = f;
      });

      updateDashboard(health, State.facilities);

      const pill = document.getElementById("backend-status-pill");
      if (pill) {
        pill.innerHTML = `<span class="status-indicator"></span> Backend Ready &bull; ${health.facilities_count} facilities`;
      }

      updateSimulationCandidateCount();
      hideLoader();
    } catch (err) {
      console.error("Initialization error:", err);
      showErrorBanner(
        `Failed to connect to backend (${err.message}). Make sure Flask is active.`
      );
      hideLoader();
    }
  }

  function updateDashboard(health, facilities) {
    const counts = health.agency_breakdown || {};
    const total = health.facilities_count || 1255;
    const hosp = counts.hospital || 1097;
    const pol = counts.police_station || 138;
    const fire = counts.fire_station || 20;

    setText("metric-total-facilities", total.toLocaleString());
    setText("metric-hospitals", hosp.toLocaleString());
    setText("metric-police", pol.toLocaleString());
    setText("metric-fire", fire.toLocaleString());
    setText("metric-mst-connections", "1,254");
    setText("metric-mst-length", "480.1784 km");

    const hospPct = ((hosp / total) * 100).toFixed(1);
    const polPct = ((pol / total) * 100).toFixed(1);
    const firePct = ((fire / total) * 100).toFixed(1);

    setBarWidth("bar-hospitals", hospPct);
    setBarWidth("bar-police", polPct);
    setBarWidth("bar-fire", firePct);

    setText("pct-hospitals", `${hospPct}%`);
    setText("pct-police", `${polPct}%`);
    setText("pct-fire", `${firePct}%`);
  }

  // --------------------------------------------------------------------------
  // Facilities Map & Incident Selection
  // --------------------------------------------------------------------------

  function initFacilitiesMap() {
    const container = document.getElementById("leaflet-map");
    if (!container || facMap) return;

    facMap = L.map("leaflet-map", {
      center: [12.9716, 77.5946],
      zoom: 12,
      zoomControl: true,
    });

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 18,
      attribution: "&copy; OpenStreetMap contributors | DMGT Bengaluru Research",
    }).addTo(facMap);

    // Marker Clustering Group (fallback to LayerGroup if plugin unavailable)
    if (typeof L.markerClusterGroup === "function") {
      facMarkersLayer = L.markerClusterGroup({
        maxClusterRadius: 40,
        spiderfyOnMaxZoom: true,
        showCoverageOnHover: false,
        zoomToBoundsOnClick: true,
      });
    } else {
      facMarkersLayer = L.layerGroup();
    }
    facMap.addLayer(facMarkersLayer);

    renderFacilityMarkers();

    // Setup initial incident pin if set
    if (State.incident.isSet) {
      placeIncidentMarker(State.incident.lat, State.incident.lon);
    }

    // Map click handler for incident placement
    facMap.on("click", (e) => {
      if (State.incidentSelectMode) {
        placeIncidentMarker(e.latlng.lat, e.latlng.lng);
        setIncidentSelectMode(false);
      }
    });
  }

  function renderFacilityMarkers() {
    if (!facMap || !facMarkersLayer) return;

    facMarkersLayer.clearLayers();

    let filtered = State.facilities;

    if (State.currentAgencyFilter !== "all") {
      filtered = filtered.filter((f) => f.agency === State.currentAgencyFilter);
    }

    if (State.activeSearchTerm) {
      const q = State.activeSearchTerm;
      filtered = filtered.filter(
        (f) =>
          f.facility_name.toLowerCase().includes(q) ||
          f.facility_id.toLowerCase().includes(q)
      );
    }

    const badge = document.getElementById("rendered-facilities-count");
    if (badge) {
      badge.textContent = `Displaying ${filtered.length.toLocaleString()} of ${State.facilities.length.toLocaleString()} facilities`;
    }

    const newMarkers = [];

    filtered.forEach((fac) => {
      const color = AGENCY_COLORS[fac.agency] || "#2563eb";
      const marker = L.circleMarker([fac.latitude, fac.longitude], {
        radius: 6,
        fillColor: color,
        color: "#ffffff",
        weight: 1.5,
        opacity: 1,
        fillOpacity: 0.88,
      });

      marker.on("click", () => {
        showFacilityDetailsCard(fac);
      });

      newMarkers.push(marker);
    });

    if (typeof facMarkersLayer.addLayers === "function") {
      facMarkersLayer.addLayers(newMarkers);
    } else {
      newMarkers.forEach((m) => facMarkersLayer.addLayer(m));
    }
  }

  function bindFacilitiesMapEvents() {
    // Agency Filter Buttons
    document.querySelectorAll(".filter-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".filter-btn").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        State.currentAgencyFilter = btn.getAttribute("data-agency");
        renderFacilityMarkers();
      });
    });

    // Facility Search
    const searchInput = document.getElementById("facility-map-search");
    if (searchInput) {
      let timer = null;
      searchInput.addEventListener("input", (e) => {
        clearTimeout(timer);
        timer = setTimeout(() => {
          State.activeSearchTerm = e.target.value.trim().toLowerCase();
          renderFacilityMarkers();
        }, 150);
      });
    }

    // Toggle Incident Mode Button
    const btnToggleMode = document.getElementById("btn-toggle-incident-mode");
    if (btnToggleMode) {
      btnToggleMode.addEventListener("click", () => {
        setIncidentSelectMode(!State.incidentSelectMode);
      });
    }

    // Confirm Incident Button
    const btnConfirm = document.getElementById("btn-confirm-incident");
    if (btnConfirm) {
      btnConfirm.addEventListener("click", () => {
        confirmIncidentLocation();
      });
    }

    // Clear Incident Button
    const btnClear = document.getElementById("btn-clear-incident");
    if (btnClear) {
      btnClear.addEventListener("click", () => {
        clearIncidentLocation();
      });
    }

    // Send to Simulation Button
    const btnSendSim = document.getElementById("btn-send-to-sim");
    if (btnSendSim) {
      btnSendSim.addEventListener("click", () => {
        Navigation.navigateTo("simulation");
      });
    }

    // Landmark Preset Buttons (Facilities Map)
    document.querySelectorAll(".incident-coords-row .landmark-pill").forEach((pill) => {
      pill.addEventListener("click", () => {
        const lat = parseFloat(pill.getAttribute("data-lat"));
        const lon = parseFloat(pill.getAttribute("data-lon"));
        const name = pill.getAttribute("data-name");
        placeIncidentMarker(lat, lon, name);
        if (facMap) facMap.setView([lat, lon], 14);
      });
    });

    // Coordinate text inputs
    const latInp = document.getElementById("incident-lat-input");
    const lonInp = document.getElementById("incident-lon-input");
    const onCoordChange = () => {
      const lat = parseFloat(latInp.value);
      const lon = parseFloat(lonInp.value);
      if (!isNaN(lat) && !isNaN(lon) && lat >= 12.5 && lat <= 13.5 && lon >= 77.3 && lon <= 77.9) {
        placeIncidentMarker(lat, lon, "Custom Coordinates");
        if (facMap) facMap.setView([lat, lon], 14);
      }
    };
    if (latInp) latInp.addEventListener("change", onCoordChange);
    if (lonInp) lonInp.addEventListener("change", onCoordChange);

    // Close Facility Card
    const btnCloseCard = document.getElementById("btn-close-facility-card");
    if (btnCloseCard) {
      btnCloseCard.addEventListener("click", () => {
        const card = document.getElementById("selected-facility-card");
        if (card) card.style.display = "none";
      });
    }
  }

  function setIncidentSelectMode(active) {
    State.incidentSelectMode = active;
    const btn = document.getElementById("btn-toggle-incident-mode");
    const coordsBar = document.getElementById("incident-coords-bar");

    if (btn) {
      if (active) {
        btn.textContent = "📍 Click Map to Place Pin";
        btn.classList.add("btn-primary");
        btn.classList.remove("btn-outline");
      } else {
        btn.textContent = "📍 Select Incident Location";
        btn.classList.remove("btn-primary");
        btn.classList.add("btn-outline");
      }
    }

    if (coordsBar) {
      coordsBar.style.display = active || State.incident.isSet ? "flex" : "none";
    }
  }

  function placeIncidentMarker(lat, lon, label = "Incident Point") {
    State.incident = {
      lat: roundCoord(lat),
      lon: roundCoord(lon),
      label: label,
      isSet: true,
    };

    // Update input fields
    const latInp = document.getElementById("incident-lat-input");
    const lonInp = document.getElementById("incident-lon-input");
    if (latInp) latInp.value = State.incident.lat.toFixed(5);
    if (lonInp) lonInp.value = State.incident.lon.toFixed(5);

    // Update status badge
    const pill = document.getElementById("incident-status-pill");
    if (pill) {
      pill.className = "badge badge-blue";
      pill.textContent = `📍 ${label}: ${State.incident.lat.toFixed(4)}°N, ${State.incident.lon.toFixed(4)}°E`;
    }

    // Show action buttons
    showElement("btn-confirm-incident", "inline-flex");
    showElement("btn-clear-incident", "inline-flex");
    showElement("btn-send-to-sim", "inline-flex");
    showElement("incident-coords-bar", "flex");

    // Remove old marker if present
    if (incidentMarker && facMap) {
      facMap.removeLayer(incidentMarker);
    }

    // Distinct Pulsing Red/Black Marker
    const icon = L.divIcon({
      className: "incident-marker-icon",
      html: '<div class="incident-pin-pulse"></div><div class="incident-pin-core"></div>',
      iconSize: [20, 20],
      iconAnchor: [10, 10],
    });

    if (facMap) {
      incidentMarker = L.marker([lat, lon], {
        icon: icon,
        draggable: true,
        zIndexOffset: 1000,
      }).addTo(facMap);

      incidentMarker.bindPopup(`<b>🚨 Incident Origin</b><br/>${label}<br/>${lat.toFixed(5)}°N, ${lon.toFixed(5)}°E`);

      // Drag event live updates
      incidentMarker.on("drag", (e) => {
        const p = e.target.getLatLng();
        if (latInp) latInp.value = p.lat.toFixed(5);
        if (lonInp) lonInp.value = p.lng.toFixed(5);
      });

      incidentMarker.on("dragend", (e) => {
        const p = e.target.getLatLng();
        placeIncidentMarker(p.lat, p.lng, "Selected Map Point");
      });
    }

    // Refresh selected facility distance if card is open
    if (State.selectedFacility) {
      showFacilityDetailsCard(State.selectedFacility);
    }

    updateSimulationCandidateCount();
  }

  function confirmIncidentLocation() {
    const pill = document.getElementById("incident-status-pill");
    if (pill) {
      pill.className = "badge badge-green";
      pill.textContent = `✓ Incident Confirmed (${State.incident.lat.toFixed(4)}°N, ${State.incident.lon.toFixed(4)}°E)`;
    }
  }

  function clearIncidentLocation() {
    if (incidentMarker && facMap) {
      facMap.removeLayer(incidentMarker);
      incidentMarker = null;
    }
    State.incident.isSet = false;
    State.incident.lat = null;
    State.incident.lon = null;
    State.incident.label = null;

    const latInp = document.getElementById("incident-lat-input");
    const lonInp = document.getElementById("incident-lon-input");
    if (latInp) latInp.value = "";
    if (lonInp) lonInp.value = "";

    const pill = document.getElementById("incident-status-pill");
    if (pill) {
      pill.className = "badge badge-gray";
      pill.textContent = "No incident placed";
    }

    hideElement("btn-confirm-incident");
    hideElement("btn-clear-incident");
    hideElement("btn-send-to-sim");
    hideElement("incident-coords-bar");

    const distBox = document.getElementById("sel-fac-distance-box");
    if (distBox) distBox.style.display = "none";

    setIncidentSelectMode(false);
    updateSimulationUI();
  }

  function showFacilityDetailsCard(fac) {
    State.selectedFacility = fac;
    const card = document.getElementById("selected-facility-card");
    if (!card) return;

    card.style.display = "block";
    const color = AGENCY_COLORS[fac.agency] || "#2563eb";
    card.style.borderLeftColor = color;

    setText("sel-fac-name", fac.facility_name);
    setText("sel-fac-agency", fac.agency_label);
    const agencyEl = document.getElementById("sel-fac-agency");
    if (agencyEl) agencyEl.style.color = color;
    setText("sel-fac-id", fac.facility_id);
    setText("sel-fac-coords", `${fac.latitude.toFixed(5)}°N, ${fac.longitude.toFixed(5)}°E`);

    // Distance calculation from incident
    const distBox = document.getElementById("sel-fac-distance-box");
    if (distBox) {
      if (State.incident.isSet) {
        const d = haversineKm(
          State.incident.lat,
          State.incident.lon,
          fac.latitude,
          fac.longitude
        );
        setText("sel-fac-dist-val", `${d.toFixed(2)} km`);
        distBox.style.display = "block";
      } else {
        distBox.style.display = "none";
      }
    }
  }

  // --------------------------------------------------------------------------
  // Global MST Network Visualization
  // --------------------------------------------------------------------------

  function initMstMap() {
    const container = document.getElementById("mst-leaflet-map");
    if (!container || mstMap) return;

    mstMap = L.map("mst-leaflet-map", {
      center: [12.9716, 77.5946],
      zoom: 12,
      zoomControl: true,
    });

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 18,
      attribution: "&copy; OpenStreetMap contributors | Bengaluru MST Model",
    }).addTo(mstMap);

    mstEdgesLayer = L.layerGroup().addTo(mstMap);
    mstNodesLayer = L.layerGroup().addTo(mstMap);

    loadAndRenderMst(State.mstAlgorithm);
  }

  async function loadAndRenderMst(algo = "kruskal") {
    if (!mstMap || !mstEdgesLayer) return;

    showLoader("Loading Global MST...", `Retrieving 1,254 ${algo.toUpperCase()} edges`);

    try {
      if (!State.mstCache[algo]) {
        const data = await API.getFullMST(algo);
        State.mstCache[algo] = data;
      }

      const mstData = State.mstCache[algo];
      mstEdgesLayer.clearLayers();
      mstNodesLayer.clearLayers();

      const edgeColor = algo === "kruskal" ? "#2563eb" : "#9333ea";

      // Render 1,254 PolyLines
      (mstData.edges || []).forEach((edge) => {
        if (edge.u_lat == null || edge.v_lat == null) return;

        const poly = L.polyline(
          [
            [edge.u_lat, edge.u_lon],
            [edge.v_lat, edge.v_lon],
          ],
          {
            color: edgeColor,
            weight: 2.2,
            opacity: 0.72,
          }
        );

        // Hover & click highlight
        poly.on("mouseover", () => {
          poly.setStyle({ weight: 4.5, opacity: 1.0, color: "#ea580c" });
        });
        poly.on("mouseout", () => {
          if (State.mstSelectedEdge !== edge) {
            poly.setStyle({ weight: 2.2, opacity: 0.72, color: edgeColor });
          }
        });
        poly.on("click", () => {
          State.mstSelectedEdge = edge;
          showEdgeDetailCard(edge, algo);
        });

        mstEdgesLayer.addLayer(poly);
      });

      hideLoader();
    } catch (err) {
      console.error("Failed to load MST:", err);
      showErrorBanner(`Unable to render global MST: ${err.message}`);
      hideLoader();
    }
  }

  function showEdgeDetailCard(edge, algo) {
    const card = document.getElementById("mst-edge-detail-card");
    if (!card) return;

    card.style.display = "block";
    setText("edge-u-name", edge.u_name || "Facility U");
    setText("edge-u-id", edge.u);
    setText("edge-v-name", edge.v_name || "Facility V");
    setText("edge-v-id", edge.v);
    setText("edge-weight", `${edge.weight_km.toFixed(4)} km`);
    setText("edge-algo", algo === "kruskal" ? "Kruskal's Algorithm" : "Prim's Algorithm");

    const rationaleEl = document.getElementById("edge-rationale");
    if (rationaleEl) {
      if (algo === "kruskal") {
        rationaleEl.innerHTML = `<strong>Cycle Property:</strong> Edge with weight ${edge.weight_km.toFixed(4)} km connects disjoint components without creating a cycle. Verified against LCA binary lifting (0 cycle violations across 785,631 candidate edges).`;
      } else {
        rationaleEl.innerHTML = `<strong>Cut Property:</strong> Selected as the minimal crossing edge across the cut separating the visited tree set from unvisited facilities.`;
      }
    }
  }

  function bindMstEvents() {
    const btnKruskal = document.getElementById("btn-mst-kruskal");
    const btnPrim = document.getElementById("btn-mst-prim");

    if (btnKruskal && btnPrim) {
      btnKruskal.addEventListener("click", () => {
        btnKruskal.classList.add("active");
        btnPrim.classList.remove("active");
        State.mstAlgorithm = "kruskal";
        loadAndRenderMst("kruskal");
      });

      btnPrim.addEventListener("click", () => {
        btnPrim.classList.add("active");
        btnKruskal.classList.remove("active");
        State.mstAlgorithm = "prim";
        loadAndRenderMst("prim");
      });
    }

    const btnCloseEdge = document.getElementById("btn-close-edge-card");
    if (btnCloseEdge) {
      btnCloseEdge.addEventListener("click", () => {
        const card = document.getElementById("mst-edge-detail-card");
        if (card) card.style.display = "none";
        State.mstSelectedEdge = null;
      });
    }
  }

  // --------------------------------------------------------------------------
  // Emergency Simulation 6-Step Workflow
  // --------------------------------------------------------------------------

  function updateSimulationUI() {
    // Sync incident info
    if (State.incident.isSet && State.incident.lat != null && State.incident.lon != null) {
      setText(
        "sim-incident-coords",
        `${State.incident.lat.toFixed(5)}° N, ${State.incident.lon.toFixed(5)}° E (${State.incident.label || "Custom Point"})`
      );
      setText("sum-incident", `${State.incident.label || "Custom Point"} (${State.incident.lat.toFixed(4)}°N, ${State.incident.lon.toFixed(4)}°E)`);
    } else {
      setText(
        "sim-incident-coords",
        "No incident location configured. Please drop a pin on the Facilities Map or select a landmark preset below."
      );
      setText("sum-incident", "No incident configured");
    }

    // Sync candidate count
    updateSimulationCandidateCount();
  }

  function updateSimulationCandidateCount() {
    if (!State.facilities.length) return;

    if (!State.incident.isSet || State.incident.lat == null || State.incident.lon == null) {
      setText("sim-candidate-count", "Select an incident location to evaluate candidate facilities.");
      setText("sim-radius-display", `${State.simRadiusKm.toFixed(1)} km`);
      setText("sum-radius", `${State.simRadiusKm.toFixed(1)} km`);
      return;
    }

    const lat = State.incident.lat;
    const lon = State.incident.lon;
    const radius = State.simRadiusKm;
    const agency = State.simAgency;

    const matched = State.facilities.filter((f) => {
      if (f.agency !== agency) return false;
      const d = haversineKm(lat, lon, f.latitude, f.longitude);
      return d <= radius;
    });

    const lbl = AGENCY_LABELS[agency] || "facilities";
    setText("sim-candidate-count", `${matched.length} ${lbl.toLowerCase()}s within ${radius.toFixed(1)} km`);
    setText("sim-radius-display", `${radius.toFixed(1)} km`);
    setText("sum-radius", `${radius.toFixed(1)} km`);
  }

  // --------------------------------------------------------------------------
  // Public App Namespace
  // --------------------------------------------------------------------------

  window.App = {
    setIncidentLocation(lat, lon, label) {
      placeIncidentMarker(lat, lon, label);
      updateSimulationUI();
      if (facMap) facMap.setView([lat, lon], 14);
    },

    selectCategory(catKey) {
      State.simCategory = catKey;
      document.querySelectorAll(".category-card").forEach((card) => {
        if (card.getAttribute("data-category") === catKey) {
          card.classList.add("active");
        } else {
          card.classList.remove("active");
        }
      });

      // Recommend agency
      if (catKey === "medical" || catKey === "traffic") {
        this.selectAgency("hospital");
      } else if (catKey === "fire") {
        this.selectAgency("fire_station");
      } else if (catKey === "police") {
        this.selectAgency("police_station");
      }
    },

    selectAgency(agencyKey) {
      State.simAgency = agencyKey;
      document.querySelectorAll(".agency-card").forEach((card) => {
        card.classList.remove("active");
      });

      const activeCard = document.getElementById(`sim-agency-${agencyKey.split("_")[0]}`);
      if (activeCard) activeCard.classList.add("active");

      const rateInfo = AGENCY_RATES[agencyKey] || { rate: 12.50, vehicle: "Emergency Vehicle" };
      setText("sum-agency", `${AGENCY_LABELS[agencyKey]} (${rateInfo.vehicle} &bull; ₹${rateInfo.rate.toFixed(2)}/km)`);

      updateSimulationCandidateCount();
    },

    onRadiusChange(val) {
      State.simRadiusKm = parseFloat(val);
      updateSimulationCandidateCount();
    },

    selectMode(modeKey) {
      State.simMode = modeKey;
      document.querySelectorAll(".mode-card").forEach((card) => {
        if (card.getAttribute("data-mode") === modeKey) {
          card.classList.add("active");
        } else {
          card.classList.remove("active");
        }
      });

      const modeNames = {
        "time": "Minimum Response Time (min T)",
        "distance": "Minimum Road Distance (min D)",
        "cost": "Minimum Fuel Cost (min C)",
        "balanced": "Balanced Multi-Objective (0.50 T + 0.50 D)",
      };
      setText("sum-mode", modeNames[modeKey] || modeKey);
    },

    runSimulationPreview() {
      const resultsContainer = document.getElementById("sim-results-output");
      const listEl = document.getElementById("sim-ranked-facilities-list");
      const statusEl = document.getElementById("sim-exec-status");

      if (!resultsContainer || !listEl) return;

      if (!State.incident.isSet || State.incident.lat == null || State.incident.lon == null) {
        if (statusEl) statusEl.textContent = "Please place or select an incident location on the Facilities Map first.";
        resultsContainer.style.display = "none";
        return;
      }

      const lat = State.incident.lat;
      const lon = State.incident.lon;
      const radius = State.simRadiusKm;
      const agency = State.simAgency;
      const rateInfo = AGENCY_RATES[agency] || { rate: 12.50, vehicle: "Fleet Unit", speedKmh: 40 };

      // Candidate selection
      let candidates = State.facilities.filter((f) => {
        if (f.agency !== agency) return false;
        const d = haversineKm(lat, lon, f.latitude, f.longitude);
        f._dist = d;
        return d <= radius;
      });

      if (candidates.length === 0) {
        statusEl.textContent = `No ${AGENCY_LABELS[agency]} found within ${radius.toFixed(1)} km. Increase search radius.`;
        resultsContainer.style.display = "none";
        return;
      }

      // Rank by distance (straight-line proxy for Stage 1.5 preview, to be replaced by full OSRM in Phase 2/3)
      candidates.sort((a, b) => a._dist - b._dist);
      const top3 = candidates.slice(0, 3);

      listEl.innerHTML = "";
      top3.forEach((fac, idx) => {
        const distKm = fac._dist;
        const estCost = distKm * rateInfo.rate;
        const estTimeMin = (distKm / rateInfo.speedKmh) * 60;

        const row = document.createElement("div");
        row.className = "ranked-card";
        row.innerHTML = `
          <div style="display:flex; align-items:center; gap:14px;">
            <div class="ranked-rank">#${idx + 1}</div>
            <div class="ranked-details">
              <div class="ranked-name">${escapeHtml(fac.facility_name)}</div>
              <div class="ranked-meta">ID: <code>${fac.facility_id}</code> &bull; ${rateInfo.vehicle}</div>
            </div>
          </div>
          <div class="ranked-metrics">
            <div class="ranked-dist">${distKm.toFixed(2)} km (Haversine)</div>
            <div class="ranked-cost">₹${estCost.toFixed(2)} &bull; ~${estTimeMin.toFixed(1)} min</div>
          </div>
        `;
        listEl.appendChild(row);
      });

      resultsContainer.style.display = "block";
      statusEl.textContent = `Preliminary preview complete: ${candidates.length} candidates evaluated, top 3 staged (straight-line Haversine proxy).`;
    },
  };

  // --------------------------------------------------------------------------
  // Helpers
  // --------------------------------------------------------------------------

  function roundCoord(v) {
    return Math.round(v * 100000) / 100000;
  }

  function setText(id, val) {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
  }

  function setBarWidth(id, pct) {
    const el = document.getElementById(id);
    if (el) el.style.width = `${pct}%`;
  }

  function showElement(id, display = "block") {
    const el = document.getElementById(id);
    if (el) el.style.display = display;
  }

  function hideElement(id) {
    const el = document.getElementById(id);
    if (el) el.style.display = "none";
  }

  function showLoader(title, subtext) {
    const el = document.getElementById("global-loader");
    if (el) {
      el.classList.remove("hidden");
      const t = el.querySelector(".loader-text");
      const s = el.querySelector(".loader-subtext");
      if (t) t.textContent = title;
      if (s) s.textContent = subtext;
    }
  }

  function hideLoader() {
    const el = document.getElementById("global-loader");
    if (el) el.classList.add("hidden");
  }

  function showErrorBanner(msg) {
    const banner = document.getElementById("api-error-banner");
    const msgEl = document.getElementById("api-error-message");
    if (banner && msgEl) {
      msgEl.textContent = msg;
      banner.style.display = "flex";
    }
  }

  function hideErrorBanner() {
    const banner = document.getElementById("api-error-banner");
    if (banner) banner.style.display = "none";
  }

  function escapeHtml(str) {
    return String(str || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
})();
