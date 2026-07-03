"""
Staggered difference-in-differences: user-fee abolition and child health.

Estimators:
  1. LP-DiD (Dube, Girardi, Jorda & Taylor 2023) via pyfixest — robust to
     heterogeneous treatment effects under staggered adoption. Primary.
  2. Classic TWFE event study — shown for comparison (known to be biased
     under staggered adoption + heterogeneous effects).

Outcomes: log under-5 mortality (IGME), log neonatal mortality,
          DTP3 and MCV1 immunization coverage (WUENIC).

Controls: never-treated sub-Saharan countries that kept fees.
Inference: cluster-robust by country.

Outputs -> results/event_study.csv, results/att_summary.csv
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pyfixest as pf
from pyfixest.did import lpdid

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)

HORIZON_PRE, HORIZON_POST = 6, 8
OUTCOMES = {
    "log_u5mr": ("Under-5 mortality (log)", True),
    "log_nmr": ("Neonatal mortality (log)", True),
    "dtp3": ("DTP3 immunization coverage (pp)", False),
    "mcv1": ("Measles immunization coverage (pp)", False),
}


def load_panel() -> pd.DataFrame:
    df = pd.read_csv(ROOT / "data" / "processed" / "panel.csv")
    df = df[df["group"].isin(["treated", "control"])].copy()
    df = df[(df["year"] >= 1995) & (df["year"] <= 2023)]
    df["log_u5mr"] = np.log(df["u5mr"])
    df["log_nmr"] = np.log(df["nmr"])
    df["log_mmr"] = np.log(df["mmr"])
    # lpdid expects never-treated coded as 0 in the cohort variable
    df["g"] = df["treated_year"].fillna(0).astype(int)
    df["iso_id"] = pd.factorize(df["iso3"])[0]
    return df


def run_lpdid(df: pd.DataFrame, outcome: str) -> pd.DataFrame:
    d = df.dropna(subset=[outcome]).copy()
    fit = lpdid(
        d,
        yname=outcome,
        idname="iso_id",
        tname="year",
        gname="g",
        vcov={"CRV1": "iso_id"},
        pre_window=HORIZON_PRE,
        post_window=HORIZON_POST,
        never_treated=0,
        att=False,
    )
    tidy = fit.tidy().reset_index().rename(columns={"Coefficient": "term"})
    tidy["rel_year"] = tidy["term"].str.extract(r"(-?\d+)").astype(int)
    tidy["estimator"] = "lpdid"
    tidy["outcome"] = outcome
    return tidy

def run_lpdid_att(df: pd.DataFrame, outcome: str) -> dict:
    d = df.dropna(subset=[outcome]).copy()
    fit = lpdid(
        d, yname=outcome, idname="iso_id", tname="year", gname="g",
        vcov={"CRV1": "iso_id"}, pre_window=HORIZON_PRE,
        post_window=HORIZON_POST, never_treated=0, att=True,
    )
    row = fit.tidy().iloc[0]
    return {
        "outcome": outcome,
        "estimator": "lpdid_att",
        "estimate": row["Estimate"],
        "se": row["Std. Error"],
        "ci_low": row["2.5%"],
        "ci_high": row["97.5%"],
        "pvalue": row["Pr(>|t|)"],
        "n_treated": int(d.loc[d.g > 0, "iso3"].nunique()),
        "n_control": int(d.loc[d.g == 0, "iso3"].nunique()),
    }


def run_twfe_event_study(df: pd.DataFrame, outcome: str) -> pd.DataFrame:
    """Classic TWFE event study with binned endpoints, ref = -1."""
    d = df.dropna(subset=[outcome]).copy()
    d["rel"] = d["rel_year"].clip(-HORIZON_PRE, HORIZON_POST)
    d.loc[d["g"] == 0, "rel"] = -1  # never treated -> reference bucket
    dummies = pd.get_dummies(d["rel"].astype(int), prefix="rel").drop(columns=["rel_-1"])
    dummies.columns = [c.replace("-", "m") for c in dummies.columns]
    d = pd.concat([d, dummies.astype(float)], axis=1)
    rhs = " + ".join(dummies.columns)
    fit = pf.feols(f"{outcome} ~ {rhs} | iso3 + year", d, vcov={"CRV1": "iso3"})
    tidy = fit.tidy().reset_index().rename(columns={"Coefficient": "term"})
    tidy = tidy[tidy["term"].str.startswith("rel_")]
    tidy["rel_year"] = (
        tidy["term"].str.replace("rel_", "", regex=False).str.replace("m", "-", regex=False).astype(int)
    )
    tidy["estimator"] = "twfe"
    tidy["outcome"] = outcome
    return tidy


def main() -> None:
    df = load_panel()
    print(f"panel: {df.iso3.nunique()} countries "
          f"({df.loc[df.g>0,'iso3'].nunique()} treated, {df.loc[df.g==0,'iso3'].nunique()} control)")

    frames, att_rows = [], []
    for outcome in OUTCOMES:
        es = run_lpdid(df, outcome)
        tw = run_twfe_event_study(df, outcome)
        frames += [es, tw]
        att_rows.append(run_lpdid_att(df, outcome))
        print(f"  {outcome}: lpdid ok ({len(es)} coefs), twfe ok ({len(tw)} coefs)")

    cols = ["outcome", "estimator", "rel_year", "Estimate", "Std. Error", "2.5%", "97.5%", "Pr(>|t|)"]
    out = pd.concat(frames)[cols].rename(
        columns={"Estimate": "estimate", "Std. Error": "se", "2.5%": "ci_low",
                 "97.5%": "ci_high", "Pr(>|t|)": "pvalue"}
    )
    out.to_csv(RESULTS / "event_study.csv", index=False)

    att = pd.DataFrame(att_rows)
    att.to_csv(RESULTS / "att_summary.csv", index=False)
    print(att[["outcome", "estimate", "ci_low", "ci_high", "pvalue"]].round(4).to_string(index=False))


if __name__ == "__main__":
    main()
