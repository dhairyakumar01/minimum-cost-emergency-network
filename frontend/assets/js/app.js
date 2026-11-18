/**
 * Main Application Module — Bengaluru Emergency Network (Phase 1.7)
 * Handles UI interactions, Leaflet maps, multi-scale clustering, incident placement,
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
    compromiseK: 5,
    simRequestCounter: 0,
    lastCompletedFingerprint: null,
    isSimulationStale: false,
    activeScenarioData: null,
    
    // MST State
    mstAlgorithm: "kruskal",
    mstCache: { kruskal: null, prim: null },
    mstSelectedEdge: null,

    // Algorithm Construction Simulator State
    simSubtab: "sim",
    simGraphContext: "global",
    simAlgorithm: "kruskal",
    simSpeedMs: 200,
    simIsPlaying: false,
    simCurrentStep: 0,
    simTraceData: null,
    simTimer: null,
    simCompareContext: "global",
  };

  // Leaflet Map Instances
  let overviewMap = null;
  let facMap = null;
  let facMarkersLayer = null;
  let incidentMarker = null;

  let mstMap = null;
  let mstEdgesLayer = null;
  let mstNodesLayer = null;

  // Simulator Map Instances & Layers
  let simMap = null;
  let simNodesLayer = null;
  let simAcceptedEdgesLayer = null;
  let simEvaluatedEdgeLayer = null;
  let simRejectedEdgeLayer = null;
  let simIncidentMarkerLayer = null;
  let simNodeMarkers = {};
  let simTraceCache = {};

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
  // Lifecycle Initialization & Global Error Boundaries
  // --------------------------------------------------------------------------

  // Global uncaught error protection (Zero Blank-Screen Requirement)
  window.addEventListener("error", (event) => {
    console.error("Global UI Error caught:", event.error || event.message);
    showErrorBanner(`A component encountered an issue: ${event.message || "Unknown error"}. Other features remain functional.`);
  });

  window.addEventListener("unhandledrejection", (event) => {
    console.error("Unhandled Promise Rejection caught:", event.reason);
    const msg = event.reason?.message || (typeof event.reason === "string" ? event.reason : "Network operation failed");
    showErrorBanner(`Operation warning: ${msg}. Click retry or check connection.`);
  });

  document.addEventListener("DOMContentLoaded", () => {
    Navigation.init();
    initApp();

    // Wire up retry connection button
    document.querySelectorAll(".btn-retry-connection").forEach((btn) => {
      btn.addEventListener("click", () => {
        hideErrorBanner();
        initApp();
      });
    });

    // Map invalidation on navigation
    Navigation.onNavigate((sectionId) => {
      try {
        if (sectionId === "dashboard") {
          setTimeout(() => {
            if (overviewMap) overviewMap.invalidateSize();
          }, 120);
        } else if (sectionId === "facilities-map") {
          setTimeout(() => {
            if (!facMap) {
              initFacilitiesMap();
            }
            if (facMap) {
              facMap.invalidateSize();
            }
          }, 100);
        } else if (sectionId === "mst-network") {
          setTimeout(() => {
            if (State.simSubtab === "sim") {
              if (!simMap) {
                initSimMap();
              }
              if (simMap) {
                simMap.invalidateSize();
              }
              if (!State.simTraceData) {
                loadSimulatorTrace(State.simGraphContext, State.simAlgorithm);
              }
            } else if (State.simSubtab === "compare") {
              loadMstComparison(State.simCompareContext);
            } else if (State.simSubtab === "static") {
              if (!mstMap) {
                initMstMap();
              }
              if (mstMap) {
                mstMap.invalidateSize();
              }
            }
          }, 100);
        } else if (sectionId === "simulation") {
          updateSimulationUI();
        }
      } catch (navErr) {
        console.warn("Navigation map refresh caught safely:", navErr);
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
      initOverviewMap();

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

  /**
   * Dashboard GIS Overview Mini-Map
   */
  function initOverviewMap() {
    try {
      const container = document.getElementById("dashboard-overview-map");
      if (!container || overviewMap || typeof L === "undefined") return;

      overviewMap = L.map("dashboard-overview-map", {
        center: [12.9716, 77.5946],
        zoom: 11,
        zoomControl: false,
        attributionControl: false,
      });

      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 16,
      }).addTo(overviewMap);

      // Render sample facility markers
      const step = Math.ceil(State.facilities.length / 150);
      for (let i = 0; i < State.facilities.length; i += step) {
        const fac = State.facilities[i];
        const color = AGENCY_COLORS[fac.agency] || "#2563eb";
        L.circleMarker([fac.latitude, fac.longitude], {
          radius: 3,
          fillColor: color,
          color: "#ffffff",
          weight: 0.8,
          fillOpacity: 0.8,
        }).addTo(overviewMap);
      }
    } catch (err) {
      console.warn("Overview mini-map fallback:", err);
    }
  }

  // --------------------------------------------------------------------------
  // Facilities Map & Incident Selection
  // --------------------------------------------------------------------------

  function initFacilitiesMap() {
    try {
      const container = document.getElementById("leaflet-map");
      if (!container || facMap || typeof L === "undefined") return;

      facMap = L.map("leaflet-map", {
        center: [12.9716, 77.5946],
        zoom: 12,
        zoomControl: true,
      });

      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 18,
        attribution: "&copy; OpenStreetMap contributors | DMGT Bengaluru Research",
      }).addTo(facMap);

      // Marker Clustering Group
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
      if (State.incident.isSet && State.incident.lat != null && State.incident.lon != null) {
        placeIncidentMarker(State.incident.lat, State.incident.lon, State.incident.label);
      }

      // Map click handler for incident placement
      facMap.on("click", (e) => {
        if (State.incidentSelectMode) {
          placeIncidentMarker(e.latlng.lat, e.latlng.lng);
          setIncidentSelectMode(false);
        }
      });

      setTimeout(() => {
        if (facMap) facMap.invalidateSize();
      }, 200);
    } catch (err) {
      console.error("Facilities map initialization failed:", err);
      showErrorBanner("Map tiles could not be initialized. Facilities catalog remains accessible in list/table views.");
    }
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
      if (State.activeSearchTerm && filtered.length === 0) {
        badge.textContent = "No registered emergency facility matched this query.";
        badge.className = "badge badge-amber";
      } else {
        badge.textContent = `Displaying ${filtered.length.toLocaleString()} of ${State.facilities.length.toLocaleString()} facilities`;
        badge.className = "badge badge-gray";
      }
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

    // Facility Search (Registered Facilities Only)
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

      searchInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
          const q = searchInput.value.trim().toLowerCase();
          if (q.length >= 2) {
            const match = State.facilities.find(
              (f) =>
                f.facility_name.toLowerCase().includes(q) ||
                f.facility_id.toLowerCase().includes(q)
            );
            if (match) {
              if (facMap) facMap.setView([match.latitude, match.longitude], 15);
              showFacilityDetailsCard(match);
            }
          }
        }
      });
    }

    // Landmark / Address Geocoding Search (Incident Location Pinning)
    const incSearchInput = document.getElementById("incident-location-search");
    if (incSearchInput) {
      incSearchInput.addEventListener("keydown", async (e) => {
        if (e.key === "Enter") {
          const q = incSearchInput.value.trim();
          if (q.length >= 2) {
            try {
              const res = await API.geocode(q);
              const candidates = res.candidates || [];
              if (candidates.length > 0) {
                const topCand = candidates[0];
                placeIncidentMarker(topCand.latitude, topCand.longitude, topCand.label);
                if (facMap) facMap.setView([topCand.latitude, topCand.longitude], 15);
              }
            } catch (err) {
              console.warn("Incident landmark query failed:", err);
            }
          }
        }
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
        btn.textContent = "📍 Place Incident Pin";
        btn.classList.remove("btn-primary");
        btn.classList.add("btn-outline");
      }
    }

    if (coordsBar) {
      coordsBar.style.display = active || State.incident.isSet ? "flex" : "none";
    }
  }

  function getSimulationFingerprint() {
    if (!State.incident.isSet || State.incident.lat == null || State.incident.lon == null) {
      return "unset";
    }
    return [
      roundCoord(State.incident.lat).toFixed(5),
      roundCoord(State.incident.lon).toFixed(5),
      State.simCategory,
      State.simAgency,
      (State.simRadiusKm || 5.0).toFixed(1),
      State.simMode,
      State.simMode === "compromise" ? (State.compromiseK !== undefined ? State.compromiseK : 5) : "na",
    ].join("|");
  }

  function invalidateSimulationResults(reason) {
    if (!State.activeScenarioData) return;
    const currentFp = getSimulationFingerprint();
    if (currentFp !== State.lastCompletedFingerprint) {
      State.isSimulationStale = true;
      const staleEl = document.getElementById("sim-stale-notice");
      if (staleEl) staleEl.style.display = "flex";
    } else {
      State.isSimulationStale = false;
      const staleEl = document.getElementById("sim-stale-notice");
      if (staleEl) staleEl.style.display = "none";
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

    // Distinct Pulsing Red Marker
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
    invalidateSimulationResults("incident_placed");
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
    invalidateSimulationResults("incident_cleared");
  }

  function showFacilityDetailsCard(fac) {
    State.selectedFacility = fac;
    const card = document.getElementById("selected-facility-card");
    if (!card) return;

    card.style.display = "block";
    const color = AGENCY_COLORS[fac.agency] || "#2563eb";

    setText("sel-fac-name", fac.facility_name);
    setText("sel-fac-agency", fac.agency_label);
    const agencyEl = document.getElementById("sel-fac-agency");
    if (agencyEl) agencyEl.style.color = color;
    setText("sel-fac-id", fac.facility_id);
    setText("sel-fac-coords", `${fac.latitude.toFixed(5)}°N, ${fac.longitude.toFixed(5)}°E`);

    // Distance calculation from incident
    const distBox = document.getElementById("sel-fac-distance-box");
    if (distBox) {
      if (State.incident.isSet && State.incident.lat != null && State.incident.lon != null) {
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
    try {
      const container = document.getElementById("mst-leaflet-map");
      if (!container || mstMap || typeof L === "undefined") return;

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
    } catch (err) {
      console.error("MST map initialization failed:", err);
      showErrorBanner("Global MST map view unavailable. Algorithm analysis tables remain accessible.");
    }
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
        rationaleEl.textContent = `Connects two separate components with minimum weight (${edge.weight_km.toFixed(4)} km) without creating a cycle.`;
      } else {
        rationaleEl.textContent = `Selected as the minimal crossing edge across the cut separating the visited tree set from unvisited facilities.`;
      }
    }
  }

  // --------------------------------------------------------------------------
  // Algorithm Construction Simulator & Comparison Suite
  // --------------------------------------------------------------------------

  function initSimMap() {
    try {
      const container = document.getElementById("sim-leaflet-map");
      if (!container || simMap || typeof L === "undefined") return;

      simMap = L.map("sim-leaflet-map", {
        center: [12.9716, 77.5946],
        zoom: 11,
        zoomControl: true,
      });

      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 18,
        attribution: "&copy; OpenStreetMap contributors | MST Simulator",
      }).addTo(simMap);

      simAcceptedEdgesLayer = L.layerGroup().addTo(simMap);
      simEvaluatedEdgeLayer = L.layerGroup().addTo(simMap);
      simRejectedEdgeLayer = L.layerGroup().addTo(simMap);
      simNodesLayer = L.layerGroup().addTo(simMap);
      simIncidentMarkerLayer = L.layerGroup().addTo(simMap);
    } catch (err) {
      console.error("Simulator map initialization failed:", err);
    }
  }

  function switchMstSubtab(targetSubtab) {
    State.simSubtab = targetSubtab;

    // Update active tab button
    document.querySelectorAll(".mst-tab-btn").forEach((btn) => {
      btn.classList.toggle("active", btn.getAttribute("data-target") === `mst-view-${targetSubtab}`);
    });

    // Update subview visibility
    const views = {
      sim: document.getElementById("mst-view-sim"),
      compare: document.getElementById("mst-view-compare"),
      static: document.getElementById("mst-view-static"),
    };

    Object.entries(views).forEach(([k, el]) => {
      if (el) el.style.display = k === targetSubtab ? "block" : "none";
    });

    if (targetSubtab === "sim") {
      setTimeout(() => {
        if (!simMap) initSimMap();
        if (simMap) simMap.invalidateSize();
        if (!State.simTraceData) {
          loadSimulatorTrace(State.simGraphContext, State.simAlgorithm);
        }
      }, 50);
    } else if (targetSubtab === "compare") {
      loadMstComparison(State.simCompareContext);
    } else if (targetSubtab === "static") {
      setTimeout(() => {
        if (!mstMap) initMstMap();
        if (mstMap) mstMap.invalidateSize();
      }, 50);
    }
  }

  async function loadSimulatorTrace(graphContext = "global", algorithm = "kruskal") {
    pauseSimulator();
    State.simGraphContext = graphContext;
    State.simAlgorithm = algorithm;

    // UI Toggle update
    document.querySelectorAll("#sim-context-toggle .sim-btn").forEach((btn) => {
      btn.classList.toggle("active", btn.getAttribute("data-context") === graphContext);
    });
    document.querySelectorAll("#sim-algo-toggle .sim-btn").forEach((btn) => {
      btn.classList.toggle("active", btn.getAttribute("data-algo") === algorithm);
    });

    // Show loading state
    const telemStatus = document.getElementById("sim-telem-status");
    if (telemStatus) {
      telemStatus.textContent = "LOADING...";
      telemStatus.className = "sim-telem-val badge badge-blue";
    }

    try {
      const cacheKey = `${graphContext}_${algorithm}`;
      let data = simTraceCache[cacheKey];
      if (!data) {
        showLoader("Loading Trace...", `Retrieving ${algorithm.toUpperCase()} execution trace`);
        data = await API.getMstTrace(graphContext, algorithm, State.activeScenarioId);
        simTraceCache[cacheKey] = data;
        hideLoader();
      }

      State.simTraceData = data;
      State.simCurrentStep = 0;

      // Update Map elements
      if (!simMap) initSimMap();
      if (simMap) {
        simAcceptedEdgesLayer.clearLayers();
        simEvaluatedEdgeLayer.clearLayers();
        simRejectedEdgeLayer.clearLayers();
        simNodesLayer.clearLayers();
        simIncidentMarkerLayer.clearLayers();
        simNodeMarkers = {};

        const vertices = data.vertices || [];
        const isDense = vertices.length > 100;
        const bounds = L.latLngBounds();

        vertices.forEach((v) => {
          if (v.lat == null || v.lon == null) return;
          const isIncident = v.id === "incident_0" || v.id.startsWith("inc_");
          const latlng = [v.lat, v.lon];
          bounds.extend(latlng);

          if (isIncident) {
            const incMarker = L.circleMarker(latlng, {
              radius: 8,
              fillColor: "#dc2626",
              color: "#ffffff",
              weight: 2,
              fillOpacity: 1.0,
            }).bindTooltip(`<strong>🚨 Incident Origin</strong><br>${v.name || v.id}`);
            simIncidentMarkerLayer.addLayer(incMarker);
          } else {
            const marker = L.circleMarker(latlng, {
              radius: isDense ? 3 : 5.5,
              fillColor: "#94a3b8",
              color: "#64748b",
              weight: 1,
              fillOpacity: 0.85,
            }).bindTooltip(`<strong>${v.name || v.id}</strong><br><span style="font-family:var(--font-mono); font-size:0.72rem; color:#64748b;">${v.id}</span>`);
            simNodesLayer.addLayer(marker);
            simNodeMarkers[v.id] = marker;
          }
        });

        if (bounds.isValid()) {
          simMap.fitBounds(bounds, { padding: [25, 25] });
        }
      }

      // Configure scrubber
      const events = data.events || [];
      const scrubber = document.getElementById("sim-scrubber");
      if (scrubber) {
        scrubber.min = "0";
        scrubber.max = String(Math.max(0, events.length - 1));
        scrubber.value = "0";
      }
      setText("sim-total-steps", String(events.length));

      // Telemetry label setup (Kruskal uses components, Prim uses visited cut)
      const compLabel = document.getElementById("sim-telem-comp-label");
      if (compLabel) {
        compLabel.textContent = algorithm === "kruskal" ? "Components" : "Visited Cut Nodes";
      }

      // Render initial step (0)
      renderSimulatorStep(0);
    } catch (err) {
      console.error("Failed to load trace:", err);
      hideLoader();
      showErrorBanner(`Failed to load algorithm trace: ${err.message}`);
      if (telemStatus) {
        telemStatus.textContent = "ERROR";
        telemStatus.className = "sim-telem-val badge badge-danger";
      }
    }
  }

  function renderSimulatorStep(stepIndex) {
    if (!State.simTraceData || !State.simTraceData.events) return;
    const events = State.simTraceData.events;
    if (stepIndex < 0 || stepIndex >= events.length) return;

    const prevIndex = State.simCurrentStep;
    State.simCurrentStep = stepIndex;

    // Update scrubber UI
    const scrubber = document.getElementById("sim-scrubber");
    if (scrubber && scrubber.value !== String(stepIndex)) {
      scrubber.value = String(stepIndex);
    }
    setText("sim-step-num", String(stepIndex));

    const curEv = events[stepIndex];

    // Map Updates:
    if (simMap) {
      // Clear evaluated & rejected overlays
      simEvaluatedEdgeLayer.clearLayers();
      simRejectedEdgeLayer.clearLayers();

      const isSequentialNext = stepIndex === prevIndex + 1;

      if (!isSequentialNext) {
        // Full rebuild of accepted edges
        simAcceptedEdgesLayer.clearLayers();

        // Reset non-incident nodes to unvisited grey
        Object.values(simNodeMarkers).forEach((marker) => {
          marker.setStyle({ fillColor: "#94a3b8", color: "#64748b" });
        });

        // Replay all accepted edges up to stepIndex - 1
        for (let i = 0; i < stepIndex; i++) {
          const ev = events[i];
          if (ev.accepted && ev.u_lat != null && ev.v_lat != null) {
            const poly = L.polyline([[ev.u_lat, ev.u_lon], [ev.v_lat, ev.v_lon]], {
              color: "#16a34a",
              weight: 2.4,
              opacity: 0.85,
            });
            simAcceptedEdgesLayer.addLayer(poly);

            if (simNodeMarkers[ev.source_vertex_id]) {
              simNodeMarkers[ev.source_vertex_id].setStyle({ fillColor: "#16a34a", color: "#14532d" });
            }
            if (simNodeMarkers[ev.target_vertex_id]) {
              simNodeMarkers[ev.target_vertex_id].setStyle({ fillColor: "#16a34a", color: "#14532d" });
            }
          }
        }
      }

      // Now process the current step event (stepIndex)
      if (curEv.u_lat != null && curEv.v_lat != null) {
        const lineCoords = [[curEv.u_lat, curEv.u_lon], [curEv.v_lat, curEv.v_lon]];

        if (curEv.accepted) {
          // Highlight in blue as currently evaluated edge
          const evalPoly = L.polyline(lineCoords, {
            color: "#2563eb",
            weight: 4.2,
            opacity: 1.0,
          });
          simEvaluatedEdgeLayer.addLayer(evalPoly);

          // Add to accepted layer
          const permPoly = L.polyline(lineCoords, {
            color: "#16a34a",
            weight: 2.4,
            opacity: 0.85,
          });
          simAcceptedEdgesLayer.addLayer(permPoly);

          // Endpoints turn green
          if (simNodeMarkers[curEv.source_vertex_id]) {
            simNodeMarkers[curEv.source_vertex_id].setStyle({ fillColor: "#16a34a", color: "#14532d" });
          }
          if (simNodeMarkers[curEv.target_vertex_id]) {
            simNodeMarkers[curEv.target_vertex_id].setStyle({ fillColor: "#16a34a", color: "#14532d" });
          }
        } else if (curEv.event_type === "EDGE_REJECTED") {
          // Candidate edge rejected (e.g. cycle): dashed red line
          const rejPoly = L.polyline(lineCoords, {
            color: "#dc2626",
            weight: 3.5,
            dashArray: "6, 6",
            opacity: 0.95,
          });
          simRejectedEdgeLayer.addLayer(rejPoly);
        }
      }
    }

    // Telemetry updates
    const telemStatus = document.getElementById("sim-telem-status");
    if (telemStatus) {
      if (curEv.event_type === "COMPLETED") {
        telemStatus.textContent = "COMPLETED";
        telemStatus.className = "sim-telem-val badge badge-success";
      } else if (curEv.accepted) {
        telemStatus.textContent = State.simIsPlaying ? "PLAYING" : "ACCEPTED";
        telemStatus.className = "sim-telem-val badge badge-success";
      } else if (curEv.event_type === "EDGE_REJECTED") {
        telemStatus.textContent = "CYCLE REJECTED";
        telemStatus.className = "sim-telem-val badge badge-danger";
      } else {
        telemStatus.textContent = "START";
        telemStatus.className = "sim-telem-val badge badge-blue";
      }
    }

    setText("sim-telem-weight", curEv.current_tree_weight_formatted || "0.0000 km");
    setText("sim-telem-edges", `${curEv.accepted_edge_count || 0} / ${curEv.total_required_edges || 0}`);
    setText("sim-telem-remaining", String(curEv.remaining_edge_count ?? 0));

    if (State.simAlgorithm === "kruskal") {
      setText("sim-telem-components", String(curEv.component_count ?? 0));
    } else {
      setText("sim-telem-components", String(curEv.visited_vertex_count ?? 0));
    }

    // Explanation Panel Updates
    setText("sim-step-type-badge", `Event #${curEv.sequence_number || stepIndex} (${curEv.event_type})`);
    
    const decisionBadge = document.getElementById("sim-step-decision-badge");
    if (decisionBadge) {
      if (curEv.accepted) {
        decisionBadge.textContent = "ACCEPTED (TREE LINK)";
        decisionBadge.className = "badge badge-success";
      } else if (curEv.event_type === "EDGE_REJECTED") {
        decisionBadge.textContent = "REJECTED (CYCLE / STALE)";
        decisionBadge.className = "badge badge-danger";
      } else if (curEv.event_type === "COMPLETED") {
        decisionBadge.textContent = "CONSTRUCTION COMPLETE";
        decisionBadge.className = "badge badge-success";
      } else {
        decisionBadge.textContent = "INITIALIZATION";
        decisionBadge.className = "badge badge-blue";
      }
    }

    setText("sim-step-u-name", curEv.u_name || curEv.source_vertex_id || "Root / Graph");
    setText("sim-step-u-id", curEv.source_vertex_id || "—");
    setText("sim-step-v-name", curEv.v_name || curEv.target_vertex_id || "—");
    setText("sim-step-v-id", curEv.target_vertex_id || "—");
    setText("sim-step-weight", curEv.edge_weight_formatted || "—");

    const principleEl = document.getElementById("sim-step-principle");
    if (principleEl) {
      if (State.simAlgorithm === "kruskal") {
        principleEl.textContent = "Global Edge Sort & Disjoint Set Union (DSU)";
      } else {
        principleEl.textContent = "Priority Queue Cut Crossing Selection";
      }
    }

    const rationaleBox = document.getElementById("sim-step-rationale-box");
    if (rationaleBox) {
      rationaleBox.className = curEv.accepted || curEv.event_type === "COMPLETED" ? "step-rationale-box" : "step-rationale-box rejected";
    }

    const rationaleText = document.getElementById("sim-step-rationale");
    if (rationaleText) {
      rationaleText.textContent = curEv.reason || "Greedy edge evaluation under MST optimality criteria.";
    }
  }

  function playSimulator() {
    if (!State.simTraceData || !State.simTraceData.events) return;
    const max = State.simTraceData.events.length - 1;
    if (State.simCurrentStep >= max) {
      renderSimulatorStep(0);
    }

    State.simIsPlaying = true;
    const playBtn = document.getElementById("btn-sim-play");
    if (playBtn) playBtn.innerHTML = "⏸ Pause";

    clearInterval(State.simTimer);
    State.simTimer = setInterval(() => {
      const nextStep = State.simCurrentStep + 1;
      if (nextStep <= max) {
        renderSimulatorStep(nextStep);
      } else {
        pauseSimulator();
      }
    }, State.simSpeedMs);
  }

  function pauseSimulator() {
    State.simIsPlaying = false;
    clearInterval(State.simTimer);
    State.simTimer = null;
    const playBtn = document.getElementById("btn-sim-play");
    if (playBtn) playBtn.innerHTML = "▶ Play";
  }

  function stepSimulatorNext() {
    pauseSimulator();
    if (!State.simTraceData || !State.simTraceData.events) return;
    const max = State.simTraceData.events.length - 1;
    if (State.simCurrentStep < max) {
      renderSimulatorStep(State.simCurrentStep + 1);
    }
  }

  function stepSimulatorPrev() {
    pauseSimulator();
    if (State.simCurrentStep > 0) {
      renderSimulatorStep(State.simCurrentStep - 1);
    }
  }

  function restartSimulator() {
    pauseSimulator();
    renderSimulatorStep(0);
  }

  async function loadMstComparison(graphContext = "global") {
    State.simCompareContext = graphContext;

    // Toggle UI buttons
    document.querySelectorAll("#cmp-context-toggle .sim-btn").forEach((btn) => {
      btn.classList.toggle("active", btn.getAttribute("data-context") === graphContext);
    });

    try {
      showLoader("Evaluating Parity...", "Comparing Prim vs Kruskal execution and invariants");
      const comp = await API.getMstCompare(graphContext, State.activeScenarioId);
      hideLoader();

      const k = comp.kruskal_summary || {};
      const p = comp.prim_summary || {};
      const parity = comp.parity || {};
      const reqEdges = comp.required_edges ?? k.tree_edges_count ?? 1254;

      setText("cmp-kruskal-weight", parity.kruskal_weight_formatted || `${k.total_tree_weight || 0} ${comp.weight_unit}`);
      setText("cmp-kruskal-edges", `${(k.tree_edges_count ?? reqEdges).toLocaleString()} (V - 1)`);
      const kConn = document.getElementById("cmp-kruskal-connected");
      if (kConn) {
        kConn.textContent = k.is_connected ? "YES" : "FOREST";
        kConn.className = k.is_connected ? "badge badge-success" : "badge badge-gray";
      }

      setText("cmp-prim-weight", parity.prim_weight_formatted || `${p.total_tree_weight || 0} ${comp.weight_unit}`);
      setText("cmp-prim-edges", `${(p.tree_edges_count ?? reqEdges).toLocaleString()} (V - 1)`);
      const pConn = document.getElementById("cmp-prim-connected");
      if (pConn) {
        pConn.textContent = p.is_connected ? "YES" : "FOREST";
        pConn.className = p.is_connected ? "badge badge-success" : "badge badge-gray";
      }

      const summaryEl = document.getElementById("cmp-parity-summary");
      if (summaryEl) {
        summaryEl.textContent = parity.academic_note || "Both algorithms converge to the exact mathematically optimal total weight.";
      }
    } catch (err) {
      console.error("Comparison load failed:", err);
      hideLoader();
      showErrorBanner(`Comparison analysis failed: ${err.message}`);
    }
  }

  function bindMstEvents() {
    // 1. Sub-navigation tabs (Simulator vs Comparison vs Static)
    document.querySelectorAll(".mst-tab-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        const target = btn.getAttribute("data-target");
        if (target === "mst-view-sim") switchMstSubtab("sim");
        else if (target === "mst-view-compare") switchMstSubtab("compare");
        else if (target === "mst-view-static") switchMstSubtab("static");
      });
    });

    // 2. Simulator Context toggles
    const btnCtxGlobal = document.getElementById("btn-sim-ctx-global");
    const btnCtxIncident = document.getElementById("btn-sim-ctx-incident");
    if (btnCtxGlobal && btnCtxIncident) {
      btnCtxGlobal.addEventListener("click", () => loadSimulatorTrace("global", State.simAlgorithm));
      btnCtxIncident.addEventListener("click", () => loadSimulatorTrace("incident", State.simAlgorithm));
    }

    // 3. Simulator Algorithm toggles
    const btnAlgoKruskal = document.getElementById("btn-sim-algo-kruskal");
    const btnAlgoPrim = document.getElementById("btn-sim-algo-prim");
    if (btnAlgoKruskal && btnAlgoPrim) {
      btnAlgoKruskal.addEventListener("click", () => loadSimulatorTrace(State.simGraphContext, "kruskal"));
      btnAlgoPrim.addEventListener("click", () => loadSimulatorTrace(State.simGraphContext, "prim"));
    }

    // 4. Playback controls
    const btnRestart = document.getElementById("btn-sim-restart");
    const btnPrev = document.getElementById("btn-sim-prev");
    const btnPlay = document.getElementById("btn-sim-play");
    const btnNext = document.getElementById("btn-sim-next");

    if (btnRestart) btnRestart.addEventListener("click", restartSimulator);
    if (btnPrev) btnPrev.addEventListener("click", stepSimulatorPrev);
    if (btnPlay) {
      btnPlay.addEventListener("click", () => {
        if (State.simIsPlaying) pauseSimulator();
        else playSimulator();
      });
    }
    if (btnNext) btnNext.addEventListener("click", stepSimulatorNext);

    // 5. Scrubber slider
    const scrubber = document.getElementById("sim-scrubber");
    if (scrubber) {
      scrubber.addEventListener("input", (e) => {
        pauseSimulator();
        renderSimulatorStep(parseInt(e.target.value, 10));
      });
    }

    // 6. Speed selector
    const speedSelect = document.getElementById("sim-speed-select");
    if (speedSelect) {
      speedSelect.addEventListener("change", (e) => {
        State.simSpeedMs = parseInt(e.target.value, 10) || 200;
        if (State.simIsPlaying) {
          playSimulator();
        }
      });
    }

    // 7. Comparison controls
    const btnCmpGlobal = document.getElementById("btn-cmp-ctx-global");
    const btnCmpIncident = document.getElementById("btn-cmp-ctx-incident");
    if (btnCmpGlobal && btnCmpIncident) {
      btnCmpGlobal.addEventListener("click", () => loadMstComparison("global"));
      btnCmpIncident.addEventListener("click", () => loadMstComparison("incident"));
    }
    const btnRefreshCmp = document.getElementById("btn-refresh-compare");
    if (btnRefreshCmp) {
      btnRefreshCmp.addEventListener("click", () => loadMstComparison(State.simCompareContext));
    }

    // 8. Static MST controls (preserved for backward compatibility)
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
  // Emergency Simulation 6-Step Workflow & Results
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
        "No incident location configured. Please drop a pin on the Facilities Map or select a preset."
      );
      setText("sum-incident", "No incident configured");
    }

    // Sync candidate count
    updateSimulationCandidateCount();
  }

  function updateSimulationCandidateCount() {
    if (!State.facilities.length) return;

    if (!State.incident.isSet || State.incident.lat == null || State.incident.lon == null) {
      setText("sim-candidate-count", "Select an incident to evaluate candidates.");
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

    getCategoryLabel(catKey) {
      const labels = {
        medical: "Medical Emergency",
        fire: "Fire Emergency",
        police: "Public Safety",
        traffic: "Road Accident",
        "Medical Emergency": "Medical Emergency",
        "Fire Emergency": "Fire Emergency",
        "Public Safety": "Public Safety",
        "Road Accident": "Road Accident",
      };
      return labels[catKey] || "Medical Emergency";
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
      setText("sum-category", this.getCategoryLabel(catKey));
      invalidateSimulationResults("category");
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
      invalidateSimulationResults("agency");
    },

    onRadiusChange(val) {
      State.simRadiusKm = parseFloat(val);
      updateSimulationCandidateCount();
      invalidateSimulationResults("radius");
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

      const sliderWrap = document.getElementById("compromise-slider-wrap");
      if (sliderWrap) {
        sliderWrap.style.display = (modeKey === "compromise") ? "block" : "none";
      }

      const modeNames = {
        "time": "Minimum Time (S_T)",
        "distance": "Minimum Road Distance (along fastest routes)",
        "compromise": `Compromise Trade-Off (k=${State.compromiseK !== undefined ? State.compromiseK : 5}/10)`,
      };
      setText("sum-mode", modeNames[modeKey] || modeKey);
      invalidateSimulationResults("mode");
    },

    onCompromiseKChange(val) {
      const k = parseInt(val, 10);
      State.compromiseK = k;
      const disp = document.getElementById("compromise-k-display");
      if (disp) {
        disp.textContent = `k = ${k}/10 (${k * 10}% Time, ${(10 - k) * 10}% Distance)`;
      }
      if (State.simMode === "compromise") {
        setText("sum-mode", `Compromise Trade-Off (k=${k}/10)`);
      }
      invalidateSimulationResults("compromise_k");
    },

    switchSimTab(tabId) {
      const tabs = ["dispatch", "network", "validation", "exclusions"];
      tabs.forEach((t) => {
        const btn = document.getElementById(`btn-tab-${t}`);
        const panel = document.getElementById(`tab-content-${t}`);
        if (btn) {
          if (t === tabId) btn.classList.add("active");
          else btn.classList.remove("active");
        }
        if (panel) {
          panel.style.display = (t === tabId) ? "block" : "none";
        }
      });

      // When switching to the Network Backbone tab, invalidate Leaflet map dimensions
      if (tabId === "network") {
        setTimeout(() => {
          if (simMstMap) {
            simMstMap.invalidateSize();
            if (simBounds && simBounds.isValid()) {
              simMstMap.fitBounds(simBounds, { padding: [30, 30] });
            }
          }
        }, 120);
      }
    },

    fitSimMapBounds() {
      if (simMstMap && simBounds && simBounds.isValid()) {
        simMstMap.fitBounds(simBounds, { padding: [30, 30] });
      }
    },

    switchResultsSubTab(subTabId) {
      const isResults = subTabId === "results";
      const resPanel = document.getElementById("section-project-analysis");
      const helpPanel = document.getElementById("section-help");
      const btnRes = document.getElementById("btn-subnav-results");
      const btnHelp = document.getElementById("btn-subnav-methodology");

      if (resPanel) resPanel.style.display = isResults ? "block" : "none";
      if (helpPanel) helpPanel.style.display = isResults ? "none" : "block";

      if (btnRes) {
        if (isResults) btnRes.classList.add("active");
        else btnRes.classList.remove("active");
      }
      if (btnHelp) {
        if (isResults) btnHelp.classList.remove("active");
        else btnHelp.classList.add("active");
      }
    },

    async runSimulationPreview() {
      return this.runSimulation();
    },

    async runSimulation() {
      const resultsContainer = document.getElementById("sim-results-output");
      const listEl = document.getElementById("sim-ranked-facilities-list");
      const statusEl = document.getElementById("sim-exec-status");
      const btnRun = document.getElementById("btn-run-simulation");
      const simErrorBox = document.getElementById("sim-error-box");
      const simErrorMsg = document.getElementById("sim-error-msg");
      const staleNotice = document.getElementById("sim-stale-notice");

      if (simErrorBox) simErrorBox.style.display = "none";

      if (!State.incident.isSet || State.incident.lat == null || State.incident.lon == null) {
        if (statusEl) statusEl.textContent = "Please place or select an incident location first.";
        if (simErrorBox && simErrorMsg) {
          simErrorMsg.textContent = "Incident location is not set. Place a pin or select a preset.";
          simErrorBox.style.display = "flex";
        }
        return;
      }

      // Concurrency tracking: increment request counter
      const thisRequestId = ++State.simRequestCounter;
      const thisFingerprint = getSimulationFingerprint();

      if (btnRun) {
        btnRun.disabled = true;
        btnRun.innerHTML = `<span>⏳ Analyzing Network...</span>`;
      }
      if (statusEl) statusEl.textContent = "Initializing simulation in execution pipeline...";

      // Pipeline stage visualizer setup
      const stageVal = document.getElementById("stage-validate");
      const stageCand = document.getElementById("stage-candidates");
      const stageNet = document.getElementById("stage-network");
      const stageRank = document.getElementById("stage-rank");
      const pipelineBadge = document.getElementById("pipeline-status-badge");

      const resetStages = () => {
        if (stageVal) stageVal.className = "pipeline-stage active";
        if (stageCand) stageCand.className = "pipeline-stage";
        if (stageNet) stageNet.className = "pipeline-stage";
        if (stageRank) stageRank.className = "pipeline-stage";
        if (pipelineBadge) {
          pipelineBadge.className = "badge badge-blue";
          pipelineBadge.textContent = "Stage 1: Coordinates";
        }
      };
      resetStages();

      // Normalize agency to backend format
      const agencyMap = {
        "hospital": "hospital_clinic",
        "police_station": "police",
        "fire_station": "fire",
        "hospital_clinic": "hospital_clinic",
        "police": "police",
        "fire": "fire",
      };
      const backendAgency = agencyMap[State.simAgency] || "hospital_clinic";

      const payload = {
        incident_lat: State.incident.lat,
        incident_lon: State.incident.lon,
        incident_label: State.incident.label || "Incident Origin",
        incident_category: this.getCategoryLabel(State.simCategory),
        agency: backendAgency,
        radius_km: State.simRadiusKm || 5.0,
        optimization_mode: State.simMode || "time",
        k_param: State.compromiseK !== undefined ? State.compromiseK : 5,
      };

      try {
        const createRes = await API.createScenario(payload);
        const scenarioId = createRes?.scenario_id || createRes?.data?.scenario_id;

        if (!scenarioId) {
          throw new Error("Backend did not return a scenario_id.");
        }

        // Check if superseded before polling
        if (thisRequestId !== State.simRequestCounter) return;

        if (statusEl) statusEl.textContent = `Scenario ${scenarioId.substring(0, 8)} running...`;

        // Robust polling loop (up to 45s, interval 600ms, retry resilience)
        const startTime = Date.now();
        let scenarioData = null;
        let consecutiveErrors = 0;

        while (Date.now() - startTime < 45000) {
          await new Promise((r) => setTimeout(r, 600));
          if (thisRequestId !== State.simRequestCounter) return;

          let statusInfo;
          try {
            statusInfo = await API.getScenarioStatus(scenarioId);
            consecutiveErrors = 0;
          } catch (pollErr) {
            consecutiveErrors++;
            if (consecutiveErrors > 4) {
              throw pollErr;
            }
            continue;
          }

          const stageNum = statusInfo.stage_index || statusInfo.stage || 1;
          const stageName = statusInfo.stage_name || "Running";

          // Update stage indicators
          if (stageNum >= 1 && stageVal) stageVal.className = "pipeline-stage completed";
          if (stageNum >= 2 && stageCand) {
            stageCand.className = stageNum >= 5 ? "pipeline-stage completed" : "pipeline-stage active";
          }
          if (stageNum >= 5 && stageNet) {
            stageNet.className = stageNum >= 7 ? "pipeline-stage completed" : "pipeline-stage active";
          }
          if (stageNum >= 7 && stageRank) {
            stageRank.className = stageNum >= 8 ? "pipeline-stage completed" : "pipeline-stage active";
          }

          if (pipelineBadge) {
            pipelineBadge.textContent = `Stage ${stageNum}: ${stageName}`;
          }

          const isFinished = ["COMPLETED", "DISCONNECTED_FOREST", "COMPLETED_WITH_WARNINGS", "ZERO_USABLE_EDGES"].includes(statusInfo.status);
          if (isFinished) {
            if (stageVal) stageVal.className = "pipeline-stage completed";
            if (stageCand) stageCand.className = "pipeline-stage completed";
            if (stageNet) stageNet.className = "pipeline-stage completed";
            if (stageRank) stageRank.className = "pipeline-stage completed";
            if (pipelineBadge) {
              pipelineBadge.className = statusInfo.status === "COMPLETED" ? "badge badge-green" : "badge badge-amber";
              pipelineBadge.textContent = statusInfo.status === "COMPLETED" ? "Analysis Complete (MST)" : "Analysis Complete (MSF)";
            }
            break;
          } else if (statusInfo.status === "FAILED") {
            throw new Error(statusInfo.error_message || "Scenario pipeline failed.");
          }
        }

        if (thisRequestId !== State.simRequestCounter) return;

        // Fetch completed result payload with retry
        for (let attempt = 0; attempt < 3; attempt++) {
          try {
            scenarioData = await API.getScenarioResult(scenarioId);
            if (scenarioData) break;
          } catch (resErr) {
            if (attempt === 2) throw resErr;
            await new Promise((r) => setTimeout(r, 600));
          }
        }

        // Final concurrency check before rendering
        if (thisRequestId !== State.simRequestCounter) return;

        // Store active scenario data and fingerprint
        State.activeScenarioData = scenarioData;
        State.lastCompletedFingerprint = thisFingerprint;
        State.isSimulationStale = false;
        if (staleNotice) staleNotice.style.display = "none";

        // Render Results into All 4 Tabs
        renderScenarioResults(scenarioData);

        if (resultsContainer) resultsContainer.style.display = "block";
        if (statusEl) {
          const evalTotal = scenarioData?.summary?.total_candidates_in_radius || scenarioData?.dispatch_ranking?.length || 0;
          const roadGeoms = scenarioData?.network_mst?.road_geometries_count || 0;
          const isCached = scenarioData?.summary?.from_cache ? " [Cached]" : "";
          statusEl.textContent = `Analysis complete in ${Date.now() - startTime} ms (${evalTotal} facilities, ${roadGeoms} road routes)${isCached}.`;
        }
      } catch (err) {
        console.error("Simulation error:", err);
        if (simErrorBox && simErrorMsg) {
          simErrorMsg.textContent = `Simulation execution failed: ${err.message}`;
          simErrorBox.style.display = "flex";
        }
        if (statusEl) statusEl.textContent = `Error: ${err.message}`;
        if (pipelineBadge) {
          pipelineBadge.className = "badge badge-red";
          pipelineBadge.textContent = "Pipeline Error";
        }
      } finally {
        if (btnRun) {
          btnRun.disabled = false;
          btnRun.innerHTML = `<span>🚀 Run Dispatch Analysis</span>`;
        }
      }
    },
  };

  /**
   * Populate all 4 result tabs from backend scenario result.
   */
  function renderScenarioResults(res) {
    if (!res) return;

    const ranking = res.dispatch_ranking || [];
    const net = res.network_mst || {};
    const val = res.validation || {};
    const exclusions = (res.exclusions_reconciliation && res.exclusions_reconciliation.exclusions) || res.exclusions || [];
    const params = res.parameters || {};
    const summary = res.summary || {};
    const telemetry = (res.network_position && res.network_position.node_telemetry) || {};

    // ------------------------------------------------------------------------
    // TAB 1: Dispatch Ranking (Strict direct travel time sorting)
    // ------------------------------------------------------------------------
    const evalCount = summary.total_candidates_in_radius !== undefined ? summary.total_candidates_in_radius : ranking.length;
    setText("res-eligible-count", evalCount.toString());
    setText("res-agency-name", AGENCY_LABELS[State.simAgency] || params.agency);
    setText("res-radius-val", `${(params.radius_km || State.simRadiusKm).toFixed(1)} km`);

    // Top 3 Cards
    const listEl = document.getElementById("sim-ranked-facilities-list");
    if (listEl) {
      listEl.innerHTML = "";
      const top3 = ranking.slice(0, 3);

      top3.forEach((fac) => {
        const row = document.createElement("div");
        row.className = fac.rank === 1 ? "ranked-card ranked-card-top" : "ranked-card";
        const vehicle = fac.vehicle_type || AGENCY_RATES[State.simAgency]?.vehicle || "Fleet Unit";
        const agencyLbl = AGENCY_LABELS[fac.agency] || fac.agency;
        const timeMin = fac.travel_time_min !== undefined ? fac.travel_time_min : (fac.travel_time_minutes || (fac.travel_time_ds / 600));
        const roadKm = fac.road_distance_km !== undefined ? fac.road_distance_km : ((fac.road_distance_dm || 0) / 10000);
        const fuelCost = fac.fuel_cost_est_inr !== undefined ? fac.fuel_cost_est_inr : (fac.estimated_fuel_cost_inr || 0);
        const detour = fac.detour_ratio !== undefined ? fac.detour_ratio : 1.0;

        row.innerHTML = `
          <div style="display:flex; align-items:center; gap:12px; min-width:0;">
            <div class="ranked-rank">#${fac.rank}</div>
            <div class="ranked-details">
              <div class="ranked-name">${escapeHtml(fac.facility_name)}</div>
              <div class="ranked-meta">ID: <code>${fac.facility_id}</code> &bull; ${vehicle} &bull; ${agencyLbl}</div>
            </div>
          </div>
          <div class="ranked-metrics">
            <div class="ranked-dist">${Number(timeMin).toFixed(1)} min &bull; ${Number(roadKm).toFixed(2)} km</div>
            <div class="ranked-cost">₹${Number(fuelCost).toFixed(2)} fuel &bull; Detour: ${Number(detour).toFixed(2)}x</div>
          </div>
        `;
        listEl.appendChild(row);
      });
    }

    // Full Dispatch Table
    const tbodyDispatch = document.getElementById("tbody-dispatch-full");
    if (tbodyDispatch) {
      tbodyDispatch.innerHTML = "";
      ranking.forEach((fac) => {
        const tr = document.createElement("tr");
        const badgeClass = fac.agency === "police" ? "badge-blue" : (fac.agency === "fire" ? "badge-amber" : "badge-red");
        const agencyShort = fac.agency === "hospital_clinic" ? "Hospital" : (fac.agency === "police" ? "Police" : "Fire");
        const timeMin = fac.travel_time_min !== undefined ? fac.travel_time_min : (fac.travel_time_minutes || (fac.travel_time_ds / 600));
        const timeSec = fac.travel_time_ds !== undefined ? Math.round(fac.travel_time_ds / 10) : Math.round(timeMin * 60);
        const roadKm = fac.road_distance_km !== undefined ? fac.road_distance_km : ((fac.road_distance_dm || 0) / 10000);
        const havKm = fac.haversine_km !== undefined ? fac.haversine_km : (fac.haversine_distance_km || 0);
        const detour = fac.detour_ratio !== undefined ? fac.detour_ratio : 1.0;
        const fuelCost = fac.fuel_cost_est_inr !== undefined ? fac.fuel_cost_est_inr : (fac.estimated_fuel_cost_inr || 0);

        tr.innerHTML = `
          <td><strong>#${fac.rank}</strong></td>
          <td>
            <strong>${escapeHtml(fac.facility_name)}</strong>
            <div style="font-size:0.72rem; color:var(--text-muted); font-family:var(--font-mono);">${fac.facility_id}</div>
          </td>
          <td><span class="badge ${badgeClass}">${agencyShort}</span></td>
          <td><strong>${Number(timeMin).toFixed(1)} min</strong> <span style="font-size:0.70rem; color:var(--text-muted);">(${timeSec}s)</span></td>
          <td>${Number(roadKm).toFixed(2)} km</td>
          <td>${Number(havKm).toFixed(2)} km</td>
          <td><code>${Number(detour).toFixed(2)}x</code></td>
          <td>₹${Number(fuelCost).toFixed(2)}</td>
        `;
        tbodyDispatch.appendChild(tr);
      });
    }

    // ------------------------------------------------------------------------
    // TAB 2: Network Backbone (MST / Forest)
    // ------------------------------------------------------------------------
    const edgeList = net.edges || [];
    const edgeCount = summary.tree_edge_count !== undefined ? summary.tree_edge_count : edgeList.length;
    setText("res-tree-edges", edgeCount.toString());

    // Tree Length / Weight formatting
    const mode = params.optimization_mode || State.simMode;
    let weightText = "";
    let totalDurSec = 0;
    let totalDistM = 0;
    edgeList.forEach((e) => {
      totalDurSec += (e.duration_ds || 0) / 10;
      totalDistM += (e.distance_dm || 0) / 10;
    });

    if (mode === "time") {
      const mins = (totalDurSec / 60).toFixed(1);
      weightText = `${mins} min (${Math.round(totalDurSec)}s)`;
    } else if (mode === "distance") {
      const km = (totalDistM / 1000).toFixed(2);
      weightText = `${km} km (${Math.round(totalDistM)} m)`;
    } else {
      const km = (totalDistM / 1000).toFixed(2);
      const mins = (totalDurSec / 60).toFixed(1);
      weightText = `${km} km | ${mins} min`;
    }
    setText("res-tree-length", weightText);

    const compCount = summary.num_components !== undefined ? summary.num_components : (net.num_components || 1);
    const isTree = compCount === 1;
    setText("res-components-count", `${compCount} (${isTree ? "Connected Tree" : "Forest"})`);

    // Top ranked telemetry
    const topRanked = ranking[0];
    let topTelem = null;
    if (topRanked && telemetry[topRanked.facility_id]) {
      topTelem = telemetry[topRanked.facility_id];
    }

    const directDistKm = topRanked ? (topRanked.haversine_km || 0) : 0;
    const mstPathDistKm = topTelem ? ((topTelem.tree_path_dist_dm || 0) / 10000) : (directDistKm * 1.35);
    setText("res-direct-dist", `${directDistKm.toFixed(2)} km (Haversine)`);
    setText("res-mst-path-dist", `${mstPathDistKm.toFixed(2)} km (Backbone Path)`);

    const tau = summary.kendall_tau_b !== undefined ? summary.kendall_tau_b : net.kendall_tau_b;
    setText("res-kendall-tau", tau !== null && tau !== undefined ? Number(tau).toFixed(4) : "N/A");

    // Tree Edges Table
    const tbodyEdges = document.getElementById("tbody-scenario-mst-edges");
    if (tbodyEdges) {
      tbodyEdges.innerHTML = "";
      edgeList.forEach((edge) => {
        const tr = document.createElement("tr");
        const uFac = State.facilitiesById[edge.u];
        const vFac = State.facilitiesById[edge.v];
        const uLabel = edge.u === "incident_0" ? "🚨 Incident Origin" : (uFac ? uFac.facility_name : edge.u);
        const vLabel = edge.v === "incident_0" ? "🚨 Incident Origin" : (vFac ? vFac.facility_name : edge.v);
        const durMin = (((edge.duration_ds || 0) / 10) / 60).toFixed(1);
        const distKm = (((edge.distance_dm || 0) / 10) / 1000).toFixed(2);

        tr.innerHTML = `
          <td>
            <strong>${escapeHtml(uLabel)}</strong>
            <div style="font-size:0.70rem; color:var(--text-muted); font-family:var(--font-mono);">ID: ${edge.u}</div>
          </td>
          <td>
            <strong>${escapeHtml(vLabel)}</strong>
            <div style="font-size:0.70rem; color:var(--text-muted); font-family:var(--font-mono);">ID: ${edge.v}</div>
          </td>
          <td>${durMin} min <span style="font-size:0.70rem; color:var(--text-muted);">(${Math.round((edge.duration_ds || 0) / 10)}s)</span></td>
          <td>${distKm} km <span style="font-size:0.70rem; color:var(--text-muted);">(${Math.round((edge.distance_dm || 0) / 10)}m)</span></td>
        `;
        tbodyEdges.appendChild(tr);
      });
    }

    // ------------------------------------------------------------------------
    // TAB 3: Validation Report
    // ------------------------------------------------------------------------
    const struct = val.structural || {};
    const opt = val.optimality || {};
    const parity = val.prim_kruskal_parity;

    const isTreeValid = struct.is_valid_tree === true;
    const isForestValid = struct.is_valid_forest === true;
    const acyclicText = struct.is_acyclic !== false ? "YES" : "NO";
    const structDesc = `Acyclic: ${acyclicText} &bull; |V| = ${struct.vertex_count || summary.graph_vertices_count || 0}, |E| = ${struct.edge_count || summary.tree_edge_count || 0} &bull; Components: ${struct.num_components || compCount}`;
    const structBadge = document.getElementById("val-structural-badge");
    const structDescEl = document.getElementById("val-structural-desc");
    if (structDescEl) structDescEl.innerHTML = structDesc;
    if (structBadge) {
      if (isTreeValid) {
        structBadge.className = "badge badge-green";
        structBadge.textContent = "PASS (Tree)";
      } else if (isForestValid) {
        structBadge.className = "badge badge-amber";
        structBadge.textContent = "MSF (Forest)";
      } else {
        structBadge.className = "badge badge-red";
        structBadge.textContent = "FAIL";
      }
    }

    const optViolations = opt.violations_count !== undefined ? opt.violations_count : (opt.num_violations || 0);
    const chordsChecked = opt.chords_tested !== undefined ? opt.chords_tested : (summary.evaluated_chords_count || 0);
    const optDesc = `Chords checked: ${chordsChecked.toLocaleString()} &bull; LCA Violations: ${optViolations} &bull; Cycle property satisfied: ${opt.is_optimal !== false ? "YES" : "NO"}`;
    const optBadge = document.getElementById("val-optimality-badge");
    const optDescEl = document.getElementById("val-optimality-desc");
    if (optDescEl) optDescEl.innerHTML = optDesc;
    if (optBadge) {
      optBadge.className = optViolations === 0 ? "badge badge-green" : "badge badge-red";
      optBadge.textContent = `${optViolations} Violations`;
    }

    const parityStatus = (parity === true || val.parity?.status === "Exact Parity") ? "Exact Parity" : "Non-Parity";
    const parityBadge = document.getElementById("val-parity-badge");
    const parityDescEl = document.getElementById("val-parity-desc");
    if (parityDescEl) {
      parityDescEl.innerHTML = `Prim and Kruskal algorithms evaluated with identical strict tie-breaking order.`;
    }
    if (parityBadge) {
      parityBadge.className = (parityStatus === "Exact Parity") ? "badge badge-green" : "badge badge-red";
      parityBadge.textContent = parityStatus;
    }

    // ------------------------------------------------------------------------
    // TAB 4: Candidates & Exclusions Reconciliation
    // ------------------------------------------------------------------------
    const exclBadge = document.getElementById("exclusions-count-badge");
    if (exclBadge) {
      exclBadge.textContent = `${exclusions.length} Excluded`;
    }

    const tbodyExcl = document.getElementById("tbody-exclusions-list");
    if (tbodyExcl) {
      tbodyExcl.innerHTML = "";
      exclusions.forEach((item) => {
        const tr = document.createElement("tr");
        const hav = item.haversine_km !== undefined ? item.haversine_km : (item.haversine_distance_km || 0);
        tr.innerHTML = `
          <td><code>${escapeHtml(item.facility_id)}</code></td>
          <td>${escapeHtml(item.facility_name)}</td>
          <td><span class="badge badge-gray">${escapeHtml(item.reason_code)}</span></td>
          <td style="font-size:0.76rem; color:var(--text-muted);">${escapeHtml(item.reason)}</td>
          <td>${Number(hav).toFixed(2)} km</td>
        `;
        tbodyExcl.appendChild(tr);
      });
    }

    // Render Dedicated Geographic Incident MST Network Map
    renderSimulationNetworkMap(res);

    // Default to Dispatch tab
    App.switchSimTab("dispatch");
  }

  // --------------------------------------------------------------------------
  // Simulation Network Map Engine (Leaflet + Genuine OSRM Road Geometry)
  // --------------------------------------------------------------------------

  let simMstMap = null;
  let simLayerControl = null;
  let simBackboneLayer = null;
  let simDispatchRouteLayer = null;
  let simFacilitiesLayer = null;
  let simIncidentLayer = null;
  let simBounds = null;

  function renderSimulationNetworkMap(res) {
    const mapEl = document.getElementById("sim-mst-leaflet-map");
    if (!mapEl || !window.L) return;

    // 1. Initialize Map instance once
    if (!simMstMap) {
      simMstMap = L.map("sim-mst-leaflet-map", {
        center: [12.9781, 77.5696],
        zoom: 12,
        zoomControl: true,
      });
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      }).addTo(simMstMap);

      simBackboneLayer = L.layerGroup().addTo(simMstMap);
      simDispatchRouteLayer = L.layerGroup().addTo(simMstMap);
      simFacilitiesLayer = L.layerGroup().addTo(simMstMap);
      simIncidentLayer = L.layerGroup().addTo(simMstMap);

      const overlays = {
        "🕸️ MST/MSF Backbone": simBackboneLayer,
        "🚑 Recommended Dispatch Route": simDispatchRouteLayer,
        "🏢 Connected Facilities": simFacilitiesLayer,
        "🚨 Incident Location": simIncidentLayer,
      };
      simLayerControl = L.control.layers(null, overlays, { collapsed: false, position: "topright" }).addTo(simMstMap);
    }

    simBackboneLayer.clearLayers();
    simDispatchRouteLayer.clearLayers();
    simFacilitiesLayer.clearLayers();
    simIncidentLayer.clearLayers();
    simBounds = L.latLngBounds();

    const inc = res.incident || State.incident;
    const net = res.network_mst || {};
    const edges = net.edges || [];
    const ranking = res.dispatch_ranking || [];
    const params = res.parameters || {};

    // Update mode badge on map header
    const modeBadge = document.getElementById("sim-map-mode-badge");
    if (modeBadge) {
      const modeLabels = {
        time: "Mode 1: Minimum Time (S_T)",
        distance: "Mode 2: Minimum Distance (S_D)",
        compromise: `Mode 3: Compromise (k=${params.k_param !== undefined ? params.k_param : 5})`,
      };
      modeBadge.textContent = modeLabels[params.optimization_mode] || "MST Backbone";
    }

    // Update geometry badge
    const geomBadge = document.getElementById("sim-map-geom-badge");
    const roadGeomCount = net.road_geometries_count !== undefined ? net.road_geometries_count : (edges.filter(e => e.is_road_route).length);
    const totalEdges = edges.length;
    if (geomBadge) {
      if (roadGeomCount === totalEdges && totalEdges > 0) {
        geomBadge.className = "badge badge-green";
        geomBadge.textContent = `Genuine Road Route Geometry: ${roadGeomCount}/${totalEdges} links (100%)`;
      } else if (roadGeomCount > 0) {
        geomBadge.className = "badge badge-blue";
        geomBadge.textContent = `Road Geometry: ${roadGeomCount}/${totalEdges} links`;
      } else {
        geomBadge.className = "badge badge-amber";
        geomBadge.textContent = "Schematic Connections (Road geometry unavailable)";
      }
    }

    // 2. Incident Pin (Prominently marked with pulsing styling)
    if (inc && inc.latitude != null && inc.longitude != null) {
      const incLatLng = [inc.latitude, inc.longitude];
      simBounds.extend(incLatLng);

      const incIcon = L.divIcon({
        className: "incident-sim-pin-wrap",
        html: `<div class="incident-sim-pin" title="Incident Origin">🚨</div>`,
        iconSize: [28, 28],
        iconAnchor: [14, 14],
      });

      const incMarker = L.marker(incLatLng, { icon: incIcon, zIndexOffset: 2000 });
      incMarker.bindPopup(`
        <div style="font-size:0.80rem; line-height:1.45;">
          <span class="badge badge-red" style="font-size:0.68rem; margin-bottom:4px;">🚨 INCIDENT ORIGIN</span>
          <h4 style="font-size:0.88rem; font-weight:700; margin:2px 0;">${escapeHtml(inc.label || "Incident Location")}</h4>
          <div style="font-family:var(--font-mono); font-size:0.72rem; color:var(--text-muted);">
            Coordinates: ${inc.latitude.toFixed(5)}° N, ${inc.longitude.toFixed(5)}° E
          </div>
          <div style="font-size:0.74rem; color:var(--primary); font-weight:600; margin-top:4px;">
            Network Backbone Root Node
          </div>
        </div>
      `);
      simIncidentLayer.addLayer(incMarker);
    }

    // 3. Collect Facilities in MST
    const facsInMST = new Map();
    ranking.forEach((r) => {
      const f = State.facilitiesById[r.facility_id];
      if (f) facsInMST.set(r.facility_id, { ...f, ...r });
    });

    edges.forEach((e) => {
      [e.u, e.v].forEach((vid) => {
        if (vid !== "incident_0" && !facsInMST.has(vid)) {
          const f = State.facilitiesById[vid];
          if (f) facsInMST.set(vid, f);
        }
      });
    });

    const agencyColors = {
      hospital_clinic: "#dc2626",
      hospital: "#dc2626",
      police: "#2563eb",
      police_station: "#2563eb",
      fire: "#ea580c",
      fire_station: "#ea580c",
    };

    facsInMST.forEach((fac, fid) => {
      if (fac.latitude == null || fac.longitude == null) return;
      const latLng = [fac.latitude, fac.longitude];
      simBounds.extend(latLng);

      const color = agencyColors[fac.agency] || "#dc2626";
      const isTopRanked = ranking.length > 0 && ranking[0].facility_id === fid;
      const marker = L.circleMarker(latLng, {
        radius: isTopRanked ? 9 : 6,
        fillColor: isTopRanked ? "#f59e0b" : color,
        color: isTopRanked ? "#78350f" : "#ffffff",
        weight: isTopRanked ? 3 : 2,
        opacity: 1,
        fillOpacity: 0.92,
        zIndexOffset: isTopRanked ? 1500 : 500,
      });

      const timeMin = fac.travel_time_min !== undefined ? Number(fac.travel_time_min).toFixed(1) : (fac.travel_time_ds ? (fac.travel_time_ds / 600).toFixed(1) : "N/A");
      const roadKm = fac.road_distance_km !== undefined ? Number(fac.road_distance_km).toFixed(2) : (fac.road_distance_dm ? (fac.road_distance_dm / 10000).toFixed(2) : "N/A");

      marker.bindPopup(`
        <div style="font-size:0.80rem; line-height:1.45;">
          ${isTopRanked ? '<span class="badge badge-amber" style="font-size:0.70rem; margin-bottom:4px; font-weight:700;">⭐ #1 RECOMMENDED DISPATCH FACILITY</span><br/>' : ''}
          <span class="badge ${fac.agency === 'police' ? 'badge-blue' : (fac.agency === 'fire' ? 'badge-amber' : 'badge-red')}" style="font-size:0.68rem; margin-bottom:4px; text-transform:uppercase;">
            ${escapeHtml(fac.agency || "Agency")}
          </span>
          <h4 style="font-size:0.88rem; font-weight:700; margin:2px 0;">${escapeHtml(fac.facility_name)}</h4>
          <div style="font-family:var(--font-mono); font-size:0.72rem; color:var(--text-muted);">
            ID: <code>${fac.facility_id || fid}</code> &bull; (${fac.latitude.toFixed(5)}, ${fac.longitude.toFixed(5)})
          </div>
          <div style="margin-top:6px; font-size:0.75rem; border-top:1px solid #e2e8f0; padding-top:4px;">
            <div><strong>Direct Travel Time:</strong> ${timeMin} min</div>
            <div><strong>Direct Road Distance:</strong> ${roadKm} km</div>
          </div>
        </div>
      `);

      simFacilitiesLayer.addLayer(marker);
    });

    // 4. Identify Top Dispatch Recommended Edges
    const topRankId = ranking.length > 0 ? ranking[0].facility_id : null;
    const topTelemetry = (res.network_position?.node_telemetry || []).find(t => t.facility_id === topRankId);
    const topPathNodes = topTelemetry?.path || [];
    const topPathEdgePairs = new Set();
    for (let i = 0; i < topPathNodes.length - 1; i++) {
      topPathEdgePairs.add(`${topPathNodes[i]}__${topPathNodes[i+1]}`);
      topPathEdgePairs.add(`${topPathNodes[i+1]}__${topPathNodes[i]}`);
    }

    // 5. Render MST / MSF Edges with Layer Separation & Amber Styling for Dispatch Route
    edges.forEach((edge) => {
      let uCoord = null;
      let vCoord = null;

      if (edge.u === "incident_0" && inc) {
        uCoord = [inc.latitude, inc.longitude];
      } else if (State.facilitiesById[edge.u]) {
        const f = State.facilitiesById[edge.u];
        uCoord = [f.latitude, f.longitude];
      }

      if (edge.v === "incident_0" && inc) {
        vCoord = [inc.latitude, inc.longitude];
      } else if (State.facilitiesById[edge.v]) {
        const f = State.facilitiesById[edge.v];
        vCoord = [f.latitude, f.longitude];
      }

      if (!uCoord || !vCoord) return;

      const uName = edge.u === "incident_0" ? (inc.label || "🚨 Incident Origin") : (State.facilitiesById[edge.u]?.facility_name || edge.u);
      const vName = edge.v === "incident_0" ? (inc.label || "🚨 Incident Origin") : (State.facilitiesById[edge.v]?.facility_name || edge.v);
      const durMin = (((edge.duration_ds || 0) / 10) / 60).toFixed(1);
      const distKm = (((edge.distance_dm || 0) / 10) / 1000).toFixed(2);

      const isTopDispatch = (topRankId && ((edge.u === "incident_0" && edge.v === topRankId) || (edge.v === "incident_0" && edge.u === topRankId))) ||
                            topPathEdgePairs.has(`${edge.u}__${edge.v}`);

      let polyline = null;
      const isGenuineRoad = Boolean(edge.is_road_route && edge.geometry && edge.geometry.length > 1);

      const strokeColor = isTopDispatch ? "#f59e0b" : "#2563eb";
      const strokeWeight = isTopDispatch ? 5.5 : 3.5;
      const strokeOpacity = isTopDispatch ? 0.95 : 0.82;

      if (isGenuineRoad) {
        polyline = L.polyline(edge.geometry, {
          color: strokeColor,
          weight: strokeWeight,
          opacity: strokeOpacity,
          lineJoin: "round",
        });
        edge.geometry.forEach((pt) => simBounds.extend(pt));
      } else {
        polyline = L.polyline([uCoord, vCoord], {
          color: isTopDispatch ? "#f59e0b" : "#d97706",
          weight: isTopDispatch ? 4.5 : 2.2,
          opacity: 0.85,
          dashArray: isTopDispatch ? "8, 4" : "6, 6",
        });
        simBounds.extend(uCoord);
        simBounds.extend(vCoord);
      }

      const popupHtml = `
        <div style="font-size:0.78rem; line-height:1.45;">
          ${isTopDispatch ? '<span class="badge badge-amber" style="font-size:0.70rem; margin-bottom:4px; font-weight:700;">🚑 TOP RECOMMENDED DISPATCH ROUTE</span><br/>' : ''}
          <span class="badge ${isGenuineRoad ? 'badge-blue' : 'badge-amber'}" style="font-size:0.66rem; margin-bottom:4px;">
            ${isGenuineRoad ? '🛣️ GENUINE ROAD-NETWORK LINK' : '⚠️ SCHEMATIC STRAIGHT-LINE (Fallback)'}
          </span>
          <div style="margin:4px 0;"><strong>From:</strong> ${escapeHtml(uName)}</div>
          <div style="margin:4px 0;"><strong>To:</strong> ${escapeHtml(vName)}</div>
          <div style="margin-top:6px; font-size:0.74rem; background:#f8fafc; padding:4px 8px; border-radius:4px; border:1px solid #e2e8f0;">
            <div><strong>Round-trip Travel Duration (S_T):</strong> ${durMin} min</div>
            <div><strong>Round-trip Road Distance (S_D):</strong> ${distKm} km</div>
          </div>
        </div>
      `;

      polyline.bindPopup(popupHtml);

      polyline.on("mouseover", function () {
        this.setStyle({ weight: strokeWeight + 2, color: isTopDispatch ? "#d97706" : "#1d4ed8", opacity: 1 });
        const tt = document.getElementById("sim-map-tooltip-card");
        const ttTitle = document.getElementById("sim-tt-title");
        const ttDesc = document.getElementById("sim-tt-desc");
        const ttBadge = document.getElementById("sim-tt-badge");
        if (tt && ttTitle && ttDesc && ttBadge) {
          ttBadge.className = isTopDispatch ? "badge badge-amber" : (isGenuineRoad ? "badge badge-blue" : "badge badge-amber");
          ttBadge.textContent = isTopDispatch ? "Top Dispatch Link" : (isGenuineRoad ? "OSRM Road Route" : "Schematic Fallback");
          ttTitle.textContent = `${uName} ⟷ ${vName}`;
          ttDesc.textContent = `Duration: ${durMin} min • Road Dist: ${distKm} km`;
          tt.style.display = "block";
        }
      });

      polyline.on("mouseout", function () {
        this.setStyle({
          weight: strokeWeight,
          color: strokeColor,
          opacity: strokeOpacity,
        });
      });

      if (isTopDispatch) {
        simDispatchRouteLayer.addLayer(polyline);
      } else {
        simBackboneLayer.addLayer(polyline);
      }
    });

    if (simBounds.isValid()) {
      simMstMap.fitBounds(simBounds, { padding: [30, 30] });
    }
  }

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
