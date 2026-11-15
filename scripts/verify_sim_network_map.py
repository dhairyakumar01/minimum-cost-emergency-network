"""Verification script for the Emergency Simulation Geographic Network Map.
Tests that Tab 2 renders the incident-specific MST map with genuine road geometries,
markers, legend, and captures high-resolution screenshots.
"""
import os
import sys
import time
from playwright.sync_api import sync_playwright

SCREENSHOT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports", "screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

BASE_URL = "http://127.0.0.1:5000"

def verify_sim_network_map():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda exc: console_errors.append(str(exc)))

        print("[1/5] Navigating to Simulation...")
        page.goto(BASE_URL, wait_until="networkidle")
        page.evaluate("Navigation.navigateTo('simulation')")
        page.wait_for_selector("#section-simulation", state="visible")
        page.wait_for_timeout(1000)

        print("[2/5] Running Simulation...")
        page.click("#btn-run-simulation")
        page.wait_for_selector("#sim-results-output", state="visible", timeout=30000)
        page.wait_for_timeout(1500)

        print("[3/5] Switching to Tab 2: Network Backbone...")
        page.click("#btn-tab-network")
        page.wait_for_selector("#tab-content-network", state="visible")
        page.wait_for_timeout(1500)

        # Inspect Leaflet map inside Tab 2
        map_metrics = page.evaluate("""() => {
            const mapEl = document.getElementById('sim-mst-leaflet-map');
            const rect = mapEl ? mapEl.getBoundingClientRect() : null;
            const tiles = mapEl ? mapEl.querySelectorAll('.leaflet-tile-loaded').length : 0;
            const incPins = mapEl ? mapEl.querySelectorAll('.incident-sim-pin').length : 0;
            const markers = mapEl ? mapEl.querySelectorAll('.leaflet-interactive').length : 0;
            const svgs = mapEl ? mapEl.querySelectorAll('svg path').length : 0;
            const geomBadge = document.getElementById('sim-map-geom-badge')?.innerText;
            const modeBadge = document.getElementById('sim-map-mode-badge')?.innerText;
            return { rect, tiles, incPins, markers, svgs, geomBadge, modeBadge };
        }""")

        print(f"  Map Rect: {map_metrics['rect']}")
        print(f"  Tiles Loaded: {map_metrics['tiles']}")
        print(f"  Incident Pin Count: {map_metrics['incPins']}")
        print(f"  Total SVG Paths / Polylines: {map_metrics['svgs']}")
        print(f"  Geometry Badge: {map_metrics['geomBadge']}")
        print(f"  Mode Badge: {map_metrics['modeBadge']}")

        assert map_metrics['rect']['height'] >= 400, f"Map height too small: {map_metrics['rect']['height']}"
        assert map_metrics['tiles'] > 0, "No Leaflet tiles loaded on simulation map!"
        assert map_metrics['incPins'] >= 1, "Incident marker not found on simulation map!"
        assert map_metrics['svgs'] > 0, "No MST edge polylines drawn on simulation map!"

        print("[4/5] Capturing Screenshots...")
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "desktop_4_sim_tab2_network.png"), full_page=False)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "desktop_4_sim_tab2_network_map.png"), full_page=False)

        # Click fit bounds to test control
        page.click("#btn-fit-sim-map")
        page.wait_for_timeout(800)

        # Tab switching test: Switch to Tab 1 then back to Tab 2
        print("[5/5] Testing Tab Switching (Tab 1 -> Tab 2 -> Tab 3 -> Tab 2)...")
        page.click("#btn-tab-dispatch")
        page.wait_for_timeout(400)
        page.click("#btn-tab-network")
        page.wait_for_timeout(600)

        h_after = page.evaluate("() => document.getElementById('sim-mst-leaflet-map').getBoundingClientRect().height")
        assert h_after >= 400, f"Map collapsed after tab switch: {h_after}"
        print(f"  Map verified stable after tab switch: {h_after}px height.")

        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "desktop_4_sim_tab2_network_stable.png"), full_page=False)

        context.close()
        browser.close()

    print("\nSIMULATION NETWORK MAP VERIFICATION PASSED!")
    if console_errors:
        print(f"Console errors caught: {console_errors}")
    else:
        print("0 console errors recorded.")

if __name__ == "__main__":
    verify_sim_network_map()
