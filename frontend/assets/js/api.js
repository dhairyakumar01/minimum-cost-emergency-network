/**
 * API Client Module for Bengaluru Emergency Network
 * Encapsulates backend HTTP calls, timeouts, error parsing, and retry helpers.
 */

const API = (function () {
  const BASE_URL = window.location.origin;

  /**
   * Universal fetch wrapper with timeout and standard envelope parsing.
   */
  async function request(endpoint, options = {}, timeoutMs = 8000) {
    const url = `${BASE_URL}${endpoint}`;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
        headers: {
          "Accept": "application/json",
          "Content-Type": "application/json",
          ...(options.headers || {}),
        },
      });

      clearTimeout(timer);
      const data = await response.json().catch(() => null);

      if (!response.ok) {
        const errorMsg = data?.error?.message || data?.message || `HTTP ${response.status}: ${response.statusText}`;
        const errorCode = data?.error?.code || data?.code || "HTTP_ERROR";
        const err = new Error(errorMsg);
        err.code = errorCode;
        err.status = response.status;
        err.data = data;
        throw err;
      }

      if (data && data.success === false) {
        const errorMsg = data?.error?.message || data?.message || "Operation failed";
        const errorCode = data?.error?.code || data?.code || "API_ERROR";
        const err = new Error(errorMsg);
        err.code = errorCode;
        throw err;
      }

      return data?.data !== undefined ? data.data : data;
    } catch (err) {
      clearTimeout(timer);
      if (err.name === "AbortError") {
        const timeoutErr = new Error(`Request timed out after ${timeoutMs}ms`);
        timeoutErr.code = "TIMEOUT";
        throw timeoutErr;
      }
      throw err;
    }
  }

  return {
    async getHealth() {
      return request("/api/health", { method: "GET" }, 4000);
    },

    async getAudit() {
      return request("/api/dataset/audit", { method: "GET" }, 6000);
    },

    async getBenchmarks() {
      return request("/api/benchmarks", { method: "GET" }, 4000);
    },

    async getManifest() {
      return request("/api/methodology/manifest", { method: "GET" }, 5000);
    },

    async getFacilities({ agency = null, search = null, page = null, perPage = null } = {}) {
      const params = new URLSearchParams();
      if (agency) params.append("agency", agency);
      if (search) params.append("search", search);
      if (page) params.append("page", page);
      if (perPage) params.append("per_page", perPage);

      const qs = params.toString();
      const endpoint = `/api/facilities${qs ? `?${qs}` : ""}`;
      return request(endpoint, { method: "GET" }, 8000);
    },

    async getFacility(facilityId) {
      return request(`/api/facilities/${encodeURIComponent(facilityId)}`, { method: "GET" });
    },

    async getFullMST(algo = "kruskal") {
      return request(`/api/global-mst?algo=${encodeURIComponent(algo)}`, { method: "GET" }, 6000);
    },

    async geocode(query) {
      return request(`/api/geocode?q=${encodeURIComponent(query)}`, { method: "GET" }, 5000);
    },

    async createScenario(payload) {
      return request("/api/scenarios", {
        method: "POST",
        body: JSON.stringify(payload),
      }, 15000);
    },

    async getScenarioStatus(scenarioId) {
      return request(`/api/scenarios/${encodeURIComponent(scenarioId)}/status`, { method: "GET" }, 8000);
    },

    async getScenarioResult(scenarioId) {
      return request(`/api/scenarios/${encodeURIComponent(scenarioId)}/result`, { method: "GET" }, 15000);
    },

    async listScenarios() {
      return request("/api/scenarios", { method: "GET" }, 4000);
    },

    async getTradeoff(scenarioId) {
      return request(`/api/scenarios/${encodeURIComponent(scenarioId)}/tradeoff`, { method: "GET" }, 5000);
    },

    async getTrace(scenarioId) {
      return request(`/api/scenarios/${encodeURIComponent(scenarioId)}/trace`, { method: "GET" }, 5000);
    },

    async getMstTrace(graph = "global", algo = "kruskal", scenarioId = null) {
      let url = `/api/mst/trace?graph=${encodeURIComponent(graph)}&algo=${encodeURIComponent(algo)}`;
      if (scenarioId) url += `&scenario_id=${encodeURIComponent(scenarioId)}`;
      return request(url, { method: "GET" }, 15000);
    },

    async getMstCompare(graph = "global", scenarioId = null) {
      let url = `/api/mst/compare?graph=${encodeURIComponent(graph)}`;
      if (scenarioId) url += `&scenario_id=${encodeURIComponent(scenarioId)}`;
      return request(url, { method: "GET" }, 15000);
    },
  };
})();

window.API = API;
