import time
from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:5000"
OUTPUT_DIR = "reports/screenshots"

def run_browser_verification():
    console_errors = []
    failed_requests = []

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)

        # -------------------------------------------------------------
        # 1. Desktop Verification (1440 x 900)
        # -------------------------------------------------------------
        context_desktop = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context_desktop.new_page()

        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("requestfailed", lambda req: failed_requests.append(req.url))

        print("Navigating to Flask App (Desktop 1440x900)...")
        page.goto(BASE_URL, wait_until="networkidle")
        time.sleep(1.0)

        # Section 1: Dashboard
        print("Capturing Section 1: Dashboard...")
        page.screenshot(path=f"{OUTPUT_DIR}/desktop_1_dashboard.png")

        # Section 2: Facilities Map
        print("Capturing Section 2: Facilities Map...")
        page.click('[data-target="facilities-map"]')
        time.sleep(1.2)
        page.screenshot(path=f"{OUTPUT_DIR}/desktop_2_facilities_map.png")

        # Section 3: MST Network
        print("Capturing Section 3: MST Network...")
        page.click('[data-target="mst-network"]')
        time.sleep(1.5)
        page.screenshot(path=f"{OUTPUT_DIR}/desktop_3_mst_network.png")

        # Section 4: Emergency Simulation
        print("Navigating to Section 4: Emergency Simulation...")
        page.click('[data-target="simulation"]')
        time.sleep(1.0)
        
        # Configure Radius to 3.0 km for immediate cached response
        page.evaluate("App.onRadiusChange(3.0)")
        time.sleep(0.5)
        page.screenshot(path=f"{OUTPUT_DIR}/desktop_4_simulation_setup.png")

        # Trigger Simulation Run
        print("Triggering Simulation Execution...")
        page.click("#btn-run-simulation")
        
        # Wait for results output to become visible (up to 30s)
        page.wait_for_selector("#sim-results-output", state="visible", timeout=30000)
        time.sleep(1.0)

        # Tab 1: Dispatch Ranking
        print("Capturing Simulation Tab 1: Dispatch Ranking...")
        page.screenshot(path=f"{OUTPUT_DIR}/desktop_4_sim_tab1_dispatch.png")

        # Tab 2: Network Backbone
        print("Capturing Simulation Tab 2: Network Backbone...")
        page.click("#btn-tab-network")
        time.sleep(0.5)
        page.screenshot(path=f"{OUTPUT_DIR}/desktop_4_sim_tab2_network.png")

        # Tab 3: Validation
        print("Capturing Simulation Tab 3: Validation...")
        page.click("#btn-tab-validation")
        time.sleep(0.5)
        page.screenshot(path=f"{OUTPUT_DIR}/desktop_4_sim_tab3_validation.png")

        # Tab 4: Candidates & Exclusions
        print("Capturing Simulation Tab 4: Candidates & Exclusions...")
        page.click("#btn-tab-exclusions")
        time.sleep(0.5)
        page.screenshot(path=f"{OUTPUT_DIR}/desktop_4_sim_tab4_exclusions.png")

        # Section 5: Project Analysis & Results
        print("Capturing Section 5: Project Analysis & Results...")
        page.click('[data-target="project-analysis"]')
        time.sleep(1.0)
        page.screenshot(path=f"{OUTPUT_DIR}/desktop_5_project_analysis.png")

        # Section 6: Help & Methodology
        print("Capturing Section 6: Help & Methodology...")
        page.click('[data-target="help"]')
        time.sleep(1.0)
        page.screenshot(path=f"{OUTPUT_DIR}/desktop_6_help_methodology.png")

        context_desktop.close()

        # -------------------------------------------------------------
        # 2. Tablet Verification (834 x 1112)
        # -------------------------------------------------------------
        print("\nTesting Tablet Viewport (834 x 1112)...")
        context_tablet = browser.new_context(viewport={"width": 834, "height": 1112})
        page_tab = context_tablet.new_page()
        page_tab.goto(BASE_URL, wait_until="networkidle")
        time.sleep(1.0)
        page_tab.screenshot(path=f"{OUTPUT_DIR}/tablet_1_dashboard.png")

        page_tab.click('[data-target="simulation"]')
        time.sleep(1.0)
        page_tab.screenshot(path=f"{OUTPUT_DIR}/tablet_4_simulation.png")
        context_tablet.close()

        # -------------------------------------------------------------
        # 3. Mobile Verification (390 x 844)
        # -------------------------------------------------------------
        print("\nTesting Mobile Viewport (390 x 844)...")
        context_mobile = browser.new_context(viewport={"width": 390, "height": 844})
        page_mob = context_mobile.new_page()
        page_mob.goto(BASE_URL, wait_until="networkidle")
        time.sleep(1.0)
        page_mob.screenshot(path=f"{OUTPUT_DIR}/mobile_1_dashboard.png")

        # On mobile, navigation might be accessed via menu or programmatic
        page_mob.evaluate("Navigation.navigateTo('facilities-map')")
        time.sleep(1.2)
        page_mob.screenshot(path=f"{OUTPUT_DIR}/mobile_2_facilities_map.png")

        page_mob.evaluate("Navigation.navigateTo('simulation')")
        time.sleep(1.0)
        page_mob.screenshot(path=f"{OUTPUT_DIR}/mobile_4_simulation.png")
        context_mobile.close()

        browser.close()

    print("\n=== BROWSER VERIFICATION SUMMARY ===")
    print(f"Total Console Errors: {len(console_errors)}")
    if console_errors:
        print("Console errors:", console_errors[:5])
    print(f"Total Failed Requests: {len(failed_requests)}")
    if failed_requests:
        print("Failed requests:", failed_requests[:5])
    print("All screenshots captured and saved successfully into reports/screenshots/!")

if __name__ == "__main__":
    run_browser_verification()
