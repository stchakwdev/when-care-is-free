# CLAUDE.md — when-care-is-free

Quasi-experimental analysis of user-fee abolition and maternal & child survival in sub-Saharan Africa. Python pipeline + Observable Framework site deployed to GitHub Pages.

## Setup & commands

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

# Full pipeline, in order (each step's outputs feed the next):
.venv/bin/python pipeline/fetch_data.py            # World Bank API -> data/raw/*.csv + data/processed/panel.csv
.venv/bin/python pipeline/validate_data.py         # anomaly repair + data/processed/data_quality_log.csv
.venv/bin/python analysis/run_did.py               # LP-DiD + TWFE -> results/event_study.csv, att_summary.csv
.venv/bin/python analysis/run_synth.py --stage main
.venv/bin/python analysis/run_synth.py --stage placebos   # slow (~20 donors x 2 outcomes); appends to synth_placebos.csv
.venv/bin/python analysis/run_synth.py --stage summary
.venv/bin/python analysis/robustness.py            # leave-one-cohort-out
.venv/bin/python analysis/robustness_specs.py --stage specs   # timing/coding/Ebola attacks
.venv/bin/python analysis/robustness_specs.py --stage ri      # 1,000-perm randomization inference (~1 min, seeded)
.venv/bin/python analysis/run_equity.py            # wealth-quintile mechanism -> results/equity_*.csv

# Site (Observable Framework):
cd site && npm install && npm run dev     # local preview
cd site && npm run build                  # must pass before pushing; validates pages + links
```

Deploy: push to `main` → `.github/workflows/deploy.yml` builds `site/` and publishes to GitHub Pages.

## Architecture — one rule that matters

**Every number in the site's prose is computed at render time from `site/src/data/*.csv`. Never hardcode a statistic in a page.** The result files in `results/` are the source of truth; after re-running any analysis, copy the changed CSVs to `site/src/data/` (they are duplicated there deliberately so the site is self-contained). If you add a claim to a page, derive it from a FileAttachment in JS — a hardcoded "6%" that drifts from the data is the exact failure mode this repo is designed to prevent. (One rounding bug was already caught this way: a `.round(1)` in a console print masked a 0.98 control percentile as 1.0 and nearly shipped an overclaim.)

```
pipeline/    data acquisition + validation (World Bank API; extract_equity.py reads a local WHO export)
analysis/    run_did.py is imported by robustness*.py (load_panel/run_lpdid_att are shared)
data/        raw API pulls + processed panel + equity_wq.csv (committed extract) + quality log
results/     model outputs — the only interface between analysis/ and site/
site/        Observable Framework app; src/data/ holds copies of results/ CSVs
```

## Treatment coding

The 9 adoption years live in `TREATED` in `pipeline/fetch_data.py` and are **duplicated** in `ADOPTION` in `analysis/run_equity.py` and in the adopter tables inside `site/src/index.md` / `site/src/equity.md`. If a coding decision changes, update all four. Coding sources are documented on the methods page (`site/src/methods.md`).

## Data caveats

- `pipeline/fetch_data.py` re-pulls from the live World Bank API — estimates get revised, so a re-fetch can shift results slightly. Don't re-fetch casually while the writeup cites current numbers; the analysis is deterministic from the committed `data/processed/panel.csv`.
- `pipeline/extract_equity.py` needs the 1.1 GB WHO MNCAH export (`../data_export_MNCAH_MCA_FACT_DATA.csv`, not committed, retrieved Nov 2022). Its output `data/raw/equity_wq.csv` IS committed; everything downstream reproduces from it.
- `run_synth.py --stage placebos` **appends** to `results/synth_placebos.csv` — delete the file first when regenerating, or you'll double-count placebos (summary dedupes on iso3+outcome as a guard).
- Randomization inference is seeded (`SEED` in `robustness_specs.py`); changing the seed changes the p-value slightly — that's expected, cite the committed run.

## Voice and framing (site prose)

The project's brand is calibrated honesty. When editing pages:
- Report the conservative number alongside the headline one (e.g., cluster-robust p AND randomization-inference p).
- Weaknesses are displayed, not buried: the pre-trend, the suggestive-only Sierra Leone result, the 5-of-9-adopters equity coverage.
- The equity page is framed as **mechanism evidence, not a causal design** — keep it that way.
- Each page targets one audience: index = technical-curious, brief = decision-maker (plain language, no jargon), methods = skeptical reviewer, equity = mechanism deep-dive.
