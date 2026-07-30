# When Care Is Free

**Quasi-experimental evidence on user-fee abolition and maternal & child survival in sub-Saharan Africa.**

**Live site:** https://stchakwdev.github.io/when-care-is-free/

Between 2001 and 2016, nine African countries abolished point-of-care user fees for maternal and child health services, each in a different year. This project treats that staggered rollout as a natural experiment and asks whether removing fees saved lives.

## Findings

- **Under-5 mortality fell ~6%** (95% CI −10.2% to −1.5%) in the eight years after abolition, pooled across nine adopters against 26 never-treated controls. The estimate holds its sign and size across every specification I attacked: timing shifts, broad vs. narrow treatment coding, dropping Ebola countries, dropping any single cohort (ATT range −5.2% to −7.1%, all p < 0.05 cluster-robust). The two inference approaches disagree in strength. Cluster-robust standard errors give p = 0.01; 1,000-permutation randomization inference gives p = 0.05 one-sided. I grade the evidence moderate and report both.
- **Sierra Leone's maternal mortality ran ~11% below its synthetic counterfactual on average across 2010–13** (pre-Ebola), and ~23% below averaged across 2010–19, with the yearly gap widening throughout. Placebo rank tests put the 2010–13 gap at p ≈ 0.14, so a single-country result like this one is suggestive, not conclusive.
- **The mechanism shows up in the survey data.** DHS/MICS wealth-quintile data (WHO MNCAH database) show service use surged fastest in the poorest fifth of households after abolition. Poorest-quintile facility deliveries tripled in Sierra Leone within three years, and all 13 adopter country-service pairs with bracketing surveys improved faster than the control-country median — the best of them ahead of 98% of control survey pairs.
- **Neonatal mortality barely moved**, consistent with newborn survival depending on quality of care rather than fees at the door. Free doors don't staff operating theatres.
- A validation pass caught a real error in the World Bank API: CAR's 2009 under-5 mortality is returned as 489.3 per 1,000, bracketed by ~135 and ~151. Every repair is logged; documented catastrophes (Rwanda 1994, Somalia 2011) are whitelisted, never "repaired."

## Why this question

User fees are one of the oldest fights in health financing. The 1987 Bamako Initiative institutionalized cost recovery across Africa; the 2001–2016 abolition wave unwound it country by country. UNICEF co-sponsored that initiative, and I later spent four years there producing exactly the child-mortality statistics this analysis models. I grew up partly in Uganda and Kenya, two of the countries in the treatment table. The fee debate ran underneath much of my UNICEF work but never got a clean causal answer in the rooms I sat in; the field ran on before/after comparisons. This project is me going back for that answer with better machinery.

## Methods

- **LP-DiD** (Dube, Girardi, Jordà & Taylor 2023) via [pyfixest](https://github.com/py-econometrics/pyfixest): staggered difference-in-differences robust to heterogeneous treatment effects, with classic TWFE event studies shown for comparison. Cluster-robust inference by country.
- **Synthetic control + ridge-augmented synthetic control** (Abadie et al. 2010; Ben-Michael, Feller & Rothstein 2021) via [pysyncon](https://github.com/sdfordham/pysyncon), with in-space placebo inference.
- Full design discussion, treatment-coding table, identifying assumptions, and a "what would change my mind" section: see the [methods page](https://stchakwdev.github.io/when-care-is-free/methods).

## Reproduce everything

```bash
pip install -r requirements.txt
python pipeline/fetch_data.py       # pull 12 indicators, 44 countries from the World Bank API
python pipeline/validate_data.py    # flag & repair data anomalies, write audit log
python analysis/run_did.py          # LP-DiD + TWFE event studies
python analysis/run_synth.py --stage main
python analysis/run_synth.py --stage placebos
python analysis/run_synth.py --stage summary
python analysis/robustness.py       # leave-one-cohort-out
python analysis/robustness_specs.py --stage specs   # timing / coding / Ebola attacks
python analysis/robustness_specs.py --stage ri      # randomization inference (1,000 perms)
python analysis/run_equity.py                       # wealth-quintile mechanism analysis
```

The site (Observable Framework) reads the CSVs those scripts produce. Every number on the page is computed from the result files at render time, so prose and statistics cannot drift apart:

```bash
cd site && npm install && npm run dev
```

## Repository layout

```
pipeline/    data acquisition + validation (World Bank API, reproducible)
analysis/    LP-DiD, synthetic control, robustness
data/        raw API pulls + processed panel + data-quality log
results/     model outputs consumed by the site
site/        Observable Framework app (GitHub Pages)
```

## Data

World Bank Open Data API. Child mortality: UN IGME. Maternal mortality: UN MMEIG. Immunization: WHO/UNICEF (WUENIC). These are modeled estimates, smooth by construction, which attenuates sharp policy discontinuities; effect estimates here are conservative. See the methods page for the full discussion.

## Author

Samuel Chakwera ([@stchakwdev](https://github.com/stchakwdev)), Malawian data scientist. I work on global health statistics and ML: previously UNICEF (official MNCAH statistics, published in *The Lancet*), currently building data systems for a provincial regulator and AI analytics tooling for UNICEF.

Built with Claude as a pair analyst. I directed and reviewed every design decision, robustness check, and line of interpretation.
