from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    page = browser.new_page()
    page.on("console", lambda msg: print(f"CONSOLE [{msg.type}]: {msg.text}"))
    page.on("pageerror", lambda err: print(f"PAGE ERROR: {err}"))
    page.goto("http://127.0.0.1:5000", wait_until="networkidle")
    page.evaluate("Navigation.navigateTo('simulation')")
    page.wait_for_timeout(1000)
    print("Clicking #btn-run-simulation...")
    page.click("#btn-run-simulation")
    for _ in range(10):
        page.wait_for_timeout(1000)
        status_text = page.locator("#sim-exec-status").inner_text()
        print(f"Status: {status_text}")
        results_disp = page.evaluate("() => document.getElementById('sim-results-output')?.style.display")
        print(f"Results display: {results_disp}")
        if results_disp == "block":
            break
    browser.close()
