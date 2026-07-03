"""
Fetch World Bank indicator data for the user-fee abolition analysis.

Pulls annual country-level series for sub-Saharan African countries from the
World Bank API (v2, public, no key required) and writes:
  - data/raw/<indicator>.csv        one file per indicator (long format)
  - data/processed/panel.csv        merged country-year panel with treatment coding

Reproducible: `python pipeline/fetch_data.py`
"""

import json
import time
import urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"

INDICATORS = {
    # outcomes
    "SH.DYN.MORT": "u5mr",            # under-5 mortality rate per 1,000 (UN IGME)
    "SP.DYN.IMRT.IN": "imr",          # infant mortality rate per 1,000 (UN IGME)
    "SH.DYN.NMRT": "nmr",             # neonatal mortality rate per 1,000 (UN IGME)
    "SH.STA.MMRT": "mmr",             # maternal mortality ratio per 100,000 (modeled)
    "SH.IMM.IDPT": "dtp3",            # DTP3 coverage % of 12-23m (WUENIC)
    "SH.IMM.MEAS": "mcv1",            # measles coverage % of 12-23m (WUENIC)
    "SH.STA.BRTC.ZS": "sba",          # skilled birth attendance % (survey years only)
    # covariates / synthetic-control predictors
    "NY.GDP.PCAP.KD": "gdp_pc",       # GDP per capita, constant 2015 USD
    "SP.URB.TOTL.IN.ZS": "urban",     # urban population %
    "SP.DYN.TFRT.IN": "tfr",          # total fertility rate
    "SH.XPD.CHEX.PC.CD": "che_pc",    # current health expenditure per capita USD (2000+)
    "SP.POP.TOTL": "pop",             # total population
}

# ---------------------------------------------------------------------------
# Treatment coding: national-scale abolition of point-of-care user fees for
# maternal and/or under-five health services. Year = first full-ish year of
# implementation. Sources documented on the methods page (site/src/methods.md).
# ---------------------------------------------------------------------------
TREATED = {
    "UGA": 2001,  # Uganda — all public facilities, March 2001
    "ZMB": 2006,  # Zambia — rural districts, April 2006 (extended later)
    "BDI": 2006,  # Burundi — under-5s and deliveries, May 2006
    "NER": 2006,  # Niger — under-5s + antenatal care, late 2006
    "LBR": 2007,  # Liberia — public primary facilities, 2007
    "GHA": 2008,  # Ghana — free maternal care via NHIS, July 2008
    "SLE": 2010,  # Sierra Leone — Free Health Care Initiative, April 2010
    "KEN": 2013,  # Kenya — free maternity in public facilities, June 2013
    "BFA": 2016,  # Burkina Faso — women and under-5s, April 2016
}

# Excluded from BOTH treatment and control: always-free systems, partial or
# sub-national policies, or ambiguous timing. Documented on the methods page.
EXCLUDED = {
    "MWI": "always free at point of use (never 'treated' in window)",
    "ZAF": "free care for pregnant women/children since 1994 (pre-window)",
    "SEN": "partial: free deliveries/c-sections in selected regions, 2005",
    "MLI": "partial: c-sections only, 2005",
    "BEN": "partial: c-sections only, 2009",
    "LSO": "phased primary-care fee removal 2008, ambiguous scale-up",
    "BWA": "nominal flat fee, effectively free — ambiguous",
    "RWA": "mutuelles (insurance) model 2006 — different intervention",
    "TZA": "exemptions for under-5s/deliveries long-standing but fees remain — ambiguous",
}

# Control pool: sub-Saharan countries that retained point-of-care fees for
# maternal/child services throughout 1995-2019 (no national abolition).
CONTROLS = [
    "NGA", "CMR", "CIV", "GIN", "GNB", "TGO", "TCD", "CAF", "COD", "COG",
    "GAB", "AGO", "ETH", "MOZ", "MDG", "ZWE", "NAM", "GMB", "MRT", "COM",
    "ERI", "SSD", "SOM", "SWZ", "DJI", "GNQ",
]

YEARS = "1990:2023"
BASE = "https://api.worldbank.org/v2/country/{codes}/indicator/{ind}?format=json&per_page=20000&date={years}"


def fetch_indicator(ind_code: str) -> pd.DataFrame:
    codes = ";".join(list(TREATED) + CONTROLS + list(EXCLUDED))
    url = BASE.format(codes=codes, ind=ind_code, years=YEARS)
    payload = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                payload = json.loads(r.read())
            if len(payload) >= 2 and payload[1]:
                break
        except Exception:
            pass
        time.sleep(1 + attempt)
    if payload is None or len(payload) < 2:
        raise RuntimeError(f"API error for {ind_code}: {payload}")
    meta, rows = payload[0], payload[1]
    assert meta["total"] == len(rows), f"pagination missed rows for {ind_code}"
    df = pd.DataFrame(
        {
            "iso3": [x["countryiso3code"] for x in rows],
            "country": [x["country"]["value"] for x in rows],
            "year": [int(x["date"]) for x in rows],
            "value": [x["value"] for x in rows],
        }
    )
    return df.sort_values(["iso3", "year"]).reset_index(drop=True)


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)

    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(max_workers=3) as ex:
        results = dict(zip(INDICATORS, ex.map(fetch_indicator, INDICATORS)))

    wide = None
    for ind_code, name in INDICATORS.items():
        df = results[ind_code]
        df.to_csv(RAW / f"{name}.csv", index=False)
        print(f"{ind_code:>18} -> {name:<8} {df['value'].notna().sum():>6} obs")
        col = df.rename(columns={"value": name})[["iso3", "country", "year", name]]
        wide = col if wide is None else wide.merge(col, on=["iso3", "country", "year"], how="outer")

    # treatment coding
    wide["treated_year"] = wide["iso3"].map(TREATED)
    wide["group"] = wide["iso3"].map(
        lambda c: "treated" if c in TREATED else ("excluded" if c in EXCLUDED else "control")
    )
    wide["post"] = (wide["year"] >= wide["treated_year"]).fillna(False).astype(int)
    wide["rel_year"] = wide["year"] - wide["treated_year"]

    wide = wide.sort_values(["iso3", "year"]).reset_index(drop=True)
    wide.to_csv(PROCESSED / "panel.csv", index=False)
    print(f"\npanel: {wide.shape[0]} rows, {wide['iso3'].nunique()} countries -> {PROCESSED/'panel.csv'}")


if __name__ == "__main__":
    main()
