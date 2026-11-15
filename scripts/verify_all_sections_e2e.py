"""End-to-End browser verification and screenshot capture script.
Tests all 6 sections, runs emergency simulation, verifies all 4 tabs,
and captures fresh desktop and mobile screenshots.
"""

import sys
import os
import time
from playwright.sync_api import sync_playwright

SCREENSHOT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports", "screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

BASE_URL = "http://127.0.0.1:5000"

def run_e2e_verification():
    console_errors = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        
        # ---------------------------------------------------------------------
        # 1. Desktop Viewport (1440 x 900)
        # ---------------------------------------------------------------------
        print("[1/3] Launching Desktop context (1440x900)...")
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda exc: console_errors.append(str(exc)))
        
        # Section 1: Dashboard
        print("  - Navigating to Dashboard...")
        page.goto(BASE_URL, wait_until="networkidle")
        page.wait_for_selector("#section-dashboard", state="visible")
        page.wait_for_timeout(1000)
        
        dash_fac_count = page.locator("#metric-total-facilities").inner_text()
        print(f"    Total Facilities on Dashboard: {dash_fac_count}")
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "desktop_1_dashboard.png"), full_page=False)
        
        # Section 2: Facilities Map
        print("  - Navigating to Facilities Map...")
        page.click("button:has-text('Facilities Map')")
        page.wait_for_selector("#section-facilities-map", state="visible")
        page.wait_for_timeout(2000)
        
        # Verify map container has height > 0 and tiles loaded
        map_info = page.evaluate("""() => {
            const el = document.getElementById('leaflet-map');
            const tiles = el ? el.querySelectorAll('.leaflet-tile-loaded').length : 0;
            const markers = el ? el.querySelectorAll('.leaflet-marker-icon').length : 0;
            const rect = el ? el.getBoundingClientRect() : null;
            return { rect, tiles, markers };
        }""")
        print(f"    Facilities Map rect: {map_info['rect']}, tiles: {map_info['tiles']}, markers: {map_info['markers']}")
        assert map_info['rect']['height'] > 500, f"Map height too small: {map_info['rect']['height']}"
        assert map_info['tiles'] > 0, "No Leaflet map tiles loaded!"
        
        # Test preset click
        page.click("button.landmark-pill:has-text('Majestic')")
        page.wait_for_timeout(500)
        
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "desktop_2_facilities_map.png"), full_page=False)
        
        # Section 3: MST Network
        print("  - Navigating to MST Network...")
        page.click("nav button:has-text('MST Network'), a:has-text('MST Network')")
        page.wait_for_selector("#section-mst-network", state="visible")
        page.wait_for_timeout(2000)
        
        mst_map_info = page.evaluate("""() => {
            const el = document.getElementById('mst-leaflet-map');
            const tiles = el ? el.querySelectorAll('.leaflet-tile-loaded').length : 0;
            const lines = el ? el.querySelectorAll('svg path').length : 0;
            return { tiles, lines };
        }""")
        print(f"    MST Network map tiles: {mst_map_info['tiles']}, svg lines: {mst_map_info['lines']}")
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "desktop_3_mst_network.png"), full_page=False)
        
        # Section 4: Emergency Simulation
        print("  - Navigating to Emergency Simulation...")
        page.click("nav button:has-text('Simulation'), a:has-text('Simulation')")
        page.wait_for_selector("#section-simulation", state="visible")
        page.wait_for_timeout(800)
        
        # Step screenshot before running
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "desktop_4_simulation_setup.png"), full_page=False)
        
        # Run simulation
        print("  - Triggering Run Dispatch Analysis...")
        page.click("#btn-run-simulation")
        
        # Wait for results container to become visible
        page.wait_for_selector("#sim-results-output", state="visible", timeout=30000)
        page.wait_for_timeout(1000)
        
        # Tab 1: Dispatch Ranking
        print("    Verifying Tab 1: Dispatch Ranking...")
        top3_count = page.locator("#sim-ranked-facilities-list .ranked-card").count()
        table_rows = page.locator("#tbody-dispatch-full tr").count()
        print(f"    Top 3 cards: {top3_count}, Table rows: {table_rows}")
        assert top3_count == 3, f"Expected 3 top ranked cards, got {top3_count}"
        assert table_rows > 0, "Dispatch table is empty"
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "desktop_4_sim_tab1_dispatch.png"), full_page=False)
        
        # Tab 2: Network Backbone
        print("    Verifying Tab 2: Network Backbone...")
        page.click("#btn-tab-network")
        page.wait_for_selector("#tab-content-network", state="visible")
        page.wait_for_timeout(500)
        tree_edges_val = page.locator("#res-tree-edges").inner_text()
        print(f"    Spanning edges: {tree_edges_val}")
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "desktop_4_sim_tab2_network.png"), full_page=False)
        
        # Tab 3: Validation
        print("    Verifying Tab 3: Validation...")
        page.click("#btn-tab-validation")
        page.wait_for_selector("#tab-content-validation", state="visible")
        page.wait_for_timeout(500)
        val_status = page.locator("#val-structural-badge").inner_text()
        opt_status = page.locator("#val-optimality-badge").inner_text()
        print(f"    Structural: {val_status}, Optimality: {opt_status}")
        assert "PASS" in val_status or "MSF" in val_status, f"Unexpected validation status: {val_status}"
        assert "0 Violations" in opt_status, f"Unexpected optimality violations: {opt_status}"
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "desktop_4_sim_tab3_validation.png"), full_page=False)
        
        # Tab 4: Candidates & Exclusions
        print("    Verifying Tab 4: Candidates & Exclusions...")
        page.click("#btn-tab-exclusions")
        page.wait_for_selector("#tab-content-exclusions", state="visible")
        page.wait_for_timeout(500)
        excl_badge = page.locator("#exclusions-count-badge").inner_text()
        print(f"    Exclusions badge: {excl_badge}")
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "desktop_4_sim_tab4_exclusions.png"), full_page=False)
        
        # Section 5: Project Analysis
        print("  - Navigating to Project Analysis...")
        page.click("nav button:has-text('Project Analysis'), a:has-text('Project Analysis')")
        page.wait_for_selector("#section-project-analysis", state="visible")
        page.wait_for_timeout(1000)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "desktop_5_project_analysis.png"), full_page=False)
        
        # Section 6: Help & Methodology
        print("  - Navigating to Help & Methodology...")
        page.click("nav button:has-text('Help'), a:has-text('Help')")
        page.wait_for_selector("#section-help", state="visible")
        page.wait_for_timeout(800)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "desktop_6_help_methodology.png"), full_page=False)
        
        context.close()
        
        # ---------------------------------------------------------------------
        # 2. Tablet Viewport (768 x 1024)
        # ---------------------------------------------------------------------
        print("[2/3] Launching Tablet context (768x1024)...")
        tab_context = browser.new_context(viewport={"width": 768, "height": 1024})
        tab_page = tab_context.new_page()
        tab_page.goto(BASE_URL, wait_until="networkidle")
        tab_page.wait_for_selector("#section-dashboard", state="visible")
        tab_page.wait_for_timeout(1000)
        tab_page.screenshot(path=os.path.join(SCREENSHOT_DIR, "tablet_1_dashboard.png"), full_page=False)
        
        # Tablet Simulation
        tab_page.click("button:has-text('Start Emergency Simulation')")
        tab_page.wait_for_selector("#section-simulation", state="visible")
        tab_page.wait_for_timeout(800)
        tab_page.screenshot(path=os.path.join(SCREENSHOT_DIR, "tablet_4_simulation.png"), full_page=False)
        tab_context.close()
        
        # ---------------------------------------------------------------------
        # 3. Mobile Viewport (375 x 812 - iPhone X)
        # ---------------------------------------------------------------------
        print("[3/3] Launching Mobile context (375x812)...")
        mob_context = browser.new_context(viewport={"width": 375, "height": 812}, is_mobile=True)
        mob_page = mob_context.new_page()
        mob_page.goto(BASE_URL, wait_until="networkidle")
        mob_page.wait_for_selector("#section-dashboard", state="visible")
        mob_page.wait_for_timeout(1000)
        mob_page.screenshot(path=os.path.join(SCREENSHOT_DIR, "mobile_1_dashboard.png"), full_page=False)
        
        # Mobile Map
        mob_page.evaluate("Navigation.navigateTo('facilities-map')")
        mob_page.wait_for_selector("#section-facilities-map", state="visible")
        mob_page.wait_for_timeout(1500)
        mob_page.screenshot(path=os.path.join(SCREENSHOT_DIR, "mobile_2_facilities_map.png"), full_page=False)
        
        # Mobile Sim
        mob_page.evaluate("Navigation.navigateTo('simulation')")
        mob_page.wait_for_selector("#section-simulation", state="visible")
        mob_page.wait_for_timeout(1000)
        mob_page.screenshot(path=os.path.join(SCREENSHOT_DIR, "mobile_4_simulation.png"), full_page=False)
        mob_context.close()
        
        browser.close()
        
    print("\nE2E VERIFICATION COMPLETED SUCCESSFULLY!")
    if console_errors:
        print(f"Warning: {len(console_errors)} console errors caught:")
        for err in console_errors[:5]:
            print(f"  {err}")
    else:
        print("0 uncaught console or page errors recorded!")

if __name__ == "__main__":
    run_e2e_verification()
