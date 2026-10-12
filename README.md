# The Impact of Generative AI on Commercial Visual Artists

## Authors
- Zhanerke Abdumalik
- Zhansaya Baikenova

## Project Overview
This project investigates how generative text-to-image AI is associated with paid opportunities and professional autonomy among commercial visual artists between 2023 and 2026.

The research uses a mixed-methods comparative synthesis of published empirical studies. It combines quantitative evidence on labor-market outcomes with qualitative findings about illustrators' workflows and creative autonomy.

## Research Questions
- **RQ1:** What changes in paid opportunities, compensation, and labor conditions have been documented?
- **RQ2:** How is platform authorization of AI-generated assets associated with changes in the production and sales of human-created assets?
- **RQ3:** How does client adoption of generative AI affect illustrators' daily tasks and creative autonomy?

## Methodology
The project compares empirical studies published between 2023 and 2026. Quantitative findings will be compared where measurement methods and data are sufficiently similar. Qualitative findings will be synthesized thematically.

The study is observational and does not automatically establish causal relationships.

## Repository Structure
```text
ai-artist-labor-research/
├── README.md
├── LICENSE
├── .gitignore
├── Dockerfile
├── requirements.txt
├── config.json
├── data/
│   ├── sample/
│   └── processed/
├── docs/
│   └── methodology_passport.md
├── src/
│   └── benchmark.py
└── tests/
    └── test_benchmark.py
```

## Planned Benchmarks

| Indicator | Measurement | Data Source |
|---|---|---|
| Paid opportunities | Reported percentage change where comparable values exist | Verified empirical studies |
| Earnings | Reported percentage change where available | Verified empirical studies |
| Human-created asset sales | Reported percentage change where available | Marketplace studies |
| Creative autonomy | Thematic synthesis of qualitative findings | Interviews and surveys |
| Data completeness | Percentage of records with required fields | Extracted study records |
| Pipeline execution | Successful completion of the benchmark script | Local or Docker run |

## Requirements
- Python 3.12
- Git (optional)
- Docker (optional)

## Quickstart Guide

Run the benchmark script from the repository root:

```bash
python src/benchmark.py --config config.json
```

Run the test suite:

```bash
python -m unittest discover -s tests
```

Build and run the Docker container:

```bash
docker build -t ai-artist-labor-research .
docker run --rm ai-artist-labor-research
```

## Data Notice
Sample records are synthetic examples used only to test the analysis pipeline. They are not real empirical findings and must not be cited as evidence. Replace them with verified data extracted from the reviewed publications before conducting substantive analysis.

## License
This project is intended to be released under the MIT License. See `LICENSE`.
