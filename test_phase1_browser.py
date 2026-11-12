"""Headless browser verification for Phase 1 Flask frontend."""
import asyncio
import os
from playwright.async_api import async_playwright


async def run_browser_verification():
    os.makedirs("screenshots/phase1", exist_ok=True)
    results = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="msedge", headless=True)
        
        # 1. Desktop Viewport
        page = await browser.new_page(viewport={"width": 1440, "height": 900})
        
        # Collect console errors
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda exc: console_errors.append(str(exc)))

        print("Navigating to http://127.0.0.1:5000 ...")
        resp = await page.goto("http://127.0.0.1:5000", wait_until="networkidle")
        assert resp.status == 200, f"Expected 200 OK, got {resp.status}"

        # Wait for metrics to populate from API
        await page.wait_for_selector("#metric-total-facilities", timeout=5000)
        await page.wait_for_timeout(1000)

        total_fac_text = await page.locator("#metric-total-facilities").text_content()
        print(f"Loaded Total Facilities: {total_fac_text}")
        assert "1,255" in total_fac_text

        # Verify Dashboard is visible
        dash_display = await page.locator("#section-dashboard").evaluate("el => window.getComputedStyle(el).display")
        assert dash_display != "none", "Dashboard section should be visible initially"

        await page.screenshot(path="screenshots/phase1/01_dashboard_desktop.png")
        print("Captured 01_dashboard_desktop.png")

        # 2. Test Navigation to Facilities Map
        print("Navigating to Facilities Map...")
        map_nav_link = page.locator("a[data-target='facilities-map']")
        await map_nav_link.click()
        await page.wait_for_timeout(1500)

        map_display = await page.locator("#section-facilities-map").evaluate("el => window.getComputedStyle(el).display")
        assert map_display != "none", "Facilities Map section should be visible after click"

        # Check Leaflet map container rendered
        map_rendered = await page.locator("#leaflet-map .leaflet-pane").count()
        assert map_rendered > 0, "Leaflet map pane should be rendered"

        # Check facilities count badge
        count_badge = await page.locator("#rendered-facilities-count").text_content()
        print(f"Facilities Map Count Badge: {count_badge}")
        assert "1,255" in count_badge

        # Test filtering by Fire Stations
        fire_filter_btn = page.locator("button[data-agency='fire_station']")
        await fire_filter_btn.click()
        await page.wait_for_timeout(500)
        fire_badge = await page.locator("#rendered-facilities-count").text_content()
        print(f"After Fire Filter: {fire_badge}")
        assert "20" in fire_badge

        # Test searching for 'Victoria'
        search_inp = page.locator("#facility-map-search")
        all_filter_btn = page.locator("button[data-agency='all']")
        await all_filter_btn.click()
        await search_inp.fill("Victoria")
        await page.wait_for_timeout(500)
        search_badge = await page.locator("#rendered-facilities-count").text_content()
        print(f"After Search 'Victoria': {search_badge}")

        await page.screenshot(path="screenshots/phase1/02_facilities_map.png")
        print("Captured 02_facilities_map.png")

        # 3. Test Navigation to All Remaining Sections
        sections = ["mst-network", "simulation", "project-analysis", "help"]
        for sec in sections:
            print(f"Testing navigation to #{sec} ...")
            link = page.locator(f"a[data-target='{sec}']")
            await link.click()
            await page.wait_for_timeout(400)
            sec_display = await page.locator(f"#section-{sec}").evaluate("el => window.getComputedStyle(el).display")
            assert sec_display != "none", f"Section {sec} should be visible"

        await page.screenshot(path="screenshots/phase1/03_help_section.png")
        print("Captured 03_help_section.png")

        # 4. Mobile Viewport Usability (375x667 iPhone SE)
        print("Testing Mobile Viewport (375x667) ...")
        mobile_page = await browser.new_page(viewport={"width": 375, "height": 667})
        await mobile_page.goto("http://127.0.0.1:5000", wait_until="networkidle")
        await mobile_page.wait_for_timeout(800)
        await mobile_page.screenshot(path="screenshots/phase1/04_mobile_dashboard.png")
        print("Captured 04_mobile_dashboard.png")

        await browser.close()

    print(f"\nBrowser Verification Completed! Console errors: {len(console_errors)}")
    if console_errors:
        print("Console errors found:", console_errors)
    assert len(console_errors) == 0, f"Expected 0 console errors, got {len(console_errors)}"


if __name__ == "__main__":
    asyncio.run(run_browser_verification())
