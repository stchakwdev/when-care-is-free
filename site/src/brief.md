# Policy brief
## Should governments abolish point-of-care fees for mothers and children?

<div class="note" label="Who this page is for">Ministers, advisors, and budget holders deciding whether to remove user fees for maternal and child health services. It contains the same numbers as the <a href="/">technical findings</a> and <a href="/methods">methods</a> pages, without the machinery. Reading time: three minutes.</div>

```js
const att = FileAttachment("data/att_summary.csv").csv({typed: true});
const es = FileAttachment("data/event_study.csv").csv({typed: true});
const synthSummary = FileAttachment("data/synth_summary.csv").csv({typed: true});
const riSummary = FileAttachment("data/randomization_inference_summary.csv").csv({typed: true});
```

```js
const riS = riSummary[0];
const u5 = att.find((d) => d.outcome === "log_u5mr");
const nmr = att.find((d) => d.outcome === "log_nmr");
const mmrRow = synthSummary.find((d) => d.outcome === "log_mmr");
const pct = (x) => Math.expm1(x) * 100;
```

## The bottom line

1. **Removing fees is followed by fewer child deaths.** Across nine African countries that abolished fees between 2001 and 2016, under-5 mortality fell about **${Math.abs(pct(u5.estimate)).toFixed(0)}%** relative to 26 countries that kept charging — roughly ${Math.abs(pct(u5.ci_low)).toFixed(0)}% to ${Math.abs(pct(u5.ci_high)).toFixed(0)}% once statistical uncertainty is included. In a country where 1 child in 12 dies before age five, a 6% reduction is about 5 deaths averted per 1,000 births, every year.
2. **The policy is not free — it is a financing switch.** Fees move from families at the clinic door to the national budget. The evidence says the switch buys survival *when it is funded*: the boldest, best-resourced version (Sierra Leone, 2010) shows the clearest divergence; famously underfunded versions (Uganda, 2001) show the weakest.
3. **The gains go to the poorest first.** In every country with survey data spanning its reform, service use rose fastest in the poorest fifth of households — facility deliveries among the poorest tripled in Sierra Leone within three years — and rich–poor coverage gaps narrowed. If your objective is equity, this policy targets well by construction: fees are the barrier the poor face most.
4. **Do not expect it to fix newborn deaths.** Neonatal mortality barely moved in any country. Newborn survival depends on what happens *inside* the facility — skilled staff, equipment, referral — not on whether the door is open. Fee removal needs a companion investment in quality of delivery care.

## What was studied

Between 2001 and 2016, nine countries — Uganda, Zambia, Burundi, Niger, Liberia, Ghana, Sierra Leone, Kenya and Burkina Faso — stopped charging mothers and young children at public clinics, each in a different year. Because they acted at different times, their trajectories can be compared against 26 sub-Saharan countries that kept charging, before and after each country's own switch. That staggered pattern is hard for a coincidence to mimic: whatever else was happening in 2006 cannot also explain 2010, 2013 and 2016.

## What the data show

The chart below is the core result. Each point compares countries that removed fees against countries that never did, in the years before and after the change. Differences left of the line are small and shrinking — countries that acted were already converging with their neighbours, a caveat the [methods page](/methods) treats at length. Right of the line, child mortality in the fee-removing countries breaks below the comparison group and keeps falling.

```js
const esU5 = es.filter((d) => d.outcome === "log_u5mr" && d.estimator === "lpdid");
```

```js
Plot.plot({
  height: 380,
  x: {label: "Years before / after fees removed", tickFormat: "d"},
  y: {label: "Under-5 mortality vs. countries that kept fees (%)", grid: true, tickFormat: (d) => `${(Math.expm1(d) * 100).toFixed(0)}%`},
  marks: [
    Plot.ruleY([0]),
    Plot.ruleX([-0.5], {stroke: "#bbb", strokeDasharray: "4,4"}),
    Plot.text([{x: 0.6, y: 0}], {x: "x", frameAnchor: "top-left", dy: 8, text: () => "fees removed →", fill: "#888"}),
    Plot.areaY(esU5, {x: "rel_year", y1: "ci_low", y2: "ci_high", fill: "var(--theme-foreground-focus)", fillOpacity: 0.12}),
    Plot.line(esU5, {x: "rel_year", y: "estimate", stroke: "var(--theme-foreground-focus)", strokeWidth: 2}),
    Plot.dot(esU5, {x: "rel_year", y: "estimate", fill: "var(--theme-foreground-focus)", r: 3.5,
      tip: true, title: (d) => `${d.rel_year} years ${d.rel_year < 0 ? "before" : "after"}\n${(Math.expm1(d.estimate) * 100).toFixed(1)}% vs. control countries`})
  ]
})
```

The shaded band is the uncertainty range; where it sits clearly below zero, the difference is unlikely to be chance.

## How confident should you be?

Different findings in this analysis deserve different weight. Stated plainly:

| Finding | Confidence | Why |
|---|---|---|
| Child mortality fell ~${Math.abs(pct(u5.estimate)).toFixed(0)}% after fee removal | **Moderate** | Nine countries, nine different years; the estimate barely moves under any specification change, and survives removing any single country. The conventional statistical test passes clearly (p = ${u5.pvalue.toFixed(2)}); the strictest one sits at the edge (p = ${riS.p_one_sided.toFixed(2)}) |
| Sierra Leone's maternal mortality fell ~${Math.abs(mmrRow.att_pct_2010_2013).toFixed(0)}% below its expected path by 2013 | **Suggestive only** | One country; the gap is real but cannot be statistically separated from regional noise (p ≈ ${mmrRow.p_att_2010_2013.toFixed(2)}) |
| Newborn mortality was unaffected | **Moderate** | Consistent across all nine countries (${pct(nmr.estimate).toFixed(1)}%, statistically indistinguishable from zero) |
| Underfunded abolition underperforms | **Qualitative** | Pattern across case studies, not a formal test |

Two honest caveats. Countries choose *when* to act, and those that acted were already improving slightly faster — the comparison design mostly handles this, but not perfectly. And the international mortality estimates used here are smoothed, which blurs sharp policy effects; if anything, the true short-run effect is likely somewhat larger than reported.

## If you are considering this policy

- **Budget the replacement revenue before announcing.** Fee income is small nationally but large at the facility level; clinics that lose it without compensation cut supplies and informal charges reappear. This is the single most consistent failure mode in the case-study record.
- **Expect utilization to jump immediately, and stock accordingly.** Demand responds to price fast. Sierra Leone saw facility deliveries surge within months of its 2010 launch.
- **Pair it with delivery-care quality investment if newborn deaths are the target.** Free access alone did not move neonatal mortality anywhere in this study.
- **Announce it nationally and at once if you can.** The sharpest measured effects come from clean national implementations; phased or partial rollouts (regions, c-sections only) are also the hardest to evaluate afterwards.

## Where these numbers come from

Public World Bank / UN mortality estimates for 44 countries, 1990–2023, analysed with two independent quasi-experimental designs; every number on this page is computed live from the same result files as the [technical writeup](/), so this brief cannot drift from the underlying analysis. The [methods page](/methods) documents every judgment call, including the coding of each country's policy and a data error in the World Bank series this project caught and corrected. The full analysis is [reproducible from source](https://github.com/stchakwdev/when-care-is-free).

<style>
@media print {
  #observablehq-sidebar, #observablehq-header, #observablehq-footer, .observablehq-toc {display: none;}
}
</style>
