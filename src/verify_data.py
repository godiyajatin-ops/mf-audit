
"""Stage A1 data-quality validator for mf-audit."""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import yaml
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"

load_dotenv(ROOT / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL missing from project .env")

engine = create_engine(DATABASE_URL)


def load_config():
    with open(ROOT / "config.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def add_check(report, check, status, detail, scheme_code=None):
    report.append({
        "check": check,
        "scheme_code": scheme_code,
        "status": status,
        "detail": str(detail),
    })


def load_data():
    queries = {
        "schemes": """
            SELECT scheme_code, scheme_name, category, plan,
                   pair_id, benchmark_id, benchmark_confirmed
            FROM dim_scheme
            ORDER BY scheme_code
        """,
        "nav": """
            SELECT scheme_code, nav_date, nav
            FROM fact_nav
            ORDER BY scheme_code, nav_date
        """,
        "tri": """
            SELECT benchmark_id, tri_date, tri
            FROM fact_benchmark_tri
            ORDER BY benchmark_id, tri_date
        """,
        "rf": """
            SELECT rf_date, annual_rate
            FROM fact_rf
            ORDER BY rf_date
        """,
    }

    data = {}

    with engine.connect() as conn:
        for name, query in queries.items():
            data[name] = pd.read_sql(text(query), conn)

    return data


def validate(data, config):
    report = []
    schemes = data["schemes"]
    nav = data["nav"]
    tri = data["tri"]
    rf = data["rf"]

    start = pd.Timestamp(config["window"]["start"])
    end = pd.Timestamp(config["window"]["end"])

    # --------------------------------------------------
    # 1. Universe checks
    # --------------------------------------------------

    add_check(
        report,
        "scheme_universe",
        "PASS" if len(schemes) == 32 else "FAIL",
        f"Expected 32 schemes; found {len(schemes)}",
    )

    add_check(
        report,
        "nav_scheme_count",
        "PASS" if nav["scheme_code"].nunique() == 32 else "FAIL",
        f"Found {nav['scheme_code'].nunique()} distinct NAV schemes",
    )

    # --------------------------------------------------
    # 2. NAV integrity
    # --------------------------------------------------

    duplicate_nav = nav.duplicated(
        ["scheme_code", "nav_date"]
    ).sum()

    add_check(
        report,
        "nav_duplicates",
        "FAIL" if duplicate_nav else "PASS",
        f"Duplicate scheme/date rows: {duplicate_nav}",
    )

    invalid_nav = (
        nav["nav"].isna() | (nav["nav"] <= 0)
    ).sum()

    add_check(
        report,
        "nav_validity",
        "FAIL" if invalid_nav else "PASS",
        f"Null or non-positive NAV values: {invalid_nav}",
    )

    # --------------------------------------------------
    # 3. Benchmark TRI integrity
    # --------------------------------------------------

    duplicate_tri = tri.duplicated(
        ["benchmark_id", "tri_date"]
    ).sum()

    invalid_tri = (
        tri["tri"].isna() | (tri["tri"] <= 0)
    ).sum()

    add_check(
        report,
        "tri_duplicates",
        "FAIL" if duplicate_tri else "PASS",
        f"Duplicate benchmark/date rows: {duplicate_tri}",
    )

    add_check(
        report,
        "tri_validity",
        "FAIL" if invalid_tri else "PASS",
        f"Null or non-positive TRI values: {invalid_tri}",
    )

    monotonic_failures = []

    for benchmark_id, group in tri.groupby("benchmark_id"):
        dates = pd.to_datetime(group["tri_date"])

        if not dates.is_monotonic_increasing or dates.duplicated().any():
            monotonic_failures.append(benchmark_id)

    add_check(
        report,
        "tri_date_order",
        "FAIL" if monotonic_failures else "PASS",
        f"Benchmark IDs with invalid date ordering: {monotonic_failures}",
    )

    # --------------------------------------------------
    # 4. Risk-free integrity
    # --------------------------------------------------

    invalid_rf = (
        rf["annual_rate"].isna()
        | (rf["annual_rate"] < 0)
        | (rf["annual_rate"] > 0.20)
    ).sum()

    add_check(
        report,
        "risk_free_validity",
        "FAIL" if invalid_rf else "PASS",
        f"Invalid risk-free observations: {invalid_rf}",
    )

    add_check(
        report,
        "risk_free_availability",
        "FAIL" if rf.empty else "PASS",
        f"Risk-free observations: {len(rf)}",
    )

    # --------------------------------------------------
    # 5. Benchmark inventory
    # --------------------------------------------------

    benchmark_counts = (
        tri.groupby("benchmark_id")
        .size()
        .to_dict()
    )

    # --------------------------------------------------
    # 6. Scheme-level coverage
    # --------------------------------------------------

    coverage = []

    for _, scheme in schemes.iterrows():
        code = int(scheme["scheme_code"])
        benchmark_id = int(scheme["benchmark_id"])

        scheme_nav = nav[
            nav["scheme_code"] == code
        ].copy()

        scheme_nav["nav_date"] = pd.to_datetime(
            scheme_nav["nav_date"]
        )

        scheme_nav = scheme_nav.sort_values("nav_date")

        benchmark_dates = set(
            pd.to_datetime(
                tri.loc[
                    tri["benchmark_id"] == benchmark_id,
                    "tri_date",
                ]
            )
        )

        nav_dates = scheme_nav["nav_date"]

        nav_rows = len(scheme_nav)
        aligned_rows = sum(
            date in benchmark_dates for date in nav_dates
        )

        alignment_pct = (
            100 * aligned_rows / nav_rows
            if nav_rows else 0
        )

        first_nav = nav_dates.min() if nav_rows else None
        last_nav = nav_dates.max() if nav_rows else None

        aligned_dates = [
            date for date in nav_dates
            if date in benchmark_dates
        ]

        first_aligned = (
            min(aligned_dates) if aligned_dates else None
        )

        last_aligned = (
            max(aligned_dates) if aligned_dates else None
        )

        coverage.append({
            "scheme_code": code,
            "scheme_name": scheme["scheme_name"],
            "category": scheme["category"],
            "plan": scheme["plan"],
            "benchmark_id": benchmark_id,
            "benchmark_confirmed": scheme["benchmark_confirmed"],
            "nav_rows": nav_rows,
            "aligned_rows": aligned_rows,
            "alignment_pct": round(alignment_pct, 2),
            "first_nav_date": first_nav,
            "last_nav_date": last_nav,
            "first_aligned_date": first_aligned,
            "last_aligned_date": last_aligned,
        })

        # NAV coverage window
        if not nav_rows:
            add_check(
                report, "nav_coverage", "FAIL",
                "No NAV observations", code
            )
        else:
            date_ok = (
                first_nav <= start + pd.Timedelta(days=10)
                and last_nav >= end - pd.Timedelta(days=7)
            )

            add_check(
                report,
                "nav_coverage",
                "PASS" if date_ok else "FAIL",
                f"First={first_nav.date()}, last={last_nav.date()}",
                code,
            )

        # Missing benchmark data is a documented limitation.
        benchmark_rows = benchmark_counts.get(benchmark_id, 0)

        if benchmark_rows == 0:
            add_check(
                report,
                "benchmark_coverage",
                "WARN",
                f"Benchmark ID {benchmark_id} has no TRI observations; "
                "benchmark-relative metrics unavailable",
                code,
            )
        else:
            add_check(
                report,
                "benchmark_coverage",
                "PASS",
                f"Benchmark ID {benchmark_id}: {benchmark_rows} TRI rows",
                code,
            )

            add_check(
                report,
                "alignment",
                "PASS" if alignment_pct >= 98 else "FAIL",
                f"Alignment={alignment_pct:.2f}%",
                code,
            )

        # NAV gaps
        if nav_rows > 1:
            gaps = nav_dates.diff().dt.days.dropna()
            max_gap = int(gaps.max())

            if max_gap > 10:
                status = "FAIL"
            elif max_gap > 5:
                status = "WARN"
            else:
                status = "PASS"

            add_check(
                report,
                "nav_gap",
                status,
                f"Maximum calendar-day gap: {max_gap}",
                code,
            )

        # Daily NAV jumps
        if nav_rows > 1:
            returns = scheme_nav["nav"].pct_change()
            jumps = int((returns.abs() > 0.10).sum())

            add_check(
                report,
                "nav_daily_jump",
                "WARN" if jumps else "PASS",
                f"Daily NAV changes above 10%: {jumps}",
                code,
            )

    # --------------------------------------------------
    # 7. Direct-Regular pair integrity
    # --------------------------------------------------

    pair_failures = []

    for pair_id, group in schemes.groupby("pair_id"):
        plans = group["plan"].astype(str).str.strip().str.lower()

        if (
            len(group) != 2
            or (plans == "direct").sum() != 1
            or (plans == "regular").sum() != 1
        ):
            pair_failures.append(pair_id)

    add_check(
        report,
        "direct_regular_pairs",
        "FAIL" if pair_failures else "PASS",
        f"Invalid pair IDs: {pair_failures}",
    )

    return pd.DataFrame(report), pd.DataFrame(coverage)


def write_outputs(report, coverage):
    RESULTS.mkdir(parents=True, exist_ok=True)

    report.to_csv(
        RESULTS / "dq_report.csv",
        index=False,
    )

    coverage.to_csv(
        RESULTS / "coverage.csv",
        index=False,
        date_format="%Y-%m-%d",
    )

    counts = report["status"].value_counts().to_dict()

    lines = [
        "# MF-Audit Data Quality Report",
        "",
        f"- Total checks: {len(report)}",
        f"- PASS: {counts.get('PASS', 0)}",
        f"- WARN: {counts.get('WARN', 0)}",
        f"- FAIL: {counts.get('FAIL', 0)}",
        "",
        "## Warnings and failures",
        "",
    ]

    exceptions = report[
        report["status"].isin(["WARN", "FAIL"])
    ]

    if exceptions.empty:
        lines.append("No warnings or failures.")
    else:
        for _, row in exceptions.iterrows():
            lines.append(
                f"- **{row['status']}** | {row['check']} "
                f"| Scheme: {row['scheme_code']} "
                f"| {row['detail']}"
            )

    (RESULTS / "dq_report.md").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def main():
    config = load_config()
    data = load_data()

    report, coverage = validate(data, config)

    write_outputs(report, coverage)

    counts = report["status"].value_counts().to_dict()

    print("\n=== MF-AUDIT DATA QUALITY REPORT ===")
    print(f"PASS: {counts.get('PASS', 0)}")
    print(f"WARN: {counts.get('WARN', 0)}")
    print(f"FAIL: {counts.get('FAIL', 0)}")

    print("\nGenerated:")
    print(RESULTS / "dq_report.csv")
    print(RESULTS / "coverage.csv")
    print(RESULTS / "dq_report.md")

    if counts.get("FAIL", 0):
        raise SystemExit(1)


if __name__ == "__main__":
    try:
        main()
    finally:
        engine.dispose()
