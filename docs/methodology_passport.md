# Research methodology passport

**Title:** The Impact of Generative Text-to-Image Models on Commercial Visual Artists' Paid Opportunities and Professional Autonomy (2023–2026)
**Authors:** Zhanerke Abdumalik and Zhansaya Baikenova
**Bibliography:** [`Zhansaya_Zhanerke.bib`](Zhansaya_Zhanerke.bib) — a mixture of journal/conference contributions and working-paper or other research records. The existence of a record does not independently verify every numerical claim.
**Design:** comparative mixed-methods **literature synthesis**, supported by a *separate synthetic software-engineering demonstration*.

## Research questions

| RQ | Question | Intended outcome | What can be concluded from this repository? |
|---|---|---|---|
| RQ1 | How has text-to-image AI diffusion been associated with paid commissions, job postings and compensation? | Separate measures of paid work, compensation and postings | Bibliographic synthesis is possible; the sample CSV is illustrative and cannot establish significance |
| RQ2 | How does platform permission for generative assets relate to human-created asset production/sales? | Platform-specific sales or revenue with an explicit policy and comparison group | One unverified example row; no causal or statistical inference |
| RQ3 | How is creative autonomy/work allocation changing for illustrators? | Interview themes or valid participant-level autonomy surveys | Descriptive and qualitative synthesis only; no participant-level numerator/denominator for a binomial test |

### Hypotheses are preregistered research goals, not results

- **RQ1 H0:** nonnegative change in comparable paid-work outcomes; **H1:** negative change. An appropriately harmonized sample and valid study variances are needed before testing.
- **RQ2 H0:** no decrease in human asset sales following platform-policy exposure; **H1:** decrease. Credible comparison groups and policy timing are needed to separate association from causation.
- **RQ3 H0:** at most 50% of a defined population experiences loss of creative autonomy; **H1:** more than 50%. A binomial test requires observed participant counts and sampling design; these are **not** provided by the demo CSV.

**Important:** The seven illustrative `ST01`–`ST07` rows in `data/sample/sample_dataset.csv` are tagged `illustrative_unverified`. Their before/after counts and percentages must **not** be cited as factual findings of named articles. We intentionally do not compute a pooled mean across incompatible metrics or fabricate p-values. Some abstracts in the BibTeX independently mention selected numbers, but that does not validate invented row-level before/after counts.

## Study-selection and extraction protocol (required before empirical claims)

1. Select publications dated 2023–2026 relevant to paid commercial visual art, online asset platforms, or professional creative autonomy.
2. Record bibliographic key, study design, sampling frame, exposure definition, comparison group, outcome unit, observation period, effect estimate and uncertainty.
3. Independently check that exact numbers quoted appear in the paper, not merely in its title or a secondary claim.
4. Keep earnings, postings, asset sales, productivity and qualitative autonomy themes in **distinct analyses**. Never pool percent change across unlike outcomes.
5. If no verified observations or variance estimates exist, report descriptive qualitative synthesis only, with **no hypothesis significance result**.

## Variables and threats to validity

- **Exposure (IV):** model release, client adoption, or platform policy change depending on RQ; not interchangeable.
- **Outcomes (DV):** paid opportunities, compensation, sales, and creative autonomy; different units and populations.
- **Confounders:** sector, geographic market, artist experience, seasonal demand, simultaneous platform changes, study time windows and self-selection.
- **Limitations:** publication selection bias, heterogeneous study measures, observational/qualitative designs, incomplete verification of the small sample, and no causal identification in the synthetic benchmark.

## Task 3 software-engineering demonstration

The separate testbed in `src/benchmark.py` generates **260 synthetic JSONL rows**: 20 warm-up and 240 evaluation records across five **modeled load labels** (50–250 requests/s) and two methods. It does not create real network traffic or measure actual machine performance. The sample models *hypothetical* higher latency for baseline vs lower latency for proposed; therefore any simulated difference follows assumptions of the data generator.

### Evaluation metrics and guardrails

| Metric | Definition | Threshold/behavior |
|---|---|---|
| JSONL correctness | Valid objects, required fields, UTC timestamps, valid status/load/IDs | Fail fast on any bad record |
| Warm-up | Phase explicitly tagged `warmup` | Exclude from evaluation only; preserve in raw JSONL |
| Success-only median and p25/p75/p95/p99 | Evaluation latencies conditional on `status == ok` | Report alongside error rate, not as all-request latency |
| Error rate | All failed evaluation attempts / all evaluation attempts in every method × load stratum | Pass only when **≤10%** in **every** stratum |
| Outlier candidates | 1.5×IQR fences within each method × load | Flag without removing successful rows |
| Uncertainty | 95% percentile bootstrap of simulated successful latencies | 10,000 resamples; seed 42 |
| Plot quality | Explicit axis units, 95% CIs, accessible palette plus line/marker distinctions | Export both 300 DPI PNG and vector PDF |
| Source provenance | Study numbers must be independently checked | Demo rows remain labeled unverified; cannot support hypothesis rejection |

In the committed sample, Proposed @ 250 RPS has a **12.50%** simulated failure rate and **BREACHES** the 10% threshold, even though overall Proposed is 4.17%. The breach is **not repaired by hiding data or tuning results**. `python src/process_data.py` emits the CSV and prints a warning; `python src/process_data.py --strict` still writes the audit artifacts but exits with **code 2** so a validation job can block release. This is an *implemented CLI gate*, not a claim that CI/CD is connected.

## Baselines and interpretation

- **Research baseline:** each eligible paper's own pre-adoption or untreated group, if documented.
- **Technical baseline:** a slower **simulated** distribution at the same load label, NOT the pre-AI period for artists.
- **Research conclusion:** none of H1–H3 can be confirmed with this demonstration dataset. Statements about labor impact must be based on independently verified primary sources.

See architecture and equations in [`domain_model.md`](domain_model.md).
