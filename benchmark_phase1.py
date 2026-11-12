"""Empirical performance measurement script for Phase 1 Flask backend foundation."""
import json
import statistics
import time
import os
import urllib.request
from backend.flask_app import create_app
from backend.config import Config

TRIALS = 30


def measure_startup_time():
    """Measure the time to import and initialize create_app()."""
    times = []
    for _ in range(10):
        t0 = time.perf_counter()
        app = create_app()
        elapsed = time.perf_counter() - t0
        times.append(elapsed)
    return {
        "min_ms": round(min(times) * 1000.0, 2),
        "median_ms": round(statistics.median(times) * 1000.0, 2),
        "mean_ms": round(statistics.mean(times) * 1000.0, 2),
        "max_ms": round(max(times) * 1000.0, 2),
    }


def measure_client_benchmarks():
    """Measure endpoint latencies using Flask test_client."""
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()

    # Pre-warm
    client.get("/api/health")

    endpoints = [
        ("/", "Initial HTML Document"),
        ("/assets/css/style.css", "Static Stylesheet CSS"),
        ("/assets/js/app.js", "Main Frontend JavaScript"),
        ("/api/health", "Health API Endpoint (/api/health)"),
        ("/api/facilities", "All Facilities API (/api/facilities)"),
        ("/api/facilities?agency=hospital", "Agency Filter: Hospitals (/api/facilities?agency=hospital)"),
        ("/api/facilities?agency=police_station", "Agency Filter: Police (/api/facilities?agency=police_station)"),
        ("/api/facilities?agency=fire_station", "Agency Filter: Fire (/api/facilities?agency=fire_station)"),
        ("/api/mst/full?algo=kruskal", "Global MST API (/api/mst/full?algo=kruskal)"),
    ]

    results = {}

    for path, label in endpoints:
        durations = []
        payload_size = 0
        for i in range(TRIALS):
            t0 = time.perf_counter()
            resp = client.get(path)
            dur = (time.perf_counter() - t0) * 1000.0
            durations.append(dur)
            if i == 0:
                payload_size = len(resp.data)

        results[path] = {
            "label": label,
            "status_code": resp.status_code,
            "payload_bytes": payload_size,
            "payload_kb": round(payload_size / 1024.0, 2),
            "trials": TRIALS,
            "min_ms": round(min(durations), 2),
            "median_ms": round(statistics.median(durations), 2),
            "mean_ms": round(statistics.mean(durations), 2),
            "max_ms": round(max(durations), 2),
            "p95_ms": round(statistics.quantiles(durations, n=20)[18], 2) if len(durations) >= 20 else round(max(durations), 2),
        }

    return results


if __name__ == "__main__":
    print("=== MEASURING STARTUP PERFORMANCE ===")
    startup_stats = measure_startup_time()
    print("Startup stats (ms):", startup_stats)

    print("\n=== MEASURING ENDPOINT PERFORMANCE ===")
    benchmarks = measure_client_benchmarks()
    for path, data in benchmarks.items():
        print(f"\n{data['label']} [{path}]:")
        print(f"  Payload: {data['payload_bytes']:,} bytes ({data['payload_kb']} KB)")
        print(f"  Median: {data['median_ms']} ms | Mean: {data['mean_ms']} ms | Min: {data['min_ms']} ms | Max: {data['max_ms']} ms | P95: {data['p95_ms']} ms")

    output_file = "results/phase1_performance_benchmark.json"
    with open(output_file, "w") as f:
        json.dump({"startup": startup_stats, "endpoints": benchmarks}, f, indent=2)
    print(f"\nSaved benchmark results to {output_file}")

