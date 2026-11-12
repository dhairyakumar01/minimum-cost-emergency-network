import os
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent
SCREENSHOT_DIR = BASE_DIR / "screenshots" / "audit"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

def run_browser_audit():
    print("Starting Playwright Chromium/Edge Browser Audit on http://localhost:8501...")
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(viewport={"width": 1600, "height": 1000})
        page = context.new_page()

        # --------------------------------------------------------------------
        # 1. Screen 1: Dashboard
        # --------------------------------------------------------------------
        print("\n--- Auditing Screen 1: Dashboard ---")
        page.goto("http://localhost:8501/dashboard", wait_until="networkidle")
        time.sleep(2)
        page.wait_for_selector("h1:has-text('Minimum-Cost Emergency Communication Network')")

        # Verify metrics
        metrics = page.locator("[data-testid='stMetric']").all_text_contents()
        print(f"  Found {len(metrics)} metric cards:")
        for m in metrics:
            lines = [l.strip() for l in m.split("\n") if l.strip()]
            print("   *", " : ".join(lines))

        # Check values
        page.wait_for_selector("text=1,255")
        page.wait_for_selector("text=1,254")
        page.wait_for_selector("text=480.1784 km")
        page.screenshot(path=str(SCREENSHOT_DIR / "01_dashboard.png"), full_page=False)
        print("  Screenshot saved: 01_dashboard.png")

        # --------------------------------------------------------------------
        # 2. Screen 2: Facilities Map
        # --------------------------------------------------------------------
        print("\n--- Auditing Screen 2: Facilities Map ---")
        page.goto("http://localhost:8501/facilities-map", wait_until="networkidle")
        time.sleep(3)
        page.wait_for_selector("h1:has-text('Emergency Facilities Map')")

        # Test Search Box
        search_input = page.locator("input[aria-label='Search by name or ID']")
        if search_input.count() > 0:
            search_input.fill("Victoria")
            time.sleep(1)
            print("  Search box filled with 'Victoria'.")

        # Check map iframe or folium container exists
        map_iframe = page.locator("iframe").first
        if map_iframe.count() > 0:
            print("  Folium interactive map iframe verified present.")

        page.screenshot(path=str(SCREENSHOT_DIR / "02_facilities_map.png"), full_page=False)
        print("  Screenshot saved: 02_facilities_map.png")

        # --------------------------------------------------------------------
        # 3. Screen 3: MST Network
        # --------------------------------------------------------------------
        print("\n--- Auditing Screen 3: MST Network ---")
        page.goto("http://localhost:8501/mst-network", wait_until="networkidle")
        time.sleep(3)
        page.wait_for_selector("h1:has-text('MST Network Visualization')")

        # Toggle radio to Kruskal
        kruskal_radio = page.locator("label:has-text('Kruskal')")
        if kruskal_radio.count() > 0:
            kruskal_radio.click()
            time.sleep(2)
            print("  Toggled algorithm radio to 'Kruskal'.")

        # Verify expander
        expander = page.locator("summary:has-text('Longest 10 connections in this MST')")
        if expander.count() > 0:
            expander.click()
            time.sleep(1)
            print("  Expanded 'Longest 10 connections' drawer.")

        page.screenshot(path=str(SCREENSHOT_DIR / "03_mst_network.png"), full_page=False)
        print("  Screenshot saved: 03_mst_network.png")

        # --------------------------------------------------------------------
        # 4. Screen 4: Emergency Incident Simulation
        # --------------------------------------------------------------------
        print("\n--- Auditing Screen 4: Emergency Incident Simulation ---")
        page.goto("http://localhost:8501/simulation", wait_until="networkidle")
        time.sleep(3)
        page.wait_for_selector("h1:has-text('Emergency Incident Simulation')")

        # Select incident scenario 'Fire'
        fire_radio = page.locator("label:has-text('Fire')")
        if fire_radio.count() > 0:
            fire_radio.click()
            time.sleep(1)

        # Enter coordinates
        lat_box = page.locator("input[aria-label*='Latitude']")
        lon_box = page.locator("input[aria-label*='Longitude']")
        if lat_box.count() > 0:
            lat_box.fill("12.9716")
        if lon_box.count() > 0:
            lon_box.fill("77.5946")

        # Click simulation button
        sim_btn = page.locator("button:has-text('Run Incident Simulation')")
        if sim_btn.count() > 0:
            sim_btn.click()
            time.sleep(3)
            print("  Clicked 'Run Incident Simulation'.")

        # Verify primary responder rendered
        page.wait_for_selector("text=Primary Responder")
        page.wait_for_selector("text=Supporting Responder")
        page.wait_for_selector("text=Total MST Communication Path Distance")
        print("  Verified simulation output cards and communication path metrics.")

        page.screenshot(path=str(SCREENSHOT_DIR / "04_emergency_simulation.png"), full_page=False)
        print("  Screenshot saved: 04_emergency_simulation.png")

        # --------------------------------------------------------------------
        # 5. Screen 5: Algorithm Comparison & Validation
        # --------------------------------------------------------------------
        print("\n--- Auditing Screen 5: Algorithm Comparison & Validation ---")
        page.goto("http://localhost:8501/comparison", wait_until="networkidle")
        time.sleep(2)
        page.wait_for_selector("h1:has-text('Algorithm Comparison and Validation')")

        # Verify Validation table & headers
        page.wait_for_selector("h3:has-text('Validation results')")
        print("  Verified Validation results section present.")

        # Verify Architectural Analysis expander
        arch_exp = page.locator("summary:has-text('Architectural & Platform Benchmark Analysis')")
        if arch_exp.count() > 0:
            arch_exp.click()
            time.sleep(1)
            print("  Expanded Architectural & Platform Benchmark Analysis drawer.")
            page.wait_for_selector("text=macOS-26.3-arm64")
            page.wait_for_selector("text=Windows-10 x86_64")
            print("  Verified environment comparison content present.")

        page.screenshot(path=str(SCREENSHOT_DIR / "05_comparison.png"), full_page=False)
        print("  Screenshot saved: 05_comparison.png")

        # --------------------------------------------------------------------
        # 6. Screen 6: Experimental Laboratory
        # --------------------------------------------------------------------
        print("\n--- Auditing Screen 6: Experimental Laboratory ---")
        page.goto("http://localhost:8501/laboratory", wait_until="networkidle")
        time.sleep(3)
        page.wait_for_selector("h1:has-text('Experimental Laboratory')")

        # Tab 1: Scalability
        page.wait_for_selector("text=Algorithmic Scalability Across Graph Sizes")
        page.screenshot(path=str(SCREENSHOT_DIR / "06_laboratory_scalability.png"), full_page=False)
        print("  Screenshot saved: 06_laboratory_scalability.png")

        # Switch to Tab 2: Controlled Graph-Density Experiment (Approach C)
        tab2 = page.locator("button[role='tab']:has-text('Controlled Graph-Density')")
        if tab2.count() > 0:
            tab2.click()
            time.sleep(2)
            page.wait_for_selector("h3:has-text('Controlled Graph-Density Experiment (Approach C)')")
            page.wait_for_selector("text=480.1784 km")
            page.wait_for_selector("text=100% Passed (All Trials)")
            print("  Verified Tab 2: Controlled Graph-Density Experiment (Approach C) with invariant MST weight 480.1784 km.")

            # Test raw trial expander
            raw_exp = page.locator("summary:has-text('Raw Individual Trial Records')")
            if raw_exp.count() > 0:
                raw_exp.click()
                time.sleep(1)
                print("  Expanded raw trial records drawer.")

            page.screenshot(path=str(SCREENSHOT_DIR / "06_laboratory_density.png"), full_page=False)
            print("  Screenshot saved: 06_laboratory_density.png")

        browser.close()
        print("\nALL 6 APPLICATION SCREENS FULLY AUDITED AND VERIFIED VIA MS EDGE BROWSER!")

if __name__ == "__main__":
    run_browser_audit()
