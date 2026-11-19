"""Task 2 extraction audit and Task 3 simulated scenario generator.

Two separate strands live in this module:

* ``run_benchmark`` audits the REAL secondary data extracted from the
  bibliography (``data/extracted/*.csv``): schema, provenance, vocabulary and
  arithmetic re-expression of reported coefficients. It does not pool unlike
  outcomes and does not run new hypothesis tests.
* ``generate_raw_benchmark_logs`` creates the SYNTHETIC software-engineering
  testbed (Gaussian latency draws). The 50-250 req/s values are scenario labels,
  not achieved load, and nothing there bears on RQ1-RQ3.
"""

import argparse
import datetime
import json
import os
import math
import random
import re
import sys
import numpy as np
import pandas as pd

# Ensure UTF-8 output on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf-8-sig"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


EFFECT_REQUIRED = {"effect_id", "bib_key", "rq", "outcome_domain", "outcome", "estimate", "estimate_unit",
                   "se", "direction", "location_in_source", "verification_status", "source_version"}
SURVEY_REQUIRED = {"item_id", "bib_key", "rq", "construct", "response_category", "value_pct", "n_total",
                   "location_in_source", "verification_status"}
THEME_REQUIRED = {"theme_id", "bib_key", "rq", "theme", "description", "support", "method", "sample",
                  "location_in_source", "verification_status"}
VERIFICATION_STATUSES = {"fulltext_cross_checked", "fulltext_single_read", "abstract_or_secondary", "not_retrieved"}
RQ_LABELS = {"RQ1", "RQ2", "RQ3", "CONTEXT"}
DIRECTIONS = {"negative", "positive", "no_clear_effect", "mixed", "null_or_positive"}


def _bib_keys(bib_path: str) -> set:
    with open(bib_path, "r", encoding="utf-8") as fh:
        return set(re.findall(r"@\w+\{([^,\s]+),", fh.read()))


def _normal_two_sided_p(z: float) -> float:
    return math.erfc(abs(z) / math.sqrt(2.0))


def derive_effect_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add arithmetic re-expressions of REPORTED estimates (not new inference).

    * ``derived_pct``: exp(b) - 1 in percent, only for log-point / IHS coefficients.
    * ``z_reported`` and ``p_normal_approx``: estimate / SE with a normal approximation,
      only where the paper's own SE was extracted. These restate the authors' standard
      errors; they do not account for clustering beyond what the authors did.
    """
    out = df.copy()
    est = pd.to_numeric(out["estimate"], errors="coerce")
    se = pd.to_numeric(out["se"], errors="coerce")
    is_log = out["estimate_unit"].astype(str).str.contains("log points|IHS", case=False, regex=True)
    out["derived_pct"] = np.where(is_log & est.notna(), (np.exp(est) - 1.0) * 100.0, np.nan)
    out["z_reported"] = np.where(est.notna() & se.gt(0), est / se, np.nan)
    out["p_normal_approx"] = [(_normal_two_sided_p(z) if pd.notna(z) else np.nan) for z in out["z_reported"]]
    return out


def run_benchmark(config_path: str):
    """Audit the extracted real-data files without pooling unlike outcomes.

    Checks schema, unique identifiers, controlled vocabularies, that every ``bib_key``
    exists in the BibTeX file, and that each row records where it came from. Writes a
    derived table (percent re-expression of log coefficients, z from reported SE) and a
    JSON summary. No pooled mean, causal claim, or new hypothesis test is produced.
    """
    with open(config_path, "r", encoding="utf-8") as fh:
        config = json.load(fh)
    effects = pd.read_csv(config.get("data_path", "data/extracted/effect_estimates.csv"))
    survey = pd.read_csv(config.get("survey_path", "data/extracted/survey_items.csv"))
    themes = pd.read_csv(config.get("themes_path", "data/extracted/qualitative_themes.csv"))
    keys = _bib_keys(config.get("bib_path", "docs/Zhansaya_Zhanerke.bib"))

    for name, frame, required, id_col in (("effect_estimates", effects, EFFECT_REQUIRED, "effect_id"),
                                          ("survey_items", survey, SURVEY_REQUIRED, None),
                                          ("qualitative_themes", themes, THEME_REQUIRED, "theme_id")):
        missing = required - set(frame.columns)
        if missing:
            raise ValueError(f"{name}.csv missing columns: {sorted(missing)}")
        if frame.empty:
            raise ValueError(f"{name}.csv is empty")
        if id_col and frame[id_col].duplicated().any():
            raise ValueError(f"{name}.csv has duplicate {id_col}")
        if not set(frame["verification_status"]).issubset(VERIFICATION_STATUSES):
            raise ValueError(f"{name}.csv has unknown verification_status values")
        if not set(frame["rq"]).issubset(RQ_LABELS):
            raise ValueError(f"{name}.csv has unknown rq labels")
        unknown_keys = set(frame["bib_key"]) - keys
        if unknown_keys:
            raise ValueError(f"{name}.csv cites bib keys missing from the .bib file: {sorted(unknown_keys)}")
        if frame["location_in_source"].isna().any():
            raise ValueError(f"{name}.csv has rows without location_in_source")
    if not set(effects["direction"]).issubset(DIRECTIONS):
        raise ValueError("effect_estimates.csv has unknown direction values")
    numeric = effects["estimate"].notna()
    if effects.loc[numeric, "estimate_unit"].isna().any():
        raise ValueError("Every numeric estimate needs an estimate_unit")
    if (pd.to_numeric(effects["se"], errors="coerce").dropna() <= 0).any():
        raise ValueError("Reported standard errors must be positive")
    items = survey.drop_duplicates("item_id")
    if survey["value_pct"].lt(0).any() or survey["value_pct"].gt(100).any():
        raise ValueError("Survey percentages must lie in [0, 100]")

    derived = derive_effect_columns(effects)
    fulltext = effects["verification_status"].isin(["fulltext_cross_checked", "fulltext_single_read"])
    completeness = 100 * float(fulltext.mean())
    threshold = float(config.get("guardrail_completion_threshold", 0.0))
    status = "PASSED" if completeness >= threshold else "FAILED"

    print("[NOTE] Real secondary data extracted from the bibliography; descriptive audit only.")
    print(f"Effect rows: {len(effects)} from {effects['bib_key'].nunique()} sources; "
          f"{completeness:.1f}% read from full text; guardrail: {status}")
    for rq, group in effects.groupby("rq", sort=True):
        print(f"  {rq}: {len(group)} effect row(s) from " + ", ".join(sorted(group['bib_key'].unique())))
    print(f"Survey items: {items['item_id'].nunique()} items, {len(survey)} response rows; "
          f"qualitative themes: {len(themes)}")
    print("[NOTE] No pooled mean across outcomes, causal claim, or new hypothesis test is produced here.")

    output_path = config.get("output_path", "data/processed/extraction_audit.json")
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    derived_path = config.get("derived_path", "data/processed/effect_estimates_derived.csv")
    derived.to_csv(derived_path, index=False)
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump({"status": status,
                   "effect_rows": int(len(effects)),
                   "survey_response_rows": int(len(survey)),
                   "qualitative_themes": int(len(themes)),
                   "fulltext_share_pct": round(completeness, 2),
                   "verification_counts": {str(k): int(v) for k, v in effects["verification_status"].value_counts().items()},
                   "research_question_counts": {str(k): int(v) for k, v in effects["rq"].value_counts().items()},
                   "data_scope": "real_secondary_data_extracted_from_bibliography",
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
