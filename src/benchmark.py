"""Task 2 descriptive sample audit and Task 3 simulated scenario generator.

The 50–250 req/s values are *scenario labels*, not achieved load from a live
service. Latencies are draws from Gaussian distributions, NOT stopwatch timings.
The purpose is to test JSONL ingestion, statistics, and visualization. Neither
these synthetic latencies nor the illustrative study rows test RQ1–RQ3.
"""

import argparse
import datetime
import json
import os
import random
import sys
import pandas as pd

# Ensure UTF-8 output on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf-8-sig"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def run_benchmark(config_path: str):
    """Validate and describe illustrative study rows without false pooled inference.

    The input CSV is an unverified teaching dataset, *not* extracted empirical
    study estimates. In particular, do not pool % differences across unlike
    outcomes, nor report p-values from these examples.
    """
    with open(config_path, "r", encoding="utf-8") as fh:
        config = json.load(fh)
    data_file = config.get("data_path", "data/sample/sample_dataset.csv")
    df = pd.read_csv(data_file)
    required = {"study_id", "metric_name", "value_before", "value_after",
                "pct_change", "research_question", "data_provenance", "has_required_fields"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Sample dataset missing columns: {sorted(missing)}")
    if df.empty or df["study_id"].duplicated().any():
        raise ValueError("Study examples must be nonempty and have unique study_id")
    if (df["value_before"] == 0).any():
        raise ValueError("Cannot calculate percentage change with zero baseline")
    calculated = (df["value_after"] - df["value_before"]) / df["value_before"] * 100
    if not ((calculated - df["pct_change"]).abs() <= 0.15).all():
        raise ValueError("Sample pct_change does not agree with before/after values")
    required_fields = ["study_id", "metric_name", "value_before", "value_after", "pct_change"]
    complete_mask = df[required_fields].notna().all(axis=1) & df["has_required_fields"].eq(True)
    completeness = 100 * complete_mask.mean()
    threshold = float(config.get("guardrail_completion_threshold", 95.0))
    status = "PASSED" if completeness >= threshold else "FAILED"
    print("[NOTE] Illustrative/unverified study values; descriptive checks only.")
    print(f"Rows: {len(df)}; data completeness: {completeness:.1f}%; guardrail: {status}")
    for rq, group in df.groupby("research_question", sort=True):
        print(f"  {rq}: {len(group)} illustrative row(s) — "
              + ", ".join(group["metric_name"].astype(str)))
    print("[NOTE] No pooled mean, causal claim, or hypothesis test is justified by these rows.")
    output_path = config.get("output_path", "data/processed/benchmark_results.json")
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump({"status": status, "processed_records": int(len(df)),
                   "data_completeness_pct": round(float(completeness), 2),
                   "research_question_counts": {str(k): int(v) for k, v in
                       df["research_question"].value_counts().items()},
                   "data_scope": "illustrative_unverified",
                   "hypothesis_testing_performed": False}, fh, indent=2)
    return status


def generate_raw_benchmark_logs(output_file: str = "data/raw/test_run.jsonl", seed: int = 42):
    """
    Generates synthetic IT benchmarking records simulating data ingestion under load.

    Compares:
      - 'baseline': Modeled higher latency attributed to I/O and contention.
      - 'proposed': Modeled lower latency, with 20 warm-up records tagged.
    IMPORTANT: no live HTTP traffic or perf_counter measurement occurs here.

    Workloads: 50, 100, 150, 200, 250 RPS (24 runs each = 120 evaluation runs per method).
    """
    print(f"[INFO] Generating synthetic benchmark scenario logs (NOT real measurements), seed={seed}...")
    rng = random.Random(seed)
    records = []
    studies = [f"ST{i:02d}" for i in range(1, 8)]
    load_levels = [50, 100, 150, 200, 250]
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    run_id = 0

    # 1. Proposed Method — Warm-up phase (20 runs)
    for i in range(20):
        rps = rng.choice(load_levels)
        # Simulated elevated warm-up latency; no actual cache/JIT measurements
        lat = round(rng.gauss(5200, 500), 2)
        records.append({
            "run_id": run_id,
            "method": "proposed",
            "phase": "warmup",
            "timestamp_utc": datetime.datetime(2026, 11, 4, 18, 0, i).isoformat() + "Z",
            "study_id": rng.choice(studies),
            "load_rps": rps,
            "latency_us": lat,
            "status": "ok",
            "error_code": None
        })
        run_id += 1

    # 2. Proposed Method — Benchmark evaluation runs (120 runs across 5 loads)
    # Monotonically increasing base latency: 2700 us at 50 RPS up to 4800 us at 250 RPS
    base_latencies = {50: 2750, 100: 3200, 150: 3700, 200: 4300, 250: 4950}
    std_devs       = {50: 220,  100: 280,  150: 340,  200: 420,  250: 520}

    for rps in load_levels:
        for _ in range(24):
            err_roll = rng.random()
            # Errors at high load (HTTP 429 rate limit at 200/250 RPS, HTTP 500 at 250 RPS)
            if rps >= 200 and err_roll < 0.08:
                status = "error"
                error_code = 429
                lat = round(rng.gauss(1400, 200), 2)  # fast rejected response
            elif rps == 250 and err_roll < 0.12:
                status = "error"
                error_code = 500
                lat = round(rng.gauss(6500, 500), 2)  # timeout failure
            else:
                status = "ok"
                error_code = None
                lat = round(rng.gauss(base_latencies[rps], std_devs[rps]), 2)

            # Deliberate synthetic outlier scenario at 250 RPS (run_id 135)
            if run_id == 135:
                lat = 7850.00

            records.append({
                "run_id": run_id,
                "method": "proposed",
                "phase": "benchmark",
                "timestamp_utc": datetime.datetime(2026, 11, 4, 18, (run_id // 60) + 1, run_id % 60).isoformat() + "Z",
                "study_id": rng.choice(studies),
                "load_rps": rps,
                "latency_us": lat,
                "status": status,
                "error_code": error_code
            })
            run_id += 1

    # 3. Baseline Method (Task 2 Naive implementation) — 120 benchmark runs
    # Assumed relative overhead (not independently measured)
    base_lat_baseline = {50: 5400, 100: 5900, 150: 6500, 200: 7300, 250: 8200}
    std_baseline      = {50: 650,  100: 780,  150: 920,  200: 1100, 250: 1350}

    for rps in load_levels:
        for _ in range(24):
            err_roll = rng.random()
            if rps >= 200 and err_roll < 0.10:
                status = "error"
                error_code = 504  # Gateway timeout
                lat = round(rng.gauss(10500, 1200), 2)
            else:
                status = "ok"
                error_code = None
                lat = round(rng.gauss(base_lat_baseline[rps], std_baseline[rps]), 2)

            records.append({
                "run_id": run_id,
                "method": "baseline",
                "phase": "benchmark",
                "timestamp_utc": datetime.datetime(2026, 11, 4, 18, (run_id // 60) + 1, run_id % 60).isoformat() + "Z",
                "study_id": rng.choice(studies),
                "load_rps": rps,
                "latency_us": lat,
                "status": status,
                "error_code": error_code
            })
            run_id += 1

    with open(output_file, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    print(f"[INFO] Written {len(records)} records (20 warmup + 120 proposed + 120 baseline) to {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run or Generate Benchmark Pipeline")
    parser.add_argument("--config", default="config.json", help="Path to config file")
    parser.add_argument("--generate-raw", action="store_true", help="Generate synthetic test_run.jsonl")
    args = parser.parse_args()

    if args.generate_raw:
        generate_raw_benchmark_logs()
    else:
        run_benchmark(args.config)
