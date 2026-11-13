import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

FLASK_BASE = "http://127.0.0.1:5000"
ROOT = Path(r"c:\Users\DHAIRYA\Downloads\minimum_cost_emergency_network\minimum_cost_emergency_network")
SCREENSHOT_PATH = ROOT / "reports" / "screenshots" / "test_api_error_state.png"

def test_deliberate_api_failure():
    print("Testing deliberate API failure and error recovery...")
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # Intercept /api/health and abort / fail with 500
        fail_api = True
        def handle_route(route):
            if fail_api and "/api/health" in route.request.url:
                print("  Intercepted /api/health -> returning HTTP 500 Internal Error")
                route.fulfill(status=500, body='{"error": "Simulated backend database outage"}')
            else:
                route.continue_()

        page.route("**/api/health", handle_route)

        print("Navigating to page with failing /api/health...")
        page.goto(f"{FLASK_BASE}/")
        
        # Verify error banner appears
        page.wait_for_selector("#api-error-banner", state="visible", timeout=6000)
        error_text = page.inner_text("#api-error-message")
        print(f"  Error banner successfully displayed: '{error_text}'")
        
        # Confirm retry button exists
        retry_btn = page.query_selector(".btn-retry-connection")
        assert retry_btn is not None, "Retry button not found"
        print("  Retry button verified visible.")

        # Capture screenshot of graceful error boundary
        page.screenshot(path=str(SCREENSHOT_PATH))
        print(f"  Captured error state screenshot: {SCREENSHOT_PATH}")

        # Now simulate API recovery
        print("\nRestoring /api/health to normal operation and clicking Retry...")
        fail_api = False
        page.click(".btn-retry-connection")
        
        # Verify recovery
        page.wait_for_selector("#metric-total-facilities", state="visible", timeout=8000)
        facilities_metric = page.inner_text("#metric-total-facilities")
        print(f"  Recovery successful! Dashboard metric populated: {facilities_metric}")
        assert "1,255" in facilities_metric or "1255" in facilities_metric

        context.close()
        browser.close()
        print("\nALL ERROR BOUNDARY AND RECOVERY TESTS PASSED!")

if __name__ == "__main__":
    test_deliberate_api_failure()
