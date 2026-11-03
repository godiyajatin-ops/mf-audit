
"""Load the frozen mutual-fund universe and processed data into PostgreSQL."""

from __future__ import annotations

import os
from decimal import Decimal
from pathlib import Path

import pandas as pd
import yaml
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

CONFIG = Path("config.yaml")
UNIVERSE = Path("config/universe.csv")
BENCHMARK_MAP = Path("docs/benchmark_confirmation.csv")
SCHEME_MASTER = Path("data/processed/scheme_master.parquet")
NAV_FILE = Path("data/processed/nav_long.parquet")
TRI_FILE = Path("data/processed/benchmark_tri_long.parquet")

BENCHMARKS = {
    1: "NIFTY 50 TRI",
    2: "NIFTY 100 TRI",
    3: "NIFTY 500 TRI",
    4: "NIFTY MIDCAP 150 TRI",
    5: "NIFTY NEXT 50 TRI",
    6: "BSE 100 TRI",
    7: "BSE 500 TRI",
}


def read_inputs():
    with CONFIG.open(encoding="utf-8") as f:
        config = yaml.safe_load(f)

    start = pd.Timestamp(config["window"]["start"])
    end = pd.Timestamp(config["window"]["end"])

    universe = pd.read_csv(UNIVERSE)
    benchmark_map = pd.read_csv(BENCHMARK_MAP)
    master = pd.read_parquet(SCHEME_MASTER)
    nav = pd.read_parquet(NAV_FILE)
    tri = pd.read_parquet(TRI_FILE)

    # Scheme metadata: frozen universe joined to AMFI master.
    schemes = universe.merge(
        master[["scheme_code", "option"]],
        on="scheme_code",
        how="left",
        validate="one_to_one",
    )

    if schemes["option"].isna().any():
        raise ValueError("Some universe schemes are missing from scheme master.")

    # Factsheet benchmark takes precedence over the default benchmark.
    schemes = schemes.merge(
        benchmark_map[
            ["scheme_code", "default_benchmark", "factsheet_stated_benchmark"]
        ],
        on="scheme_code",
        how="left",
        validate="one_to_one",
    )

    schemes["benchmark_name"] = (
        schemes["factsheet_stated_benchmark"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    schemes["benchmark_confirmed"] = schemes["benchmark_name"].ne("")

    schemes.loc[
        ~schemes["benchmark_confirmed"], "benchmark_name"
    ] = schemes.loc[
        ~schemes["benchmark_confirmed"], "default_benchmark"
    ]

    def benchmark_id(name):
        normalized = str(name).strip().upper()
        normalized = normalized.replace(" TOTAL RETURNS INDEX", "")
        normalized = normalized.replace(" TRI", "")
        normalized = " ".join(normalized.split())

        for bid, full_name in BENCHMARKS.items():
            if normalized == full_name.replace(" TRI", ""):
                return bid

        raise ValueError(f"Unknown benchmark: {name}")

    schemes["benchmark_id"] = schemes["benchmark_name"].map(benchmark_id)

    if schemes["scheme_code"].nunique() != 32:
        raise ValueError("Expected exactly 32 unique schemes.")

    if schemes["benchmark_id"].isna().any():
        raise ValueError("Missing benchmark ID for one or more schemes.")

    # Restrict observations to the approved window.
    nav["nav_date"] = pd.to_datetime(nav["nav_date"])
    nav = nav[nav["nav_date"].between(start, end)].copy()

    tri["tri_date"] = pd.to_datetime(tri["tri_date"])
    tri = tri[tri["tri_date"].between(start, end)].copy()

    if nav.duplicated(["scheme_code", "nav_date"]).any():
        raise ValueError("Duplicate scheme/date keys found in NAV data.")

    if tri.duplicated(["benchmark_id", "tri_date"]).any():
        raise ValueError("Duplicate benchmark/date keys found in TRI data.")

    if nav["scheme_code"].nunique() != 32:
        raise ValueError("NAV data does not cover all 32 schemes.")

    return config, schemes, nav, tri


def decimal_value(value):
    return Decimal(str(value))


def main():
    load_dotenv()

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise EnvironmentError("DATABASE_URL is missing from .env.")

    config, schemes, nav, tri = read_inputs()

    rf_rate = Decimal(str(config["rf"]["fallback_constant"]))

    engine = create_engine(database_url)

    print("=== STAGE A1 DATABASE LOADING ===")
    print(f"Schemes: {len(schemes)}")
    print(f"NAV observations: {len(nav)}")
    print(f"TRI observations: {len(tri)}")
    print(f"Risk-free fallback: {rf_rate}")

    benchmark_records = [
        {"benchmark_id": bid, "name": name}
        for bid, name in BENCHMARKS.items()
    ]

    scheme_records = []
    for row in schemes.itertuples(index=False):
        scheme_records.append({
            "scheme_code": int(row.scheme_code),
            "scheme_name": str(row.scheme_name),
            "amc": str(row.amc),
            "category": str(row.category),
            "plan": str(row.plan),
            "option": str(row.option),
            "pair_id": int(row.pair_id),
            "is_passive": bool(row.is_passive),
            "benchmark_id": int(row.benchmark_id),
            "benchmark_confirmed": bool(row.benchmark_confirmed),
            "inception": None,
        })

    nav_records = [
        {
            "scheme_code": int(row.scheme_code),
            "nav_date": row.nav_date.date(),
            "nav": decimal_value(row.nav),
        }
        for row in nav.itertuples(index=False)
    ]

    tri_records = [
        {
            "benchmark_id": int(row.benchmark_id),
            "tri_date": row.tri_date.date(),
            "tri": decimal_value(row.tri),
        }
        for row in tri.itertuples(index=False)
    ]

    # Use actual NAV observation dates for the constant RF series.
    rf_dates = sorted(nav["nav_date"].dt.date.unique())
    rf_records = [
        {"rf_date": date, "annual_rate": rf_rate}
        for date in rf_dates
    ]

    try:
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO dim_benchmark (benchmark_id, name)
                    VALUES (:benchmark_id, :name)
                    ON CONFLICT (benchmark_id)
                    DO UPDATE SET name = EXCLUDED.name
                """),
                benchmark_records,
            )

            conn.execute(
                text("""
                    INSERT INTO dim_scheme (
                        scheme_code, scheme_name, amc, category,
                        plan, option, pair_id, is_passive,
                        benchmark_id, benchmark_confirmed, inception
                    )
                    VALUES (
                        :scheme_code, :scheme_name, :amc, :category,
                        :plan, :option, :pair_id, :is_passive,
                        :benchmark_id, :benchmark_confirmed, :inception
                    )
                    ON CONFLICT (scheme_code)
                    DO UPDATE SET
                        scheme_name = EXCLUDED.scheme_name,
                        amc = EXCLUDED.amc,
                        category = EXCLUDED.category,
                        plan = EXCLUDED.plan,
                        option = EXCLUDED.option,
                        pair_id = EXCLUDED.pair_id,
                        is_passive = EXCLUDED.is_passive,
                        benchmark_id = EXCLUDED.benchmark_id,
                        benchmark_confirmed = EXCLUDED.benchmark_confirmed
                """),
                scheme_records,
            )

            conn.execute(
                text("""
                    INSERT INTO fact_nav (scheme_code, nav_date, nav)
                    VALUES (:scheme_code, :nav_date, :nav)
                    ON CONFLICT (scheme_code, nav_date)
                    DO UPDATE SET nav = EXCLUDED.nav
                """),
                nav_records,
            )

            conn.execute(
                text("""
                    INSERT INTO fact_benchmark_tri (
                        benchmark_id, tri_date, tri
                    )
                    VALUES (:benchmark_id, :tri_date, :tri)
                    ON CONFLICT (benchmark_id, tri_date)
                    DO UPDATE SET tri = EXCLUDED.tri
                """),
                tri_records,
            )

            conn.execute(
                text("""
                    INSERT INTO fact_rf (rf_date, annual_rate)
                    VALUES (:rf_date, :annual_rate)
                    ON CONFLICT (rf_date)
                    DO UPDATE SET annual_rate = EXCLUDED.annual_rate
                """),
                rf_records,
            )

            # Final database counts.
            for table in (
                "dim_benchmark",
                "dim_scheme",
                "fact_nav",
                "fact_benchmark_tri",
                "fact_rf",
            ):
                count = conn.execute(
                    text(f"SELECT COUNT(*) FROM {table}")
                ).scalar_one()
                print(f"{table}: {count:,} rows")

            # Confirm all frozen schemes were loaded.
            loaded_schemes = conn.execute(
                text("SELECT COUNT(*) FROM dim_scheme")
            ).scalar_one()

            if loaded_schemes != 32:
                raise ValueError(
                    f"Expected 32 schemes in database, found {loaded_schemes}."
                )

    finally:
        engine.dispose()

    print("\nStage A1 database loading completed.")


if __name__ == "__main__":
    main()
