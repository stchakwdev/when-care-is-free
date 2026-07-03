# Explore the data

Every series used in the analysis: 44 sub-Saharan African countries, 1990–2023, from the World Bank API (UN IGME and MMEIG estimates, WHO/UNICEF immunization coverage). Solid vertical lines mark each country's fee-abolition year.

```js
const panel = FileAttachment("data/panel.csv").csv({typed: true});
```

```js
const indicators = new Map([
  ["Under-5 mortality (per 1,000)", "u5mr"],
  ["Infant mortality (per 1,000)", "imr"],
  ["Neonatal mortality (per 1,000)", "nmr"],
  ["Maternal mortality (per 100,000)", "mmr"],
  ["DTP3 immunization (%)", "dtp3"],
  ["Measles immunization (%)", "mcv1"],
  ["Skilled birth attendance (%)", "sba"],
  ["GDP per capita (constant US$)", "gdp_pc"]
]);
const indicator = view(Inputs.select(indicators, {label: "Indicator"}));
```

```js
const allCountries = [...new Set(panel.map((d) => d.country))].sort();
const defaultPick = ["Sierra Leone", "Uganda", "Ghana", "Nigeria", "Chad"];
const picked = view(Inputs.select(allCountries, {label: "Countries", multiple: 8, value: defaultPick}));
```

```js
const logScale = view(Inputs.toggle({label: "Log scale", value: false}));
```

```js
const sel = panel.filter((d) => picked.includes(d.country) && d[indicator] != null);
const treatLines = [...new Set(sel.filter((d) => d.treated_year).map((d) => JSON.stringify({country: d.country, year: d.treated_year})))].map(JSON.parse);
```

```js
Plot.plot({
  height: 440,
  x: {label: null, tickFormat: "d"},
  y: {label: [...indicators].find(([, v]) => v === indicator)[0], grid: true, type: logScale ? "log" : "linear"},
  color: {legend: true},
  marks: [
    Plot.line(sel, {x: "year", y: indicator, stroke: "country", strokeWidth: 1.8, tip: true}),
    Plot.ruleX(treatLines, {x: "year", stroke: "#999", strokeDasharray: "4,4"}),
    Plot.text(treatLines, {x: "year", frameAnchor: "top", dy: 4, dx: 4,
      text: (d) => `${d.country} abolishes fees`, fill: "#888", fontSize: 10, rotate: 0, textAnchor: "start"})
  ]
})
```

```js
const groupCounts = d3.rollup(panel.filter((d) => d.year === 2019), (v) => v.length, (d) => d.group);
```

The study sample: ${groupCounts.get("treated") ?? 0} treated countries, ${groupCounts.get("control") ?? 0} never-treated controls, ${groupCounts.get("excluded") ?? 0} countries excluded for ambiguous or partial policies (see [Methods](/methods)).

## The raw table

```js
const tableRows = panel.filter((d) => picked.includes(d.country));
```

```js
Inputs.table(tableRows, {
  columns: ["country", "year", "u5mr", "imr", "nmr", "mmr", "dtp3", "mcv1", "sba", "group"],
  header: {country: "Country", year: "Year", u5mr: "U5MR", imr: "IMR", nmr: "NMR", mmr: "MMR", dtp3: "DTP3 %", mcv1: "MCV1 %", sba: "SBA %", group: "Group"},
  rows: 15
})
```

Download the full processed panel from the [GitHub repository](https://github.com/stchakwdev/when-care-is-free), or rebuild it from scratch with `python pipeline/fetch_data.py && python pipeline/validate_data.py`.
