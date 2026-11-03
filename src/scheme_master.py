from pathlib import Path
import csv
import re

import pandas as pd


INPUT = Path("data/raw/amfi/probe/NAVAll.txt")
OUTPUT = Path("data/processed/scheme_master.parquet")


def clean_text(value):
    return re.sub(r"\s+", " ", str(value or "").strip())


def parse_number(value):
    value = clean_text(value).replace(",", "")
    try:
        return float(value) if value and value.upper() != "N.A." else None
    except ValueError:
        return None


def parse_date(value):
    value = clean_text(value)
    for fmt in ("%d-%b-%Y", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return pd.to_datetime(value, format=fmt).date()
        except (ValueError, TypeError):
            pass
    return None


def normalize_category(category_header, scheme_name):
    text = f"{category_header} {scheme_name}".lower()

    if "flexi cap" in text or "flexicap" in text:
        return "Flexi Cap"
    if "mid cap" in text or "midcap" in text:
        return "Mid Cap"
    if "large cap" in text or "largecap" in text:
        return "Large Cap"
    if "index" in text:
        return "Index"

    return "Other"


def derive_plan(name):
    return "Direct" if re.search(r"\bdirect\b", name, re.I) else "Regular"

def normalize_plan(value):
    value = clean_text(value).lower()

    if "direct" in value:
        return "Direct"
    if "regular" in value:
        return "Regular"
    if not value:
        return "Other"

    return "Other"


def normalize_option(value):
    value = clean_text(value).lower()
    if "growth" in value and "idcw" not in value and "dividend" not in value:
        return "Growth"
    return "Other"


def derive_option(name):
    if re.search(r"\b(growth)\b", name, re.I) and not re.search(
        r"\b(idcw|dividend)\b", name, re.I
    ):
        return "Growth"
    return "Other"


def derive_base_name(name):
    value = name.lower()

    # Remove plan and option labels used for Direct/Regular pairing
    value = re.sub(
        r"\b(direct|regular|plan|growth|option|idcw|dividend)\b",
        " ",
        value,
    )
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def find_column(header, candidates):
    normalized = [clean_text(x).lower() for x in header]
    for candidate in candidates:
        for i, name in enumerate(normalized):
            if candidate in name:
                return i
    return None


def parse_scheme_master():
    if not INPUT.exists():
        raise FileNotFoundError(f"AMFI file not found: {INPUT}")

    records = []
    category_header = ""
    amc_header = ""
    header = None

    with INPUT.open("r", encoding="utf-8-sig", errors="replace", newline="") as f:
        reader = csv.reader(f, delimiter=";")

        for row in reader:
            row = [clean_text(x) for x in row]

            if not row or not any(row):
                continue

            first = row[0]

            # Identify the actual data header
            if "scheme code" in first.lower():
                header = row
                continue

            # Skip non-data lines before the header
            if header is None:
                continue

            # Carry forward category and AMC headings
            if not first.isdigit():
                if "scheme" in first.lower() and "(" in first:
                    category_header = first
                elif "mutual fund" in first.lower():
                    amc_header = first
                continue

            if len(row) < len(header):
                row += [""] * (len(header) - len(row))

            code_idx = find_column(header, ["scheme code"])
            growth_idx = find_column(header, ["isin div payout", "isin growth"])
            reinvest_idx = find_column(header, ["isin div reinvestment"])
            name_idx = find_column(header, ["scheme name"])
            nav_idx = find_column(header, ["net asset value"])
            date_idx = find_column(header, ["date"])
            plan_idx = find_column(header, ["plan"])
            option_idx = find_column(header, ["option"])

            if None in (code_idx, name_idx, nav_idx, date_idx):
                raise ValueError(f"Required AMFI columns not found: {header}")

            name = row[name_idx]
            records.append({
                "scheme_code": int(row[code_idx]),
                "scheme_name": name,
                "isin_growth": row[growth_idx] if growth_idx is not None else None,
                "isin_reinv": row[reinvest_idx] if reinvest_idx is not None else None,
                "latest_nav": parse_number(row[nav_idx]),
                "latest_date": parse_date(row[date_idx]),
                "category_header": category_header,
                "amc_header": amc_header,
                "amfi_plan": row[plan_idx] if plan_idx is not None else "",
                "amfi_option": row[option_idx] if option_idx is not None else "",
            })

    if not records:
        raise ValueError("No scheme records parsed. Check the AMFI file format.")

    df = pd.DataFrame(records)

    df["plan"] = df["amfi_plan"].apply(normalize_plan)
    df["option"] = df["amfi_option"].apply(normalize_option)

    df = df.drop(columns=["amfi_plan", "amfi_option"])
    df["base_name"] = df["scheme_name"].apply(derive_base_name)
    df["category"] = df.apply(
        lambda r: normalize_category(r["category_header"], r["scheme_name"]),
        axis=1,
    )

    if df["scheme_code"].duplicated().any():
        duplicates = df.loc[
            df["scheme_code"].duplicated(), "scheme_code"
        ].tolist()
        raise ValueError(f"Duplicate scheme codes found: {duplicates[:10]}")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUTPUT, index=False)

    print(f"Parsed schemes: {len(df):,}")
    print(f"Output: {OUTPUT}")
    print("\nCounts by category:")
    print(df["category"].value_counts().to_string())
    print("\nCounts by plan:")
    print(df["plan"].value_counts().to_string())
    print("\nCounts by category and plan:")
    print(pd.crosstab(df["category"], df["plan"]).to_string())

if __name__ == "__main__":
    parse_scheme_master()