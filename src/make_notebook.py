"""Regenerate and execute the Task 3 notebook with outputs embedded.

Run from any working directory: python src/make_notebook.py
Uses nbformat and nbclient (pip install nbformat nbclient ipykernel).
"""
from pathlib import Path
import nbformat as nbf
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'notebooks' / '01_data_analysis.ipynb'


def md(content):
    return nbf.v4.new_markdown_cell(content.strip())


def code(content):
    return nbf.v4.new_code_cell(content.strip())


def build():
    nb = nbf.v4.new_notebook()
    nb.metadata = {
        'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
        'language_info': {'name': 'python', 'version': '3.11'},
    }
    nb.cells = [
        md(r'''
# Task 3 — Reproducible Data Analysis and Scientific Visualization

**Project:** The Impact of Generative AI on Commercial Visual Artists (2023–2026)  
**Authors:** Zhanerke Abdumalik and Zhansaya Baikenova  
**Sources:** [Bibliography](../docs/Zhansaya_Zhanerke.bib) · [Domain model](../docs/domain_model.md) · [Methodology](../docs/methodology_passport.md)

## Scope and validity

Two independent strands are included: (1) an **unverified illustrative dataset** for research questions RQ1–RQ3 and (2) a **simulated** workload/latency testbed for Task 3 data-engineering methods. Simulated latencies are Gaussian samples, **not measured real requests or real speedup**. The illustrative study values cannot support t-test, Wilcoxon, or binomial conclusions about artists. The benchmark demonstrates reproducible schema validation, guardrails, uncertainty quantification, and scientific graphics.

We report successful-request latency **conditionally on success** and failure rate on **all evaluation attempts**. The simulated 250 RPS proposed scenario deliberately breaches the 10% error-rate guardrail; this is a documented failure, not a passing result.
'''),
        md('## 1. Setup and provenance'),
        code(r'''
from pathlib import Path
import sys
import pandas as pd
import numpy as np
from IPython.display import display, Image

ROOT = Path.cwd()
if ROOT.name == 'notebooks':
    ROOT = ROOT.parent
sys.path.insert(0, str(ROOT))
from src.process_data import (load_jsonl, validate_schema, filter_warmup,
    handle_errors, detect_outliers_iqr_grouped, aggregate_benchmarks,
    format_markdown_table, RAW_LOG_PATH, REQUIRED_FIELDS)
from src.visualize import (plot_fig1_latency_vs_load,
    plot_fig2_distribution_boxplot, FIGURES_DIR)
print('Repository root:', ROOT)
print('Input is SIMULATED: no real service was benchmarked.')
'''),
        md(r'''
## 2. Ingestion, schema validation, and warm-up exclusion

MCP-1 validates JSON structure, numeric constraints, UTC timestamps, unique IDs, and status/error consistency. No malformed record is silently dropped. The first 20 tagged warm-up rows are excluded from **evaluation** but remain in the original JSONL. MCP-2 retains all error outcomes for the guardrail. The clean audit CSV retains both successful and failed evaluation records.
'''),
        code(r'''
raw = validate_schema(load_jsonl(str(ROOT / RAW_LOG_PATH)), REQUIRED_FIELDS)
warmup, evaluation = filter_warmup(raw)
success, error_rate = handle_errors(evaluation)
clean = evaluation.copy()
clean['is_outlier'] = False
clean.loc[success.index, 'is_outlier'] = detect_outliers_iqr_grouped(success)
(ROOT / 'data/processed').mkdir(parents=True, exist_ok=True)
clean.to_csv(ROOT / 'data/processed/benchmark_clean.csv', index=False)
print('Warm-up:', len(warmup), '| Evaluation:', len(evaluation),
      '| OK:', len(success), '| Failed:', len(evaluation)-len(success),
      '| Error rate:', round(error_rate,2), '%')
display(clean.head(6))
'''),
        md(r'''
## 3. Aggregation, IQR outliers and bootstrap intervals

MCP-3 groups by method and scenario load. For each, we calculate mean, standard deviation, median, p25, p75, p95, p99, and the median's **95% percentile bootstrap CI** (10,000 draws, fixed RNG seed 42). The IQR fence flags unusual points; an outlier is not automatically hardware noise. Failed attempts are excluded from the **conditional success-latency distribution** but **included in error rates**. The guardrail must pass at **each individual load**, not only on average.
'''),
        code(r'''
summary = aggregate_benchmarks(evaluation)
summary.to_csv(ROOT / 'data/processed/metrics_summary.csv', index=False)
display(summary[['condition','n_total','n_ok','error_rate_pct','guardrail_status',
    'latency_median_us','latency_median_ci95_lo','latency_median_ci95_hi']])
print('Guardrail breaches:')
display(summary.loc[summary['guardrail_status'].str.startswith('BREACHED'),
    ['condition','error_rate_pct','guardrail_status']])
print('Flagged IQR candidates (not deleted):', int(clean['is_outlier'].sum()))
'''),
        md(r'''
## 4. Research example audit — RQ1/RQ2/RQ3

The seven **illustrative** rows are intentionally separated into research domains to avoid a scientifically invalid pooled mean of wages, sales, productivity, and autonomy. Values are marked `illustrative_unverified` and **are not extracted primary-source effect estimates**. The bibliography is an inventory of potentially relevant references, not independent validation of these fabricated demonstration counts. Hypothesis p-values are not calculated because the necessary verified study-level or participant-level samples are unavailable.
'''),
        code(r'''
examples = pd.read_csv(ROOT / 'data/sample/sample_dataset.csv')
assert examples['data_provenance'].eq('illustrative_unverified').all()
assert np.allclose((examples['value_after']-examples['value_before']) /
                   examples['value_before'] * 100, examples['pct_change'], atol=.15)
print('Illustrative example counts by research question:')
display(examples.groupby('research_question', as_index=False).agg(
    illustrative_rows=('study_id','count'), metrics=('metric_name', lambda x: ', '.join(x))))
display(examples[['study_id','research_question','metric_name',
                  'pct_change','source_bib_key','data_provenance']])
print('NO hypothesis significance claim; the rows cannot be pooled across outcomes.')
'''),
        md(r'''
## 5. Three scientific visualization rules

**Rule 1:** units and correct axes; modeled request rate (requests/s) is **not achieved live RPS**.  
**Rule 2:** show uncertainty (median 95% CI) and dispersion (IQR) without pretending the intervals establish real-system performance.  
**Rule 3:** use a colorblind-safe palette plus separate markers/line styles so the figure remains legible without color.

Figure 1 compares **Baseline vs Proposed at each identical workload** instead of comparing a load-specific curve to a pooled baseline. Figure 2 places pairs of boxplots side-by-side per load. Both export PNG (300 DPI) and vector PDF.
'''),
        code(r'''
import matplotlib.pyplot as plt
fig1 = plot_fig1_latency_vs_load(summary, clean)
plt.close(fig1)
display(Image(filename=str(ROOT / FIGURES_DIR / 'fig1_latency_vs_load.png')))
'''),
        code(r'''
fig2 = plot_fig2_distribution_boxplot(clean, summary)
plt.close(fig2)
display(Image(filename=str(ROOT / FIGURES_DIR / 'fig2_distribution_boxplot.png')))
'''),
        md('## 6. Automated output checks and research limitations'),
        code(r'''
assert len(raw) == 260 and len(warmup) == 20 and len(evaluation) == 240
assert len(clean) == len(evaluation)  # failed attempts preserved
assert clean['status'].ne('ok').sum() == evaluation['status'].ne('ok').sum()
assert not summary['latency_median_ci95_lo'].isna().all()
assert (summary['guardrail_status'].str.startswith('BREACHED')).any()
for label in ['fig1_latency_vs_load','fig2_distribution_boxplot']:
    for ext in ['pdf','png']:
        assert (ROOT / FIGURES_DIR / f'{label}.{ext}').is_file()
print('PASS: schema, counts, preserved failures, median CIs, deliberate breach, figure exports.')
print('LIMITATION: numerical research hypotheses remain UNTESTED; live request rates were NOT measured.')
'''),
        md(r'''
### Interpretation

The lower *simulated* proposed medians are consequences of assumptions chosen in the two Gaussian generators, not proof that data collection became faster in production. Since there is a deliberate >10% failure-rate breach at one load, the proposed scenario **does not pass** the per-load reliability criterion. This synthetic software-pipeline exercise must not be interpreted as evidence that generative AI raises or reduces real commercial artists' earnings, sales, or autonomy. Full study-level primary-source extraction and appropriate outcome-specific methods would be a separate required research step.
'''),
    ]
    return nb


def main():
    DEST.parent.mkdir(parents=True, exist_ok=True)
    notebook = build()
    NotebookClient(notebook, timeout=300, kernel_name='python3',
                   resources={'metadata': {'path': str(ROOT)}}).execute()
    nbf.write(notebook, DEST)
    print(f'Notebook EXECUTED, saved outputs: {DEST} ({len(notebook.cells)} cells)')


if __name__ == '__main__':
    main()
