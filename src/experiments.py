"""Experimental Laboratory Module: Scalability & Graph Structure Evaluation.

Executes reproducible scalability experiments on vertex subsets of varying sizes N,
measuring execution times, edge counts, and tree properties for Prim and Kruskal.
Persists structured experiment records for independent analysis and dashboard rendering.
"""
import json
import platform
import statistics
import sys
import time
from pathlib import Path
import numpy as np
import pandas as pd

from src.mst_network import build_complete_edges, kruskal_mst, load_facilities, prim_mst
from src.validation import validate_mst

DEFAULT_SUBSETS = [50, 100, 200, 400, 600, 800, 1000, 1255]
DEFAULT_TRIALS = 5
RANDOM_SEED = 42

DEFAULT_DENSITY_LEVELS = [0.0, 0.05, 0.10, 0.25, 0.50, 0.75, 1.0]
DEFAULT_DENSITY_SEEDS = [101, 202, 303]


def run_scalability_experiments(
    facilities_df: pd.DataFrame,
    subset_sizes: list = None,
    trials_per_size: int = DEFAULT_TRIALS,
    seed: int = RANDOM_SEED,
    progress_callback=None,
) -> dict:
    """Execute reproducible scalability experiments over specified subset sizes.
    
    Both Prim and Kruskal receive identical vertex sets and candidate edges for each subset.
    """
    total_available = len(facilities_df)
    if subset_sizes is None:
        subset_sizes = DEFAULT_SUBSETS
        valid_sizes = sorted(list(set([s for s in subset_sizes if 3 <= s <= total_available])))
        if total_available not in valid_sizes and total_available >= 3:
            valid_sizes.append(total_available)
    else:
        valid_sizes = sorted(list(set([s for s in subset_sizes if 3 <= s <= total_available])))
        
    records = []
    summary_rows = []
    
    total_steps = len(valid_sizes)
    step = 0
    
    for n in valid_sizes:
        step += 1
        if progress_callback:
            progress_callback(step, total_steps, n)
            
        # Deterministic sampling
        if n == total_available:
            subset = facilities_df.copy().reset_index(drop=True)
        else:
            subset = facilities_df.sample(n=n, random_state=seed).reset_index(drop=True)
            
        candidate_edges = build_complete_edges(subset)
        edge_count = len(candidate_edges)
        
        # Benchmarking Prim
        prim_trials = []
        p_mst = None
        p_wt = 0.0
        for t_idx in range(trials_per_size):
            t0 = time.perf_counter()
            p_mst, p_wt = prim_mst(subset, candidate_edges)
            dt = time.perf_counter() - t0
            prim_trials.append(dt)
            records.append({
                "experiment_id": f"scalability_N{n}_prim_t{t_idx+1}",
                "experiment_type": "scalability",
                "vertices": n,
                "candidate_edges": edge_count,
                "algorithm": "Prim",
                "trial": t_idx + 1,
                "runtime_seconds": round(dt, 5),
                "mst_edges": len(p_mst),
                "mst_weight_km": round(p_wt, 6),
                "seed": seed,
            })
            
        # Benchmarking Kruskal
        kruskal_trials = []
        k_mst = None
        k_wt = 0.0
        for t_idx in range(trials_per_size):
            t0 = time.perf_counter()
            k_mst, k_wt = kruskal_mst(subset, candidate_edges)
            dt = time.perf_counter() - t0
            kruskal_trials.append(dt)
            records.append({
                "experiment_id": f"scalability_N{n}_kruskal_t{t_idx+1}",
                "experiment_type": "scalability",
                "vertices": n,
                "candidate_edges": edge_count,
                "algorithm": "Kruskal",
                "trial": t_idx + 1,
                "runtime_seconds": round(dt, 5),
                "mst_edges": len(k_mst),
                "mst_weight_km": round(k_wt, 6),
                "seed": seed,
            })
            
        # Independent validation of the final run
        p_val = validate_mst(subset, p_mst)
        k_val = validate_mst(subset, k_mst)
        val_passed = all(p_val.values()) and all(k_val.values()) and abs(p_wt - k_wt) < 1e-6
        
        summary_rows.append({
            "vertices": n,
            "candidate_edges": edge_count,
            "prim_median_s": round(statistics.median(prim_trials), 5),
            "prim_mean_s": round(statistics.mean(prim_trials), 5),
            "prim_stdev_s": round(statistics.stdev(prim_trials) if len(prim_trials) > 1 else 0.0, 5),
            "kruskal_median_s": round(statistics.median(kruskal_trials), 5),
            "kruskal_mean_s": round(statistics.mean(kruskal_trials), 5),
            "kruskal_stdev_s": round(statistics.stdev(kruskal_trials) if len(kruskal_trials) > 1 else 0.0, 5),
            "mst_weight_km": round(p_wt, 4),
            "validation_passed": val_passed,
        })
        
    result_data = {
        "metadata": {
            "experiment": "Scalability across Graph Sizes N",
            "seed": seed,
            "trials_per_size": trials_per_size,
            "sizes_tested": valid_sizes,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "python_version": sys.version.split()[0],
            "platform": platform.platform(),
        },
        "summary": summary_rows,
        "trials": records,
    }
    return result_data


def save_experiment_results(results: dict, results_dir: Path):
    """Save structured experiment results to JSON and CSV."""
    results_dir.mkdir(exist_ok=True, parents=True)
    json_path = results_dir / "scalability_results.json"
    json_path.write_text(json.dumps(results, indent=2))
    
    summary_df = pd.DataFrame(results["summary"])
    csv_path = results_dir / "scalability_summary.csv"
    summary_df.to_csv(csv_path, index=False)
    return json_path, csv_path


def load_saved_scalability(results_dir: Path):
    """Load previously saved scalability experiment results if available."""
    json_path = results_dir / "scalability_results.json"
    if json_path.exists():
        try:
            return json.loads(json_path.read_text())
        except Exception:
            return None
    return None


def run_density_experiments(
    facilities_df: pd.DataFrame,
    complete_edges: pd.DataFrame,
    mst_edges: pd.DataFrame,
    density_levels: list = None,
    seeds: list = None,
    progress_callback=None,
) -> dict:
    """Execute reproducible graph-density experiments under Controlled Non-Tree Sparsification.
    
    1. Retains all 1,254 verified MST edges at every density level to guarantee connectivity.
    2. Samples non-MST candidate edges exclusively from the remaining (786,885 - 1,254 = 785,631) links.
    3. Density rho is defined precisely as the proportion of non-MST candidate edges retained.
    4. Evaluates identical candidate edge sets for Prim and Kruskal within each trial.
    5. Measures actual execution runtimes across multiple reproducible random seeds.
    """
    if density_levels is None:
        density_levels = DEFAULT_DENSITY_LEVELS
    if seeds is None:
        seeds = DEFAULT_DENSITY_SEEDS

    # Partition candidate edges into base MST and non-MST subsets
    u_c = complete_edges["u"].astype(str).values
    v_c = complete_edges["v"].astype(str).values
    c_keys = np.where(u_c < v_c, u_c + "__" + v_c, v_c + "__" + u_c)

    u_m = mst_edges["u"].astype(str).values
    v_m = mst_edges["v"].astype(str).values
    m_keys = set(np.where(u_m < v_m, u_m + "__" + v_m, v_m + "__" + u_m))

    is_mst_edge = np.isin(c_keys, list(m_keys))
    base_mst_edges = complete_edges[is_mst_edge].reset_index(drop=True)
    non_mst_edges = complete_edges[~is_mst_edge].reset_index(drop=True)

    total_mst_count = len(base_mst_edges)
    total_non_mst_count = len(non_mst_edges)
    total_facilities = len(facilities_df)

    records = []
    summary_rows = []

    total_steps = len(density_levels) * len(seeds)
    current_step = 0

    for rho in sorted(density_levels):
        rho_val = float(rho)
        k_sample = int(round(rho_val * total_non_mst_count))
        total_graph_edges = total_mst_count + k_sample

        prim_times = []
        kruskal_times = []
        last_val_passed = True
        last_mst_wt = 0.0

        for s_idx, seed in enumerate(seeds):
            current_step += 1
            if progress_callback:
                progress_callback(current_step, total_steps, rho_val, seed)

            # Construct identical candidate edge set for this trial
            if rho_val == 0.0:
                sampled_graph = base_mst_edges.copy()
            elif rho_val == 1.0:
                sampled_graph = complete_edges.copy()
            else:
                sampled_non_mst = non_mst_edges.sample(n=k_sample, random_state=seed)
                sampled_graph = pd.concat([base_mst_edges, sampled_non_mst], ignore_index=True)

            # Benchmark Prim
            t0 = time.perf_counter()
            p_mst, p_wt = prim_mst(facilities_df, sampled_graph)
            dt_p = time.perf_counter() - t0
            prim_times.append(dt_p)

            # Benchmark Kruskal
            t0 = time.perf_counter()
            k_mst, k_wt = kruskal_mst(facilities_df, sampled_graph)
            dt_k = time.perf_counter() - t0
            kruskal_times.append(dt_k)

            # Validate connectivity and tree properties for this trial
            p_val = validate_mst(facilities_df, p_mst)
            k_val = validate_mst(facilities_df, k_mst)
            trial_val = (
                all(p_val.values())
                and all(k_val.values())
                and abs(p_wt - k_wt) < 1e-6
                and len(p_mst) == total_facilities - 1
            )
            last_val_passed = last_val_passed and trial_val
            last_mst_wt = float(k_wt)

            records.append({
                "experiment_id": f"density_rho{rho_val:.2f}_s{seed}_prim",
                "experiment_type": "controlled_density",
                "vertices": total_facilities,
                "non_mst_candidate_edges": total_non_mst_count,
                "density_rho": rho_val,
                "sampled_non_mst_edges": k_sample,
                "total_edges": total_graph_edges,
                "random_seed": seed,
                "algorithm": "Prim",
                "trial": s_idx + 1,
                "runtime_seconds": round(dt_p, 5),
                "mst_edges": len(p_mst),
                "mst_weight_km": round(p_wt, 6),
                "connectivity_validated": trial_val,
            })
            records.append({
                "experiment_id": f"density_rho{rho_val:.2f}_s{seed}_kruskal",
                "experiment_type": "controlled_density",
                "vertices": total_facilities,
                "non_mst_candidate_edges": total_non_mst_count,
                "density_rho": rho_val,
                "sampled_non_mst_edges": k_sample,
                "total_edges": total_graph_edges,
                "random_seed": seed,
                "algorithm": "Kruskal",
                "trial": s_idx + 1,
                "runtime_seconds": round(dt_k, 5),
                "mst_edges": len(k_mst),
                "mst_weight_km": round(k_wt, 6),
                "connectivity_validated": trial_val,
            })

        summary_rows.append({
            "density_rho": rho_val,
            "sampled_non_mst_edges": k_sample,
            "total_edges": total_graph_edges,
            "vertices": total_facilities,
            "prim_median_s": round(statistics.median(prim_times), 5),
            "prim_mean_s": round(statistics.mean(prim_times), 5),
            "prim_stdev_s": round(statistics.stdev(prim_times) if len(prim_times) > 1 else 0.0, 5),
            "kruskal_median_s": round(statistics.median(kruskal_times), 5),
            "kruskal_mean_s": round(statistics.mean(kruskal_times), 5),
            "kruskal_stdev_s": round(statistics.stdev(kruskal_times) if len(kruskal_times) > 1 else 0.0, 5),
            "mst_weight_km": round(last_mst_wt, 4),
            "validation_passed": last_val_passed,
        })

    result_data = {
        "metadata": {
            "experiment": "Controlled Non-Tree Edge Sparsification (Density rho)",
            "research_question": "How does candidate edge density affect the execution performance of Prim and Kruskal on a fixed, geographically weighted emergency-facility graph?",
            "density_definition": "rho = sampled_non_mst_edges / 785631 (retaining all 1254 verified base MST edges)",
            "seeds_tested": seeds,
            "density_levels_tested": density_levels,
            "timing_methodology": "Each trial record represents one single execution on one sampled graph. Summary medians and standard deviations are computed across the three distinct sampled graphs generated by seeds 101, 202, 303 (not repeated executions on the same graph). Standard deviation reflects variation across sampled-graph observations rather than pure runtime measurement noise.",
            "baseline_rho_zero_note": "At density 0.0, the graph is already an acyclic tree; Prim lower runtime is a plausible implementation-overhead explanation (DSU initialization and edge-sort overhead in Kruskal vs direct queue traversal in Prim), not a proven causal finding, and should not be generalized to all sparse graphs.",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "python_version": sys.version.split()[0],
            "platform": platform.platform(),
            "mst_weight_invariant_note": "MST total weight remains invariant at 480.1784 km across all density levels because all original 1,254 optimal edges are retained to guarantee connectivity.",
        },
        "summary": summary_rows,
        "trials": records,
    }
    return result_data


def save_density_results(results: dict, results_dir: Path):
    """Save structured density experiment results to JSON and CSV."""
    results_dir.mkdir(exist_ok=True, parents=True)
    json_path = results_dir / "density_results.json"
    json_path.write_text(json.dumps(results, indent=2))

    summary_df = pd.DataFrame(results["summary"])
    csv_path = results_dir / "density_summary.csv"
    summary_df.to_csv(csv_path, index=False)
    return json_path, csv_path


def load_saved_density(results_dir: Path):
    """Load previously saved density experiment results if available."""
    json_path = results_dir / "density_results.json"
    if json_path.exists():
        try:
            return json.loads(json_path.read_text())
        except Exception:
            return None
    return None

