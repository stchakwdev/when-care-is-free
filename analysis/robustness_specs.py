"""
Specification robustness for the pooled LP-DiD effect (log U5MR).

Four attacks on the headline estimate, each targeting a distinct threat:

1. Randomization inference (Fisher permutation). With 9 treated countries,
   cluster-robust SEs lean on asymptotics they may not have earned. Reassign
   the nine actual adoption years to nine randomly chosen countries from the
   35-country pool, re-estimate the pooled ATT, repeat N times. The share of
   placebo ATTs at least as negative as the real one is a finite-sample,
   model-free p-value — the same logic as the synthetic-control placebos.

2. Timing shifts. Most reforms launched mid-year (Uganda March 2001, Ghana
   July 2008, Sierra Leone April 2010). Recode adoption to the first full
   calendar year (+1) and to one year earlier (anticipation, -1).

3. Broad treatment coding. The main spec excludes partial or ambiguous
   reformers from both groups. Recode them as treated instead: Senegal 2005,
   Mali 2005 (c-sections/regional), Lesotho 2008 (phased), Benin 2009
   (c-sections), Rwanda 2006 (mutuelles). If the headline depends on the
   narrow coding, that is worth knowing.

4. Ebola exclusion. Drop Sierra Leone, Liberia (treated) and Guinea (control)
   — the 2014-16 epidemic is a post-period shock correlated with treatment.

Outputs -> results/robustness_specs.csv, results/randomization_inference.csv
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_did import load_panel, run_lpdid_att  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"

N_PERMUTATIONS = 1000
SEED = 20260703
BROAD_CODING = {"SEN": 2005, "MLI": 2005, "LSO": 2008, "BEN": 2009, "RWA": 2006}
EBOLA = {"SLE", "LBR", "GIN"}


def load_full_panel() -> pd.DataFrame:
    """Panel including the countries the main spec excludes (for broad coding)."""
    df = pd.read_csv(ROOT / "data" / "processed" / "panel.csv")
    df = df[(df["year"] >= 1995) & (df["year"] <= 2023)].copy()
    df["log_u5mr"] = np.log(df["u5mr"])
    df["iso_id"] = pd.factorize(df["iso3"])[0]
    return df


def att_with_g(df: pd.DataFrame, g_map: dict) -> dict:
    """Pooled LP-DiD ATT under an explicit iso3 -> adoption-year map."""
    d = df.copy()
    d["g"] = d["iso3"].map(g_map).fillna(0).astype(int)
    return run_lpdid_att(d, "log_u5mr")


def spec_rows() -> list:
    base_df = load_panel()
    g_actual = (
        base_df.loc[base_df["g"] > 0, ["iso3", "g"]]
        .drop_duplicates().set_index("iso3")["g"].to_dict()
    )
    rows = []

    r = run_lpdid_att(base_df, "log_u5mr")
    rows.append({"spec": "main", **r})

    for shift, name in [(1, "timing_plus1"), (-1, "timing_minus1")]:
        g = {k: v + shift for k, v in g_actual.items()}
        r = att_with_g(base_df, g)
        rows.append({"spec": name, **r})
        print(f"{name}: ATT {r['estimate']:+.4f}  p={r['pvalue']:.4f}")

    full = load_full_panel()
    g_broad = {**g_actual, **BROAD_CODING}
    r = att_with_g(full[full["group"].isin(["treated", "control"]) |
                        full["iso3"].isin(BROAD_CODING)], g_broad)
    rows.append({"spec": "broad_coding", **r})
    print(f"broad_coding: ATT {r['estimate']:+.4f}  p={r['pvalue']:.4f}")

    no_ebola = base_df[~base_df["iso3"].isin(EBOLA)]
    r = run_lpdid_att(no_ebola, "log_u5mr")
    rows.append({"spec": "drop_ebola", **r})
    print(f"drop_ebola: ATT {r['estimate']:+.4f}  p={r['pvalue']:.4f}")

    return rows


def randomization_inference(n_perm: int = N_PERMUTATIONS) -> None:
    df = load_panel()
    g_actual = (
        df.loc[df["g"] > 0, ["iso3", "g"]]
        .drop_duplicates().set_index("iso3")["g"].to_dict()
    )
    years = sorted(g_actual.values())
    pool = sorted(df["iso3"].unique())
    observed = att_with_g(df, g_actual)["estimate"]

    rng = np.random.default_rng(SEED)
    perm_atts = []
    for i in range(n_perm):
        chosen = rng.choice(pool, size=len(years), replace=False)
        g = dict(zip(chosen, rng.permutation(years)))
        try:
            perm_atts.append(att_with_g(df, g)["estimate"])
        except Exception:
            perm_atts.append(np.nan)
        if (i + 1) % 100 == 0:
            done = np.array([a for a in perm_atts if not np.isnan(a)])
            p_now = (np.sum(done <= observed) + 1) / (len(done) + 1)
            print(f"  {i+1}/{n_perm} permutations, running one-sided p = {p_now:.4f}", flush=True)

    atts = np.array([a for a in perm_atts if not np.isnan(a)])
    p_one = float((np.sum(atts <= observed) + 1) / (len(atts) + 1))
    p_two = float((np.sum(np.abs(atts) >= abs(observed)) + 1) / (len(atts) + 1))

    pd.DataFrame({"perm_att": atts}).to_csv(RESULTS / "randomization_inference.csv", index=False)
    summary = pd.DataFrame([{
        "outcome": "log_u5mr", "observed_att": observed, "n_permutations": len(atts),
        "p_one_sided": p_one, "p_two_sided": p_two,
        "perm_att_p5": float(np.percentile(atts, 5)),
        "perm_att_p95": float(np.percentile(atts, 95)),
    }])
    summary.to_csv(RESULTS / "randomization_inference_summary.csv", index=False)
    print(summary.round(4).to_string(index=False))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=["specs", "ri"], required=True)
    parser.add_argument("--n-perm", type=int, default=N_PERMUTATIONS)
    args = parser.parse_args()

    if args.stage == "specs":
        rows = spec_rows()
        out = pd.DataFrame(rows)[["spec", "estimate", "se", "ci_low", "ci_high",
                                  "pvalue", "n_treated", "n_control"]]
        out.to_csv(RESULTS / "robustness_specs.csv", index=False)
        print(out.round(4).to_string(index=False))
    else:
        randomization_inference(args.n_perm)
