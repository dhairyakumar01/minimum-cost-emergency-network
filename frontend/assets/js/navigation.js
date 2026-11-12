/**
 * Navigation Module for Single-Page Application (SPA)
 * Manages view switching across the 6 primary sections.
 */

const Navigation = (function () {
  const SECTIONS = {
    "dashboard": { title: "System Dashboard", icon: "📊" },
    "facilities-map": { title: "Facilities Map", icon: "🗺️" },
    "mst-network": { title: "MST Network Visualization", icon: "🕸️" },
    "simulation": { title: "Emergency Simulation", icon: "🚨" },
    "project-analysis": { title: "Project Analysis & Results", icon: "📈" },
    "help": { title: "Help & System Methodology", icon: "❓" },
  };

  let currentSection = "dashboard";
  const listeners = [];

  function init() {
    // Bind click events to navigation links
    document.querySelectorAll(".nav-link").forEach((link) => {
      link.addEventListener("click", (e) => {
        e.preventDefault();
        const target = link.getAttribute("data-target");
        if (target && SECTIONS[target]) {
          navigateTo(target);
        }
      });
    });

    // Check URL hash on load
    const hash = window.location.hash.replace("#", "").trim();
    if (hash && SECTIONS[hash]) {
      navigateTo(hash, false);
    } else {
      navigateTo("dashboard", false);
    }

    // Handle browser back/forward buttons
    window.addEventListener("hashchange", () => {
      const h = window.location.hash.replace("#", "").trim();
      if (h && SECTIONS[h] && h !== currentSection) {
        navigateTo(h, false);
      }
    });
  }

  function navigateTo(sectionId, updateHash = true) {
    if (!SECTIONS[sectionId]) return;

    currentSection = sectionId;

    // Update active nav link
    document.querySelectorAll(".nav-link").forEach((link) => {
      const t = link.getAttribute("data-target");
      if (t === sectionId) {
        link.classList.add("active");
      } else {
        link.classList.remove("active");
      }
    });

    // Toggle content visibility
    document.querySelectorAll(".view-section").forEach((sec) => {
      if (sec.id === `section-${sectionId}`) {
        sec.style.display = "block";
      } else {
        sec.style.display = "none";
      }
    });

    // Update top bar title
    const meta = SECTIONS[sectionId];
    const titleEl = document.getElementById("current-page-title");
    if (titleEl) {
      titleEl.innerHTML = `<span style="margin-right:8px;">${meta.icon}</span> ${meta.title}`;
    }

    // Update URL hash without jumping
    if (updateHash) {
      history.pushState(null, "", `#${sectionId}`);
    }

    // Trigger registered view listeners
    listeners.forEach((fn) => fn(sectionId));
  }

  return {
    init,
    navigateTo,
    getCurrentSection: () => currentSection,
    onNavigate: (fn) => listeners.push(fn),
  };
})();

window.Navigation = Navigation;

