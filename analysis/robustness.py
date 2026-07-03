"""
Robustness: leave-one-cohort-out LP-DiD for the pooled U5MR effect.

Drops each treated country in turn and re-estimates the pooled ATT. If the
headline result depends on any single adopter (e.g., Uganda's early, deep
reform), this will show it.

Output -> results/robustness_loo.csv
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_did import load_panel, run_lpdid_att  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"


def main() -> None:
    df = load_panel()
    treated = sorted(df.loc[df["g"] > 0, "iso3"].unique())
    rows = []

    base = run_lpdid_att(df, "log_u5mr")
    base["dropped"] = "none"
    rows.append(base)

    for iso in treated:
        sub = df[df["iso3"] != iso]
        r = run_lpdid_att(sub, "log_u5mr")
        r["dropped"] = iso
        rows.append(r)
        print(f"drop {iso}: ATT {r['estimate']:+.4f}  p={r['pvalue']:.4f}")

    out = pd.DataFrame(rows)[["dropped", "estimate", "se", "ci_low", "ci_high", "pvalue"]]
    out.to_csv(RESULTS / "robustness_loo.csv", index=False)
    print(out.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
