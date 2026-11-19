# Source assessment: is the library enough for a mixed-methods study on secondary data?

**Scope.** The 11 records in [`Zhansaya_Zhanerke.bib`](Zhansaya_Zhanerke.bib) were read (full text where openly available, otherwise abstract and secondary reports) to decide how far they support a study that combines **quantitative** and **qualitative** **secondary** data on generative AI and commercial visual artists (RQ1 paid work, RQ2 human-made asset sales, RQ3 creative autonomy). The structured results are in [`data/extracted/`](../data/extracted/); this note explains what they mean.

## 1. Verdict

| Strand | Is the library enough? | Why |
|---|---|---|
| **Qualitative** | Yes, for a descriptive synthesis | Jiang et al. (2026) gives 12 open-text themes from 378 professional visual artists; Kyi et al. (2025) gives interview themes (20 participants, 7 of them visual artists). Neither reports theme counts, so prevalence claims are not possible. |
| **Quantitative, RQ2** (asset sales) | Yes, but with one study | Goldberg & Lam (2025) is a full DiD with tables. It is a single unnamed platform and an unreviewed working paper, so nothing can be pooled or generalised. |
| **Quantitative, RQ1** (paid work) | Partly | Hui et al. (2024) has full estimates with standard errors. Demirci et al. (2025) and Makridis are in the library but their full texts are still unread (Demirci: working-paper decimals only; Makridis: direction only). Teutloff et al. (2025) was added and read in full, but its treated clusters are text-based and graphic design sits in its control group. Hui, Demirci and Teutloff are all online freelance platforms, so the evidence says little about commissioned illustrators outside platforms. |
| **RQ3 as currently worded** | No | No source measures "creative autonomy" with participant-level counts. The closest items (reduced negotiation power, workplace pressure) come from a non-probability survey with unstated item denominators. |

**Bottom line.** The library supports a sound *narrative* mixed-methods synthesis and a small set of properly sourced effect estimates. It does **not** yet support pooled estimates (RQ1) or the binomial test planned for RQ3. Section 6 lists what to add.

## 2. What changed in the repository

The seven rows in the old `data/sample/sample_dataset.csv` were invented teaching values. They have been removed and replaced by:

| File | Content | Rows |
|---|---|---|
| `effect_estimates.csv` | Reported estimates (coefficient, SE, unit, design, window, location in source, verification status) | 51 |
| `survey_items.csv` | Survey proportions: Lovato Tables 2–3 (N=459), Jiang 2026 captions (N=378), AOI 2026 (N=549, via news reports), SoA 2024 (N=787, via secondary reports) | 76 |
| `qualitative_themes.csv` | 12 themes (Jiang 2026) and 8 themes (Kyi 2025) with the authors' own support wording | 20 |
| `source_register.csv` | One row per bibliography entry: design, access, tier, limits | 12 |
| `candidate_sources.csv` | Sources to add, with what each fills and quality flags | 10 |

The simulated latency testbed (`data/raw/`, `data/processed/benchmark_clean.csv`, `metrics_summary.csv`, the two figures) is untouched. It is a software-engineering demonstration and cannot be replaced with article data. Decide separately whether the course still requires it.

## 3. Suitability by source

Tier: **A** core evidence, **B** useful with care, **C** context only, **D** not usable as data.

| Source | Design and data | RQ | Tier | Extractable now | Main limits |
|---|---|---|---|---|---|
| Hui, Reshef & Zhou (2024), *Org. Science* | DiD on Upwork, about 81k image-sample freelancers, Jan 2022–Apr 2023 | RQ1 | **A** | Jobs −2.1%, income −5.2%, any-job −1.4 pp, heterogeneity, all with SEs | One platform; "image" means design, image editing and art; pooled (not pre-period) means only |
| Demirci, Hannane & Zhu (2025), *Mgmt. Science* | Job-post counts, about 1.4M–2M posts (reports differ), Jul 2021–Jul 2023 (secondary) | RQ1 | **A−** | −17.01% image-related posts, graphic design −18.49%, 3D modelling −15.57% (working-paper excerpts), −21% automation-prone (abstract) | PDF not read; no SE; demand-side outcome |
| Goldberg & Lam (2025), MSI working paper | Market-month DiD, 1,841 markets, 62k artists, 3.3M images | RQ2 | **A** | Human sales −0.379 log points (SE 0.058), images, authors, quality, variety | Working paper; single platform; internal inconsistencies (section 4) |
| Makridis (2026), *J. Cultural Economics* | DiD / event study on BLS, ACS, Gallup Panel; U.S. artists, 2017–2024 | RQ1 | **A−** once read | Direction only: earnings near zero, employment mixed, hours up from 2022 | Full text not read (Springer DOI 10.1007/s10824-026-09575-3); no magnitudes in any summary |
| Teutloff et al. (2025), *JEBO* | DiD on weekly postings in 116 skill clusters, one platform, Jan 2021–Sep 2023 | RQ1 (demand) | **B+** | Substitutable −0.28 log points (SE 0.09) ≈ −24%; short jobs −0.29; novices −0.16 (0.07) | Text-LLM exposure only; graphic design is a control cluster; 12 treated clusters |
| Jiang, Taylor & Agnew (2026), CHI EA | Survey N=378 plus open-text themes | RQ3, RQ1 | **A** (mixed methods) | 19 survey items, 12 themes | Six-page abstract; descriptive only; recruitment framed around workplace impact |
| Lovato et al. (2024), AIES | Survey N=459 (214 professionals), Likert | RQ3 proxy | **B** | Tables 2–3; odds ratios in Tables 6–11 not yet extracted | Opinions, not labor outcomes; mixed professional status |
| Kyi et al. (2025), CHI | 20 interviews (7 visual artists, 6 writers, 7 developers) | RQ3 | **B** | 8 themes | Small, young, mixed-domain sample |
| Zhou & Lee (2024), *PNAS Nexus* | Event-study DiD, over 4M artworks, 53k users | Context | **B+** | Output +50%/+100% early, +25% long run; favorites per view +50% relative | Outcomes are not income; effects only in figures |
| Jiang et al. (2023), AIES | Position paper, no systematic data | Framing | **C** | None | Not an empirical source |
| Shan et al. (2023), USENIX Security | Technical tool paper with user studies of the tool | Context | **C−** | None | Measures tool performance, not labor outcomes |
| Liu (2023), *Arte, Individuo y Sociedad* | Philosophical argument | Context | **D** | None | No empirical content |

## 4. Inconsistencies found in the sources themselves

These are in the papers, not extraction errors (the main ones were re-read to confirm). Cite the table value and say which figure you use.

| Source | Inconsistency | How it is recorded |
|---|---|---|
| Goldberg & Lam | Introduction says images +78% (about 4,900/month); Section 5.1 says +119%. | Both stated in `GL-08` and `GL-15`; not reconciled by the authors |
| Goldberg & Lam | "Total sales +39%" equals the raw coefficient; exp(0.390)−1 is about +48%. | `GL-10` caveat |
| Zhou & Lee | Abstract says productivity +25%; Results show +50% in the adoption month and about doubling in the next. An institutional summary says output doubles then stabilises near 25%. | `ZL-01` to `ZL-03`; cite 25% as long-run only |
| Zhou & Lee | Text calls both Gini differences significant; one has p=0.0673. | `ZL-05` caveat |
| Lovato et al. | Table 2 ownership rows sum to 102.4–102.6%; Table 3 implies a denominator near 465; "not comfortable" is 11.18% in text and 9.03% in the table. | Recorded as printed, with caveats |
| Jiang et al. (2026) | Organized-labor shares use unclear denominators (43/137 is 31%, reported 12%). | `JIA-17`, `JIA-18` caveats |
| Hui et al. | Image sample 80,993 freelancers in text, 80,983 in Table 1. | `n_observations` |
| Makridis | BibTeX title and SSRN ID (5179390) differed from the artist-specific paper (SSRN 5992400, CESifo 12368; journal version doi 10.1007/s10824-026-09575-3). | BibTeX entry corrected in this patch; confirm the author list |
| Teutloff et al. | Substitutable decline is 25% in the Introduction but 24% in Sec. 3.2 and the Discussion; machine learning +24% vs +29%. | `TEU-01`, `TEU-02` captions |
| Demirci et al. | Press reports give about 1.39M or about 2M job posts; the abstract gives none. | `DEM-02` data_source note |

## 5. What the old demonstration rows claimed versus what the papers say

| Old row | Old claim | What the source actually reports |
|---|---|---|
| ST01 Goldberg & Lam | Human sales −32% | −0.379 log points (about −31.5% derived); the −32% was not stated in the paper |
| ST02 Hui et al. | Monthly earnings −19% | Image income −5.2% (SE 0.019); no −19% result |
| ST03 Demirci et al. | Image postings −17% | −17% (abstract); the raw counts were invented |
| ST04 Makridis | Aggregate employment −0.4% | No such figure; earnings near zero, employment mixed |
| ST05 Jiang et al. | Autonomy score 8.5 → 4.2 | No autonomy score exists; items are percentages |
| ST06 Zhou & Lee | Productivity +25% | +25% is the abstract's long-run headline; early effects are larger |
| ST07 Lovato et al. | Career optimism 72 → 31 | The survey did not measure career optimism, income or job loss |

## 6. Gaps and what to add

**What is missing for the planned tests**

1. **RQ1 pooling.** A pooled estimate needs several comparable estimates with standard errors. Only Hui et al. has them so far. A defensible synthesis class is "image-related online-freelance demand or earnings", which needs Demirci's tables, Teutloff et al., and Makridis. Even then k ≤ 3–4, so use a narrative synthesis with direction counting rather than a meta-analytic p-value.
2. **RQ2 breadth.** Only one platform. Treat the result as a single case study, or add a second marketplace study if one exists.
3. **RQ3 construct and sampling.** "Creative autonomy" is not measured. Either redefine RQ3 around what is measurable (workplace pressure, bargaining power, control over data use) or collect counts. A binomial test against 50% also treats a convenience sample as random; report proportions with Wilson intervals and state the sampling limits instead.
4. **Time and geography.** Evidence ends around 2023–24 and is mostly U.S. and UK. The title says 2023–2026.

**Candidate sources** (details and quality flags in [`candidate_sources.csv`](../data/extracted/candidate_sources.csv)):

| Priority | Source | Fills |
|---|---|---|
| P1 (done) | Teutloff et al. (2025), *JEBO* | Added and read in full: `TEU-01..05`. Does not cover visual art (graphic design is a control cluster) |
| P1 (partly) | Makridis, full text | Journal version identified, still unread; three secondary summaries give direction only (`MAK-01..03`) |
| P1 (partly) | Association of Illustrators (UK) 2025–2026 surveys | Extracted as `AOI-01..10` from two news reports (46% of 549 know a client chose genAI, 32% a year earlier); the primary report is still needed |
| P1 (partly) | Society of Authors (UK) survey, Jan 2024 | Extracted as `SOA-01..02` (26% of illustrators lost work, 12% used genAI; illustrator n not stated); the 37% income-decline figure is not yet recorded |
| P2 | U.S. BLS OEWS and projections | Official occupation time series for your own descriptive analysis |
| P2 | CVL Economics (2024) | Employer expectations for concept art and illustration; advocacy-commissioned forecast |
| P3 | Swedish and Japanese illustrator surveys; Shi et al. (2023); Graphics Interface 2024 study | Non-Western and qualitative triangulation; secondary or unread |

**Caution on advocacy surveys.** The UK association surveys are self-selected and run by bodies that campaign on this issue. They are valid evidence of reported experience, not of prevalence in the profession. One aggregator site quotes 6,844 respondents for the Association of Illustrators survey while the news report says 549; do not use the aggregator.

## 7. Before the final submission

1. **Re-check numbers against the PDFs.** The extraction was done by reading page text through an automated reader, and rows marked `fulltext_single_read` were read once. Rows marked `fulltext_cross_checked` were confirmed a second way (a second read, percentages stated in the paper's own text, or an independent report); every `fulltext_single_read` row, including the central RQ2 estimate `GL-01`, needs a human spot-check against the cited table or figure.
2. **Download Demirci et al. and Makridis** (the reader could not reach either PDF; EconStor blocks automated access, and the Springer, ifo, UCL and BU hosts were refused) and extract their tables into `effect_estimates.csv`. Demirci's image-generating AI table (coefficients and SEs for overall, graphic design and 3D modelling) and Makridis's DiD tables are the two missing pieces for RQ1.
3. **Check the BibTeX file.** This patch moves the Goldberg & Lam title out of the `journal` field and rewrites `LaborMarketEffect` as the Journal of Cultural Economics article (DOI above); confirm the Makridis author list and title against the Springer page. Three entries were added (Teutloff et al., AOI 2026, SoA 2024); the last two are `@misc` entries built from secondary reports and should be replaced by the primary reports.
4. **Disclose limits in the report.** Selection and publication bias, mixed outcome units, non-probability surveys, and that two of the five quantitative sources are working papers.

## 8. Method note

Sources were located by web search and read through an automated page reader. Each extracted number carries `location_in_source` and a `verification_status`: `fulltext_cross_checked` (read from full text and confirmed by a second read, by percentages stated in the paper, or by an independent report), `fulltext_single_read`, `abstract_or_secondary`, or `not_retrieved`. The audit (`python src/benchmark.py --config config.json`) checks vocabularies, unique IDs, that every `bib_key` exists in the BibTeX file, and re-expresses log coefficients as percentages; the percentages match the papers' own text (for example −19.5% against the stated "about −20%"). No new hypothesis test is run.
