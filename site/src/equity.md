# Who benefited?
## Inside the averages: wealth-quintile evidence on the mechanism

The [headline results](/) say fee abolition was followed by fewer child deaths. This page asks *how* — and for *whom*. User fees are a price at the door, so if removing them saved lives, the footprints should be visible in service **use**, and they should be deepest where fees bit hardest: the poorest households.

DHS and MICS surveys split every indicator by household wealth quintile. The WHO's MNCAH database compiles those splits; a [scripted extraction](https://github.com/stchakwdev/when-care-is-free/blob/main/pipeline/extract_equity.py) pulls three fee-sensitive services for all 44 panel countries:

- **Births delivered in a health facility** — the service with the largest fees attached
- **Care-seeking for child pneumonia** — the illness where delay kills fastest
- **ORS treatment for child diarrhoea** — cheap, but requires contact with the system

<div class="note" label="What this page is and is not">Surveys arrive every 3–7 years, not annually, so this is a <b>descriptive pre/post comparison benchmarked against never-treated countries</b> — mechanism evidence that complements the causal designs, not a third causal design. Five of the nine adopters (Burundi, Ghana, Kenya, Niger, Sierra Leone) have usable surveys on both sides of their abolition year; Uganda, Zambia, Liberia and Burkina Faso do not. Surveys fielded in the adoption year itself are plotted but excluded from all summaries, because field dates within the year are ambiguous relative to policy launch dates.</div>

```js
const traj = FileAttachment("data/equity_trajectories.csv").csv({typed: true});
const summary = FileAttachment("data/equity_summary.csv").csv({typed: true});
const bench = FileAttachment("data/equity_benchmark.csv").csv({typed: true});
```

## Sierra Leone: the poorest fifth caught up

Before the 2010 Free Health Care Initiative, a woman from the poorest fifth of Sierra Leonean households had a ${traj.find(d => d.iso3 === "SLE" && d.indicator === "BC_BHF" && d.year === 2008)?.q1?.toFixed(0)}% chance of delivering in a health facility; from the richest fifth, ${traj.find(d => d.iso3 === "SLE" && d.indicator === "BC_BHF" && d.year === 2008)?.q5?.toFixed(0)}%. Watch what happens to the quintile fan after 2010:

```js
const sle = traj.filter((d) => d.iso3 === "SLE" && d.indicator === "BC_BHF" && d.year >= 2000);
const sleLong = sle.flatMap((d) => [
  {year: d.year, q: "Poorest 20%", v: d.q1},
  {year: d.year, q: "Q2", v: d.q2},
  {year: d.year, q: "Q3", v: d.q3},
  {year: d.year, q: "Q4", v: d.q4},
  {year: d.year, q: "Richest 20%", v: d.q5}
]).filter((d) => d.v != null);
```

```js
Plot.plot({
  height: 400,
  x: {label: null, tickFormat: "d"},
  y: {label: "Births in a health facility (%)", domain: [0, 100], grid: true},
  color: {legend: true, domain: ["Poorest 20%", "Q2", "Q3", "Q4", "Richest 20%"],
          range: ["var(--theme-foreground-focus)", "#b6b6c8", "#a3a3ba", "#8f8fac", "#444"]},
  marks: [
    Plot.ruleX([2010], {stroke: "#888", strokeDasharray: "4,4"}),
    Plot.text([{x: 2010}], {x: "x", frameAnchor: "top", text: () => "Free Health Care Initiative", fill: "#666", dx: -6, rotate: -90, dy: 72}),
    Plot.line(sleLong, {x: "year", y: "v", stroke: "q", strokeWidth: (d) => d.q === "Poorest 20%" || d.q === "Richest 20%" ? 2.5 : 1.25, curve: "monotone-x"}),
    Plot.dot(sleLong, {x: "year", y: "v", fill: "q", r: 3, tip: true, title: (d) => `${d.q}, ${d.year}: ${d.v.toFixed(1)}%`})
  ]
})
```

Facility delivery in the poorest quintile nearly **tripled within three years** of abolition (16.9% in 2008 → 48.4% in 2013) and reached 78.6% by 2019 — faster growth than any richer quintile, shrinking the rich–poor gap from 22 to 13 percentage points. The same pattern holds for pneumonia care-seeking (39% → 68% in the poorest fifth) and ORS treatment (43% → 87%), where the gap didn't just narrow — it inverted.

## Five countries, same fingerprint

Poorest-quintile (dark) versus richest-quintile (light) trajectories for each adopter with surveys on both sides of its abolition year (dashed line):

```js
const adopters5 = ["BDI", "GHA", "KEN", "NER", "SLE"];
const adoptYear = {BDI: 2006, GHA: 2008, KEN: 2013, NER: 2006, SLE: 2010};
const indChoice = view(Inputs.radio(
  new Map([["Facility births", "BC_BHF"], ["Pneumonia care-seeking", "TECI_PNEUHCP"], ["Diarrhoea: ORS", "TECI_ORS"]]),
  {label: "Service", value: "BC_BHF"}
));
```

```js
const multi = traj
  .filter((d) => adopters5.includes(d.iso3) && d.indicator === indChoice && d.year >= 1998 && d.q1 != null && d.q5 != null)
  .flatMap((d) => [
    {country: d.country, year: d.year, q: "Poorest 20%", v: d.q1},
    {country: d.country, year: d.year, q: "Richest 20%", v: d.q5}
  ]);
const adoptMarks = [...new Set(multi.map((d) => d.country))].map((c) => ({
  country: c, x: adoptYear[traj.find((d) => d.country === c).iso3]
}));
```

```js
Plot.plot({
  height: 320,
  marginRight: 40,
  x: {label: null, tickFormat: "d", ticks: 4},
  y: {label: "%", domain: [0, 100], grid: true},
  fx: {label: null},
  color: {legend: true, domain: ["Poorest 20%", "Richest 20%"], range: ["var(--theme-foreground-focus)", "#999"]},
  marks: [
    Plot.ruleX(adoptMarks, {fx: "country", x: "x", stroke: "#888", strokeDasharray: "4,4"}),
    Plot.line(multi, {fx: "country", x: "year", y: "v", stroke: "q", strokeWidth: 2, curve: "monotone-x"}),
    Plot.dot(multi, {fx: "country", x: "year", y: "v", fill: "q", r: 2.5, tip: true,
      title: (d) => `${d.country}, ${d.q}, ${d.year}: ${d.v.toFixed(1)}%`})
  ]
})
```

## Faster than the region was moving anyway?

The obvious objection: everything in the chart above was improving everywhere in Africa. The right comparison is the **secular rate** — how fast the poorest quintile was gaining in the 26 never-treated control countries over the same era. Every consecutive survey pair in a control country gives one estimate of that rate (${bench.length} pairs in total). Grey dots below; each adopter's post-abolition rate in color:

```js
const benchLabels = new Map([["BC_BHF", "Facility births"], ["TECI_PNEUHCP", "Pneumonia care-seeking"], ["TECI_ORS", "Diarrhoea: ORS"]]);
const benchPts = bench.map((d) => ({...d, label: benchLabels.get(d.indicator), kind: "Control countries (secular trend)"}));
const treatPts = summary.map((d) => ({...d, label: benchLabels.get(d.indicator), kind: "Adopters, after abolition"}));
```

```js
Plot.plot({
  height: 300,
  marginLeft: 180,
  x: {label: "Annualized change in poorest-quintile coverage (pp/year)", grid: true},
  y: {label: null},
  color: {legend: true, domain: ["Control countries (secular trend)", "Adopters, after abolition"], range: ["#ccc", "var(--theme-foreground-focus)"]},
  marks: [
    Plot.ruleX([0]),
    Plot.dot(benchPts, {x: "q1_change_annual", y: "label", fill: "kind", r: 3, fillOpacity: 0.55,
      tip: true, title: (d) => `${d.iso3} ${d.year0}–${d.year1}: ${d.q1_change_annual.toFixed(2)} pp/yr`}),
    Plot.dot(treatPts, {x: "q1_change_annual", y: "label", fill: "kind", r: 5.5, stroke: "white", strokeWidth: 1,
      tip: true, title: (d) => `${d.country} ${d.pre_year}→${d.post_year}: ${d.q1_change_annual.toFixed(2)} pp/yr (faster than ${(d.control_percentile * 100).toFixed(0)}% of control pairs)`})
  ]
})
```

All **${summary.length} adopter country-service pairs** improved faster than the control-country median; ${summary.filter((d) => d.control_percentile >= 0.9).length} of them sit in the top tenth of the control distribution, with poorest-quintile facility births in Burundi and Sierra Leone faster than ${(Math.max(...summary.map(d => d.control_percentile)) * 100).toFixed(0)}% of control pairs. For facility births — the service with the biggest price tag — the poorest quintile gained ${(summary.filter(d => d.indicator === "BC_BHF").reduce((s, d) => s + d.q1_change_annual, 0) / summary.filter(d => d.indicator === "BC_BHF").length).toFixed(1)} pp/year after abolition versus a control-country median of ${(() => { const v = bench.filter(d => d.indicator === "BC_BHF").map(d => d.q1_change_annual).sort((a, b) => a - b); return v[Math.floor(v.length / 2)].toFixed(1); })()} pp/year.

```js
Inputs.table(summary.map((d) => ({
  Country: d.country, Service: d.indicator_label, Abolition: d.adopt_year,
  "Survey pair": `${d.pre_year} → ${d.post_year}`,
  "Poorest 20% before": d.q1_pre?.toFixed(1) + "%", "Poorest 20% after": d.q1_post?.toFixed(1) + "%",
  "Rich−poor gap before": d.gap_pre?.toFixed(1) + " pp", "Gap at latest survey": d.gap_last?.toFixed(1) + " pp",
  "vs. control pairs": (d.control_percentile * 100).toFixed(0) + "th pctile"
})), {rows: 14})
```

## Why this makes the mortality result more believable

The three findings of this project now fit one mechanism. Fees gate *contact* with the health system, so removing them should — and did — raise use fastest among the poorest. Under-5 mortality is dominated by illnesses where contact is most of the battle (malaria, pneumonia, diarrhoea), so the [pooled −6% effect](/) lands exactly where the utilization surge says it should. And neonatal mortality, which depends on the *quality* of care once inside the facility, barely moved — free doors don't staff operating theatres. A mortality effect without a utilization footprint would have been suspicious. This one has footprints.

## Limits

- **No causal claim.** Five countries, irregular surveys, no counterfactual for any single one. The benchmark comparison shows the gains were unusually fast, not that the policy caused them.
- **Four adopters are missing** (Uganda, Zambia, Liberia, Burkina Faso) for lack of quintile surveys bracketing their abolition year. Their absence is a data constraint, not a selection choice — the [extraction script](https://github.com/stchakwdev/when-care-is-free/blob/main/pipeline/extract_equity.py) pulls whatever exists.
- **Niger's survey pair spans 12 years** (2000 → 2012), so its "post" change absorbs half a decade of pre-policy drift. Treat its dots accordingly.
- **Pneumonia care-seeking has small denominators** (children with symptoms in the survey window), so single-quintile values are noisy — visible as the wobble in the small multiples.
- **Concurrent programs** (malaria control scale-up, PMTCT, CHW expansion) also pushed these indicators. That is exactly why this page is framed as mechanism evidence for the causal designs rather than a design of its own.

**Data:** WHO Maternal, Newborn, Child & Adolescent Health database export (November 2022), underlying estimates from DHS and MICS surveys. The committed extract (`data/raw/equity_wq.csv`) reproduces everything on this page without the 1.1 GB source file.
