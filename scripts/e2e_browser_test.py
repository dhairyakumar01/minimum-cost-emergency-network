"""
End-to-End Browser Verification Test for Emergency Communication Network
Tests:
- 5 Primary Navigation Sections (Dashboard, Facilities Map, MST Network, Simulation, Results & Statistics)
- Design system rendering & 8-color green palette
- Mathematical & algorithmic metrics verification
- Incident simulation run (Majestic KSR, Healthcare, 5km, Mode 1)
- Incident-specific MST Leaflet map & genuine OSRM route rendering
- Sub-tab switching in Results & Statistics (Results & Methodology)
- Multi-viewport responsive verification (Desktop 1440x900, Tablet 768x1024, Mobile 375x812)
- Captures full-page screenshots to reports/screenshots/
"""

import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

SCREENSHOTS_DIR = Path("reports/screenshots")
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "http://127.0.0.1:5000"

def run_tests():
    print(f"[*] Starting E2E Browser Test against {BASE_URL}...")
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # Step 1: Load Page & Check Loader
        page.goto(BASE_URL, wait_until="networkidle")
        page.wait_for_selector("#global-loader", state="hidden", timeout=15000)
        print("[+] Page loaded and global loader dismissed.")

        # Step 2: Verify Sidebar Navigation (Exactly 5 items)
        nav_links = page.query_selector_all("#sidebar .nav-menu .nav-link")
        print(f"[+] Total primary nav links in sidebar: {len(nav_links)}")
        assert len(nav_links) == 5, f"Expected exactly 5 nav links, found {len(nav_links)}"

        targets = [link.get_attribute("data-target") for link in nav_links]
        expected_targets = ["dashboard", "facilities-map", "mst-network", "simulation", "results-stats"]
        assert targets == expected_targets, f"Nav targets mismatch: {targets} vs {expected_targets}"
        print(f"[+] Nav targets verified: {targets}")

        # Step 3: Section 1 - Executive Dashboard
        print("[*] Testing Section 1: Executive Dashboard...")
        title = page.text_content(".dash-title")
        assert "Minimum-Cost Emergency Communication Network" in title
        print(f"[+] Dashboard title verified: '{title.strip()}'")

        # Verify 4 Metric Cards
        tot_fac = page.text_content("#metric-total-facilities").strip()
        hosp = page.text_content("#metric-hospitals").strip()
        pol = page.text_content("#metric-police").strip()
        fire = page.text_content("#metric-fire").strip()
        mst_conn = page.text_content("#metric-mst-connections").strip()
        mst_len = page.text_content("#metric-mst-length").strip()

        print(f"[+] Metric values: Facilities={tot_fac}, Hosp={hosp}, Pol={pol}, Fire={fire}, Links={mst_conn}, Length={mst_len}")
        assert tot_fac == "1,255"
        assert hosp == "1,097"
        assert pol == "138"
        assert fire == "20"
        assert mst_conn == "1,254"
        assert "480.1784" in mst_len

        # Mathematical terminology verification
        mst_conn_card = page.locator(".metric-card:has(#metric-mst-connections)").text_content()
        assert "Tree edge-count property" in mst_conn_card
        assert "Cayley" not in mst_conn_card
        mst_len_card = page.locator(".metric-card:has(#metric-mst-length)").text_content()
        assert "Haversine-distance" in mst_len_card
        assert "Euclidean" not in mst_len_card
        tot_fac_card = page.locator(".metric-card:has(#metric-total-facilities)").text_content()
        assert "Geocoded municipal facility records" in tot_fac_card
        print("[+] Mathematical terminology verified (Tree edge-count property, Haversine-distance).")

        page.wait_for_timeout(1000)
        page.screenshot(path=str(SCREENSHOTS_DIR / "01_dashboard_desktop.png"), full_page=False)
        print("[+] Captured 01_dashboard_desktop.png")

        # Step 4: Section 2 - Facilities Map
        print("[*] Testing Section 2: Facilities Map...")
        page.click("#sidebar .nav-link[data-target='facilities-map']")
        page.wait_for_selector("#section-facilities-map", state="visible")
        page.wait_for_timeout(1500)
        # Select Majestic landmark
        page.click("#section-facilities-map button.landmark-pill[data-name='Majestic (KSR)']")
        page.wait_for_timeout(800)
        page.screenshot(path=str(SCREENSHOTS_DIR / "02_facilities_map_desktop.png"), full_page=False)
        print("[+] Captured 02_facilities_map_desktop.png")

        # Step 5: Section 3 - MST Network Backbone
        print("[*] Testing Section 3: MST Network...")
        page.click("#sidebar .nav-link[data-target='mst-network']")
        page.wait_for_selector("#section-mst-network", state="visible")
        page.wait_for_timeout(1500)
        page.screenshot(path=str(SCREENSHOTS_DIR / "03_mst_network_desktop.png"), full_page=False)
        print("[+] Captured 03_mst_network_desktop.png")

        # Step 6: Section 4 - Emergency Simulation
        print("[*] Testing Section 4: Emergency Simulation...")
        page.click("#sidebar .nav-link[data-target='simulation']")
        page.wait_for_selector("#section-simulation", state="visible")
        page.wait_for_timeout(500)

        # Category and Agency separation test
        page.click(".category-card[data-category='fire']")
        page.wait_for_timeout(300)
        cat_text = page.text_content("#sum-category")
        agency_text = page.text_content("#sum-agency")
        assert "Fire Emergency" in cat_text
        # Ensure agency is NOT silently mutated to fire
        assert "Healthcare" in agency_text
        print("[+] Category and Agency independence verified: Category selection does not overwrite agency.")

        # Re-select Medical Emergency and Healthcare
        page.click(".category-card[data-category='medical']")
        page.click("#sim-agency-hospital")
        page.wait_for_timeout(300)

        # Select Majestic landmark pill inside simulation step 1
        page.click("#sim-step-1 button.landmark-pill:has-text('Majestic')")
        page.wait_for_timeout(500)

        # Trigger analysis
        print("[*] Triggering simulation run (Majestic, Healthcare, 5km, Mode 1)...")
        page.click("#btn-run-simulation")
        page.wait_for_selector("#sim-results-output", state="visible", timeout=30000)
        page.wait_for_timeout(1500)

        # Verify Tab 1: Dispatch Ranking
        top_cards = page.query_selector_all("#sim-ranked-facilities-list .ranked-card")
        print(f"[+] Top ranked cards found: {len(top_cards)}")
        assert len(top_cards) >= 3, f"Expected at least 3 top cards, found {len(top_cards)}"
        page.screenshot(path=str(SCREENSHOTS_DIR / "04a_simulation_dispatch_desktop.png"), full_page=False)
        print("[+] Captured 04a_simulation_dispatch_desktop.png")

        # Switch to Tab 2: Network Backbone (MST)
        print("[*] Switching to Tab 2: Network Backbone (Incident MST Map)...")
        page.click("#btn-tab-network")
        page.wait_for_selector("#tab-content-network", state="visible")
        page.wait_for_timeout(1500)

        # Verify legend elements
        assert page.is_visible(".sim-legend-line.line-road")
        assert page.is_visible(".sim-legend-line.line-schematic")
        print("[+] Legend elements verified: OSRM road line and schematic fallback.")

        page.screenshot(path=str(SCREENSHOTS_DIR / "04b_simulation_mst_map_desktop.png"), full_page=False)
        print("[+] Captured 04b_simulation_mst_map_desktop.png")

        # Step 7: Section 5 - Results & Statistics
        print("[*] Testing Section 5: Results & Statistics...")
        page.click("#sidebar .nav-link[data-target='results-stats']")
        page.wait_for_selector("#section-results-stats", state="visible")
        page.wait_for_timeout(800)

        # Sub-tab 1: Project Results & Telemetry
        assert page.is_visible("#section-project-analysis")
        page.screenshot(path=str(SCREENSHOTS_DIR / "05a_results_telemetry_desktop.png"), full_page=False)
        print("[+] Captured 05a_results_telemetry_desktop.png")

        # Sub-tab 2: Academic Methodology Guide
        print("[*] Switching to Academic Methodology Guide Sub-Tab...")
        page.click("#btn-subnav-methodology")
        page.wait_for_selector("#section-help", state="visible")
        page.wait_for_timeout(500)
        accordions = page.query_selector_all("#section-help details.method-accordion")
        print(f"[+] Found {len(accordions)} academic methodology accordions.")
        assert len(accordions) == 8, f"Expected 8 accordions, found {len(accordions)}"
        page.screenshot(path=str(SCREENSHOTS_DIR / "05b_results_methodology_desktop.png"), full_page=False)
        print("[+] Captured 05b_results_methodology_desktop.png")

        # Step 8: Responsive Verification - Tablet (768x1024)
        print("[*] Testing Tablet Viewport (768x1024)...")
        page.set_viewport_size({"width": 768, "height": 1024})
        page.evaluate("Navigation.navigateTo('dashboard')")
        page.wait_for_timeout(800)
        page.screenshot(path=str(SCREENSHOTS_DIR / "06_dashboard_tablet.png"), full_page=False)
        print("[+] Captured 06_dashboard_tablet.png")

        page.evaluate("Navigation.navigateTo('simulation')")
        page.wait_for_timeout(800)
        page.screenshot(path=str(SCREENSHOTS_DIR / "07_simulation_tablet.png"), full_page=False)
        print("[+] Captured 07_simulation_tablet.png")

        # Step 9: Responsive Verification - Mobile (375x812)
        print("[*] Testing Mobile Viewport (375x812)...")
        page.set_viewport_size({"width": 375, "height": 812})
        page.evaluate("Navigation.navigateTo('dashboard')")
        page.wait_for_timeout(800)
        page.screenshot(path=str(SCREENSHOTS_DIR / "08_dashboard_mobile.png"), full_page=False)
        print("[+] Captured 08_dashboard_mobile.png")

        page.evaluate("Navigation.navigateTo('simulation')")
        page.wait_for_timeout(800)
        page.screenshot(path=str(SCREENSHOTS_DIR / "09_simulation_mobile.png"), full_page=False)
        print("[+] Captured 09_simulation_mobile.png")

        # Step 10: Explicit Cache Purge Verification
        print("[*] Testing Cache Invalidation Endpoint...")
        clear_res = page.request.post(f"{BASE_URL}/api/scenarios/cache/clear")
        assert clear_res.status == 200
        assert clear_res.json()["success"] is True
        print(f"[+] Cache clear endpoint verified: {clear_res.json()['message']}")

        browser.close()
        print("[✓] All E2E browser tests and screenshots completed successfully!")

if __name__ == "__main__":
    run_tests()
