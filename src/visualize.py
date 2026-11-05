"""Task 3 publication graphs of explicitly SIMULATED baseline/proposed scenarios.

Both variants are compared at the SAME load (req/s is a scenario label, not
verified achieved throughput). The plots report success-only latency and
failure-rate guardrails are documented separately in the summary table.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style='whitegrid', font_scale=1.12)
PALETTE = sns.color_palette('colorblind')
DPI = 300
FIGURES_DIR = 'reports/figures'


def export_figure(fig, basename):
    Path(FIGURES_DIR).mkdir(parents=True, exist_ok=True)
    for ext in ('pdf', 'png'):
        destination = Path(FIGURES_DIR) / f'{basename}.{ext}'
        fig.savefig(destination, dpi=DPI, bbox_inches='tight')
        print(f'[plot] {destination}')


def plot_fig1_latency_vs_load(summary_df: pd.DataFrame, clean_df=None):
    """Baseline and proposed median with 95% bootstrap CIs at matched load."""
    fig, ax = plt.subplots(figsize=(9.5, 5.8))
    definitions = (
        ('baseline', 'Baseline (simulated)', PALETTE[1], '--', 's'),
        ('proposed', 'Proposed (simulated)', PALETTE[0], '-', 'o'),
    )
    for key, name, color, linestyle, marker in definitions:
        subset = summary_df.loc[
            summary_df['method'].str.lower().str.startswith(key) & (summary_df['load_rps'] > 0)
        ].sort_values('load_rps')
        if subset.empty:
            raise ValueError(f'No summary rows for {name}')
        x = subset['load_rps'].to_numpy(float)
        y = subset['latency_median_us'].to_numpy(float)
        low = subset['latency_median_ci95_lo'].to_numpy(float)
        high = subset['latency_median_ci95_hi'].to_numpy(float)
        ax.plot(x, y, linestyle=linestyle, color=color, marker=marker,
                linewidth=2.4, markersize=8, label=f'{name}: median')
        ax.fill_between(x, low, high, color=color, alpha=.18,
                        label=f'{name}: median 95% bootstrap CI')
    ax.set_xlabel('Modeled request rate (requests/s)', weight='bold')
    ax.set_ylabel('Successful-request latency (µs)', weight='bold')
    ax.set_title('Figure 1 — Matched-load median latency (synthetic scenarios)', pad=12)
    ax.set_xticks(sorted(summary_df.loc[summary_df['load_rps'] > 0, 'load_rps'].unique()))
    ax.set_ylim(bottom=0)
    ax.legend(loc='upper left', fontsize=9)
    ax.text(.01, -.19,
            'Shaded regions: 95% percentile bootstrap CI for median (10,000 resamples, seed 42).  '
            'Failure rates reported separately.\n'
            'Simulation only: modeled request rates, not measured throughput; no real system speedup claim.',
            transform=ax.transAxes, va='top', fontsize=9)
    fig.tight_layout()
    export_figure(fig, 'fig1_latency_vs_load')
    return fig


def plot_fig2_distribution_boxplot(clean_df: pd.DataFrame, summary_df: pd.DataFrame | None = None):
    """Side-by-side baseline/proposed distributions for each identical load."""
    if summary_df is None:
        summary_df = pd.read_csv('data/processed/metrics_summary.csv')
    ok = clean_df.loc[clean_df['status'] == 'ok'].copy()
    loads = sorted(ok['load_rps'].unique())
    if not loads:
        raise ValueError('No successful samples for figure 2')
    fig, ax = plt.subplots(figsize=(10.5, 6.2))
    positions, distributions, shades = [], [], []
    for idx, load in enumerate(loads):
        for key, offset, color in [('baseline', -.18, PALETTE[1]),
                                   ('proposed', .18, PALETTE[0])]:
            subset = ok.loc[(ok['method'] == key) & (ok['load_rps'] == load)]
            if subset.empty:
                continue
            pos = idx + offset
            positions.append(pos)
            distributions.append(subset['latency_us'].to_numpy(float))
            shades.append(color)
            if 'is_outlier' in subset.columns:
                outliers = subset.loc[subset['is_outlier'].astype(bool)]
                if not outliers.empty:
                    ax.scatter(np.full(len(outliers), pos), outliers['latency_us'],
                               marker='^', s=62, color='black', zorder=6)
            label = f'{key.capitalize()} @ {load} RPS'
            ci = summary_df.loc[summary_df['condition'] == label]
            if len(ci):
                row = ci.iloc[0]
                med = float(row['latency_median_us'])
                lower, upper = float(row['latency_median_ci95_lo']), float(row['latency_median_ci95_hi'])
                ax.errorbar(pos, med, yerr=[[max(0., med-lower)], [max(0., upper-med)]],
                            fmt='D', markerfacecolor='white', markeredgecolor='black',
                            ecolor='black', elinewidth=1.4, capsize=4, markersize=5.5, zorder=7)
    boxes = ax.boxplot(distributions, positions=positions, widths=.29, patch_artist=True,
                       whis=1.5, showfliers=False,
                       medianprops={'color': 'black', 'linewidth': 1.8},
                       whiskerprops={'linestyle': '--'},
                       capprops={'linewidth': 1.3})
    for patch, shade in zip(boxes['boxes'], shades):
        patch.set_facecolor(shade)
        patch.set_alpha(.45)
    ax.set_xticks(range(len(loads)))
    ax.set_xticklabels([str(x) for x in loads])
    ax.set_xlabel('Modeled request rate (requests/s)', weight='bold')
    ax.set_ylabel('Successful-request latency (µs)', weight='bold')
    ax.set_title('Figure 2 — Matched-load latency dispersion (synthetic scenarios)', pad=12)
    ax.set_ylim(bottom=0)
    from matplotlib.patches import Patch
    from matplotlib.lines import Line2D
    ax.legend(handles=[Patch(facecolor=PALETTE[1], alpha=.45, label='Baseline'),
                       Patch(facecolor=PALETTE[0], alpha=.45, label='Proposed'),
                       Line2D([0], [0], marker='D', color='black', markerfacecolor='white',
                              linestyle='None', label='Median + 95% bootstrap CI'),
                       Line2D([0], [0], marker='^', color='black', linestyle='None',
                              label='Grouped 1.5×IQR flagged observation')],
              loc='upper left', fontsize=9)
    ax.text(.01, -.19,
            'Boxes: p25–p75, black lines: median, dashed whiskers: 1.5×IQR. '
            'Black triangles flag statistical outliers; they are not proven hardware noise.\n'
            'Diamonds with capped bars: median ± 95% percentile-bootstrap interval. '
            'Error events remain in CSV and guardrail table.',
            transform=ax.transAxes, va='top', fontsize=8.8)
    fig.tight_layout()
    export_figure(fig, 'fig2_distribution_boxplot')
    return fig


def generate_all_figures():
    summary = pd.read_csv('data/processed/metrics_summary.csv')
    clean = pd.read_csv('data/processed/benchmark_clean.csv')
    fig1 = plot_fig1_latency_vs_load(summary, clean)
    fig2 = plot_fig2_distribution_boxplot(clean, summary)
    plt.close(fig1)
    plt.close(fig2)


if __name__ == '__main__':
    generate_all_figures()
