"""
Data validation: flag and repair impossible values in the mortality series.

UN IGME mortality estimates are produced by a penalized B-spline model, so the
published series are smooth by construction. A year-over-year jump of more than
40% in U5MR is therefore not a plausible estimate — it is an ingestion or
transcription error in the upstream API (crisis years such as conflicts show up
as bumps of tens of percent, not 3x spikes bracketed by normal values).

Rule: flag any point whose value is >40% away from BOTH neighbors while the
neighbors agree with each other (within 20%). Repair by geometric interpolation
of the neighbors. Every repair is logged to data/processed/data_quality_log.csv
and marked in a boolean `<col>_repaired` column. Sensitivity analyses rerun the
models dropping repaired points entirely.

Run after fetch_data.py: `python pipeline/validate_data.py`
"""

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
SERIES = ["u5mr", "imr", "nmr", "mmr"]

# Documented real catastrophes — spikes here are history, not errors.
# These points are flagged in the log but NEVER repaired.
KNOWN_CRISES = {
    ("RWA", 1994),  # genocide
    ("SOM", 2011),  # famine
    ("SSD", 1998),  # civil war famine (Bahr el Ghazal)
    ("MOZ", 2021), ("NAM", 2021), ("SWZ", 2021), ("ZAF", 2021), ("ZMB", 2021),  # COVID-era MMR revisions
}


def flag_spikes(s: pd.Series) -> list:
    """Return indices of isolated spikes in a smooth positive series."""
    bad = []
    v = s.dropna()
    idx = v.index.to_list()
    for i in range(1, len(idx) - 1):
        prev_v, cur, nxt = v.loc[idx[i - 1]], v.loc[idx[i]], v.loc[idx[i + 1]]
        jump_prev = abs(np.log(cur / prev_v))
        jump_next = abs(np.log(cur / nxt))
        neighbors_agree = abs(np.log(nxt / prev_v)) < np.log(1.20)
        if jump_prev > np.log(1.40) and jump_next > np.log(1.40) and neighbors_agree:
            bad.append(idx[i])
    return bad


def main() -> None:
    panel = pd.read_csv(PROCESSED / "panel.csv")
    log_rows = []
    for col in SERIES:
        panel[f"{col}_repaired"] = False
        for iso, g in panel.groupby("iso3"):
            s = g.set_index("year")[col]
            for year in flag_spikes(s):
                is_crisis = (iso, year) in KNOWN_CRISES
                yrs = s.dropna().index.to_list()
                i = yrs.index(year)
                repaired = float(np.sqrt(s.loc[yrs[i - 1]] * s.loc[yrs[i + 1]]))
                log_rows.append({
                    "iso3": iso, "year": year, "column": col,
                    "original": float(s.loc[year]),
                    "action": "kept (documented crisis)" if is_crisis else "repaired",
                    "repaired_value": None if is_crisis else repaired,
                })
                if not is_crisis:
                    mask = (panel["iso3"] == iso) & (panel["year"] == year)
                    panel.loc[mask, col] = repaired
                    panel.loc[mask, f"{col}_repaired"] = True

    log = pd.DataFrame(log_rows)
    log.to_csv(PROCESSED / "data_quality_log.csv", index=False)
    panel.to_csv(PROCESSED / "panel.csv", index=False)
    if len(log):
        print("repaired points:")
        print(log.to_string(index=False))
    else:
        print("no anomalies found")


if __name__ == "__main__":
    main()
