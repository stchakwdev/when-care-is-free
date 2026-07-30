# When care is free
## Quasi-experimental evidence from Africa's user-fee abolition wave, 2001–2016

For decades, most public clinics in sub-Saharan Africa charged patients a fee before treatment. A delivery might cost one week of income. Treatment for a child with malaria might cost one day of income. Between 2001 and 2016, nine countries stopped these charges for mothers and young children. Each country stopped in a different year and for different reasons. This difference in timing makes the question possible to answer: **did the removal of fees save lives?**

This analysis treats the staggered rollout as a natural experiment. It compares the nine countries that abolished fees against 26 sub-Saharan countries that kept them. It uses two designs. The first design is local-projections difference-in-differences (LP-DiD) across all nine adopters. The second design is a synthetic control case study of Sierra Leone's 2010 Free Health Care Initiative.

```js
const att = FileAttachment("data/att_summary.csv").csv({typed: true});
const es = FileAttachment("data/event_study.csv").csv({typed: true});
const paths = FileAttachment("data/synth_paths.csv").csv({typed: true});
const placebos = FileAttachment("data/synth_placebos.csv").csv({typed: true});
const synthSummary = FileAttachment("data/synth_summary.csv").csv({typed: true});
const riSummary = FileAttachment("data/randomization_inference_summary.csv").csv({typed: true});
```

```js
const riS = riSummary[0];
const u5 = att.find((d) => d.outcome === "log_u5mr");
const pct = (x) => (Math.expm1(x) * 100);
const mmrRow = synthSummary.find((d) => d.outcome === "log_mmr");
```

<div class="grid grid-cols-3">
  <div class="card">
    <h2>Under-5 mortality, pooled effect</h2>
    <span class="big">${pct(u5.estimate).toFixed(1)}%</span>
    <p>LP-DiD across 9 adopting countries, 95% CI ${pct(u5.ci_low).toFixed(1)}% to ${pct(u5.ci_high).toFixed(1)}%. p = ${u5.pvalue.toFixed(3)} (cluster-robust); p = ${riS.p_one_sided.toFixed(2)} under ${riS.n_permutations.toLocaleString("en-US")}-permutation randomization inference — <a href="/methods#robustness-four-attacks-on-the-headline-number">both tests reported</a></p>
  </div>
  <div class="card">
    <h2>Sierra Leone maternal mortality, 2010–13</h2>
    <span class="big">${mmrRow.att_pct_2010_2013.toFixed(1)}%</span>
    <p>vs. synthetic Sierra Leone (ridge-augmented), before Ebola. Placebo rank test p = ${mmrRow.p_att_2010_2013.toFixed(2)} — suggestive, not conclusive</p>
  </div>
  <div class="card">
    <h2>Design</h2>
    <span class="big">9 + 26</span>
    <p>countries: 9 staggered adopters, 26 never-treated controls, 1995–2023, World Bank / UN IGME public data</p>
  </div>
</div>

The analysis pipeline writes result files. This page calculates every number from those files when it renders. No person types a number into the text, so the text and the statistics always agree.

## The policy wave

```js
const adopters = [
  {iso3: "UGA", country: "Uganda", year: 2001, scope: "All user fees, public facilities"},
  {iso3: "ZMB", country: "Zambia", year: 2006, scope: "Rural districts, later extended"},
  {iso3: "BDI", country: "Burundi", year: 2006, scope: "Under-5s and deliveries"},
  {iso3: "NER", country: "Niger", year: 2006, scope: "Under-5s and antenatal care"},
  {iso3: "LBR", country: "Liberia", year: 2007, scope: "Public primary facilities"},
  {iso3: "GHA", country: "Ghana", year: 2008, scope: "Free maternal care via NHIS"},
  {iso3: "SLE", country: "Sierra Leone", year: 2010, scope: "Pregnant women, mothers, under-5s"},
  {iso3: "KEN", country: "Kenya", year: 2013, scope: "Free maternity, public facilities"},
  {iso3: "BFA", country: "Burkina Faso", year: 2016, scope: "Women and under-5s"}
];
```

```js
Plot.plot({
  height: 300,
  marginLeft: 90,
  x: {label: "Year of abolition", domain: [1999, 2018], tickFormat: "d"},
  y: {label: null, domain: adopters.map((d) => d.country)},
  marks: [
    Plot.ruleY(adopters, {y: "country", x1: 1999, x2: "year", stroke: "#ddd"}),
    Plot.dot(adopters, {x: "year", y: "country", r: 7, fill: "var(--theme-foreground-focus)",
      tip: true, title: (d) => `${d.country} ${d.year}\n${d.scope}`}),
    Plot.text(adopters, {x: "year", y: "country", text: (d) => String(d.year), dx: 24, fill: "currentColor"})
  ]
})
```

The staggered timing is important for the method. A single before/after comparison mixes the effect of the policy with the effect of all other events in the same period. This design uses nine different adoption years and compares each one against countries that never adopted. A confounding variable is much less likely to produce that pattern.

## Nine countries, fewer child deaths

The event study below shows outcomes for each year before and after the year of abolition. Estimates to the left of zero test the identifying assumption. If the treated countries and the control countries changed at different rates before the policy, the design is not valid. Estimates to the right of zero measure the effect of the policy.

```js
const outcomeLabels = new Map([
  ["Under-5 mortality (log)", "log_u5mr"],
  ["Neonatal mortality (log)", "log_nmr"],
  ["DTP3 immunization (pp)", "dtp3"],
  ["Measles immunization (pp)", "mcv1"]
]);
const outcomeChoice = view(Inputs.select(outcomeLabels, {label: "Outcome"}));
const estimatorChoice = view(Inputs.radio(new Map([["LP-DiD (robust)", "lpdid"], ["Classic TWFE", "twfe"]]), {label: "Estimator", value: "lpdid"}));
```

```js
const esData = es.filter((d) => d.outcome === outcomeChoice && d.estimator === estimatorChoice);
const isLog = outcomeChoice.startsWith("log");
```

```js
Plot.plot({
  height: 380,
  x: {label: "Years since fee abolition", tickFormat: "d"},
  y: {label: isLog ? "Effect on log outcome" : "Effect (percentage points)", grid: true},
  marks: [
    Plot.ruleY([0]),
    Plot.ruleX([-0.5], {stroke: "#bbb", strokeDasharray: "4,4"}),
    Plot.text([{x: 0.6, y: 0}], {x: "x", frameAnchor: "top-left", dy: 8,
      text: () => "policy begins →", fill: "#888"}),
    Plot.areaY(esData, {x: "rel_year", y1: "ci_low", y2: "ci_high",
      fill: "var(--theme-foreground-focus)", fillOpacity: 0.12}),
    Plot.line(esData, {x: "rel_year", y: "estimate", stroke: "var(--theme-foreground-focus)", strokeWidth: 2}),
    Plot.dot(esData, {x: "rel_year", y: "estimate", fill: "var(--theme-foreground-focus)", r: 3.5,
      tip: true, title: (d) => `t${d.rel_year >= 0 ? "+" : ""}${d.rel_year}\nestimate: ${d.estimate.toFixed(3)}\n95% CI [${d.ci_low.toFixed(3)}, ${d.ci_high.toFixed(3)}]`})
  ]
})
```

Under-5 mortality decreases by approximately **${Math.abs(pct(u5.estimate)).toFixed(0)}%** on average in the eight years after abolition (95% CI ${pct(u5.ci_low).toFixed(1)}% to ${pct(u5.ci_high).toFixed(1)}%). Neonatal mortality changes very little. This result is expected, because the survival of a newborn depends on the quality of care at delivery and not only on the removal of the fee. The estimates for immunization coverage are positive but not precise. The [Who benefited?](/equity) page uses wealth-quintile survey data to show the mechanism: use of services increased most in the poorest households.

Four things to know before believing this chart:

1. **The pre-period trend is not zero.** At t−6 the point estimate is positive and marginally significant. This shows that the treated countries improved more quickly than the control countries before they abolished fees. Governments do not select health policy at random. The effect estimate stays valid, because the decrease after the policy is larger and more rapid than the pre-trend. But the reader must know that the pre-trend is present. Select the classic TWFE estimator to see the effect of estimator choice on staggered adoption.
2. **UN IGME models the mortality series.** The estimates make large year-to-year changes smooth. This makes it more difficult to find a sudden policy effect. The true short-run effect is probably larger than the smoothed data can show.
3. **This is an intent-to-treat estimate of a policy announcement.** The quality of implementation was very different between countries. Uganda did not give sufficient funds to its abolition. The average includes strong implementations and weak implementations.
4. **The p-value changes with the strictness of the test.** Cluster-robust inference gives p = ${u5.pvalue.toFixed(2)}. A second test assigns the nine adoption years to random countries 1,000 times and gives a design-based p = ${riS.p_one_sided.toFixed(2)} (one-sided). The estimate keeps the same sign and approximately the same size in every specification tested: timing shifts, broad treatment coding, removal of Ebola countries, and removal of any cohort. But in the strictest test the estimate is at the limit of significance and not clearly better than the limit. The [methods page](/methods) shows all the tests.

## Sierra Leone: the sharpest test

In April 2010, Sierra Leone abolished all fees for pregnant women, lactating mothers, and children less than five years old. The policy is called the Free Health Care Initiative. It removed more fees at one time than the equivalent policy in any other country, and it did this in a country with one of the highest maternal mortality rates in the world.

The synthetic control method builds a "counterfactual Sierra Leone" from a weighted group of countries that kept their fees. It matches these countries on their trajectories before 2010 and on their structural characteristics. The mortality rate of Sierra Leone was near the maximum of the donor pool. Thus the classic estimator cannot match that level accurately. The ridge-augmented estimator (AugSynth) matches the pre-period almost exactly. This page shows both estimators.

```js
const synthOutcome = view(Inputs.radio(new Map([["Maternal mortality", "log_mmr"], ["Under-5 mortality", "log_u5mr"]]), {label: "Outcome", value: "log_mmr"}));
const synthEstimator = view(Inputs.radio(new Map([["AugSynth (tight pre-fit)", "augsynth"], ["Classic synthetic control", "synth"]]), {label: "Estimator", value: "augsynth"}));
```

```js
const sp = paths.filter((d) => d.outcome === synthOutcome && d.estimator === synthEstimator);
const spLong = sp.flatMap((d) => [
  {year: d.year, series: "Sierra Leone (actual)", value: d.actual},
  {year: d.year, series: "Synthetic Sierra Leone", value: d.synthetic}
]);
const yLabel = synthOutcome === "log_mmr" ? "Maternal deaths per 100,000 live births" : "Under-5 deaths per 1,000 live births";
```

```js
Plot.plot({
  height: 400,
  x: {label: null, tickFormat: "d"},
  y: {label: yLabel, grid: true},
  color: {legend: true, domain: ["Sierra Leone (actual)", "Synthetic Sierra Leone"], range: ["var(--theme-foreground-focus)", "#999"]},
  marks: [
    Plot.rectX([{x1: 2014, x2: 2016.5}], {x1: "x1", x2: "x2", fill: "#f4c7c3", fillOpacity: 0.25}),
    Plot.text([{x: 2015.2}], {x: "x", frameAnchor: "top", text: () => "Ebola", fill: "#c0504d", dy: 6}),
    Plot.ruleX([2010], {stroke: "#888", strokeDasharray: "4,4"}),
    Plot.text([{x: 2010}], {x: "x", frameAnchor: "top", text: () => "Free Health Care Initiative", fill: "#666", dx: -6, rotate: -90, dy: 60}),
    Plot.line(spLong, {x: "year", y: "value", stroke: "series", strokeWidth: 2,
      strokeDasharray: (d) => d.series.startsWith("Synthetic") ? "6,3" : null, tip: true})
  ]
})
```

The two outcomes give different results:

**Maternal mortality diverges.** Across 2010–13, before the Ebola epidemic started, actual maternal mortality was on average approximately ${Math.abs(mmrRow.att_pct_2010_2013).toFixed(0)}% less than its synthetic counterfactual. Across the full 2010–19 period the average difference is ${Math.abs(mmrRow.att_pct_2010_2019).toFixed(0)}%. The chart above shows that the difference increases each year. Pregnant women were the primary target group of the FHCI. The difference continues through the Ebola epidemic, although the epidemic was expected to decrease it.

**Under-5 mortality shows no effect.** The actual path and the synthetic path are almost the same. For a single country, and with smoothed mortality data, you cannot detect an effect of the FHCI on child survival. The pooled nine-country design does detect such an effect.

### Placebo tests

Synthetic control has no standard errors. Therefore inference applies the policy to each donor country in turn and measures the false "effects." If the difference for Sierra Leone is not unusual in that distribution, the result is random variation.

```js
const placYears = Array.from({length: 18}, (_, i) => 2002 + i);
const placLong = placebos
  .filter((d) => d.outcome === synthOutcome)
  .flatMap((d) => placYears.map((y) => ({iso3: d.iso3, year: y, gap: d[`gap_${y}`], kind: "placebo"})));
const sleGap = paths
  .filter((d) => d.outcome === synthOutcome && d.estimator === "augsynth")
  .map((d) => ({iso3: "SLE", year: d.year, gap: d.gap_log, kind: "Sierra Leone"}));
```

```js
Plot.plot({
  height: 380,
  x: {label: null, tickFormat: "d"},
  y: {label: "Gap: actual − synthetic (log points)", grid: true},
  marks: [
    Plot.ruleY([0]),
    Plot.ruleX([2010], {stroke: "#888", strokeDasharray: "4,4"}),
    Plot.line(placLong, {x: "year", y: "gap", z: "iso3", stroke: "#ccc", strokeWidth: 1,
      tip: true, title: (d) => `${d.iso3} (placebo)`}),
    Plot.line(sleGap, {x: "year", y: "gap", stroke: "var(--theme-foreground-focus)", strokeWidth: 2.5})
  ]
})
```

For maternal mortality, the 2010–13 difference for Sierra Leone is larger than 18 of the 20 placebos (rank test p ≈ ${mmrRow.p_att_2010_2013.toFixed(2)}). This result is suggestive, but it does not reach conventional significance. Several placebo countries in southern Africa show large false "effects". The increase in HIV treatment changed their maternal mortality in the same period. Therefore you must not give too much weight to a result from a single country, and this includes the result for Sierra Leone.

## What I would tell a policymaker

After the nine African countries removed point-of-care fees for mothers and children, child survival increased more quickly. Under-5 mortality was approximately 6% lower. This estimate stays the same in every specification tested, but the strictest statistical test grades the evidence as moderate and not as conclusive. In Sierra Leone, the country that removed the most fees, the effect on maternal mortality is large. But you cannot separate that effect from regional variation with data from one country. The policy fails when a country removes the fees but does not supply the necessary funds. The two clearest differences agree with the quantity of resources supplied for implementation: Sierra Leone supplied more, and Uganda gave mixed results.

## Why I built this

User fees are one of health financing's oldest arguments. The 1987 Bamako Initiative institutionalized them across Africa; the abolition wave this analysis studies unwound them. I spent four years at UNICEF producing the maternal and child mortality statistics these models run on, and grew up partly in two of the countries in the treatment table. The debate surfaced constantly in that work; a clean causal answer never did. This is me going back for it.

## Read next

- [Who benefited?](/equity) — the mechanism: wealth-quintile survey data show service use rose fastest in the poorest fifth of households after abolition, with every adopter country-service pair beating the control-country median
- [Policy brief](/brief) — the three-minute version for a decision-maker
- [Explore the data](/explorer) — every indicator, every country, every year used in this analysis
- [Methods & data quality](/methods) — treatment coding decisions, estimator details, the data error we caught in the World Bank series, and everything that could be wrong with this analysis

<style>
.big {font-size: 32px; font-weight: 700; display: block; margin: 4px 0;}
.card h2 {font-size: 13px; text-transform: uppercase; letter-spacing: 0.03em; color: var(--theme-foreground-muted);}
</style>
