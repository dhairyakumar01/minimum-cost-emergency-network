/**
 * Navigation Module for Single-Page Application (SPA)
 * Manages view switching across the 5 primary sections.
 */

const Navigation = (function () {
  const SECTIONS = {
    "dashboard": { title: "Executive Dashboard", icon: "📊" },
    "facilities-map": { title: "Facilities Map", icon: "🗺️" },
    "mst-network": { title: "MST Network Backbone", icon: "🕸️" },
    "simulation": { title: "Emergency Simulation", icon: "🚨" },
    "results-stats": { title: "Results & Statistics", icon: "📈" },
  };

  const ALIASES = {
    "project-analysis": "results-stats",
    "help": "results-stats",
  };

  let currentSection = "dashboard";
  const listeners = [];

  function init() {
    // Bind click events to navigation links
    document.querySelectorAll(".nav-link").forEach((link) => {
      link.addEventListener("click", (e) => {
        e.preventDefault();
        let target = link.getAttribute("data-target");
        if (target && ALIASES[target]) {
          const subTarget = target;
          target = ALIASES[target];
          navigateTo(target);
          if (window.App && typeof window.App.switchResultsSubTab === "function") {
            window.App.switchResultsSubTab(subTarget === "help" ? "methodology" : "results");
          }
          return;
        }
        if (target && SECTIONS[target]) {
          navigateTo(target);
        }
      });
    });

    // Check URL hash on load
    let hash = window.location.hash.replace("#", "").trim();
    if (hash && ALIASES[hash]) {
      const subTarget = hash;
      hash = ALIASES[hash];
      navigateTo(hash, false);
      setTimeout(() => {
        if (window.App && typeof window.App.switchResultsSubTab === "function") {
          window.App.switchResultsSubTab(subTarget === "help" ? "methodology" : "results");
        }
      }, 50);
    } else if (hash && SECTIONS[hash]) {
      navigateTo(hash, false);
    } else {
      navigateTo("dashboard", false);
    }

    // Handle browser back/forward buttons
    window.addEventListener("hashchange", () => {
      let h = window.location.hash.replace("#", "").trim();
      if (h && ALIASES[h]) {
        const subTarget = h;
        h = ALIASES[h];
        if (h !== currentSection) {
          navigateTo(h, false);
        }
        if (window.App && typeof window.App.switchResultsSubTab === "function") {
          window.App.switchResultsSubTab(subTarget === "help" ? "methodology" : "results");
        }
      } else if (h && SECTIONS[h] && h !== currentSection) {
        navigateTo(h, false);
      }
    });
  }

  function navigateTo(sectionId, updateHash = true) {
    if (ALIASES[sectionId]) {
      const subTarget = sectionId;
      sectionId = ALIASES[sectionId];
      if (window.App && typeof window.App.switchResultsSubTab === "function") {
        window.App.switchResultsSubTab(subTarget === "help" ? "methodology" : "results");
      }
    }

    if (!SECTIONS[sectionId]) return;

    currentSection = sectionId;

    // Update active nav link
    document.querySelectorAll(".nav-link").forEach((link) => {
      const t = link.getAttribute("data-target");
      if (t === sectionId || (ALIASES[t] && ALIASES[t] === sectionId)) {
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

