from pathlib import Path
from datetime import date, timedelta
from datetime import datetime
import csv
import hashlib
import re
import time

import pandas as pd
import requests
import yaml


MASTER = Path("data/processed/scheme_master.parquet")
CONFIG = Path("config.yaml")
CACHE = Path("data/raw/amfi/history/universe_eligibility.txt")
UNIVERSE = Path("config/universe.csv")
LOG = Path("docs/universe_selection_log.md")

EXCLUDE = ["fund of fund", "fof", "etf", "segregated", "overseas"]

URL = "https://portal.amfiindia.com/DownloadNAVHistoryReport_Po.aspx"


def norm(value):
    return re.sub(r"[^a-z0-9]+", " ", str(value).lower()).strip()


def load_config():
    with CONFIG.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def download_eligibility(start, end):
    CACHE.parent.mkdir(parents=True, exist_ok=True)

    if CACHE.exists() and CACHE.stat().st_size > 0:
        print("Using cached AMFI eligibility response.")
        return CACHE.read_text(encoding="utf-8", errors="replace")

    params = {
        "frmdt": start.strftime("%d-%b-%Y"),
        "todt": end.strftime("%d-%b-%Y"),
    }

    for attempt in range(3):
        try:
            response = requests.get(
                URL,
                params=params,
                headers={"User-Agent": "mf-audit-research/1.0"},
                timeout=120,
            )
            response.raise_for_status()

            content = response.content.decode("utf-8-sig", errors="replace")

            # Reject an empty or obviously invalid response
            if not content.strip() or "Scheme Code" not in content:
                raise ValueError("AMFI returned an invalid history response.")

            CACHE.write_text(content, encoding="utf-8")
            return content

        except Exception:
            if attempt == 2:
                raise
            time.sleep(2 ** (attempt + 1))


def extract_eligible_codes(content):
    eligible = set()
    reader = csv.reader(content.splitlines(), delimiter=";")

    header_indices = None

    for row in reader:
        normalized = [norm(col) for col in row]

        if (
            "scheme code" in normalized
            and "net asset value" in normalized
            and "date" in normalized
        ):
            header_indices = {
                "code": normalized.index("scheme code"),
                "nav": normalized.index("net asset value"),
                "date": normalized.index("date"),
            }
            break

    if header_indices is None:
        raise ValueError(
            "Could not identify Scheme Code, Net Asset Value and Date columns."
        )

    counts = {"parsed": 0, "eligible": 0, "invalid": 0}

    for row in reader:
        try:
            code = int(row[header_indices["code"]].strip())
            nav = float(
                row[header_indices["nav"]].strip().replace(",", "")
            )
            nav_date = datetime.strptime(
                row[header_indices["date"]].strip(),
                "%d-%b-%Y"
            ).date()

            counts["parsed"] += 1

            if nav > 0:
                eligible.add(code)

        except (ValueError, IndexError, AttributeError):
            counts["invalid"] += 1
            continue

    counts["eligible"] = len(eligible)

    print(f"Historical records parsed: {counts['parsed']}")
    print(f"Invalid rows skipped: {counts['invalid']}")

    return eligible

def is_excluded(name):
    value = norm(name)
    return any(term in value for term in EXCLUDE)


def matches_amc(value, amc):
    # Normalize away the common "Mutual Fund" suffix
    a = norm(value).replace(" mutual fund", "").strip()
    b = norm(amc).replace(" mutual fund", "").strip()
    return a == b


def get_candidates(df, category, amc):
    candidates = df[
        (df["category"] == category)
        & (df["plan"] == "Direct")
        & (df["option"] == "Growth")
        & df["amc_header"].apply(lambda x: matches_amc(x, amc))
        & ~df["scheme_name"].apply(is_excluded)
    ].copy()

    return candidates.sort_values("scheme_code")


def select_active(df, config, eligible):
    selected = []
    log = []

    for category in config["categories"]:
        accepted = 0

        for amc in config["amcs_in_aum_rank_order"]:
            candidates = get_candidates(df, category, amc)

            if candidates.empty:
                log.append(f"- REJECTED: {category}, {amc}: no candidate.")
                continue

            # Try candidates in ascending scheme-code order.
            # If one lacks NAV, try the next candidate in the same AMC.
            chosen = None

            for _, candidate in candidates.iterrows():
                code = int(candidate["scheme_code"])

                if code not in eligible:
                    log.append(
                        f"- REJECTED: {category}, {amc}, {code}: "
                        "no NAV in eligibility window."
                    )
                    continue

                chosen = candidate
                break

            if chosen is None:
                continue

            selected.append(chosen)
            accepted += 1

            log.append(
                f"- ACCEPTED: {category}, {amc}, "
                f"{int(chosen['scheme_code'])}: {chosen['scheme_name']}."
            )

            if accepted == config["active_per_category"]:
                break

        if accepted < config["active_per_category"]:
            raise RuntimeError(
                f"Only {accepted} qualifying {category} schemes found. "
                "Pre-registered target not met; stop for human decision."
            )

    return selected, log


def select_passive(df, config, eligible):
    selected = []
    log = []
    amcs = config["amcs_in_aum_rank_order"]
    selected_amcs = set()

    # First pass: one qualifying Nifty 50 fund per AMC.
    for amc in amcs:
        candidates = get_candidates(df, "Index", amc)
        candidates = candidates[
            candidates["scheme_name"].str.contains(
                r"\bNifty 50\b", case=False, na=False, regex=True
            )
        ]

        if candidates.empty:
            log.append(f"- NO NIFTY 50 CANDIDATE: {amc}.")
            continue

        chosen = None

        for _, candidate in candidates.iterrows():
            code = int(candidate["scheme_code"])

            if code not in eligible:
                log.append(
                    f"- REJECTED passive Nifty 50: {code}, {amc}: "
                    "no NAV in eligibility window."
                )
                continue

            chosen = candidate
            break

        if chosen is not None:
            selected.append(chosen)
            selected_amcs.add(norm(amc))
            log.append(
                f"- ACCEPTED passive Nifty 50: "
                f"{int(chosen['scheme_code'])}, {amc}."
            )

        if len(selected) == config["passive_count"]:
            return selected, log

    # Fallback: Nifty Next 50, then Nifty 100.
    # Preserve one passive fund per AMC.
    if len(selected) < config["passive_count"]:
        for index_name in ["Nifty Next 50", "Nifty 100"]:
            for amc in amcs:
                if norm(amc) in selected_amcs:
                    log.append(
                        f"- SKIPPED passive {index_name}: {amc} "
                        "already has a selected passive fund."
                    )
                    continue

                candidates = get_candidates(df, "Index", amc)
                candidates = candidates[
                    candidates["scheme_name"].str.contains(
                        index_name, case=False, na=False, regex=False
                    )
                ]

                if candidates.empty:
                    log.append(
                        f"- NO {index_name} CANDIDATE: {amc}."
                    )
                    continue

                chosen = None

                for _, candidate in candidates.iterrows():
                    code = int(candidate["scheme_code"])

                    if code not in eligible:
                        log.append(
                            f"- REJECTED passive {index_name}: "
                            f"{code}, {amc}: no NAV in eligibility window."
                        )
                        continue

                    chosen = candidate
                    break

                if chosen is not None:
                    selected.append(chosen)
                    selected_amcs.add(norm(amc))
                    log.append(
                        f"- ACCEPTED passive {index_name}: "
                        f"{int(chosen['scheme_code'])}, {amc}."
                    )

                if len(selected) == config["passive_count"]:
                    break

            if len(selected) == config["passive_count"]:
                break

    if len(selected) < config["passive_count"]:
        raise RuntimeError(
            f"Only {len(selected)} passive schemes qualified. "
            "Human decision required."
        )

    return selected, log


def pair_schemes(selected, df, eligible):
    rows = []
    used_regular_codes = set()

    for pair_id, direct in enumerate(selected, start=1):
        direct_code = int(direct["scheme_code"])

        if direct_code not in eligible:
            raise RuntimeError(
                f"Direct scheme {direct_code} is not eligible."
            )

        regular = df[
            (df["plan"] == "Regular")
            & (df["option"] == "Growth")
            & (df["base_name"] == direct["base_name"])
            & (df["category"] == direct["category"])
            & (
                df["amc_header"].apply(norm)
                == norm(direct["amc_header"])
            )
        ]

        if len(regular) != 1:
            raise RuntimeError(
                f"Direct scheme {direct_code} has "
                f"{len(regular)} Regular-Growth matches "
                "within the same AMC and category. Stop."
            )

        counterpart = regular.iloc[0]
        regular_code = int(counterpart["scheme_code"])

        if regular_code not in eligible:
            raise RuntimeError(
                f"Regular counterpart {regular_code} for "
                f"Direct scheme {direct_code} has no NAV "
                "in the eligibility window."
            )

        if regular_code in used_regular_codes:
            raise RuntimeError(
                f"Regular scheme {regular_code} is reused "
                "in multiple pairs."
            )

        used_regular_codes.add(regular_code)

        for scheme in [direct, counterpart]:
            rows.append({
                "scheme_code": int(scheme["scheme_code"]),
                "pair_id": pair_id,
                "scheme_name": scheme["scheme_name"],
                "amc": scheme["amc_header"],
                "category": direct["category"],
                "plan": scheme["plan"],
                "is_passive": direct["category"] == "Index",
                "group": (
                    "Passive" if direct["category"] == "Index"
                    else "Active"
                ),
            })

    return pd.DataFrame(rows)

def main():
    config = load_config()
    df = pd.read_parquet(MASTER)

    start = date.fromisoformat(config["window"]["start"])
    end = start + timedelta(days=10)

    print(f"Eligibility window: {start} to {end}")

    content = download_eligibility(start, end)
    eligible = extract_eligible_codes(content)

    print(f"Eligible scheme codes found: {len(eligible):,}")

    active, active_log = select_active(df, config, eligible)
    passive, passive_log = select_passive(df, config, eligible)

    selected = active + passive

    if len(selected) != 16:
        raise RuntimeError(f"Expected 16 schemes, found {len(selected)}.")

    universe = pair_schemes(selected, df, eligible)

    if len(universe) != 32:
        raise RuntimeError(f"Expected 32 NAV series, found {len(universe)}.")

    if universe["scheme_code"].duplicated().any():
        raise RuntimeError("Duplicate scheme codes in universe.")

    UNIVERSE.parent.mkdir(parents=True, exist_ok=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)

    universe.to_csv(UNIVERSE, index=False)

    digest = hashlib.sha256(UNIVERSE.read_bytes()).hexdigest()

    log_text = [
        "# Universe Selection Log",
        "",
        f"- Eligibility window: {start} to {end}",
        f"- Selected schemes: {len(selected)}",
        f"- NAV series: {len(universe)}",
        "",
        "## Active selection",
        *active_log,
        "",
        "## Passive selection",
        *passive_log,
        "",
        f"- Universe SHA-256: `{digest}`",
        "",
    ]

    LOG.write_text("\n".join(log_text), encoding="utf-8")

    print("\nUniverse selection complete.")
    print(f"Output: {UNIVERSE}")
    print(f"Log: {LOG}")
    print(f"SHA-256: {digest}")
    print("\nSelected schemes:")
    print(universe.to_string(index=False))


if __name__ == "__main__":
    main()