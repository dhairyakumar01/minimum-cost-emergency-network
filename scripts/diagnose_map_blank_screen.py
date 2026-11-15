import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

FLASK_BASE = "http://127.0.0.1:5000"
ROOT = Path(r"c:\Users\DHAIRYA\Downloads\minimum_cost_emergency_network\minimum_cost_emergency_network")

def diagnose_frontend():
    print("Launching Microsoft Edge to diagnose frontend and map...")
    console_logs = []
    page_errors = []
    failed_requests = []

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))
        page.on("pageerror", lambda err: page_errors.append(str(err)))
        page.on("requestfailed", lambda req: failed_requests.append(f"{req.url} - {req.failure}"))

        print("Navigating to http://127.0.0.1:5000...")
        try:
            page.goto(f"{FLASK_BASE}/", timeout=10000, wait_until="networkidle")
        except Exception as e:
            print("Navigation error:", e)

        print("\nPage Title:", page.title())

        # Check console logs
        print("\nConsole Logs:")
        for log in console_logs:
            print("  ", log)

        print("\nPage Errors:", page_errors)
        print("\nFailed Requests:", failed_requests)

        # Check facilities map
        print("\nNavigating to Facilities Map...")
        try:
            page.evaluate("() => Navigation.navigateTo('facilities-map')")
            page.wait_for_timeout(2500)
            
            # Check map container dimensions
            map_box = page.evaluate("""() => {
                const el = document.getElementById('leaflet-map');
                if (!el) return { error: 'No #leaflet-map element found!' };
                const rect = el.getBoundingClientRect();
                const tiles = el.querySelectorAll('.leaflet-tile');
                const markers = el.querySelectorAll('.leaflet-marker-icon, circle');
                const computed = window.getComputedStyle(el);
                const parentComputed = window.getComputedStyle(el.parentElement);
                return {
                    id: el.id,
                    className: el.className,
                    width: rect.width,
                    height: rect.height,
                    offsetWidth: el.offsetWidth,
                    offsetHeight: el.offsetHeight,
                    computedHeight: computed.height,
                    computedWidth: computed.width,
                    computedDisplay: computed.display,
                    parentHeight: parentComputed.height,
                    parentDisplay: parentComputed.display,
                    tileCount: tiles.length,
                    markerCount: markers.length,
                    hasLeafletPane: !!el.querySelector('.leaflet-pane'),
                    innerHTML_len: el.innerHTML.length
                };
            }""")
            print("\nFacilities Map Container Inspection:", map_box)

            # Take diagnostic screenshot of Facilities Map
            page.screenshot(path=str(ROOT / "reports" / "screenshots" / "diagnose_facilities_map.png"))
            print("Screenshot saved to: reports/screenshots/diagnose_facilities_map.png")

        except Exception as e:
            print("Facilities map navigation error:", e)

        context.close()
        browser.close()

if __name__ == "__main__":
    diagnose_frontend()
