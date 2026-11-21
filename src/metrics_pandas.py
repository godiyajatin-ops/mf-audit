
from __future__ import annotations

from pathlib import Path
import sys
import os

import numpy as np
import pandas as pd
import yaml
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)

load_dotenv(ROOT / ".env")

_engine = None

def get_engine():
    global _engine
    if _engine is None:
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            raise RuntimeError("DATABASE_URL not found in .env")
        _engine = create_engine(database_url)
    return _engine

with open(ROOT / "config.yaml", "r", encoding="utf-8") as f:
    CONFIG = yaml.safe_load(f)

WINDOW_END = pd.Timestamp(CONFIG["window"]["end"])
TRADING_DAYS = 252
SQRT_252 = np.sqrt(TRADING_DAYS)



def fetch_table(table_name: str) -> pd.DataFrame:
    """Read a raw source table from PostgreSQL."""
    allowed = {
        "dim_scheme",
        "fact_nav",
        "fact_benchmark_tri",
        "fact_rf",
    }

    if table_name not in allowed:
        raise ValueError(f"Unexpected table: {table_name}")

    with get_engine().connect() as conn:
        return pd.read_sql(
            text(f"SELECT * FROM {table_name}"),
            conn,
        )


def calculate_drawdown(nav_series: pd.Series):
    """
    Calculate maximum drawdown within the evaluation window.

    Returns:
        max_drawdown, peak_date, trough_date
    """
    if nav_series.empty:
        return np.nan, pd.NaT, pd.NaT

    running_peak = nav_series.cummax()
    drawdown = nav_series / running_peak - 1.0

    trough_date = drawdown.idxmin()
    max_drawdown = float(drawdown.loc[trough_date])

    peak_value = running_peak.loc[trough_date]

    # Use the latest date at which the running peak was reached.
    peak_candidates = nav_series.loc[:trough_date]
    peak_candidates = peak_candidates[
        peak_candidates == peak_value
    ]

    peak_date = peak_candidates.index.max()

    return max_drawdown, peak_date, trough_date


def calculate_nav_metrics(
    nav_window: pd.DataFrame,
    rf: pd.Series,
) -> dict:
    """Calculate NAV-based metrics for one scheme-window."""

    nav_window = nav_window.sort_values("nav_date").copy()
    nav_window = nav_window.set_index("nav_date")

    nav = nav_window["nav"].astype(float)

    returns = nav.pct_change().dropna()

    if len(returns) == 0:
        raise ValueError("No valid NAV returns in evaluation window")

    # Exact-date risk-free join. Missing RF is an error, never zero.
    rf_window = rf.reindex(returns.index)

    if rf_window.isna().any():
        missing_dates = rf_window[rf_window.isna()].index.tolist()
        raise ValueError(
            f"Missing risk-free observations: {missing_dates[:5]}"
        )

    daily_rf = rf_window.astype(float) / TRADING_DAYS
    excess = returns - daily_rf

    first_nav = float(nav.iloc[0])
    last_nav = float(nav.iloc[-1])

    elapsed_days = (nav.index[-1] - nav.index[0]).days

    if elapsed_days <= 0:
        raise ValueError("Invalid date range for CAGR")

    cagr = (
        (last_nav / first_nav) ** (365.25 / elapsed_days)
    ) - 1.0

    daily_vol = returns.std(ddof=1)
    vol_ann = daily_vol * SQRT_252

    excess_std = excess.std(ddof=1)

    sharpe = (
        excess.mean() / excess_std * SQRT_252
        if pd.notna(excess_std) and excess_std != 0
        else np.nan
    )

    downside_deviation = np.sqrt(
        np.mean(np.minimum(excess.to_numpy(), 0.0) ** 2)
    )

    sortino = (
        excess.mean() / downside_deviation * SQRT_252
        if downside_deviation != 0
        else np.nan
    )

    max_dd, dd_start, dd_end = calculate_drawdown(nav)

    return {
        "cagr": cagr,
        "vol_ann": vol_ann,
        "sharpe": sharpe,
        "sortino": sortino,
        "max_dd": max_dd,
        "max_dd_start": dd_start,
        "max_dd_end": dd_end,
        "n_obs": len(returns),
        "start_date": nav.index.min(),
        "end_date": nav.index.max(),
    }


def calculate_benchmark_metrics(
    nav_window: pd.DataFrame,
    tri: pd.DataFrame,
    benchmark_id: int,
) -> dict:
    """Calculate benchmark-relative metrics using raw TRI data."""

    fund = nav_window[
        ["nav_date", "nav"]
    ].copy()

    benchmark = tri[
        tri["benchmark_id"] == benchmark_id
    ][["tri_date", "tri"]].copy()

    benchmark = benchmark.rename(
        columns={"tri_date": "nav_date"}
    )

    aligned = fund.merge(
        benchmark,
        on="nav_date",
        how="inner",
        validate="one_to_one",
    ).sort_values("nav_date")

    aligned = aligned.set_index("nav_date")

    aligned_returns = aligned.pct_change().dropna()

    if aligned_returns.empty:
        return {
            "te_ann": np.nan,
            "info_ratio": np.nan,
            "up_capture": np.nan,
            "down_capture": np.nan,
        }

    fund_return = aligned_returns["nav"]
    benchmark_return = aligned_returns["tri"]

    active_return = fund_return - benchmark_return

    daily_te = active_return.std(ddof=1)
    te_ann = daily_te * SQRT_252

    info_ratio = (
        active_return.mean() * TRADING_DAYS / te_ann
        if pd.notna(te_ann) and te_ann != 0
        else np.nan
    )

    positive = benchmark_return > 0
    negative = benchmark_return < 0

    positive_bench_mean = benchmark_return[positive].mean()
    negative_bench_mean = benchmark_return[negative].mean()

    up_capture = (
        fund_return[positive].mean() / positive_bench_mean
        if pd.notna(positive_bench_mean)
        and positive_bench_mean != 0
        else np.nan
    )

    down_capture = (
        fund_return[negative].mean() / negative_bench_mean
        if pd.notna(negative_bench_mean)
        and negative_bench_mean != 0
        else np.nan
    )

    return {
        "te_ann": te_ann,
        "info_ratio": info_ratio,
        "up_capture": up_capture,
        "down_capture": down_capture,
    }


def main():
    print("Loading raw database tables...")

    schemes = fetch_table("dim_scheme")
    nav = fetch_table("fact_nav")
    tri = fetch_table("fact_benchmark_tri")
    rf_data = fetch_table("fact_rf")

    nav["nav_date"] = pd.to_datetime(nav["nav_date"])
    tri["tri_date"] = pd.to_datetime(tri["tri_date"])
    rf_data["rf_date"] = pd.to_datetime(rf_data["rf_date"])

    nav["nav"] = pd.to_numeric(nav["nav"])
    tri["tri"] = pd.to_numeric(tri["tri"])
    rf_data["annual_rate"] = pd.to_numeric(
        rf_data["annual_rate"]
    )

    rf = (
        rf_data.set_index("rf_date")["annual_rate"]
        .sort_index()
    )

    records = []

    windows = {
        "FULL": None,
        "3Y": 3,
        "1Y": 1,
    }

    print(
        f"Loaded {len(schemes)} schemes, "
        f"{len(nav)} NAV rows, "
        f"{len(tri)} TRI rows, "
        f"{len(rf_data)} RF rows."
    )

    for scheme in schemes.itertuples(index=False):

        scheme_nav = nav[
            nav["scheme_code"] == scheme.scheme_code
        ].sort_values("nav_date").copy()

        scheme_nav = scheme_nav[
            scheme_nav["nav_date"] <= WINDOW_END
        ]

        if scheme_nav.empty:
            raise ValueError(
                f"No NAV data for scheme {scheme.scheme_code}"
            )

        first_nav_date = scheme_nav["nav_date"].min()
        end_date = scheme_nav["nav_date"].max()

        for window_label, years in windows.items():

            if years is None:
                window_start = first_nav_date
            else:
                window_start = (
                    end_date - pd.DateOffset(years=years)
                )

            nav_window = scheme_nav[
                (scheme_nav["nav_date"] >= window_start)
                & (scheme_nav["nav_date"] <= end_date)
            ].copy()

            nav_metrics = calculate_nav_metrics(
                nav_window,
                rf,
            )

            benchmark_metrics = calculate_benchmark_metrics(
                nav_window,
                tri,
                scheme.benchmark_id,
            )

            record = {
                "scheme_code": scheme.scheme_code,
                "window_label": window_label,
                **nav_metrics,
                **benchmark_metrics,
            }

            records.append(record)

        print(
            f"Processed scheme {scheme.scheme_code}"
        )

    output = pd.DataFrame(records)

    output = output.sort_values(
        ["scheme_code", "window_label"]
    ).reset_index(drop=True)

    output_path = RESULTS / "metrics_pandas.csv"
    output.to_csv(output_path, index=False, float_format="%.12f")

    print("\nPandas calculation completed.")
    print(f"Records: {len(output)}")
    print(f"Schemes: {output['scheme_code'].nunique()}")
    print(f"Windows: {output['window_label'].nunique()}")
    print(f"Output: {output_path}")

    if len(output) != 96:
        raise AssertionError(
            f"Expected 96 records, got {len(output)}"
        )

    print("\nSample results:")
    print(
        output[
            output["scheme_code"].isin([100377, 103215])
        ].to_string(index=False)
    )


if __name__ == "__main__":
    try:
        main()
    finally:
        if _engine is not None:
            _engine.dispose()
