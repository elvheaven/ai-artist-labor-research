"""Task 3 tests: numeric invariants, schema robustness, reproducibility and outputs."""
import csv
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import nbformat
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.benchmark import generate_raw_benchmark_logs, run_benchmark
from src.process_data import (REQUIRED_FIELDS, bootstrap_ci, validate_schema,
    load_jsonl, filter_warmup, handle_errors, detect_outliers_iqr_grouped,
    aggregate_benchmarks, format_markdown_table, guardrail_status)


class Task3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = validate_schema(load_jsonl(str(ROOT / 'data/raw/test_run.jsonl')), REQUIRED_FIELDS)
        cls.warm, cls.eval = filter_warmup(cls.raw)
        cls.summary = aggregate_benchmarks(cls.eval)

    def test_raw_count_and_phases(self):
        self.assertEqual(len(self.raw), 260)
        self.assertEqual(len(self.warm), 20)
        self.assertEqual(len(self.eval), 240)

    def test_seeded_generator_is_deterministic(self):
        with tempfile.TemporaryDirectory() as temp:
            a = Path(temp)/'a.jsonl'; b = Path(temp)/'b.jsonl'
            generate_raw_benchmark_logs(str(a), seed=42)
            generate_raw_benchmark_logs(str(b), seed=42)
            self.assertEqual(a.read_bytes(), b.read_bytes())
            self.assertEqual(a.read_bytes(), (ROOT/'data/raw/test_run.jsonl').read_bytes())

    def test_invalid_jsonl_fails_fast(self):
        with tempfile.TemporaryDirectory() as temp:
            fn = Path(temp)/'bad.jsonl'
            fn.write_text('{"valid":1}\nnot json\n', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'line 2'):
                load_jsonl(str(fn))

    def test_schema_missing_column_rejected(self):
        with self.assertRaisesRegex(ValueError, 'missing'):
            validate_schema(self.raw.drop(columns=['status']))

    def test_schema_duplicate_id_rejected(self):
        df = self.raw.copy()
        df.loc[df.index[-1], 'run_id'] = df.iloc[0].run_id
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            validate_schema(df)

    def test_schema_non_numeric_latency_rejected(self):
        df = self.raw.copy()
        df.loc[df.index[0], 'latency_us'] = 'invalid'
        with self.assertRaises((ValueError, TypeError)):
            validate_schema(df)

    def test_schema_negative_latency_rejected(self):
        df = self.raw.copy()
        df.loc[df.index[0], 'latency_us'] = -1
        with self.assertRaisesRegex(ValueError, 'Negative'):
            validate_schema(df)

    def test_schema_missing_error_code_rejected(self):
        df = self.raw.copy()
        idx = df.index[df.status == 'error'][0]
        df.loc[idx, 'error_code'] = None
        with self.assertRaisesRegex(ValueError, 'error_code'):
            validate_schema(df)

    def test_schema_utc_bad_rejected(self):
        df = self.raw.copy()
        df.loc[df.index[0], 'timestamp_utc'] = 'today'
        with self.assertRaisesRegex(ValueError, 'UTC'):
            validate_schema(df)

    def test_guardrail_denominator_includes_failures(self):
        success, rate = handle_errors(self.eval)
        self.assertEqual(len(success), int(self.eval.status.eq('ok').sum()))
        self.assertAlmostEqual(rate, 100 * self.eval.status.ne('ok').mean(), places=8)
        self.assertGreater(rate, 0)

    def test_grouped_iqr_spike_preserved(self):
        ok = self.eval[self.eval.status == 'ok'].copy()
        flags = detect_outliers_iqr_grouped(ok)
        spike = ok[ok.run_id == 135]
        self.assertEqual(len(spike), 1)
        self.assertEqual(float(spike.iloc[0].latency_us), 7850.0)
        self.assertTrue(bool(flags.loc[spike.index[0]]))
        self.assertEqual(len(flags), len(ok))

    def test_bootstrap_reproducible(self):
        a = bootstrap_ci(np.array([1., 2., 4., 8., 16.]), n_boot=300, seed=42)
        b = bootstrap_ci(np.array([1., 2., 4., 8., 16.]), n_boot=300, seed=42)
        self.assertEqual(a, b)
        self.assertLessEqual(a[0], 4)
        self.assertGreaterEqual(a[1], 4)

    def test_bootstrap_rejects_empty(self):
        with self.assertRaises(ValueError):
            bootstrap_ci(np.array([]))

    def test_10_summary_strata_plus_overall(self):
        self.assertEqual(len(self.summary), 12)
        self.assertIn('Proposed @ 250 RPS', self.summary.condition.values)

    def test_guardrail_per_condition_not_pooled(self):
        proposed_250 = self.summary[self.summary.condition == 'Proposed @ 250 RPS'].iloc[0]
        proposed_all = self.summary[self.summary.condition == 'Proposed OVERALL'].iloc[0]
        self.assertAlmostEqual(proposed_250.error_rate_pct, 12.5)
        self.assertEqual(guardrail_status(proposed_250.error_rate_pct), 'BREACHED (>10.0%)')
        self.assertEqual(proposed_all.guardrail_status, 'PASSED')

    def test_clean_csv_retains_errors(self):
        df = pd.read_csv(ROOT/'data/processed/benchmark_clean.csv')
        self.assertEqual(len(df), 240)
        self.assertEqual(int(df.status.ne('ok').sum()), int(self.eval.status.ne('ok').sum()))
        self.assertTrue((df.loc[df.status.ne('ok'), 'is_outlier'] == False).all())

    def test_summary_csv_coherent(self):
        summary = pd.read_csv(ROOT/'data/processed/metrics_summary.csv')
        self.assertEqual(len(summary), 12)
        self.assertTrue((summary.latency_median_ci95_lo <= summary.latency_median_ci95_hi).all())
        self.assertTrue((summary.n_total >= summary.n_ok).all())

    def test_markdown_table_uses_real_summary(self):
        table = format_markdown_table(self.summary)
        self.assertIn('Proposed @ 250 RPS', table)
        self.assertIn('BREACHED', table)
        self.assertIn('95', table)

    def test_sample_provenance_and_rq_classification(self):
        sample = pd.read_csv(ROOT/'data/sample/sample_dataset.csv')
        self.assertEqual(set(sample.research_question), {'RQ1','RQ2','RQ3','CONTEXT'})
        self.assertTrue(sample.data_provenance.eq('illustrative_unverified').all())
        self.assertTrue(np.allclose((sample.value_after - sample.value_before) / sample.value_before * 100,
                                    sample["pct_change"], atol=.15))
        self.assertNotIn('mean_pct_change', run_benchmark.__doc__ or '')

    def test_config_and_bib_and_docs(self):
        for f in ['config.json','docs/domain_model.md',
                  'docs/methodology_passport.md','docs/Zhansaya_Zhanerke.bib']:
            self.assertTrue((ROOT/f).is_file())
        self.assertIn('MCP-1', (ROOT/'docs/domain_model.md').read_text(encoding='utf-8'))

    def test_all_figures_have_both_formats(self):
        for f in ['fig1_latency_vs_load','fig2_distribution_boxplot']:
            for ext in ['png','pdf']:
                self.assertGreater((ROOT/f'reports/figures/{f}.{ext}').stat().st_size, 1000)

    def test_notebook_is_executed_with_outputs(self):
        notebook = nbformat.read(ROOT/'notebooks/01_data_analysis.ipynb', as_version=4)
        code_cells = [cell for cell in notebook.cells if cell.cell_type == 'code']
        self.assertGreaterEqual(len(code_cells), 5)
        self.assertTrue(all(isinstance(c.execution_count, int) and c.execution_count > 0 for c in code_cells))
        self.assertTrue(all(len(c.outputs) > 0 for c in code_cells))
        self.assertFalse(any(output.output_type == 'error' for c in code_cells for output in c.outputs))

    def test_no_dockerfile_or_requirements(self):
        self.assertFalse((ROOT/'Dockerfile').exists())
        self.assertFalse((ROOT/'requirements.txt').exists())

    def test_gitignore_protects_runtime_garbage(self):
        ig = (ROOT/'.gitignore').read_text(encoding='utf-8')
        self.assertIn('__pycache__/', ig)
        self.assertIn('.ipynb_checkpoints/', ig)
        self.assertIn('.venv/', ig)

    def test_strict_mode_exits_nonzero_on_breach(self):
        result = subprocess.run([sys.executable, 'src/process_data.py', '--strict'],
            cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn('STRICT MODE', result.stderr)

if __name__ == '__main__':
    unittest.main()
