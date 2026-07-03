"""
Extract wealth-quintile equity data from the WHO MNCAH fact-table export.

Source: WHO Maternal, Newborn, Child & Adolescent Health data export
(data_export_MNCAH_MCA_FACT_DATA.csv, ~1.1 GB, retrieved November 2022).
The raw export is too large to commit, so this script extracts the small
slice the equity analysis needs and commits THAT: three fee-sensitive
care-seeking indicators, split by household wealth quintile (DHS/MICS
surveys), for the 44 sub-Saharan panel countries.

Indicators:
  BC_BHF        births delivered in a health facility (%)
  TECI_PNEUHCP  children with pneumonia symptoms taken to a health provider (%)
  TECI_ORS      children with diarrhoea treated with ORS (%)

Usage:
  python pipeline/extract_equity.py [path/to/data_export_MNCAH_MCA_FACT_DATA.csv]

Output -> data/raw/equity_wq.csv  (committed; the rest of the pipeline and
site reproduce from this file without the 1.1 GB export)
"""

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT.parent / "data_export_MNCAH_MCA_FACT_DATA.csv"

INDICATORS = {"BC_BHF", "TECI_PNEUHCP", "TECI_ORS"}

# WHO country names -> panel iso3 (sub-Saharan panel, all 44)
WHO_TO_ISO3 = {
    "Angola": "AGO", "Burundi": "BDI", "Benin": "BEN", "Burkina Faso": "BFA",
    "Botswana": "BWA", "Central African Republic": "CAF", "Côte d'Ivoire": "CIV",
    "Cameroon": "CMR", "Democratic Republic of the Congo": "COD", "Congo": "COG",
    "Comoros": "COM", "Djibouti": "DJI", "Eritrea": "ERI", "Ethiopia": "ETH",
    "Gabon": "GAB", "Ghana": "GHA", "Guinea": "GIN", "Gambia": "GMB",
    "Guinea-Bissau": "GNB", "Equatorial Guinea": "GNQ", "Kenya": "KEN",
    "Liberia": "LBR", "Lesotho": "LSO", "Madagascar": "MDG", "Mali": "MLI",
    "Mozambique": "MOZ", "Mauritania": "MRT", "Malawi": "MWI", "Namibia": "NAM",
    "Niger": "NER", "Nigeria": "NGA", "Rwanda": "RWA", "Senegal": "SEN",
    "Sierra Leone": "SLE", "Somalia": "SOM", "South Sudan": "SSD",
    "Eswatini": "SWZ", "Chad": "TCD", "Togo": "TGO",
    "United Republic of Tanzania": "TZA", "Uganda": "UGA", "South Africa": "ZAF",
    "Zambia": "ZMB", "Zimbabwe": "ZWE",
}

KEEP = ["INDICATOR_FK", "YEAR_FK", "COUNTRY_FK", "ValueNumeric",
        "WEALTHQUINTILE_FK", "DatasourceShort", "DatasourceLong"]


def main() -> None:
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SOURCE
    if not source.exists():
        sys.exit(f"source not found: {source}\n"
                 "Pass the path to the WHO MNCAH export as the first argument.")
    csv.field_size_limit(sys.maxsize)

    out_path = ROOT / "data" / "raw" / "equity_wq.csv"
    n = 0
    with open(source, encoding="utf-8-sig") as fh, open(out_path, "w", newline="") as out:
        writer = csv.writer(out)
        writer.writerow(["iso3", "indicator", "year", "quintile", "value", "source"])
        for row in csv.DictReader(fh):
            if row["INDICATOR_FK"] not in INDICATORS:
                continue
            if not row["WEALTHQUINTILE_FK"].strip():
                continue
            iso3 = WHO_TO_ISO3.get(row["COUNTRY_FK"])
            if iso3 is None:
                continue
            writer.writerow([
                iso3, row["INDICATOR_FK"], int(row["YEAR_FK"]),
                row["WEALTHQUINTILE_FK"], float(row["ValueNumeric"]),
                row["DatasourceLong"] or row["DatasourceShort"],
            ])
            n += 1
    print(f"wrote {n} rows -> {out_path}")


if __name__ == "__main__":
    main()
