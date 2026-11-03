"""Download and process historical AMFI NAV data for the frozen universe."""

from __future__ import annotations

import csv
import os
import re
import time
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
import requests
import yaml
from dotenv import load_dotenv
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)
from tqdm import tqdm


CONFIG = Path("config.yaml")
UNIVERSE = Path("config/universe.csv")
CACHE_DIR = Path("data/raw/amfi/history")
OUTPUT = Path("data/processed/nav_long.parquet")

URL = "https://portal.amfiindia.com/DownloadNAVHistoryReport_Po.aspx"
MAX_DAYS = 88
TIMEOUT = 120


def normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def chunk_ranges(
    start: date,
    end: date,
    max_days: int = MAX_DAYS,
) -> list[tuple[date, date]]:
    """Create contiguous, non-overlapping inclusive date ranges."""

    if start > end:
        raise ValueError("Start date cannot be after end date.")

    if max_days < 1:
        raise ValueError("max_days must be at least 1.")

    chunks = []
    current = start

    while current <= end:
        chunk_end = min(
            current + timedelta(days=max_days - 1),
            end,
        )
        chunks.append((current, chunk_end))
        current = chunk_end + timedelta(days=1)

    return chunks


def load_project_config() -> dict:
    with CONFIG.open(encoding="utf-8") as file:
        return yaml.safe_load(file)


def load_universe() -> set[int]:
    universe = pd.read_csv(UNIVERSE, dtype={"scheme_code": str})

    if "scheme_code" not in universe.columns:
        raise ValueError("scheme_code column missing from universe.csv")

    codes = {
        int(code)
        for code in universe["scheme_code"].dropna()
    }

    if len(codes) != 32:
        raise ValueError(
            f"Expected 32 unique scheme codes, found {len(codes)}."
        )

    return codes


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception_type(
        (requests.RequestException, ValueError)
    ),
    reraise=True,
)
def request_amfi(
    start: date,
    end: date,
    user_agent: str,
) -> str:
    params = {
        "frmdt": start.strftime("%d-%b-%Y"),
        "todt": end.strftime("%d-%b-%Y"),
    }

    response = requests.get(
        URL,
        params=params,
        headers={"User-Agent": user_agent},
        timeout=TIMEOUT,
    )

    response.raise_for_status()

    content = response.content.decode(
        "utf-8-sig",
        errors="replace",
    )

    if not content.strip() or "Scheme Code" not in content:
        raise ValueError(
            f"Invalid AMFI response for {start} to {end}."
        )

    return content


def get_chunk(
    start: date,
    end: date,
    user_agent: str,
) -> tuple[str, bool]:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    cache_file = CACHE_DIR / (
        f"{start.isoformat()}_{end.isoformat()}.txt"
    )

    if cache_file.exists() and cache_file.stat().st_size > 0:
        return (
            cache_file.read_text(
                encoding="utf-8-sig",
                errors="replace",
            ),
            True,
        )

    content = request_amfi(start, end, user_agent)

    cache_file.write_text(content, encoding="utf-8")

    return content, False


def parse_amfi_response(
    content: str,
    universe_codes: set[int],
) -> tuple[list[dict], int]:
    """Find the header dynamically and extract relevant NAV records."""

    rows = list(
        csv.reader(content.splitlines(), delimiter=";")
    )

    header_index = None
    indices = {}

    for i, row in enumerate(rows):
        normalized = [normalize(col) for col in row]

        required = {
            "scheme code",
            "net asset value",
            "date",
        }

        if required.issubset(set(normalized)):
            header_index = i
            indices = {
                "code": normalized.index("scheme code"),
                "nav": normalized.index("net asset value"),
                "date": normalized.index("date"),
            }
            break

    if header_index is None:
        raise ValueError("AMFI response does not contain a valid header.")

    records = []
    invalid_rows = 0

    for row in rows[header_index + 1:]:
        if not row or len(row) <= max(indices.values()):
            continue

        try:
            code = int(row[indices["code"]].strip())

            if code not in universe_codes:
                continue

            nav_text = row[indices["nav"]].strip()

            if not nav_text or nav_text.upper() == "N.A.":
                continue

            nav = float(nav_text)

            nav_date = datetime.strptime(
                row[indices["date"]].strip(),
                "%d-%b-%Y",
            ).date()

            if nav <= 0:
                invalid_rows += 1
                continue

            records.append({
                "scheme_code": code,
                "nav_date": nav_date,
                "nav": nav,
            })

        except (ValueError, IndexError):
            invalid_rows += 1

    return records, invalid_rows


def main() -> None:
    load_dotenv()

    contact_email = os.getenv("AMFI_CONTACT_EMAIL")

    if not contact_email:
        raise EnvironmentError(
            "AMFI_CONTACT_EMAIL is missing from the environment."
        )

    user_agent = (
        "mf-audit-research/1.0 "
        f"(educational; contact: {contact_email})"
    )

    config = load_project_config()

    start = date.fromisoformat(config["window"]["start"])
    end = date.fromisoformat(config["window"]["end"])

    universe_codes = load_universe()
    chunks = chunk_ranges(start, end)

    print("=== AMFI NAV DOWNLOAD ===")
    print(f"Universe schemes: {len(universe_codes)}")
    print(f"Date range: {start} to {end}")
    print(f"Chunks: {len(chunks)}")
    print(f"Maximum days per chunk: {MAX_DAYS}")

    all_records = []
    invalid_rows = 0

    requests_made = 0
    cache_hits = 0
    failures = []

    for chunk_start, chunk_end in tqdm(
        chunks,
        desc="Downloading NAV",
    ):
        try:
            content, cached = get_chunk(
                chunk_start,
                chunk_end,
                user_agent,
            )

            if cached:
                cache_hits += 1
            else:
                requests_made += 1
                time.sleep(1)

            records, invalid = parse_amfi_response(
                content,
                universe_codes,
            )

            all_records.extend(records)
            invalid_rows += invalid

        except Exception as exc:
            failures.append(
                (chunk_start, chunk_end, str(exc))
            )

    print("\n=== DOWNLOAD SUMMARY ===")
    print(f"Requests made: {requests_made}")
    print(f"Cache hits: {cache_hits}")
    print(f"Failed chunks: {len(failures)}")
    print(f"Invalid rows skipped: {invalid_rows}")

    if failures:
        for chunk_start, chunk_end, error in failures:
            print(
                f"FAILED: {chunk_start} to {chunk_end}: {error}"
            )

        raise RuntimeError(
            "NAV download incomplete. Fix failed chunks and rerun."
        )

    if not all_records:
        raise RuntimeError("No NAV records were extracted.")

    nav = pd.DataFrame(all_records)

    nav["scheme_code"] = nav["scheme_code"].astype("int64")
    nav["nav_date"] = pd.to_datetime(nav["nav_date"])
    nav["nav"] = nav["nav"].astype("float64")

    # Remove exact duplicates, but reject conflicting NAV values.
    duplicate_keys = nav.duplicated(
        subset=["scheme_code", "nav_date"],
        keep=False,
    )

    if duplicate_keys.any():
        duplicate_rows = nav.loc[duplicate_keys]

        conflicts = (
            duplicate_rows.groupby(
                ["scheme_code", "nav_date"]
            )["nav"]
            .nunique()
        )

        if (conflicts > 1).any():
            raise ValueError(
                "Conflicting NAV values found for the same "
                "scheme code and date."
            )

        nav = nav.drop_duplicates(
            subset=["scheme_code", "nav_date"]
        )

    nav = nav.sort_values(
        ["scheme_code", "nav_date"]
    ).reset_index(drop=True)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    nav.to_parquet(OUTPUT, index=False)

    print("\n=== SCHEME-WISE NAV COUNTS ===")

    counts = (
        nav.groupby("scheme_code")
        .size()
        .reindex(sorted(universe_codes), fill_value=0)
    )

    for code, count in counts.items():
        print(f"{code}: {count:,} observations")

    print("\n=== FINAL SUMMARY ===")
    print(f"Total NAV rows: {len(nav):,}")
    print(f"Unique schemes: {nav['scheme_code'].nunique()}")
    print(f"Date range: {nav['nav_date'].min().date()} "
          f"to {nav['nav_date'].max().date()}")
    print(f"Output: {OUTPUT}")


if __name__ == "__main__":
    main()