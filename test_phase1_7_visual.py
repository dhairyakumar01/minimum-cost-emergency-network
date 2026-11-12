"""
Phase 1.7 Visual Acceptance and Interaction Verification Suite
Evaluates the redesigned Bengaluru Emergency Network Analysis Platform across:
- 1440 x 900 (Desktop Standard)
- 1366 x 768 (Laptop Standard)
- 768 x 1024 (Tablet Portrait)
- 375 x 667 (Mobile Standard)
"""

import asyncio
import os
import sys
from playwright.async_api import async_playwright

RESOLUTIONS = [
    {"name": "desktop_1440x900", "width": 1440, "height": 900},
    {"name": "laptop_1366x768", "width": 1366, "height": 768},
    {"name": "tablet_768x1024", "width": 768, "height": 1024},
    {"name": "mobile_375x667", "width": 375, "height": 667},
]

SECTIONS = [
    {"target": "dashboard", "name": "01_dashboard"},
    {"target": "facilities-map", "name": "02_facilities_map"},
    {"target": "mst-network", "name": "03_mst_network"},
    {"target": "simulation", "name": "04_simulation"},
    {"target": "project-analysis", "name": "05_project_analysis"},
    {"target": "help", "name": "06_help_methodology"},
]


async def run_visual_audit():
    console_errors = []
    base_url = "http://127.0.0.1:5000"

    print("=== Starting Phase 1.7 Visual & Interaction Audit ===")

    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="msedge", headless=True)

        for res in RESOLUTIONS:
            res_name = res["name"]
            width = res["width"]
            height = res["height"]
            out_dir = os.path.join("screenshots", "phase1_7", res_name)
            os.makedirs(out_dir, exist_ok=True)

            print(f"\n--- Testing Resolution: {res_name} ({width}x{height}) ---")
            page = await browser.new_page(viewport={"width": width, "height": height})

            page.on("console", lambda msg: console_errors.append(f"[{res_name}] {msg.text}") if msg.type == "error" else None)
            page.on("pageerror", lambda exc: console_errors.append(f"[{res_name}] {str(exc)}"))

            # 1. Load Application
            resp = await page.goto(base_url, wait_until="networkidle")
            assert resp.status == 200, f"Expected 200, got {resp.status}"

            await page.wait_for_selector("#metric-total-facilities", timeout=8000)
            await page.wait_for_timeout(800)

            # Capture all 6 pages at this resolution
            for sec in SECTIONS:
                target = sec["target"]
                file_name = sec["name"]

                print(f"   Navigating to: {target} ...")
                # Navigate via JS or click
                await page.evaluate(f"Navigation.navigateTo('{target}')")
                await page.wait_for_timeout(1000)

                # Special interactions for specific views to show active states
                if target == "facilities-map":
                    # Check facilities rendered
                    fac_count = await page.locator("#rendered-facilities-count").text_content()
                    assert "1,255" in fac_count

                    # Ensure incident coords bar is visible
                    coords_display = await page.locator("#incident-coords-bar").evaluate("el => window.getComputedStyle(el).display")
                    if coords_display == "none":
                        await page.locator("#btn-toggle-incident-mode").click()
                        await page.wait_for_timeout(400)

                    # Click Jayanagar preset
                    jayanagar = page.locator(".incident-coords-row button.landmark-pill:has-text('Jayanagar')")
                    if await jayanagar.count() > 0:
                        await jayanagar.click()
                        await page.wait_for_timeout(400)

                elif target == "mst-network":
                    # Toggle Prim then back to Kruskal
                    await page.locator("#btn-mst-prim").click()
                    await page.wait_for_timeout(800)
                    await page.locator("#btn-mst-kruskal").click()
                    await page.wait_for_timeout(600)

                elif target == "simulation":
                    # Configure simulation
                    await page.locator(".category-card[data-category='fire']").click()
                    await page.wait_for_timeout(300)
                    await page.locator("#sim-agency-hospital").click()
                    await page.wait_for_timeout(300)
                    await page.locator("#sim-radius-slider").evaluate("el => { el.value = '7.5'; el.dispatchEvent(new Event('input')); }")
                    await page.wait_for_timeout(300)
                    await page.locator(".mode-card[data-mode='balanced']").click()
                    await page.wait_for_timeout(300)

                    # Run dispatch analysis
                    await page.locator("#btn-run-simulation").click()
                    await page.wait_for_timeout(1000)

                elif target == "help":
                    # Open multiple accordions
                    await page.evaluate("""() => {
                        document.querySelectorAll('.method-accordion').forEach((acc, idx) => {
                            if (idx < 3) acc.setAttribute('open', 'true');
                        });
                    }""")
                    await page.wait_for_timeout(400)

                # Capture full screenshot
                screenshot_path = os.path.join(out_dir, f"{file_name}.png")
                await page.screenshot(path=screenshot_path)
                print(f"   Saved: {screenshot_path}")

            await page.close()

        await browser.close()

    print("\n=== Browser Verification Complete ===")
    print(f"Total console/page errors detected: {len(console_errors)}")
    if console_errors:
        print("Console Errors:")
        for err in console_errors:
            print(f"  - {err}")
    assert len(console_errors) == 0, f"Encountered {len(console_errors)} console errors."
    print("ALL VISUAL ACCEPTANCE AND INTERACTION CHECKS PASSED WITH 0 ERRORS.")


if __name__ == "__main__":
    asyncio.run(run_visual_audit())
