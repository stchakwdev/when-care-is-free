"""
Synthetic control: Sierra Leone's Free Health Care Initiative (April 2010).

Design
------
Treated unit:  Sierra Leone, treatment year 2010 (free care for pregnant women,
               lactating mothers, and children under five).
Outcomes:      log maternal mortality ratio (primary — the FHCI's target
               population) and log under-5 mortality (secondary).
Donor pool:    never-treated sub-Saharan countries that kept user fees.
               Excluded: SOM (2011 famine), ERI (data reliability), GNQ
               (oil-enclave GDP outlier), CAF (2013 civil war + two repaired
               data points).
Estimators:    classic Abadie synthetic control AND ridge-augmented synthetic
               control (Ben-Michael, Feller & Rothstein 2021). Sierra Leone's
               mortality sits near the edge of the donor convex hull, so the
               classic estimator fits poorly; AugSynth extrapolates with a
               ridge penalty and achieves tight pre-fit. Both are reported.
Pre-period:    2002-2009 (civil war ended 2002; war years share no donor dynamics).
Inference:     in-space placebos — refit on every donor, compare post/pre
               RMSPE ratios (Abadie, Diamond & Hainmueller 2010).
Caveats:       Ebola (2014-16) is a direct post-period shock, so the headline
               window is 2010-2013 (pre-Ebola); IGME/MMEIG series are
               model-smoothed, attenuating sharp changes -> estimates are
               conservative. Full paths shown to 2019.

Stages (chunk-friendly): --stage main | placebos [--donors A,B] | summary
"""

from pathlib import Path

import numpy as np
import pandas as pd
from pysyncon import AugSynth, Dataprep, Synth

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)

TREAT_YEAR = 2010
PRE = list(range(2002, TREAT_YEAR))
POST = list(range(TREAT_YEAR, 2020))
HEADLINE_POST = list(range(2010, 2014))  # pre-Ebola
PREDICTORS = ["gdp_pc", "tfr", "urban", "dtp3"]
LAG_YEARS = [2002, 2004, 2006, 2008, 2009]
OUTCOMES = ["log_mmr", "log_u5mr"]
DONOR_EXCLUDE = {"SOM", "ERI", "GNQ", "CAF"}


def load() -> pd.DataFrame:
    df = pd.read_csv(ROOT / "data" / "processed" / "panel.csv")
    df["log_u5mr"] = np.log(df["u5mr"])
    df["log_mmr"] = np.log(df["mmr"])
    keep = (df["group"] == "control") | (df["iso3"] == "SLE")
    df = df[keep & df["year"].between(2000, 2019) & ~df["iso3"].isin(DONOR_EXCLUDE)].copy()
    ok = []
    for iso, g in df.groupby("iso3"):
        gy = g.set_index("year")
        if (
            gy.loc[PRE + POST, OUTCOMES].notna().all().all()
            and gy.loc[PRE, PREDICTORS].notna().all().all()
        ):
            ok.append(iso)
    return df[df["iso3"].isin(ok)]


def fit_one(df: pd.DataFrame, treated: str, outcome: str, estimator: str):
    donors = [c for c in df["iso3"].unique() if c != treated]
    dp = Dataprep(
        foo=df,
        predictors=PREDICTORS,
        predictors_op="mean",
        time_predictors_prior=range(PRE[0], TREAT_YEAR),
        special_predictors=[(outcome, [y], "mean") for y in LAG_YEARS],
        dependent=outcome,
        unit_variable="iso3",
        time_variable="year",
        treatment_identifier=treated,
        controls_identifier=donors,
        time_optimize_ssr=range(PRE[0], TREAT_YEAR),
    )
    model = Synth() if estimator == "synth" else AugSynth()
    model.fit(dataprep=dp)
    Z0, Z1 = dp.make_outcome_mats(time_period=PRE + POST)
    synthetic = pd.Series(model._synthetic(Z0).values.ravel(), index=Z1.index)
    actual = pd.Series(Z1.values.ravel(), index=Z1.index)
    return model, actual, synthetic


def rmspe(gap: pd.Series, years: list) -> float:
    return float(np.sqrt((gap.loc[years] ** 2).mean()))


def run_main(df: pd.DataFrame) -> None:
    rows, weight_rows = [], []
    for outcome in OUTCOMES:
        for estimator in ["synth", "augsynth"]:
            model, actual, synthetic = fit_one(df, "SLE", outcome, estimator)
            for y in actual.index:
                rows.append({
                    "outcome": outcome, "estimator": estimator, "year": int(y),
                    "actual_log": float(actual.loc[y]),
                    "synthetic_log": float(synthetic.loc[y]),
                    "actual": float(np.exp(actual.loc[y])),
                    "synthetic": float(np.exp(synthetic.loc[y])),
                    "gap_log": float(actual.loc[y] - synthetic.loc[y]),
                })
            w = model.weights().round(4)
            for iso, wt in w[abs(w) > 0.01].items():
                weight_rows.append({
                    "outcome": outcome, "estimator": estimator, "iso3": iso, "weight": float(wt)
                })
            gap = actual - synthetic
            print(f"{outcome:>9} {estimator:>8}  preRMSPE {rmspe(gap, PRE):.4f}  "
                  f"ATT10-13 {gap.loc[HEADLINE_POST].mean():+.4f}  "
                  f"ATT10-19 {gap.loc[POST].mean():+.4f}")
    pd.DataFrame(rows).to_csv(RESULTS / "synth_paths.csv", index=False)
    pd.DataFrame(weight_rows).to_csv(RESULTS / "synth_weights.csv", index=False)


def run_placebos(df: pd.DataFrame, donors: list) -> None:
    out_path = RESULTS / "synth_placebos.csv"
    rows = []
    for donor in donors:
        for outcome in OUTCOMES:
            try:
                _, a, s = fit_one(df, donor, outcome, "augsynth")
                gap = a - s
                rows.append({
                    "iso3": donor, "outcome": outcome,
                    "pre_rmspe": rmspe(gap, PRE), "post_rmspe": rmspe(gap, POST),
                    "att_headline": float(gap.loc[HEADLINE_POST].mean()),
                    "att_full": float(gap.loc[POST].mean()),
                    **{f"gap_{y}": float(gap.loc[y]) for y in PRE + POST},
                })
                print(f"placebo {donor} {outcome} ok")
            except Exception as e:
                print(f"placebo {donor} {outcome} FAILED: {e}")
    plac = pd.DataFrame(rows)
    plac.to_csv(out_path, mode="a", header=not out_path.exists(), index=False)


def summarize(df: pd.DataFrame) -> None:
    paths = pd.read_csv(RESULTS / "synth_paths.csv")
    plac = pd.read_csv(RESULTS / "synth_placebos.csv").drop_duplicates(["iso3", "outcome"])
    out = []
    for outcome in OUTCOMES:
        p = paths[(paths.outcome == outcome) & (paths.estimator == "augsynth")].set_index("year")
        gap = p["gap_log"]
        pre_r, post_r = rmspe(gap, PRE), rmspe(gap, POST)
        ratio = post_r / pre_r
        pl = plac[plac.outcome == outcome].copy()
        pl["ratio"] = pl["post_rmspe"] / pl["pre_rmspe"]
        p_val = float((np.sum(pl["ratio"] >= ratio) + 1) / (len(pl) + 1))
        # rank-based one-sided p on the ATT itself: more robust than the RMSPE
        # ratio when AugSynth pre-fits are near-zero for all units
        att_head = float(gap.loc[HEADLINE_POST].mean())
        att_full_ = float(gap.loc[POST].mean())
        p_att_head = float((np.sum(pl["att_headline"] <= att_head) + 1) / (len(pl) + 1))
        p_att_full = float((np.sum(pl["att_full"] <= att_full_) + 1) / (len(pl) + 1))
        out.append({
            "outcome": outcome, "estimator": "augsynth",
            "pre_rmspe": pre_r, "post_rmspe": post_r, "rmspe_ratio": ratio,
            "placebo_p_value": p_val,
            "p_att_2010_2013": p_att_head, "p_att_2010_2019": p_att_full,
            "n_placebos": len(pl),
            "att_log_2010_2013": float(gap.loc[HEADLINE_POST].mean()),
            "att_pct_2010_2013": float(np.expm1(gap.loc[HEADLINE_POST].mean()) * 100),
            "att_log_2010_2019": float(gap.loc[POST].mean()),
            "att_pct_2010_2019": float(np.expm1(gap.loc[POST].mean()) * 100),
        })
    summary = pd.DataFrame(out)
    summary.to_csv(RESULTS / "synth_summary.csv", index=False)
    print(summary.round(4).to_string(index=False))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=["main", "placebos", "summary"], required=True)
    parser.add_argument("--donors", default="")
    args = parser.parse_args()

    df = load()
    donors_all = sorted(c for c in df["iso3"].unique() if c != "SLE")
    if args.stage == "main":
        print(f"donor pool ({len(donors_all)}): {donors_all}")
        run_main(df)
    elif args.stage == "placebos":
        run_placebos(df, args.donors.split(",") if args.donors else donors_all)
    else:
        summarize(df)
