# Methods & data quality

This page documents every judgment call in the analysis, in enough detail that a skeptical reader can decide whether to believe the findings, and a motivated one can rerun them.

## Research design

**Question.** Does abolishing point-of-care user fees for maternal and child health services reduce maternal and child mortality?

**Why it is hard.** No country randomizes health financing. Countries that abolish fees differ from those that keep them, and they choose *when* to act. Any credible answer has to come from quasi-experimental designs with testable assumptions.

**Two complementary designs.**

1. **Staggered difference-in-differences** across nine adopters (2001–2016) and 26 never-treated sub-Saharan controls. The estimator is LP-DiD (Dube, Girardi, Jordà & Taylor, 2023), which avoids the negative-weighting bias that contaminates classic two-way fixed effects under staggered adoption with heterogeneous effects. The TWFE event study is reported alongside as a comparison. Inference is cluster-robust by country. Outcomes: log under-5 mortality, log neonatal mortality, DTP3 and measles immunization coverage.
2. **Synthetic control** for Sierra Leone's Free Health Care Initiative (April 2010), the sharpest single implementation. Both classic synthetic control (Abadie, Diamond & Hainmueller, 2010) and ridge-augmented synthetic control (Ben-Michael, Feller & Rothstein, 2021) are reported. Sierra Leone's mortality sits near the boundary of the donor pool, so the classic estimator cannot match its level (it collapses onto a single donor, Chad, with poor pre-fit); AugSynth extrapolates modestly beyond the convex hull and achieves near-exact pre-period fit. Inference is by in-space placebos with rank tests on the average post-period gap.

## Treatment coding

The treatment is **national-scale abolition of point-of-care fees for maternal and/or under-five services**. Coding a policy dummy from legislation is the least glamorous and most consequential step in the analysis. Decisions:

| Country | Year | Policy |
|---|---|---|
| Uganda | 2001 | All user fees abolished in public facilities (March 2001) |
| Zambia | 2006 | Fees removed in rural districts (April 2006), later extended |
| Burundi | 2006 | Free care for under-5s and deliveries (May 2006) |
| Niger | 2006 | Free care for under-5s and antenatal care |
| Liberia | 2007 | Fees suspended in public primary facilities |
| Ghana | 2008 | Free maternal care through NHIS exemption (July 2008) |
| Sierra Leone | 2010 | Free Health Care Initiative: pregnant women, lactating mothers, under-5s (April 2010) |
| Kenya | 2013 | Free maternity services in public facilities (June 2013) |
| Burkina Faso | 2016 | Free care for women and under-5s (April 2016) |

**Excluded from both treatment and control** (partial, ambiguous, or always-free):

| Country | Reason |
|---|---|
| Malawi | Care always free at point of use; never "treated" within the window |
| South Africa | Free care for pregnant women and children since 1994, pre-window |
| Senegal | Free deliveries/c-sections in selected regions only (2005) |
| Mali | C-sections only (2005) |
| Benin | C-sections only (2009) |
| Lesotho | Phased primary-care fee removal from 2008, ambiguous scale-up |
| Botswana | Nominal flat fee, effectively free; ambiguous |
| Rwanda | Mutuelles community insurance (2006) is a different intervention |
| Tanzania | Long-standing exemptions coexist with fees; ambiguous |

Coding sources: the user-fee reform literature, principally Lagarde & Palmer (2008, *Bulletin of the WHO*), Ridde & Morestin (2011, *Health Policy and Planning*), McKinnon, Harper & Kaufman (2015, *Health Policy and Planning*), and Witter et al.'s evaluations of the Sierra Leone FHCI. Anyone who disagrees with a coding decision can change one line in `pipeline/fetch_data.py` and rerun.

## Data

All data come from the [World Bank Open Data API](https://data.worldbank.org), pulled by a scripted, reproducible pipeline (`pipeline/fetch_data.py`). Mortality series originate from UN IGME (child) and the UN MMEIG (maternal); immunization coverage from WHO/UNICEF (WUENIC). 44 countries, 1990–2023, 12 indicators.

Two properties of these series matter for interpretation:

- **They are modeled estimates, not raw counts.** IGME fits penalized B-splines to survey and vital-registration data. The published series are smooth by construction, which attenuates sharp policy discontinuities. Effects estimated on smoothed data are conservative.
- **Estimates get revised.** The pipeline stamps the API retrieval date; rerunning it later can produce slightly different numbers as IGME incorporates new surveys.

## The data error we caught

A validation pass (`pipeline/validate_data.py`) flags any point that jumps more than 40% away from *both* neighbors while the neighbors agree with each other — impossible in a spline-smoothed series. It caught a real error: the World Bank API returns an under-5 mortality rate of **489.3 per 1,000 for the Central African Republic in 2009**, bracketed by 135.5 (2008) and 150.7 (2010). No published IGME estimate supports that value; it is an ingestion artifact. The validator repairs isolated errors by geometric interpolation and logs every repair.

Just as important is what the validator does **not** touch: a whitelist of documented catastrophes (Rwanda 1994, Somalia 2011, South Sudan 1998, the 2021 COVID-era maternal mortality revisions) whose spikes are history, not error. Distinguishing the two automatically is impossible; distinguishing them transparently is the whole game. The full log ships with the site:

```js
const dq = FileAttachment("data/data_quality_log.csv").csv({typed: true});
```

```js
Inputs.table(dq, {rows: 16})
```

CAR is additionally excluded from the synthetic-control donor pool (2013 civil war plus two repaired points), along with Somalia (2011 famine as a post-period shock), Eritrea (data reliability), and Equatorial Guinea (oil-enclave GDP outlier).

## Identifying assumptions, stated plainly

**For the DiD:** absent fee abolition, treated countries' outcomes would have moved in parallel with controls (in logs). Testable implication: flat pre-trends. The event study shows a mild positive pre-trend at t−6 — treated countries were improving slightly faster before acting. This is the analysis's main weakness and it is displayed, not buried. The post-treatment break is larger and sharper than the pre-trend, and results are robust to dropping any single cohort, but selection-on-trajectory cannot be fully excluded.

**For the synthetic control:** the donor-weighted combination would have continued to track Sierra Leone absent the FHCI. Threats: Ebola (2014–16) — handled by reporting the pre-Ebola window separately, and noting the shock biases *against* the finding; post-conflict recovery — handled by starting the pre-period at 2002, when the civil war ended; donor-pool contamination by HIV/ART dynamics — visible in the placebo distribution and reflected in the reported p-values.

## Robustness: four attacks on the headline number

The pooled −6% under-5 mortality effect was attacked four ways. Every number below is computed live from `results/robustness_specs.csv`.

```js
const specs = FileAttachment("data/robustness_specs.csv").csv({typed: true});
const loo = FileAttachment("data/robustness_loo.csv").csv({typed: true});
const ri = FileAttachment("data/randomization_inference.csv").csv({typed: true});
const riSummary = FileAttachment("data/randomization_inference_summary.csv").csv({typed: true});
```

```js
const specLabels = new Map([
  ["main", "Main specification"],
  ["timing_plus1", "Adoption = first full year (+1)"],
  ["timing_minus1", "Adoption one year earlier (−1)"],
  ["broad_coding", "Broad coding: partial reformers treated (n=14)"],
  ["drop_ebola", "Drop Ebola countries (SLE, LBR, GIN)"]
]);
const specData = specs.map((d) => ({...d, label: specLabels.get(d.spec) ?? d.spec}));
```

**1. Specification choices.** Recoding adoption years ±1 (most reforms launched mid-year), treating the excluded partial reformers (Senegal, Mali, Lesotho, Benin, Rwanda) as adopters instead, and dropping all three Ebola-affected countries:

```js
Plot.plot({
  height: 240,
  marginLeft: 300,
  x: {label: "ATT, log under-5 mortality", domain: [-0.15, 0.02], grid: true},
  y: {label: null, domain: specData.map((d) => d.label)},
  marks: [
    Plot.ruleX([0]),
    Plot.ruleY(specData, {y: "label", x1: "ci_low", x2: "ci_high", stroke: "var(--theme-foreground-focus)", strokeWidth: 1.5}),
    Plot.dot(specData, {x: "estimate", y: "label", fill: "var(--theme-foreground-focus)", r: 4,
      tip: true, title: (d) => `ATT ${d.estimate.toFixed(4)}\n95% CI [${d.ci_low.toFixed(4)}, ${d.ci_high.toFixed(4)}]\np = ${d.pvalue.toFixed(4)}`})
  ]
})
```

The estimate ranges from ${Math.min(...specData.map(d => (Math.expm1(d.estimate)*100))).toFixed(1)}% to ${Math.max(...specData.map(d => (Math.expm1(d.estimate)*100))).toFixed(1)}% across specifications, all p < 0.02. The broad coding *strengthens* the effect — the narrow treatment definition is the conservative choice.

**2. Leave-one-cohort-out.** Dropping each treated country in turn: ATT ranges ${Math.min(...loo.filter(d => d.dropped !== "none").map(d => (Math.expm1(d.estimate)*100))).toFixed(1)}% to ${Math.max(...loo.filter(d => d.dropped !== "none").map(d => (Math.expm1(d.estimate)*100))).toFixed(1)}%, all p < 0.05. No single adopter drives the result.

**3. Randomization inference — the strictest test on this page.** Cluster-robust standard errors with nine treated countries lean on asymptotics they may not have earned. So: reassign the nine actual adoption years to nine randomly chosen countries from the 35-country pool, re-estimate the pooled ATT, repeat 1,000 times, and ask where the real estimate falls in that placebo distribution — the same design-based logic as the synthetic-control placebos.

```js
const riS = riSummary[0];
```

```js
Plot.plot({
  height: 300,
  x: {label: "Placebo ATT (1,000 random treatment assignments)", grid: true},
  y: {label: "Count"},
  marks: [
    Plot.rectY(ri, Plot.binX({y: "count"}, {x: "perm_att", fill: "#ccc"})),
    Plot.ruleX([riS.observed_att], {stroke: "var(--theme-foreground-focus)", strokeWidth: 2.5}),
    Plot.text([{x: riS.observed_att}], {x: "x", frameAnchor: "top", dx: -6, rotate: -90, dy: 80,
      text: () => "observed ATT", fill: "var(--theme-foreground-focus)"})
  ]
})
```

The observed ATT of ${riS.observed_att.toFixed(4)} sits at the ${(riS.p_one_sided * 100).toFixed(0)}th percentile of the placebo distribution: **one-sided p = ${riS.p_one_sided.toFixed(3)}, two-sided p = ${riS.p_two_sided.toFixed(2)}** — weaker than the model-based p = 0.01. This is worth being blunt about. Under the inference that makes the fewest assumptions, the pooled child-mortality effect sits at the edge of conventional significance, not comfortably past it. Mortality outcomes are strongly serially correlated within countries, so random "policies" produce sizeable spurious effects more often than textbook standard errors imply. The fair summary of the evidence is **moderate, not overwhelming**: a ~6% effect, robust in sign and magnitude across every specification, whose p-value is 0.01 by the conventional test and 0.05 by the strictest one.

**4. Which placebo test to believe for Sierra Leone.** Two rank tests are reported in `synth_summary.csv` and they disagree: the classic RMSPE-ratio test gives p ≈ 0.81, while the rank test on the average post-period gap gives p ≈ 0.14. The RMSPE ratio divides by each unit's pre-period fit — and AugSynth fits every unit's pre-period nearly exactly, so the denominators are all near zero and the ratio ranking is dominated by numerical noise rather than effect size. Abadie's ratio test was designed for the classic estimator, where pre-fit differences are informative. For AugSynth the gap-rank test is the meaningful one; both are reported so the reader can check that this choice is disclosed, not buried.

## What would change my mind

A flat placebo distribution built from better outcome data (facility-level DHIS2 records rather than smoothed national estimates) showing no divergence; evidence that a concurrent 2010 program (not the FHCI) drove Sierra Leone's maternal mortality drop; or a re-coding of adoption years that erases the pooled effect. The repository is structured so any of these tests takes minutes, not weeks.

## Reproducibility

```
git clone https://github.com/stchakwdev/when-care-is-free
pip install -r requirements.txt
python pipeline/fetch_data.py      # pull from World Bank API (~10s)
python pipeline/validate_data.py   # flag & repair anomalies, write log
python analysis/run_did.py         # LP-DiD + TWFE event studies
python analysis/run_synth.py --stage main
python analysis/run_synth.py --stage placebos
python analysis/run_synth.py --stage summary
python analysis/robustness.py                    # leave-one-cohort-out
python analysis/robustness_specs.py --stage specs  # timing, coding, Ebola
python analysis/robustness_specs.py --stage ri     # 1,000-permutation randomization inference
python analysis/run_equity.py                    # wealth-quintile mechanism analysis
```

The equity analysis additionally uses a committed extract (`data/raw/equity_wq.csv`) of DHS/MICS wealth-quintile breakdowns from the WHO MNCAH database export (November 2022). Regenerating that extract from the 1.1 GB source requires `python pipeline/extract_equity.py <path-to-export>`; everything downstream reproduces from the committed file.

The site is an [Observable Framework](https://observablehq.com/framework) app; every chart reads the CSVs the scripts above produce. `npm run dev` inside `site/` for a local preview.

## References

- Abadie, Diamond & Hainmueller (2010). Synthetic control methods for comparative case studies. *JASA*.
- Ben-Michael, Feller & Rothstein (2021). The augmented synthetic control method. *JASA*.
- Dube, Girardi, Jordà & Taylor (2023). A local projections approach to difference-in-differences event studies. *NBER WP 31184*.
- Lagarde & Palmer (2008). The impact of user fees on health service utilization in low- and middle-income countries. *Bulletin of the WHO*.
- McKinnon, Harper & Kaufman (2015). Removing user fees for facility-based delivery services: a difference-in-differences evaluation from ten sub-Saharan African countries. *Health Policy and Planning*.
- Ridde & Morestin (2011). A scoping review of the literature on the abolition of user fees in health care services in Africa. *Health Policy and Planning*.
- Witter et al. (2016). The Sierra Leone Free Health Care Initiative: process and effectiveness review. *Health Policy and Planning*.
