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
          ...(options.headers || {}),
        },
      });

      clearTimeout(timer);
      const data = await response.json().catch(() => null);

      if (!response.ok) {
        const errorMsg = data?.error?.message || `HTTP ${response.status}: ${response.statusText}`;
        const errorCode = data?.error?.code || "HTTP_ERROR";
        const err = new Error(errorMsg);
        err.code = errorCode;
        err.status = response.status;
        err.data = data;
        throw err;
      }

      if (data && data.success === false) {
        const err = new Error(data.error?.message || "Operation failed");
        err.code = data.error?.code || "API_ERROR";
        throw err;
      }

      return data?.data || data;
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
    /**
     * Retrieve system health and dataset status.
     */
    async getHealth() {
      return request("/api/health", { method: "GET" }, 4000);
    },

    /**
     * Retrieve emergency facilities with optional agency filter and search.
     */
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

    /**
     * Retrieve a single facility by ID.
     */
    async getFacility(facilityId) {
      return request(`/api/facilities/${encodeURIComponent(facilityId)}`, { method: "GET" });
    },

    /**
     * Retrieve the precomputed global MST.
     */
    async getFullMST(algo = "kruskal") {
      return request(`/api/mst/full?algo=${encodeURIComponent(algo)}`, { method: "GET" }, 6000);
    },
  };
})();

// Attach to window
window.API = API;

