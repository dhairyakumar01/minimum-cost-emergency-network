"""Headless browser verification for Phase 1.5 Complete UI & Map Correction."""
import asyncio
import os
from playwright.async_api import async_playwright


async def run_phase1_5_verification():
    os.makedirs("screenshots/phase1_5", exist_ok=True)
    console_errors = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="msedge", headless=True)
        page = await browser.new_page(viewport={"width": 1440, "height": 900})

        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda exc: console_errors.append(str(exc)))

        print("1. Loading Application at http://127.0.0.1:5000 ...")
        resp = await page.goto("http://127.0.0.1:5000", wait_until="networkidle")
        assert resp.status == 200, f"Expected 200 OK, got {resp.status}"

        # Wait for metrics to load
        await page.wait_for_selector("#metric-total-facilities", timeout=6000)
        await page.wait_for_timeout(1000)

        # Verify Dashboard Metrics
        total_fac = await page.locator("#metric-total-facilities").text_content()
        mst_len = await page.locator("#metric-mst-length").text_content()
        print(f"   Dashboard Facilities: {total_fac}, MST Length: {mst_len}")
        assert "1,255" in total_fac
        assert "480.1784 km" in mst_len

        # Check Dual-Layer Architecture and Balanced Equivalence Callouts
        layer_card = await page.locator(".layer-grid").count()
        assert layer_card > 0, "Dual-layer architecture grid should be present"
        math_callouts = await page.locator(".math-callout").count()
        assert math_callouts >= 2, "Mathematical callout formulas should be present"

        await page.screenshot(path="screenshots/phase1_5/01_dashboard.png")
        print("   Captured: screenshots/phase1_5/01_dashboard.png")

        # 2. Test Facilities Map & Incident Placement
        print("2. Testing Facilities Map & Incident Placement...")
        await page.locator("a[data-target='facilities-map']").click()
        await page.wait_for_timeout(1200)

        # Check map rendered
        fac_count_badge = await page.locator("#rendered-facilities-count").text_content()
        print(f"   Facilities Count: {fac_count_badge}")
        assert "1,255" in fac_count_badge

        # Test Landmark Preset Selection (Majestic)
        print("   Testing Landmark Preset (Majestic)...")
        majestic_pill = page.locator(".incident-coords-row button.landmark-pill:has-text('Majestic')")
        # Ensure incident-coords-bar is visible by toggling incident mode if needed
        coords_bar_display = await page.locator("#incident-coords-bar").evaluate("el => window.getComputedStyle(el).display")
        if coords_bar_display == "none":
            await page.locator("#btn-toggle-incident-mode").click()
            await page.wait_for_timeout(300)

        await majestic_pill.click()
        await page.wait_for_timeout(500)

        # Verify coordinates filled
        lat_val = await page.locator("#incident-lat-input").input_value()
        lon_val = await page.locator("#incident-lon-input").input_value()
        print(f"   Incident Coordinates: {lat_val}° N, {lon_val}° E")
        assert "12.9781" in lat_val
        assert "77.5696" in lon_val

        # Confirm incident
        await page.locator("#btn-confirm-incident").click()
        await page.wait_for_timeout(300)
        status_pill_text = await page.locator("#incident-status-pill").text_content()
        print(f"   Status Pill: {status_pill_text}")
        assert "Incident Confirmed" in status_pill_text

        # Click Jayanagar Landmark to test relocation
        jayanagar_pill = page.locator(".incident-coords-row button.landmark-pill:has-text('Jayanagar')")
        await jayanagar_pill.click()
        await page.wait_for_timeout(400)
        lat_val2 = await page.locator("#incident-lat-input").input_value()
        assert "12.9298" in lat_val2

        # Filter by Police Stations
        print("   Testing Agency Filter (Police Stations)...")
        await page.locator("button[data-agency='police_station']").click()
        await page.wait_for_timeout(400)
        police_badge = await page.locator("#rendered-facilities-count").text_content()
        print(f"   Police Filter: {police_badge}")
        assert "138" in police_badge

        # Reset to All
        await page.locator("button[data-agency='all']").click()
        await page.wait_for_timeout(300)

        await page.screenshot(path="screenshots/phase1_5/02_facilities_map.png")
        print("   Captured: screenshots/phase1_5/02_facilities_map.png")

        # 3. Test MST Network Visualization
        print("3. Testing MST Network Visualization...")
        await page.locator("a[data-target='mst-network']").click()
        await page.wait_for_timeout(1500)

        mst_display = await page.locator("#section-mst-network").evaluate("el => window.getComputedStyle(el).display")
        assert mst_display != "none", "MST Network section should be visible"

        # Check Kruskal button active
        kruskal_btn = page.locator("#btn-mst-kruskal")
        assert "active" in await kruskal_btn.get_attribute("class")

        # Check Prim Algorithm switch
        print("   Switching to Prim's Algorithm...")
        prim_btn = page.locator("#btn-mst-prim")
        await prim_btn.click()
        await page.wait_for_timeout(1500)
        assert "active" in await prim_btn.get_attribute("class")

        # Switch back to Kruskal
        await kruskal_btn.click()
        await page.wait_for_timeout(1000)

        await page.screenshot(path="screenshots/phase1_5/03_mst_network.png")
        print("   Captured: screenshots/phase1_5/03_mst_network.png")

        # 4. Test Emergency Simulation 6-Step Workflow
        print("4. Testing Emergency Simulation Setup...")
        await page.locator("a[data-target='simulation']").click()
        await page.wait_for_timeout(800)

        # Verify Step 1 displays incident
        sim_incident = await page.locator("#sim-incident-coords").text_content()
        print(f"   Sim Incident Coordinates: {sim_incident}")
        assert "12.9298" in sim_incident or "12.9781" in sim_incident

        # Step 2: Select Fire Emergency Category
        print("   Selecting Category: Structural Fire & HazMat...")
        fire_cat = page.locator(".category-card[data-category='fire']")
        await fire_cat.click()
        await page.wait_for_timeout(300)
        assert "active" in await fire_cat.get_attribute("class")

        # Step 3: Check Agency auto-selected or select Hospital
        hosp_agency = page.locator("#sim-agency-hospital")
        await hosp_agency.click()
        await page.wait_for_timeout(300)
        assert "active" in await hosp_agency.get_attribute("class")

        # Step 4: Adjust Search Radius slider to 8.0 km
        print("   Adjusting Search Radius to 8.0 km...")
        await page.locator("#sim-radius-slider").evaluate("el => { el.value = '8.0'; el.dispatchEvent(new Event('input')); }")
        await page.wait_for_timeout(300)
        cand_count = await page.locator("#sim-candidate-count").text_content()
        print(f"   Candidate Count at 8.0 km: {cand_count}")
        assert "8.0 km" in cand_count

        # Step 5: Select Minimum Time mode
        time_mode = page.locator(".mode-card[data-mode='time']")
        await time_mode.click()
        await page.wait_for_timeout(200)
        assert "active" in await time_mode.get_attribute("class")

        # Step 6: Run Dispatch Preview
        print("   Running Optimization & Response Dispatch...")
        await page.locator("#btn-run-simulation").click()
        await page.wait_for_timeout(600)

        # Verify Results Output visible with 3 ranked facilities
        results_display = await page.locator("#sim-results-output").evaluate("el => window.getComputedStyle(el).display")
        assert results_display != "none", "Results output should be visible after running optimization"

        ranked_count = await page.locator(".ranked-card").count()
        print(f"   Ranked Facilities Displayed: {ranked_count}")
        assert ranked_count == 3, f"Expected Top 3 facilities, got {ranked_count}"

        await page.screenshot(path="screenshots/phase1_5/04_simulation_results.png")
        print("   Captured: screenshots/phase1_5/04_simulation_results.png")

        # 5. Test Project Analysis & Results
        print("5. Testing Project Analysis & Results...")
        await page.locator("a[data-target='project-analysis']").click()
        await page.wait_for_timeout(500)
        table_rows = await page.locator(".data-table tbody tr").count()
        print(f"   Audit Table Rows: {table_rows}")
        assert table_rows >= 8, "Expected full audit metrics table"

        await page.screenshot(path="screenshots/phase1_5/05_project_analysis.png")
        print("   Captured: screenshots/phase1_5/05_project_analysis.png")

        # 6. Test Help & Methodology
        print("6. Testing Help & Methodology...")
        await page.locator("a[data-target='help']").click()
        await page.wait_for_timeout(500)

        # Check fuel rates table
        help_tables = await page.locator(".data-table").count()
        assert help_tables >= 1, "Statutory fuel price table should be present"

        await page.screenshot(path="screenshots/phase1_5/06_help_methodology.png")
        print("   Captured: screenshots/phase1_5/06_help_methodology.png")

        # 7. Test Mobile Viewport (375x667)
        print("7. Testing Mobile Viewport (375x667)...")
        mobile_page = await browser.new_page(viewport={"width": 375, "height": 667})
        await mobile_page.goto("http://127.0.0.1:5000", wait_until="networkidle")
        await mobile_page.wait_for_timeout(800)
        await mobile_page.screenshot(path="screenshots/phase1_5/07_mobile_view.png")
        print("   Captured: screenshots/phase1_5/07_mobile_view.png")

        await browser.close()

    print("\n--- Playwright Verification Complete ---")
    if console_errors:
        print(f"Console Errors Encountered ({len(console_errors)}):")
        for err in console_errors:
            print(f"  - {err}")
    else:
        print("Zero console errors encountered across all tests.")
    assert len(console_errors) == 0, "Expected zero console errors!"


if __name__ == "__main__":
    asyncio.run(run_phase1_5_verification())
