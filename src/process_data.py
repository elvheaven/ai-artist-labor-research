"""Task 3: robust JSONL processing and descriptive statistics of SIMULATED latencies.

Usage:
    python src/process_data.py                 # produce artifacts; warn on a breach
    python src/process_data.py --strict        # also return exit status 2 on breach

Synthetic results are NOT latency measurements from a real running service and
have no evidentiary connection to artist wages, sales, or creative autonomy.
"""

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAW_LOG_PATH = 'data/raw/test_run.jsonl'
PROCESSED_DIR = 'data/processed'
REQUIRED_FIELDS = {'run_id', 'method', 'phase', 'timestamp_utc', 'study_id',
                   'load_rps', 'latency_us', 'status', 'error_code'}
GUARDRAIL_ERROR_THRESHOLD_PCT = 10.0
SEED = 42
BOOTSTRAP_REPS = 10_000


def load_jsonl(path: str) -> pd.DataFrame:
    """Fail visibly on corrupt JSON instead of silently losing failed cases."""
    records = []
    with open(path, 'r', encoding='utf-8') as fh:
        for lineno, line in enumerate(fh, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f'Invalid JSONL in {path}, line {lineno}: {exc}') from exc
            if not isinstance(record, dict):
                raise ValueError(f'Expected JSON object in {path}, line {lineno}')
            records.append(record)
    if not records:
        raise ValueError(f'No records in {path}')
    print(f'[Ingestion] {len(records)} records read from {path}')
    return pd.DataFrame(records)


def validate_schema(df: pd.DataFrame, required: set = REQUIRED_FIELDS) -> pd.DataFrame:
    """Check row-level invariants; fail fast rather than make biased omissions."""
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f'Schema missing columns: {sorted(missing)}')
    if df.empty:
        raise ValueError('Empty dataset')
    df = df.copy()
    if df[list(required - {'error_code'})].isna().any().any():
        raise ValueError('Missing mandatory field on at least one row')
    for name in ('run_id', 'load_rps', 'latency_us'):
        df[name] = pd.to_numeric(df[name], errors='raise')
    if not np.isfinite(df[['run_id', 'load_rps', 'latency_us']].to_numpy(dtype=float)).all():
        raise ValueError('Nonfinite latency/load/run ID')
    if (df['latency_us'] < 0).any() or (df['load_rps'] <= 0).any():
        raise ValueError('Negative latency or non-positive load')
    if (df['run_id'] < 0).any() or not (df['run_id'] % 1 == 0).all():
        raise ValueError('Invalid run_id')
    if not (df['load_rps'] % 1 == 0).all():
        raise ValueError('load_rps must be an integer scenario label')
    if df['run_id'].duplicated().any():
        raise ValueError('Duplicate run_id')
    if not df['method'].isin(['baseline', 'proposed']).all():
        raise ValueError('Unknown method')
    if not df['phase'].isin(['warmup', 'benchmark']).all():
        raise ValueError('Unknown phase; warmup and benchmark required')
    if not df['status'].isin(['ok', 'error']).all():
        raise ValueError('Unknown request status')
    if (df['study_id'].astype(str).str.strip() == '').any():
        raise ValueError('Empty study_id')
    times = pd.to_datetime(df['timestamp_utc'], utc=True, errors='coerce')
    if times.isna().any() or not df['timestamp_utc'].astype(str).str.endswith('Z').all():
        raise ValueError('Invalid UTC timestamp; expected ISO-8601 ending in Z')
    if df.loc[df['status'] == 'ok', 'error_code'].notna().any():
        raise ValueError('Successful row must have null error_code')
    if df.loc[df['status'] == 'error', 'error_code'].isna().any():
        raise ValueError('Failed row must include error_code')
    df['run_id'] = df['run_id'].astype(int)
    df['load_rps'] = df['load_rps'].astype(int)
    df['latency_us'] = df['latency_us'].astype(float)
    print('[Validation] Schema, types, IDs, statuses, and UTC timestamps OK')
    return df


def filter_warmup(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    warmup = df.loc[df['phase'] == 'warmup'].copy()
    benchmark = df.loc[df['phase'] == 'benchmark'].copy()
    if benchmark.empty:
        raise ValueError('No benchmark-phase records')
    print(f'[Warm-up] excluded {len(warmup)}; retained {len(benchmark)} benchmark records')
    return warmup, benchmark


def handle_errors(df: pd.DataFrame) -> tuple[pd.DataFrame, float]:
    """Keep all failures in `df`; report a success-only view for latency."""
    if df.empty:
        raise ValueError('No benchmark records')
    error_rate = 100.0 * df['status'].ne('ok').mean()
    print(f'[Guardrail] failure rate {error_rate:.2f}% ({df["status"].ne("ok").sum()}/{len(df)})')
    return df.loc[df['status'].eq('ok')].copy(), float(error_rate)


def detect_outliers_iqr(series: pd.Series, label: str = 'latency_us') -> pd.Series:
    """Return non-destructive 1.5*IQR flags; not a hardware-noise diagnosis."""
    if series.empty:
        return pd.Series(False, index=series.index, dtype=bool)
    q1, q3 = series.quantile([.25, .75])
    iqr = q3 - q1
    return (series < q1 - 1.5 * iqr) | (series > q3 + 1.5 * iqr)


def detect_outliers_iqr_grouped(df: pd.DataFrame,
                                group_cols: list[str] | None = None,
                                val_col: str = 'latency_us') -> pd.Series:
    """Flag successful runs within each (method, load) stratum; retain rows."""
    group_cols = group_cols or ['method', 'load_rps']
    flags = pd.Series(False, index=df.index, dtype=bool)
    for name, group in df.groupby(group_cols, sort=True):
        group_flags = detect_outliers_iqr(group[val_col])
        flags.loc[group.index] = group_flags
        if group_flags.any():
            print(f'[IQR] {name}: {int(group_flags.sum())} candidate outlier(s)')
    return flags


def bootstrap_ci(data: np.ndarray, stat_func=np.median, n_boot: int = BOOTSTRAP_REPS,
                 alpha: float = 0.05, seed: int = SEED) -> tuple[float, float]:
    """Percentile bootstrap CI for the chosen statistic (success samples only)."""
    data = np.asarray(data, dtype=float)
    if not len(data) or not np.isfinite(data).all() or n_boot < 1 or not 0 < alpha < 1:
        raise ValueError('Invalid bootstrap input')
    rng = np.random.default_rng(seed)
    stats = np.empty(n_boot)
    for i in range(n_boot):
        stats[i] = stat_func(rng.choice(data, size=len(data), replace=True))
    return tuple(float(x) for x in np.quantile(stats, [alpha / 2, 1 - alpha / 2]))


def guardrail_status(error_rate_pct: float) -> str:
    return 'PASSED' if error_rate_pct <= GUARDRAIL_ERROR_THRESHOLD_PCT else 'BREACHED (>10.0%)'


def _summary_row(method_label: str, condition: str, load_rps: int,
                 group: pd.DataFrame) -> dict:
    ok = group.loc[group['status'] == 'ok']
    a = ok['latency_us'].to_numpy(dtype=float)
    error_rate = 100 * (1 - len(ok) / len(group))
    if len(a):
        lo, hi = bootstrap_ci(a)
        stats = {
            'latency_median_us': np.median(a),
            'latency_p25_us': np.percentile(a, 25),
            'latency_p75_us': np.percentile(a, 75),
            'latency_mean_us': np.mean(a),
            'latency_sd_us': np.std(a, ddof=1) if len(a) > 1 else np.nan,
            'latency_median_ci95_lo': lo,
            'latency_median_ci95_hi': hi,
            'latency_p95_us': np.percentile(a, 95),
            'latency_p99_us': np.percentile(a, 99),
        }
    else:
        stats = {k: np.nan for k in (
            'latency_median_us', 'latency_p25_us', 'latency_p75_us', 'latency_mean_us',
            'latency_sd_us', 'latency_median_ci95_lo', 'latency_median_ci95_hi',
            'latency_p95_us', 'latency_p99_us')}
    return {'method': method_label, 'condition': condition, 'load_rps': load_rps,
            'n_total': len(group), 'n_ok': len(ok),
            'error_rate_pct': round(error_rate, 2),
            'guardrail_status': guardrail_status(error_rate),
            **{key: round(float(value), 2) for key, value in stats.items()}}


def aggregate_benchmarks(df_bench: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for key, label, short in (
        ('proposed', 'Proposed (Task 3)', 'Proposed'),
        ('baseline', 'Baseline (Task 2)', 'Baseline'),
    ):
        method = df_bench.loc[df_bench['method'] == key]
        if method.empty:
            continue
        for load, group in method.groupby('load_rps', sort=True):
            rows.append(_summary_row(label, f'{short} @ {load} RPS', int(load), group))
        rows.append(_summary_row(label, f'{short} OVERALL', 0, method))
    if not rows:
        raise ValueError('No methods with benchmark data')
    return pd.DataFrame(rows)


def format_markdown_table(summary: pd.DataFrame) -> str:
    """Report successes, failure guardrail, dispersion and median CI."""
    headings = ['Condition', 'n (total/OK)', 'Errors', 'Guardrail (≤10%)',
                'Median (p25–p75), µs', 'Mean ± SD, µs', 'Median CI95, µs', 'p95, µs']
    lines = ['| ' + ' | '.join(headings) + ' |', '| ' + ' | '.join(['---'] * len(headings)) + ' |']
    def fmt(v):
        return 'N/A' if pd.isna(v) else f'{v:,.2f}'
    for _, row in summary.iterrows():
        median = f'{fmt(row.latency_median_us)} ({fmt(row.latency_p25_us)}–{fmt(row.latency_p75_us)})'
        mean_sd = f'{fmt(row.latency_mean_us)} ± {fmt(row.latency_sd_us)}'
        ci = f'[{fmt(row.latency_median_ci95_lo)}, {fmt(row.latency_median_ci95_hi)}]'
        lines.append(f'| {row.condition} | {int(row.n_total)}/{int(row.n_ok)} | '
                     f'{row.error_rate_pct:.2f}% | {row.guardrail_status} | '
                     f'{median} | {mean_sd} | {ci} | {fmt(row.latency_p95_us)} |')
    return '\n'.join(lines)


def run_pipeline(strict: bool = False):
    raw = validate_schema(load_jsonl(RAW_LOG_PATH))
    warmup, benchmark = filter_warmup(raw)
    ok, overall_error_rate = handle_errors(benchmark)
    # Preserve ALL benchmark records, including failures, in the clean audit log.
    clean = benchmark.copy()
    clean['is_outlier'] = False
    clean.loc[ok.index, 'is_outlier'] = detect_outliers_iqr_grouped(ok)
    Path(PROCESSED_DIR).mkdir(parents=True, exist_ok=True)
    clean.to_csv(os.path.join(PROCESSED_DIR, 'benchmark_clean.csv'), index=False)
    summary = aggregate_benchmarks(benchmark)
    summary.to_csv(os.path.join(PROCESSED_DIR, 'metrics_summary.csv'), index=False)
    breached = summary.loc[summary['guardrail_status'].str.startswith('BREACHED')]
    print(f'[Data] {len(clean)} evaluation records retained, '
          f'{len(warmup)} warm-up excluded, {len(breached)} guardrail breach(es)')
    print('[Interpretation] Latency distributions are conditional on success; '
          'all failed cases remain in the clean audit log and error rates.')
    print('[Warning] SIMULATED latency results, not measured live throughput.')
    print(format_markdown_table(summary))
    if strict and not breached.empty:
        raise RuntimeError('STRICT MODE: one or more per-load error-rate guardrails breached')
    return summary, clean, format_markdown_table(summary)


def main():
    parser = argparse.ArgumentParser(description='Process simulated Task 3 benchmark logs')
    parser.add_argument('--strict', action='store_true',
                        help='return nonzero exit status if any error guardrail is breached')
    args = parser.parse_args()
    try:
        run_pipeline(strict=args.strict)
    except RuntimeError as exc:
        print(f'[FAIL] {exc}', file=sys.stderr)
        sys.exit(2)


if __name__ == '__main__':
    main()
