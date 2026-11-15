"""Build and load provisional estimated BSE TRI series.

Method:
    Estimated BSE TRI_t =
        BSE Price_t * (NIFTY TRI_t / NIFTY Price_t)
        / (NIFTY TRI_0 / NIFTY Price_0)

The first common observation is the normalization anchor.
These are estimated hybrid series, not actual BSE TRI.
"""

from __future__ import annotations

import os
from decimal import Decimal
from pathlib import Path

import pandas as pd
import yaml
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


CONFIG = Path("config.yaml")
PRICE_DIR = Path("data/raw/prices")
TRI_DIR = Path("data/raw/tri")
OUTPUT = Path("data/processed/bse_hybrid_tri_long.parquet")
MANIFEST = Path("results/bse_hybrid_manifest.json")

SERIES = {
    "BSE 100 TRI": {
        "benchmark_id": 6,
        "bse_price": "BSE_100_PRICE.csv",
        "nifty_price": "NIFTY_100_PRICE.csv",
        "nifty_tri_prefix": "NIFTY 100_Historical_TR_",
    },
    "BSE 500 TRI": {
        "benchmark_id": 7,
        "bse_price": "BSE_500_PRICE.csv",
        "nifty_price": "NIFTY_500_PRICE.csv",
        "nifty_tri_prefix": "NIFTY 500_Historical_TR_",
    },
}


def load_config():
    with CONFIG.open(encoding="utf-8") as file:
        return yaml.safe_load(file)


def read_price_file(filename, start, end):
    path = PRICE_DIR / filename

    if not path.exists():
        raise FileNotFoundError(path)

    df = pd.read_csv(path)
    required = {"date", "close"}

    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"{filename}: missing columns {missing}"
        )

    df = df[["date", "close"]].copy()

    df["date"] = pd.to_datetime(
        df["date"], format="%Y-%m-%d", errors="coerce"
    )
    df["close"] = pd.to_numeric(
        df["close"], errors="coerce"
    )

    if df["date"].isna().any() or df["close"].isna().any():
        raise ValueError(
            f"{filename}: invalid dates or closing prices."
        )

    if (df["close"] <= 0).any():
        raise ValueError(
            f"{filename}: non-positive closing prices."
        )

    if df["date"].duplicated().any():
        raise ValueError(
            f"{filename}: duplicate dates found."
        )

    df = df[df["date"].between(start, end)].copy()
    return df.sort_values("date").reset_index(drop=True)


def read_nifty_tri(prefix, start, end):
    files = sorted(
        TRI_DIR.glob(f"{prefix}*.csv")
    )

    if not files:
        raise FileNotFoundError(
            f"No TRI files found for prefix {prefix}"
        )

    frames = []

    for path in files:
        df = pd.read_csv(path)

        required = {
            "IndexName",
            "Date",
            "Total Returns Index",
        }

        missing = required - set(df.columns)
        if missing:
            raise ValueError(
                f"{path.name}: missing columns {missing}"
            )

        df = df[
            ["IndexName", "Date", "Total Returns Index"]
        ].copy()

        df["date"] = pd.to_datetime(
            df["Date"],
            format="%d %b %Y",
            errors="coerce",
        )

        df["tri"] = pd.to_numeric(
            df["Total Returns Index"],
            errors="coerce",
        )

        if df["date"].isna().any() or df["tri"].isna().any():
            raise ValueError(
                f"{path.name}: invalid TRI observations."
            )

        if (df["tri"] <= 0).any():
            raise ValueError(
                f"{path.name}: non-positive TRI values."
            )

        frames.append(df[["date", "tri"]])

    combined = pd.concat(frames, ignore_index=True)
    combined = combined[
        combined["date"].between(start, end)
    ].copy()

    # Duplicate dates are permitted only if values agree.
    conflicts = (
        combined.groupby("date")["tri"]
        .agg(["min", "max"])
    )
    conflicts = conflicts[
        (conflicts["max"] - conflicts["min"]).abs() > 0.000001
    ]

    if not conflicts.empty:
        raise ValueError(
            "Conflicting NIFTY TRI observations:\n"
            f"{conflicts.to_string()}"
        )

    combined = combined.drop_duplicates(
        subset=["date"], keep="first"
    )

    return combined.sort_values("date").reset_index(drop=True)


def build_one_series(name, spec, start, end):
    bse = read_price_file(spec["bse_price"], start, end)
    nifty_price = read_price_file(
        spec["nifty_price"], start, end
    )
    nifty_tri = read_nifty_tri(
        spec["nifty_tri_prefix"], start, end
    )

    merged = (
        bse.rename(columns={"close": "bse_price"})
        .merge(
            nifty_price.rename(
                columns={"close": "nifty_price"}
            ),
            on="date",
            how="inner",
            validate="one_to_one",
        )
        .merge(
            nifty_tri,
            on="date",
            how="inner",
            validate="one_to_one",
        )
        .sort_values("date")
        .reset_index(drop=True)
    )

    if merged.empty:
        raise ValueError(f"{name}: no common observations.")

    if len(merged) < 1000:
        raise ValueError(
            f"{name}: only {len(merged)} common observations."
        )

    merged["wedge"] = (
        merged["tri"] / merged["nifty_price"]
    )

    anchor_wedge = float(merged.iloc[0]["wedge"])

    if anchor_wedge <= 0:
        raise ValueError(f"{name}: invalid anchor wedge.")

    merged["normalized_wedge"] = (
        merged["wedge"] / anchor_wedge
    )

    merged["tri_estimated"] = (
        merged["bse_price"] * merged["normalized_wedge"]
    )

    if (
        merged["tri_estimated"].isna().any()
        or (merged["tri_estimated"] <= 0).any()
    ):
        raise ValueError(
            f"{name}: invalid estimated TRI values."
        )

    # Anchor check: estimated TRI must equal BSE price.
    anchor_error = abs(
        merged.iloc[0]["tri_estimated"]
        - merged.iloc[0]["bse_price"]
    )

    if anchor_error > 0.000001:
        raise ValueError(
            f"{name}: anchor normalization failed."
        )

    output = pd.DataFrame({
        "benchmark_id": spec["benchmark_id"],
        "benchmark_name": name,
        "tri_date": merged["date"],
        "tri": merged["tri_estimated"],
        "series_basis": "estimated_hybrid",
        "provisional": True,
    })

    print(
        f"{name}: {len(output)} observations | "
        f"{output['tri_date'].min().date()} to "
        f"{output['tri_date'].max().date()}"
    )
    print(
        f"  Anchor BSE price/TRI: "
        f"{merged.iloc[0]['bse_price']:.4f} / "
        f"{merged.iloc[0]['tri_estimated']:.4f}"
    )
    print(
        f"  Final estimated TRI: "
        f"{merged.iloc[-1]['tri_estimated']:.4f}"
    )
    print(
        f"  Normalized wedge range: "
        f"{merged['normalized_wedge'].min():.6f} to "
        f"{merged['normalized_wedge'].max():.6f}"
    )

    return output


def validate_database_benchmarks(connection):
    rows = connection.execute(
        text("""
            SELECT benchmark_id, name
            FROM dim_benchmark
            WHERE benchmark_id IN (6, 7)
            ORDER BY benchmark_id
        """)
    ).fetchall()

    existing = {
        row.benchmark_id: row.name
        for row in rows
    }

    expected = {
        6: "BSE 100 TRI",
        7: "BSE 500 TRI",
    }

    if existing != expected:
        raise ValueError(
            "Database benchmark definitions do not match. "
            f"Expected {expected}, found {existing}"
        )


def load_into_database(df):
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise EnvironmentError(
            "DATABASE_URL is missing from .env."
        )

    engine = create_engine(database_url)

    records = [
        {
            "benchmark_id": int(row.benchmark_id),
            "tri_date": row.tri_date.date(),
            "tri": Decimal(str(row.tri)),
        }
        for row in df.itertuples(index=False)
    ]

    try:
        with engine.begin() as connection:
            validate_database_benchmarks(connection)

            existing_rows = connection.execute(
                text("""
                    SELECT benchmark_id, tri_date, tri
                    FROM fact_benchmark_tri
                    WHERE benchmark_id IN (6, 7)
                """)
            ).fetchall()

            existing = {
                (row.benchmark_id, row.tri_date):
                    Decimal(str(row.tri))
                for row in existing_rows
            }

            for record in records:
                key = (
                    record["benchmark_id"],
                    record["tri_date"],
                )

                if key in existing:
                    if existing[key] != record["tri"]:
                        raise ValueError(
                            f"Database conflict for {key}: "
                            f"existing={existing[key]}, "
                            f"incoming={record['tri']}"
                        )

            new_records = [
                record for record in records
                if (
                    record["benchmark_id"],
                    record["tri_date"],
                ) not in existing
            ]

            if new_records:
                connection.execute(
                    text("""
                        INSERT INTO fact_benchmark_tri
                            (benchmark_id, tri_date, tri)
                        VALUES
                            (:benchmark_id, :tri_date, :tri)
                    """),
                    new_records,
                )

            final_count = connection.execute(
                text("""
                    SELECT COUNT(*)
                    FROM fact_benchmark_tri
                    WHERE benchmark_id IN (6, 7)
                      AND tri_date BETWEEN :start AND :end
                """),
                {
                    "start": min(r["tri_date"] for r in records),
                    "end": max(r["tri_date"] for r in records),
                },
            ).scalar_one()

            if final_count != len(records):
                raise ValueError(
                    f"Expected {len(records)} rows in the "
                    f"research window, found {final_count}."
                )

            print(
                f"Existing observations: {len(existing)}"
            )
            print(
                f"New observations inserted: {len(new_records)}"
            )
            print(
                f"Final observations in research window: "
                f"{final_count}"
            )

    finally:
        engine.dispose()


def main():
    load_dotenv()
    config = load_config()

    start = pd.Timestamp(config["window"]["start"])
    end = pd.Timestamp(config["window"]["end"])

    print("=== PROVISIONAL BSE HYBRID TRI INGESTION ===")
    print(f"Research window: {start.date()} to {end.date()}")

    frames = []

    for name, spec in SERIES.items():
        frames.append(
            build_one_series(name, spec, start, end)
        )

    result = pd.concat(frames, ignore_index=True)
    result = result.sort_values(
        ["benchmark_id", "tri_date"]
    ).reset_index(drop=True)

    counts = result.groupby("benchmark_id").size().to_dict()

    if counts != {6: counts.get(6), 7: counts.get(7)}:
        raise ValueError("Unexpected benchmark IDs.")

    if counts.get(6, 0) < 1000 or counts.get(7, 0) < 1000:
        raise ValueError(f"Incomplete benchmark coverage: {counts}")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    result.to_parquet(OUTPUT, index=False)

    manifest = {
        "series_basis": "estimated_hybrid",
        "provisional": True,
        "method": (
            "BSE price index multiplied by matching "
            "NIFTY TRI/NIFTY price wedge normalized "
            "to the first common observation."
        ),
        "research_window": {
            "start": str(start.date()),
            "end": str(end.date()),
        },
        "observations": {
            str(key): int(value)
            for key, value in counts.items()
        },
        "source_files": {
            "prices": [
                "BSE_100_PRICE.csv",
                "BSE_500_PRICE.csv",
                "NIFTY_100_PRICE.csv",
                "NIFTY_500_PRICE.csv",
            ],
            "tri_prefixes": [
                "NIFTY 100_Historical_TR_",
                "NIFTY 500_Historical_TR_",
            ],
        },
    }

    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    pd.Series(manifest).to_json(
        MANIFEST, indent=2, force_ascii=False
    )

    print(f"\nProcessed Parquet saved: {OUTPUT}")
    print(f"Manifest saved: {MANIFEST}")

    load_into_database(result)

    print("\nProvisional BSE hybrid TRI ingestion completed.")


if __name__ == "__main__":
    main()
