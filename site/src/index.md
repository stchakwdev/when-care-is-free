# When care is free
## Quasi-experimental evidence from Africa's user-fee abolition wave, 2001–2016

For decades, most public clinics in sub-Saharan Africa charged patients at the door. A delivery might cost a week's income; a child's malaria treatment, a day's. Between 2001 and 2016, nine countries decided to stop charging mothers and young children. They did it in different years, for different reasons, which is exactly what makes the question answerable: **did removing fees save lives?**

This analysis treats the staggered rollout as a natural experiment. Countries that abolished fees are compared against 26 sub-Saharan countries that kept charging, using two designs that answer the question from different angles: local-projections difference-in-differences (LP-DiD) across all nine adopters, and a synthetic control case study of Sierra Leone's 2010 Free Health Care Initiative.

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

Every number on this page is computed live from the result files produced by the analysis pipeline. Nothing is pasted in, so the story and the statistics cannot drift apart.

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

The staggered timing matters methodologically. A single before/after comparison confounds the policy with everything else happening at the time. Nine different adoption years, each compared against countries that never adopted, is a much harder pattern for a confounder to mimic.

## Nine countries, one answer: fewer child deaths

The event study below traces outcomes relative to each country's abolition year. Estimates left of zero test the identifying assumption: if treated and control countries were on different paths *before* the policy, the design is in trouble. Estimates right of zero measure the effect.

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

Under-5 mortality falls by about **${Math.abs(pct(u5.estimate)).toFixed(0)}%** on average in the eight years after abolition (95% CI ${pct(u5.ci_low).toFixed(1)}% to ${pct(u5.ci_high).toFixed(1)}%). Neonatal mortality barely moves, which is what you would expect: newborn survival depends on quality of care at delivery, not just whether the door is open. Immunization coverage shifts are positive but imprecise. The mechanism behind this pattern — a surge in service use concentrated among the poorest households — is documented with wealth-quintile survey data on the [Who benefited?](/equity) page.

Four things to know before believing this chart:

1. **The pre-period is not perfectly flat.** At t−6 the point estimate is positive and marginally significant, meaning treated countries were improving somewhat faster than controls before abolishing fees. Governments do not flip a coin to decide health policy. The effect estimate survives this (the post-period drop is larger and sharper than the pre-trend), but a reader should know it is there. Toggle to the classic TWFE estimator to see why estimator choice matters under staggered adoption.
2. **Mortality series are modeled.** The UN IGME estimates smooth over sharp year-to-year changes, which biases against finding sudden policy effects. The true short-run effect is likely larger than what smoothed data can show.
3. **This is an intent-to-treat estimate of a policy announcement.** Implementation quality varied enormously; Uganda's abolition was famously underfunded. The average mixes strong and weak implementations.
4. **The p-value depends on how strict you are.** Cluster-robust inference gives p = ${u5.pvalue.toFixed(2)}; reassigning the nine adoption years to random countries 1,000 times gives a design-based p = ${riS.p_one_sided.toFixed(2)} (one-sided). The estimate is robust in sign and size across every specification tested — timing shifts, broad treatment coding, dropping Ebola countries, dropping any cohort — but under the strictest test it sits at the edge of significance, not comfortably past it. The [methods page](/methods) shows all of it.

## Sierra Leone: the sharpest test

In April 2010, Sierra Leone abolished all fees for pregnant women, lactating mothers, and children under five in one stroke: the Free Health Care Initiative. It was the boldest version of the policy anywhere, in one of the world's most dangerous places to give birth.

The synthetic control method builds a "counterfactual Sierra Leone" from a weighted mix of countries that kept charging fees, matched on pre-2010 trajectories and structural characteristics. Sierra Leone's mortality was near the top of the donor pool, so the classic estimator struggles to match its level; the ridge-augmented estimator (AugSynth) fits the pre-period almost exactly. Both are shown.

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

The two outcomes tell different stories, and the difference is the point:

**Maternal mortality diverges.** By 2013, before Ebola struck, actual maternal mortality sat about ${Math.abs(mmrRow.att_pct_2010_2013).toFixed(0)}% below its synthetic counterfactual, and the gap kept widening to ${Math.abs(mmrRow.att_pct_2010_2019).toFixed(0)}% by 2019. Pregnant women were exactly who the FHCI targeted. The gap survives Ebola, which should have pushed it the other way.

**Under-5 mortality shows nothing.** The actual and synthetic paths overlap almost perfectly. On smoothed mortality data, for a single country, the child-survival effect of the FHCI is simply not detectable — even though the pooled nine-country design finds one. Both facts stay in the writeup.

### How sure can we be? Placebo tests

Synthetic control has no standard errors, so inference works by pretending each donor country passed the policy and measuring the fake "effects." If Sierra Leone's gap is not unusual against that distribution, the result is noise.

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

For maternal mortality, Sierra Leone's 2010–13 gap is larger than all but two of twenty placebos (rank test p ≈ ${mmrRow.p_att_2010_2013.toFixed(2)}). That is suggestive but short of conventional significance, and it stays described that way. Several placebo countries in southern Africa show large spurious "effects" because their maternal mortality was reshaped by HIV treatment scale-up in the same period, which is a warning against over-reading any single-country result, including this one.

## What I would tell a policymaker

Three sentences, no hedging hidden in footnotes. Removing point-of-care fees for mothers and children is followed by an acceleration in child survival across nine African adopters, on the order of 6% lower under-5 mortality — an effect that is stable across every specification tested, though the strictest statistical test grades the evidence moderate rather than overwhelming. The effect on maternal mortality in the boldest case, Sierra Leone, is large but cannot be statistically separated from regional noise using a single country. Fee removal without funding is where the policy fails; the two clearest divergences (Sierra Leone up, Uganda mixed) track how seriously implementation was resourced.

## Why I built this

User fees are one of health financing's oldest arguments — institutionalized across Africa by the 1987 Bamako Initiative, unwound by the abolition wave this analysis studies. I spent four years at UNICEF producing the maternal and child mortality statistics these models run on, and grew up partly in two of the countries in the treatment table. The debate surfaced constantly in that work; a clean causal answer never did. This is me going back for it.

## Read next

- [Who benefited?](/equity) — the mechanism: wealth-quintile survey data show the poorest fifth gained access fastest after abolition, faster than in any control country on record
- [Policy brief](/brief) — the three-minute version for a decision-maker
- [Explore the data](/explorer) — every indicator, every country, every year used in this analysis
- [Methods & data quality](/methods) — treatment coding decisions, estimator details, the data error we caught in the World Bank series, and everything that could be wrong with this analysis

<style>
.big {font-size: 32px; font-weight: 700; display: block; margin: 4px 0;}
.card h2 {font-size: 13px; text-transform: uppercase; letter-spacing: 0.03em; color: var(--theme-foreground-muted);}
</style>
