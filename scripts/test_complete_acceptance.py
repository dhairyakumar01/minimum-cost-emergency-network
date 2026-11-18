import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

FLASK_BASE = "http://127.0.0.1:5000"
ROOT = Path(r"c:\Users\DHAIRYA\Downloads\minimum_cost_emergency_network\minimum_cost_emergency_network")
SCREENSHOTS_DIR = ROOT / "reports" / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

def run_acceptance_suite():
    print("=" * 70)
    print("STARTING COMPLETE ACCEPTANCE AUDIT & BROWSER VERIFICATION SUITE")
    print("=" * 70)

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 920})
        page = context.new_page()

        js_errors = []
        page.on("pageerror", lambda err: js_errors.append(str(err)))
        page.on("console", lambda msg: print(f"  [CONSOLE] {msg.type}: {msg.text}") if msg.type in ["error", "warning"] else None)

        # -------------------------------------------------------------
        # TEST 1: Dashboard
        # -------------------------------------------------------------
        print("\n--- TEST 1: Executive Dashboard & Overview Map ---")
        page.goto(f"{FLASK_BASE}/", wait_until="domcontentloaded")
        time.sleep(2.0)

        # Verify 4 Executive Metrics
        total_facs = page.locator("#metric-total-facilities").inner_text()
        mst_len = page.locator("#metric-mst-length").inner_text()
        tree_edges = page.locator("#metric-mst-connections").inner_text()
        print(f"  Executive Metrics: Facilities={total_facs}, MST Length={mst_len}, Tree Edges={tree_edges}")
        assert "1,255" in total_facs, f"Expected 1,255 facilities, got {total_facs}"
        assert "480.1784" in mst_len, f"Expected 480.1784 km, got {mst_len}"
        assert "1,254" in tree_edges, f"Expected 1,254 edges, got {tree_edges}"

        # Check Overview Map
        overview_map = page.locator("#dashboard-overview-map")
        assert overview_map.is_visible(), "Dashboard overview map must be visible"
        page.screenshot(path=str(SCREENSHOTS_DIR / "final_1_dashboard.png"))
        print("  ✓ Dashboard verified cleanly. Screenshot captured.")

        # -------------------------------------------------------------
        # TEST 2: Facilities Map (Search Separation)
        # -------------------------------------------------------------
        print("\n--- TEST 2: Facilities Map & Search Separation ---")
        page.click("a[data-target='facilities-map']")
        time.sleep(1.5)

        # Facility search with zero match
        fac_search = page.locator("#facility-map-search")
        fac_search.fill("xyznonexistentfacility12345")
        time.sleep(0.5)
        count_badge = page.locator("#rendered-facilities-count").inner_text()
        print(f"  Zero-match search badge text: '{count_badge}'")
        assert "No registered emergency facility matched this query." in count_badge, f"Unexpected badge text: {count_badge}"

        # Clear search
        fac_search.fill("")
        time.sleep(0.5)
        count_badge_restored = page.locator("#rendered-facilities-count").inner_text()
        assert "1,255" in count_badge_restored, f"Badge not restored: {count_badge_restored}"

        # Landmark / Incident Search
        inc_search = page.locator("#incident-location-search")
        assert inc_search.is_visible(), "Incident location search input must be visible"
        inc_search.fill("Majestic")
        page.keyboard.press("Enter")
        time.sleep(1.0)
        inc_pill = page.locator("#incident-status-pill").inner_text()
        print(f"  Incident pill after geocode: '{inc_pill}'")
        assert "Majestic" in inc_pill or "12.97" in inc_pill, f"Incident not placed: {inc_pill}"

        page.screenshot(path=str(SCREENSHOTS_DIR / "final_2_facilities_map.png"))
        print("  ✓ Facilities Map verified cleanly. Screenshot captured.")

        # -------------------------------------------------------------
        # TEST 3: Algorithm Construction Simulator & Comparison Suite
        # -------------------------------------------------------------
        print("\n--- TEST 3: Algorithm Construction Simulator ---")
        page.click("a[data-target='mst-network']")
        time.sleep(1.5)

        # Simulator Subtab
        total_steps = page.locator("#sim-total-steps").inner_text()
        for _ in range(20):
            if total_steps != "0":
                break
            time.sleep(0.5)
            total_steps = page.locator("#sim-total-steps").inner_text()
        print(f"  Simulator loaded events: {total_steps}")
        assert int(total_steps) > 1000, f"Expected >1000 events, got {total_steps}"

        # Step next
        page.click("#btn-sim-next")
        time.sleep(0.3)
        assert page.locator("#sim-step-num").inner_text() == "1"

        # Convergence Subtab
        page.click("#tab-mst-compare")
        time.sleep(1.0)
        k_weight = page.locator("#cmp-kruskal-weight").inner_text()
        p_weight = page.locator("#cmp-prim-weight").inner_text()
        print(f"  Algorithm Comparison: Kruskal={k_weight}, Prim={p_weight}")
        assert k_weight == p_weight, f"Expected identical weights, got Kruskal={k_weight} vs Prim={p_weight}"
        assert "480.1784" in k_weight, f"Expected 480.1784 km, got {k_weight}"

        # Static Topology Subtab & Edge Inspector
        page.click("#tab-mst-static")
        time.sleep(1.0)
        page.screenshot(path=str(SCREENSHOTS_DIR / "final_3_simulator_static.png"))
        print("  ✓ Simulator and Comparison suite verified cleanly.")

        # -------------------------------------------------------------
        # TEST 4: Emergency Simulation & Geographic MST Map
        # -------------------------------------------------------------
        print("\n--- TEST 4: Emergency Simulation Execution & Result Verification ---")
        page.click("a[data-target='simulation']")
        time.sleep(1.5)

        # Click Run Dispatch Analysis
        print("  Triggering Run Dispatch Analysis...")
        page.click("#btn-run-simulation")
        time.sleep(1.0)

        # Wait for simulation to finish (polling up to 40s)
        for i in range(80):
            time.sleep(0.5)
            btn_text = page.locator("#btn-run-simulation").inner_text()
            if "Run Dispatch Analysis" in btn_text and page.locator("#sim-results-output").is_visible():
                break

        sim_status = page.locator("#sim-exec-status").inner_text()
        print(f"  Simulation completed status: {sim_status}")
        assert "Analysis complete" in sim_status, f"Simulation did not finish successfully: {sim_status}"

        # Tab 1: Dispatch Ranking & Detour Ratio
        top_card = page.locator(".ranked-card-top")
        assert top_card.is_visible(), "Top-1 recommended dispatch card must have ranked-card-top class"
        top_name = page.locator(".ranked-card-top .ranked-name").inner_text()
        top_dist = page.locator(".ranked-card-top .ranked-dist").inner_text()
        print(f"  Top-1 Recommendation: {top_name} ({top_dist})")

        # Tab 2: Dedicated Geographic MST Map & Layer Controls
        print("  Inspecting Simulation Geographic Network Backbone Map...")
        page.click("#btn-tab-network")
        time.sleep(1.0)
        sim_map = page.locator("#sim-mst-leaflet-map")
        assert sim_map.is_visible(), "Simulation Leaflet map must be visible"

        # Check Leaflet layer control is present
        layer_ctrl = page.locator(".leaflet-control-layers")
        assert layer_ctrl.is_visible(), "Leaflet Layer Control must be present on simulation map"

        page.screenshot(path=str(SCREENSHOTS_DIR / "final_4_simulation_map.png"))
        print("  ✓ Simulation Geographic MST map and layer controls verified.")

        # Tab 3: Optimality Validation
        page.click("#btn-tab-validation")
        time.sleep(0.5)
        val_badge = page.locator("#val-structural-badge").inner_text()
        print(f"  Structural Validation Badge: {val_badge}")
        assert "PASS" in val_badge or "MSF" in val_badge, f"Validation failure: {val_badge}"

        # Tab 4: Exclusions
        page.click("#btn-tab-exclusions")
        time.sleep(0.5)
        excl_badge = page.locator("#exclusions-count-badge").inner_text()
        print(f"  Exclusions Count Badge: {excl_badge}")

        # Invalidation Test: Modify radius and verify #sim-stale-notice displays
        print("  Testing strict result invalidation on parameter modification...")
        page.evaluate("App.onRadiusChange(7.5)")
        time.sleep(0.5)
        stale_notice = page.locator("#sim-stale-notice")
        assert stale_notice.is_visible(), "Stale result notice banner must be visible after parameter modification"
        print("  ✓ Stale result notice confirmed after parameter change.")

        # -------------------------------------------------------------
        # TEST 5: Results & Statistics
        # -------------------------------------------------------------
        print("\n--- TEST 5: Results & Statistics (Telemetry + 8-Module Guide) ---")
        page.click("a[data-target='results-stats']")
        time.sleep(1.0)

        # Telemetry panel
        telemetry_panel = page.locator("#section-project-analysis")
        assert telemetry_panel.is_visible(), "Project analysis telemetry panel must be visible"

        # Switch to 8-Module Academic Methodology Guide
        page.click("#btn-subnav-methodology")
        time.sleep(0.5)
        help_panel = page.locator("#section-help")
        assert help_panel.is_visible(), "Academic Methodology Guide panel must be visible"

        # Verify all 8 modules are present
        accordions = page.locator(".method-accordion")
        acc_count = accordions.count()
        print(f"  Academic Guide Modules found: {acc_count}")
        assert acc_count == 8, f"Expected 8 Academic Methodology Guide modules, found {acc_count}"
        print("  ✓ All 8 Academic Methodology Guide modules verified.")

        page.screenshot(path=str(SCREENSHOTS_DIR / "final_5_methodology_guide.png"))

        # -------------------------------------------------------------
        # CHECK JS ERRORS
        # -------------------------------------------------------------
        print("\n--- JAVASCRIPT CONSOLE ERROR AUDIT ---")
        if js_errors:
            print(f"  FAILED: Detected {len(js_errors)} JavaScript errors:")
            for err in js_errors:
                print(f"    - {err}")
            sys.exit(1)
        else:
            print("  ✓ ZERO JavaScript errors detected across entire session.")

        browser.close()

    print("\n" + "=" * 70)
    print("ALL ACCEPTANCE TESTS PASSED SYSTEMATICALLY AND SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    run_acceptance_suite()
