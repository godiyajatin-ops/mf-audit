"""Validate, combine and load Nifty Total Returns Index data."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pandas as pd
import yaml
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


CONFIG = Path("config.yaml")
RAW_DIR = Path("data/raw/tri")
OUTPUT = Path("data/processed/benchmark_tri_long.parquet")

BENCHMARKS = {
    "NIFTY 50": 1,
    "NIFTY 100": 2,
    "NIFTY 500": 3,
    "NIFTY MIDCAP 150": 4,
    "NIFTY NEXT 50": 5,
}

REQUIRED_COLUMNS = {
    "IndexName",
    "Date",
    "Total Returns Index",
}


def load_config():
    with CONFIG.open(encoding="utf-8") as file:
        return yaml.safe_load(file)


def read_tri_files(start, end):
    files = sorted(RAW_DIR.glob("*.csv"))

    if not files:
        raise FileNotFoundError("No TRI CSV files found.")

    frames = []

    for file in files:
        df = pd.read_csv(file)

        missing = REQUIRED_COLUMNS - set(df.columns)

        if missing:
            raise ValueError(
                f"{file.name}: missing columns {missing}"
            )

        df = df[
            ["IndexName", "Date", "Total Returns Index"]
        ].copy()

        df["Date"] = pd.to_datetime(
            df["Date"],
            format="%d %b %Y",
            errors="coerce",
        )

        df["Total Returns Index"] = pd.to_numeric(
            df["Total Returns Index"],
            errors="coerce",
        )

        invalid = (
            df["Date"].isna()
            | df["Total Returns Index"].isna()
            | (df["Total Returns Index"] <= 0)
        )

        if invalid.any():
            raise ValueError(
                f"{file.name}: {invalid.sum()} invalid observations."
            )

        unexpected = set(df["IndexName"].unique()) - set(BENCHMARKS)

        if unexpected:
            raise ValueError(
                f"{file.name}: unexpected index names {unexpected}"
            )

        frames.append(df)

        print(
            f"Read {file.name}: {len(df)} observations"
        )

    combined = pd.concat(frames, ignore_index=True)

    # Restrict observations to the approved research window.
    combined = combined[
        combined["Date"].between(start, end)
    ].copy()

    # Check duplicate observations before removing them.
    duplicate_keys = combined.duplicated(
        ["IndexName", "Date"],
        keep=False,
    )

    duplicates = combined.loc[duplicate_keys]

    if not duplicates.empty:
        conflicts = (
            duplicates.groupby(
                ["IndexName", "Date"]
            )["Total Returns Index"]
            .agg(["min", "max"])
        )

        conflicts = conflicts[
            (conflicts["max"] - conflicts["min"]).abs() > 0.000001
        ]

        if not conflicts.empty:
            raise ValueError(
                "Conflicting TRI values found:\n"
                f"{conflicts.to_string()}"
            )

    combined = combined.drop_duplicates(
        ["IndexName", "Date"]
    )

    combined["benchmark_id"] = (
        combined["IndexName"].map(BENCHMARKS)
    )

    combined = combined.rename(
        columns={
            "IndexName": "benchmark_name",
            "Date": "tri_date",
            "Total Returns Index": "tri",
        }
    )

    combined = combined[
        ["benchmark_id", "benchmark_name", "tri_date", "tri"]
    ]

    combined = combined.sort_values(
        ["benchmark_id", "tri_date"]
    ).reset_index(drop=True)

    expected = set(BENCHMARKS.values())
    actual = set(combined["benchmark_id"].unique())

    if actual != expected:
        raise ValueError(
            f"Benchmark coverage incomplete. "
            f"Expected {expected}, found {actual}"
        )

    return combined


def validate_database_benchmarks(connection):
    rows = connection.execute(
        text("""
            SELECT benchmark_id, name
            FROM dim_benchmark
            ORDER BY benchmark_id
        """)
    ).fetchall()

    existing = {
        row.benchmark_id: row.name
        for row in rows
    }

    for name, benchmark_id in BENCHMARKS.items():
        expected_name = f"{name} TRI"

        if existing.get(benchmark_id) != expected_name:
            raise ValueError(
                f"Benchmark ID {benchmark_id} mismatch. "
                f"Expected '{expected_name}', "
                f"found '{existing.get(benchmark_id)}'."
            )


def load_into_database(df):
    database_url = __import__("os").getenv("DATABASE_URL")

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

            # Check existing observations before inserting.
            existing_rows = connection.execute(
                text("""
                    SELECT benchmark_id, tri_date, tri
                    FROM fact_benchmark_tri
                    WHERE benchmark_id BETWEEN 1 AND 5
                """)
            ).fetchall()

            existing = {
                (row.benchmark_id, row.tri_date): Decimal(str(row.tri))
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
                record
                for record in records
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

            print(
                f"Database records already present: {len(existing)}"
            )
            print(
                f"New observations inserted: {len(new_records)}"
            )

            final_count = connection.execute(
                text("""
                    SELECT COUNT(*)
                    FROM fact_benchmark_tri
                    WHERE benchmark_id BETWEEN 1 AND 5
                """)
            ).scalar_one()

            print(
                f"Final database observations: {final_count}"
            )

            if final_count != len(records):
                raise ValueError(
                    f"Expected {len(records)} database records, "
                    f"found {final_count}."
                )

    finally:
        engine.dispose()


def main():
    load_dotenv()

    config = load_config()

    start = pd.Timestamp(
        config["window"]["start"]
    )
    end = pd.Timestamp(
        config["window"]["end"]
    )

    print("=== TRI INGESTION ===")
    print(f"Research window: {start.date()} to {end.date()}")

    tri = read_tri_files(start, end)

    print("\n=== BENCHMARK SUMMARY ===")

    for benchmark_id, group in tri.groupby("benchmark_id"):
        print(
            f"{group['benchmark_name'].iloc[0]}: "
            f"{len(group)} observations | "
            f"{group['tri_date'].min().date()} to "
            f"{group['tri_date'].max().date()}"
        )

    print(f"\nTotal unique observations: {len(tri)}")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    tri.to_parquet(OUTPUT, index=False)

    print(f"Processed Parquet saved: {OUTPUT}")

    load_into_database(tri)

    print("\nA1.6 TRI ingestion completed successfully.")


if __name__ == "__main__":
    main()