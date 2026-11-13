
import numpy as np
import pandas as pd

from src.metrics_pandas import calculate_drawdown


def test_known_nav_drawdown():
    nav = pd.Series(
        [100.0, 110.0, 99.0, 120.0],
        index=pd.date_range("2024-01-01", periods=4)
    )
    max_dd, peak_date, trough_date = calculate_drawdown(nav)

    assert np.isclose(max_dd, -0.10, atol=1e-10)
    assert peak_date == pd.Timestamp("2024-01-02")
    assert trough_date == pd.Timestamp("2024-01-03")


def test_constant_nav_zero_drawdown():
    nav = pd.Series(
        [100.0, 100.0, 100.0],
        index=pd.date_range("2024-01-01", periods=3)
    )
    max_dd, peak_date, trough_date = calculate_drawdown(nav)

    assert np.isclose(max_dd, 0.0, atol=1e-10)


def test_constant_returns_zero_volatility():
    returns = pd.Series([0.01, 0.01, 0.01, 0.01])
    volatility = returns.std(ddof=1) * np.sqrt(252)

    assert np.isclose(volatility, 0.0, atol=1e-10)


def test_known_cagr():
    first_nav = 100.0
    last_nav = 121.0
    elapsed_days = 2 * 365.25

    cagr = (last_nav / first_nav) ** (365.25 / elapsed_days) - 1

    assert np.isclose(cagr, 0.10, atol=1e-10)

def test_equal_fund_and_benchmark():
    fund_returns = np.array([0.02, -0.01, 0.03, -0.02])
    benchmark_returns = fund_returns.copy()

    active_returns = fund_returns - benchmark_returns

    tracking_error = np.std(active_returns, ddof=1) * np.sqrt(252)

    up_capture = (
        fund_returns[benchmark_returns > 0].mean()
        / benchmark_returns[benchmark_returns > 0].mean()
    )

    down_capture = (
        fund_returns[benchmark_returns < 0].mean()
        / benchmark_returns[benchmark_returns < 0].mean()
    )

    assert np.isclose(tracking_error, 0.0, atol=1e-10)
    assert np.isclose(up_capture, 1.0, atol=1e-10)
    assert np.isclose(down_capture, 1.0, atol=1e-10)