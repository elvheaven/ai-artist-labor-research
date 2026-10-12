import json
import os
import argparse
import pandas as pd

def run_benchmark(config_path):
    print(f"[INFO] Loading configuration from {config_path}...")
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    data_file = config.get("data_path")
    if not os.path.exists(data_file):
        raise FileNotFoundError(f"Data file not found at {data_file}")
    
    print(f"[INFO] Reading sample dataset from {data_file}...")
    df = pd.read_csv(data_file)
    
    # 1. Primary Metric Calculation (Average Reported Pct Change)
    avg_pct_change = df["pct_change"].mean()
    
    # 2. Guardrail Metric Calculation (Data Completeness)
    completeness = (df["has_required_fields"].sum() / len(df)) * 100.0
    
    print("\n================ BENCHMARK RESULTS ================")
    print(f"Total Studies Processed: {len(df)}")
    print(f"Primary Metric (Mean Pct Change): {avg_pct_change:.2f}%")
    print(f"Guardrail Metric (Data Completeness): {completeness:.1f}%")
    
    # Validation against Guardrail Threshold
    threshold = config.get("guardrail_completion_threshold", 100.0)
    status = "PASSED" if completeness >= threshold else "FAILED"
    print(f"Pipeline Guardrail Status: {status}")
    print("===================================================\n")
    
    # Save output log
    output_path = config.get("output_path", "data/processed/benchmark_results.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    results = {
        "status": status,
        "processed_records": len(df),
        "mean_pct_change": round(avg_pct_change, 2),
        "data_completeness_pct": completeness
    }
    with open(output_path, 'w') as out_f:
        json.dump(results, out_f, indent=2)
    print(f"[INFO] Benchmark completed successfully. Log saved to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Benchmark Pipeline")
    parser.add_argument("--config", default="config.json", help="Path to config file")
    args = parser.parse_args()
    run_benchmark(args.config)
