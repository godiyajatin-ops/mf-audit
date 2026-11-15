from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.validate_dashboard_data import SCHEMA, validate_pack


DATA = ROOT / "dashboard" / "data"


def test_complete_dashboard_contract():
    errors, warnings = validate_pack(ROOT)
    assert not errors, "; ".join(errors)
    assert not warnings, "; ".join(warnings)


def test_required_tables_and_rows():
    assert set(SCHEMA) == {p.name for p in DATA.glob("*.csv")}
    assert len(pd.read_csv(DATA / "alpha.csv")) == 32
    assert len(pd.read_csv(DATA / "fee_gap.csv")) == 16
    assert len(pd.read_csv(DATA / "control_check.csv")) == 4
    assert len(pd.read_csv(DATA / "glossary.csv")) == 11


def test_short_names_and_provisional_basis():
    dim = pd.read_csv(DATA / "dim_scheme.csv")
    assert dim.short_name.is_unique
    assert dim.short_name.str.len().le(28).all()
    assert dim.provisional.astype(bool).equals(dim.benchmark_basis.eq("estimated_hybrid"))
    assert int(dim.provisional.sum()) == 8


def test_alpha_plan_and_group_fields_are_available():
    alpha = pd.read_csv(DATA / "alpha.csv")
    assert {"plan", "group", "short_name"}.issubset(alpha.columns)
    assert alpha.scheme_code.is_unique


def test_rolling_series_keys_and_beta_warning_threshold():
    beta = pd.read_csv(DATA / "rolling_beta.csv", parse_dates=["nav_date"])
    assert {"scheme_code", "nav_date", "beta_252"}.issubset(beta.columns)
    assert not beta.duplicated(["scheme_code", "nav_date"]).any()
    changes = beta.sort_values(["scheme_code", "nav_date"]).groupby("scheme_code").beta_252.diff().abs()
    assert changes.max() <= 0.25
    rolling = pd.read_csv(DATA / "rolling_returns.csv")
    assert {"rolling_return_3y", "benchmark_return_3y"}.issubset(rolling.columns)
    assert rolling.rolling_return_3y.isna().equals(rolling.benchmark_return_3y.isna())


def test_control_check_arithmetic():
    control = pd.read_csv(DATA / "control_check.csv")
    discrepancy = ((control.alpha_ann - control.expected_alpha_ann) * 100 - control.deviation_pp).abs()
    assert discrepancy.max() <= 0.01
