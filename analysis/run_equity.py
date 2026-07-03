"""
Equity mechanism analysis: who used care after fees were removed?

The DiD and synthetic-control results say fee abolition was followed by fewer
child deaths. This analysis asks about the mechanism: fees gate USE of care,
so if the mortality effect is real, service use should rise most where fees
bit hardest — the poorest households. DHS/MICS wealth-quintile breakdowns
(extracted from the WHO MNCAH export by pipeline/extract_equity.py) let us
check.

Design — descriptive, and framed that way. Surveys are irregular (every 3-7
years), so this is a pre/post comparison around each country's abolition
year, benchmarked against the secular trend in never-treated countries. It
is mechanism evidence for the causal designs, not a third causal design:

  * pre  = the last survey strictly BEFORE the adoption year
  * post = surveys strictly AFTER the adoption year (adoption-year surveys
    are shown in trajectories but excluded from summaries — field dates
    within the year are ambiguous relative to policy launch dates)
  * benchmark = annualized poorest-quintile change across every consecutive
    survey pair in never-treated control countries, same indicators,
    1995-2020

Outputs -> results/equity_trajectories.csv, equity_summary.csv,
           equity_benchmark.csv
"""

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"

ADOPTION = {"UGA": 2001, "ZMB": 2006, "BDI": 2006, "NER": 2006, "LBR": 2007,
            "GHA": 2008, "SLE": 2010, "KEN": 2013, "BFA": 2016}
INDICATOR_LABELS = {
    "BC_BHF": "Births in a health facility",
    "TECI_PNEUHCP": "Pneumonia symptoms: taken to a provider",
    "TECI_ORS": "Diarrhoea: treated with ORS",
}


def load() -> pd.DataFrame:
    df = pd.read_csv(ROOT / "data" / "raw" / "equity_wq.csv")
    panel = pd.read_csv(ROOT / "data" / "processed" / "panel.csv")
    groups = panel[["iso3", "country", "group"]].drop_duplicates()
    # multiple surveys in one calendar year -> average
    wide = (df.pivot_table(index=["iso3", "indicator", "year"],
                           columns="quintile", values="value", aggfunc="mean")
              .reset_index()
              .rename(columns={"ALL": "all", "WQ1": "q1", "WQ2": "q2",
                               "WQ3": "q3", "WQ4": "q4", "WQ5": "q5"}))
    wide = wide.merge(groups, on="iso3", how="left")
    wide["adopt"] = wide["iso3"].map(ADOPTION)
    wide["rel_year"] = wide["year"] - wide["adopt"]
    wide["gap"] = wide["q5"] - wide["q1"]
    return wide


def summarize_treated(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    treated = df[df["group"] == "treated"].dropna(subset=["q1", "q5"])
    for (iso3, ind), g in treated.groupby(["iso3", "indicator"]):
        adopt = ADOPTION[iso3]
        pre = g[g["year"] < adopt]
        post = g[g["year"] > adopt]
        if pre.empty or post.empty:
            continue
        p = pre.loc[pre["year"].idxmax()]          # last pre-adoption survey
        f = post.loc[post["year"].idxmin()]        # first post-adoption survey
        l = post.loc[post["year"].idxmax()]        # latest survey
        rows.append({
            "iso3": iso3, "country": g["country"].iloc[0], "indicator": ind,
            "indicator_label": INDICATOR_LABELS[ind], "adopt_year": adopt,
            "pre_year": int(p["year"]), "post_year": int(f["year"]),
            "last_year": int(l["year"]),
            "q1_pre": p["q1"], "q1_post": f["q1"], "q1_last": l["q1"],
            "q5_pre": p["q5"], "q5_post": f["q5"], "q5_last": l["q5"],
            "gap_pre": p["gap"], "gap_post": f["gap"], "gap_last": l["gap"],
            "q1_change_annual": (f["q1"] - p["q1"]) / (f["year"] - p["year"]),
            "q5_change_annual": (f["q5"] - p["q5"]) / (f["year"] - p["year"]),
        })
    return pd.DataFrame(rows)


def benchmark_controls(df: pd.DataFrame) -> pd.DataFrame:
    """Annualized q1 change across consecutive survey pairs, never-treated countries."""
    rows = []
    ctrl = df[(df["group"] == "control") & df["year"].between(1995, 2020)]
    for (iso3, ind), g in ctrl.dropna(subset=["q1"]).groupby(["iso3", "indicator"]):
        g = g.sort_values("year")
        for (y0, v0), (y1, v1) in zip(g[["year", "q1"]].values, g[["year", "q1"]].values[1:]):
            if y1 - y0 >= 2:  # skip same/adjacent-year re-surveys
                rows.append({"iso3": iso3, "indicator": ind, "year0": int(y0),
                             "year1": int(y1), "q1_change_annual": (v1 - v0) / (y1 - y0)})
    return pd.DataFrame(rows)


def main() -> None:
    df = load()
    df[df["group"].isin(["treated", "control"])].to_csv(
        RESULTS / "equity_trajectories.csv", index=False)

    summary = summarize_treated(df)
    bench = benchmark_controls(df)
    bench.to_csv(RESULTS / "equity_benchmark.csv", index=False)

    # where does each treated post-adoption q1 change sit vs the control distribution?
    pct = []
    for _, r in summary.iterrows():
        dist = bench.loc[bench["indicator"] == r["indicator"], "q1_change_annual"]
        pct.append(float((dist < r["q1_change_annual"]).mean()) if len(dist) else np.nan)
    summary["control_percentile"] = pct
    summary.to_csv(RESULTS / "equity_summary.csv", index=False)

    print(f"treated country-indicator pairs with pre & post surveys: {len(summary)}")
    print(f"control benchmark pairs: {len(bench)}")
    cols = ["country", "indicator", "pre_year", "post_year",
            "q1_pre", "q1_post", "gap_pre", "gap_last", "control_percentile"]
    print(summary[cols].round(2).to_string(index=False))  # 2dp: .round(1) once masked a 0.98 percentile as 1.0
    print("\ncontrol q1 annualized change by indicator (median [IQR]):")
    q = bench.groupby("indicator")["q1_change_annual"].quantile([0.25, 0.5, 0.75]).unstack()
    print(q.round(2).to_string())


if __name__ == "__main__":
    main()
