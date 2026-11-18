import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

FLASK_BASE = "http://127.0.0.1:5000"
ROOT = Path(r"c:\Users\DHAIRYA\Downloads\minimum_cost_emergency_network\minimum_cost_emergency_network")
SCREENSHOTS_DIR = ROOT / "reports" / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

def test_simulator_e2e():
    print("Beginning End-to-End Playwright Verification of Algorithm Construction Simulator...")
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 920})
        page = context.new_page()

        # Capture console logs to detect any JS errors
        js_errors = []
        page.on("pageerror", lambda err: js_errors.append(str(err)))
        page.on("console", lambda msg: print(f"  [CONSOLE] {msg.type}: {msg.text}"))

        print("Navigating to application home...")
        page.goto(f"{FLASK_BASE}/", wait_until="domcontentloaded")
        time.sleep(2.0)

        # 1. Navigate to MST Network section
        print("Navigating to MST Network view...")
        page.click("a[data-target='mst-network']")
        time.sleep(2.0)

        # 2. Verify subtab navigation
        sim_view = page.locator("#mst-view-sim")
        assert sim_view.is_visible(), "Simulator subview should be visible by default"

        # Wait for trace to load if not already loaded
        total_steps = page.locator("#sim-total-steps").inner_text()
        for _ in range(20):
            if total_steps != "0":
                break
            time.sleep(0.5)
            total_steps = page.locator("#sim-total-steps").inner_text()

        print(f"  Simulator trace loaded successfully: Total Events = {total_steps}")
        assert int(total_steps) > 1000, f"Expected >1000 events, got {total_steps}"

        # 3. Step Next 3 times
        print("Testing Step Forward controls...")
        for i in range(1, 4):
            page.click("#btn-sim-next")
            time.sleep(0.3)
            step_num = page.locator("#sim-step-num").inner_text()
            assert step_num == str(i), f"Expected step {i}, got {step_num}"

        # Verify Explanation Panel
        decision = page.locator("#sim-step-decision-badge").inner_text()
        rationale = page.locator("#sim-step-rationale").inner_text()
        weight = page.locator("#sim-step-weight").inner_text()
        print(f"  Step 3 Decision: {decision}")
        print(f"  Step 3 Weight: {weight}")
        print(f"  Step 3 Rationale snippet: {rationale[:60]}...")
        assert "ACCEPTED" in decision
        assert len(rationale) > 20

        # Capture screenshot of Simulator step
        page.screenshot(path=str(SCREENSHOTS_DIR / "simulator_step_execution.png"))
        print("  Saved screenshot: simulator_step_execution.png")

        # 4. Test Scrubber interaction
        print("Testing interactive scrubber...")
        page.fill("#sim-scrubber", "50")
        page.dispatch_event("#sim-scrubber", "input")
        time.sleep(0.5)
        step_num = page.locator("#sim-step-num").inner_text()
        assert step_num == "50", f"Expected step 50, got {step_num}"

        # 5. Test Algorithm switch to Prim
        print("Testing Algorithm toggle -> Prim's Algorithm...")
        page.click("#btn-sim-algo-prim")
        time.sleep(1.5)
        algo_btn = page.locator("#btn-sim-algo-prim")
        assert "active" in (algo_btn.get_attribute("class") or "")
        comp_label = page.locator("#sim-telem-comp-label").inner_text()
        assert "visited" in comp_label.lower(), f"Expected Prim cut label, got {comp_label}"

        # 6. Test Graph Context switch to Incident
        print("Testing Graph Context toggle -> Incident-Specific Graph...")
        page.click("#btn-sim-ctx-incident")
        time.sleep(1.5)
        inc_btn = page.locator("#btn-sim-ctx-incident")
        assert "active" in (inc_btn.get_attribute("class") or "")
        inc_steps = page.locator("#sim-total-steps").inner_text()
        print(f"  Incident graph loaded: {inc_steps} events")

        # 7. Test Subtab switch to Comparison Mode
        print("Testing subtab -> Prim vs Kruskal Convergence Analysis...")
        page.click("#tab-mst-compare")
        time.sleep(1.5)
        compare_view = page.locator("#mst-view-compare")
        assert compare_view.is_visible()

        k_weight = page.locator("#cmp-kruskal-weight").inner_text()
        p_weight = page.locator("#cmp-prim-weight").inner_text()
        k_edges = page.locator("#cmp-kruskal-edges").inner_text()
        p_edges = page.locator("#cmp-prim-edges").inner_text()
        print(f"  Comparison Kruskal Weight: {k_weight}, Edges: {k_edges}")
        print(f"  Comparison Prim Weight:    {p_weight}, Edges: {p_edges}")
        assert k_weight == p_weight, f"Weights must agree! {k_weight} vs {p_weight}"
        assert "1,254" in k_edges and "1,254" in p_edges

        # Capture screenshot of Comparison view
        page.screenshot(path=str(SCREENSHOTS_DIR / "simulator_parity_comparison.png"))
        print("  Saved screenshot: simulator_parity_comparison.png")

        # 8. Test Subtab switch to Static MST view (Backward Compatibility)
        print("Testing subtab -> Static Spanning Tree (1,254 Links)...")
        page.click("#tab-mst-static")
        time.sleep(1.5)
        static_view = page.locator("#mst-view-static")
        assert static_view.is_visible()
        mst_canvas = page.locator("#mst-leaflet-map")
        assert mst_canvas.is_visible()

        # Capture screenshot of Static view
        page.screenshot(path=str(SCREENSHOTS_DIR / "static_mst_view_preserved.png"))
        print("  Saved screenshot: static_mst_view_preserved.png")

        # Verify no fatal JS errors occurred
        print(f"Total uncaught JS errors: {len(js_errors)}")
        if js_errors:
            print(f"JS Errors: {js_errors}")
        assert len(js_errors) == 0, "Encountered uncaught JavaScript errors!"

        browser.close()
        print("All E2E Playwright tests PASSED successfully!")

if __name__ == "__main__":
    test_simulator_e2e()
