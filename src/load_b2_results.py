
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"


def load_alpha(conn):
    df = pd.read_csv(RESULTS / "alpha.csv")

    required = {
        "scheme_code", "alpha_ann", "beta",
        "se_alpha_ann", "p_value", "p_bh",
        "r2", "n_obs"
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"alpha.csv missing columns: {sorted(missing)}")

    if len(df) != 32 or df["scheme_code"].nunique() != 32:
        raise ValueError("Expected exactly 32 unique alpha scheme records")

    df["window_label"] = "FULL"
    df["p_bh"] = pd.to_numeric(df["p_bh"], errors="coerce")

    records = df[
        [
            "scheme_code", "window_label", "alpha_ann",
            "beta", "se_alpha_ann", "p_value",
            "p_bh", "r2", "n_obs"
        ]
    ].where(pd.notna(df), None).to_dict("records")

    conn.execute(text("""
        INSERT INTO public.res_alpha (
            scheme_code, window_label, alpha_ann, beta,
            se_nw, p_value, p_bh, r2, n_obs
        )
        VALUES (
            :scheme_code, :window_label, :alpha_ann, :beta,
            :se_alpha_ann, :p_value, :p_bh, :r2, :n_obs
        )
        ON CONFLICT (scheme_code, window_label)
        DO UPDATE SET
            alpha_ann = EXCLUDED.alpha_ann,
            beta = EXCLUDED.beta,
            se_nw = EXCLUDED.se_nw,
            p_value = EXCLUDED.p_value,
            p_bh = EXCLUDED.p_bh,
            r2 = EXCLUDED.r2,
            n_obs = EXCLUDED.n_obs
    """), records)


def load_fee_gap(conn):
    df = pd.read_csv(RESULTS / "fee_gap.csv")

    if len(df) != 16 or df["pair_id"].nunique() != 16:
        raise ValueError("Expected 16 unique fee-gap pairs")

    df["start_date"] = pd.to_datetime(df["start_date"]).dt.date
    df["end_date"] = pd.to_datetime(df["end_date"]).dt.date

    records = df.where(pd.notna(df), None).to_dict("records")

    conn.execute(text("""
        INSERT INTO public.res_fee_gap (
            pair_id, direct_cagr, regular_cagr, gap_pp,
            rupee_gap, common_nav_observations, start_date,
            end_date, amc, scheme_base_name, ter_direct_pct,
            ter_regular_pct, expected_pp, residual_pp, ter_status,
            provisional, median_gap_pp, minimum_gap_pp,
            maximum_gap_pp, wilcoxon_statistic, wilcoxon_p_value
        )
        VALUES (
            :pair_id, :direct_cagr, :regular_cagr, :gap_pp,
            :rupee_gap, :common_nav_observations, :start_date,
            :end_date, :amc, :scheme_base_name, :ter_direct_pct,
            :ter_regular_pct, :expected_pp, :residual_pp, :ter_status,
            :provisional, :median_gap_pp, :minimum_gap_pp,
            :maximum_gap_pp, :wilcoxon_statistic, :wilcoxon_p_value
        )
        ON CONFLICT (pair_id)
        DO UPDATE SET
            direct_cagr = EXCLUDED.direct_cagr,
            regular_cagr = EXCLUDED.regular_cagr,
            gap_pp = EXCLUDED.gap_pp,
            rupee_gap = EXCLUDED.rupee_gap,
            common_nav_observations = EXCLUDED.common_nav_observations,
            start_date = EXCLUDED.start_date,
            end_date = EXCLUDED.end_date,
            amc = EXCLUDED.amc,
            scheme_base_name = EXCLUDED.scheme_base_name,
            ter_direct_pct = EXCLUDED.ter_direct_pct,
            ter_regular_pct = EXCLUDED.ter_regular_pct,
            expected_pp = EXCLUDED.expected_pp,
            residual_pp = EXCLUDED.residual_pp,
            ter_status = EXCLUDED.ter_status,
            provisional = EXCLUDED.provisional,
            median_gap_pp = EXCLUDED.median_gap_pp,
            minimum_gap_pp = EXCLUDED.minimum_gap_pp,
            maximum_gap_pp = EXCLUDED.maximum_gap_pp,
            wilcoxon_statistic = EXCLUDED.wilcoxon_statistic,
            wilcoxon_p_value = EXCLUDED.wilcoxon_p_value
    """), records)


def load_mandate_audit(conn):
    df = pd.read_csv(
        RESULTS / "mandate_audit.csv",
        keep_default_na=False
    )

    if len(df) != 32 or df["scheme_code"].nunique() != 32:
        raise ValueError("Expected 32 unique mandate-audit schemes")

    numeric_columns = [
        "r2", "beta", "max_dd", "R2_beta_z",
        "R2_max_dd_z", "gap_pp", "expected_pp",
        "residual_pp", "R3_abs_residual_pp"
    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    records = df.to_dict("records")

    conn.execute(text("""
        INSERT INTO public.res_mandate_audit (
            scheme_code, scheme_name, amc, category, plan,
            pair_id, is_passive, benchmark_name, benchmark_confirmed,
            r2, beta, max_dd, te_ann, R1_benchmark_fit,
            R2_peer_risk, R2_beta_z, R2_max_dd_z,
            gap_pp, expected_pp, residual_pp, R3_abs_residual_pp,
            R3_cost_fit, R4_tracking_error_pct, R4_passive_fit,
            R5_closet_indexer_screen, provisional
        )
        VALUES (
            :scheme_code, :scheme_name, :amc, :category, :plan,
            :pair_id, :is_passive, :benchmark_name, :benchmark_confirmed,
            :r2, :beta, :max_dd, :te_ann, :R1_benchmark_fit,
            :R2_peer_risk, :R2_beta_z, :R2_max_dd_z,
            :gap_pp, :expected_pp, :residual_pp, :R3_abs_residual_pp,
            :R3_cost_fit, :R4_tracking_error_pct, :R4_passive_fit,
            :R5_closet_indexer_screen, :provisional
        )
        ON CONFLICT (scheme_code)
        DO UPDATE SET
            scheme_name = EXCLUDED.scheme_name,
            amc = EXCLUDED.amc,
            category = EXCLUDED.category,
            plan = EXCLUDED.plan,
            pair_id = EXCLUDED.pair_id,
            is_passive = EXCLUDED.is_passive,
            benchmark_name = EXCLUDED.benchmark_name,
            benchmark_confirmed = EXCLUDED.benchmark_confirmed,
            r2 = EXCLUDED.r2,
            beta = EXCLUDED.beta,
            max_dd = EXCLUDED.max_dd,
            te_ann = EXCLUDED.te_ann,
            R1_benchmark_fit = EXCLUDED.R1_benchmark_fit,
            R2_peer_risk = EXCLUDED.R2_peer_risk,
            R2_beta_z = EXCLUDED.R2_beta_z,
            R2_max_dd_z = EXCLUDED.R2_max_dd_z,
            gap_pp = EXCLUDED.gap_pp,
            expected_pp = EXCLUDED.expected_pp,
            residual_pp = EXCLUDED.residual_pp,
            R3_abs_residual_pp = EXCLUDED.R3_abs_residual_pp,
            R3_cost_fit = EXCLUDED.R3_cost_fit,
            R4_tracking_error_pct = EXCLUDED.R4_tracking_error_pct,
            R4_passive_fit = EXCLUDED.R4_passive_fit,
            R5_closet_indexer_screen = EXCLUDED.R5_closet_indexer_screen,
            provisional = EXCLUDED.provisional
    """), records)


def main():
    load_dotenv(ROOT / ".env")

    import os
    database_url = os.environ["DATABASE_URL"]
    engine = create_engine(database_url)

    try:
        with engine.begin() as conn:
            load_alpha(conn)
            load_fee_gap(conn)
            load_mandate_audit(conn)

            counts = {}
            for table in (
                "res_alpha",
                "res_fee_gap",
                "res_mandate_audit"
            ):
                counts[table] = conn.execute(
                    text(f"SELECT COUNT(*) FROM public.{table}")
                ).scalar_one()

        print("B2 RESULT LOAD COMPLETED")
        for table, count in counts.items():
            print(f"{table}: {count}")

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
