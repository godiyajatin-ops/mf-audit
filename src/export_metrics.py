
from pathlib import Path
import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()
engine = create_engine(os.environ["DATABASE_URL"])

Path("results").mkdir(exist_ok=True)

query = """
SELECT
    m.scheme_code,
    s.scheme_name,
    s.amc,
    s.category,
    s.plan,
    s.option,
    s.benchmark_id,
    s.benchmark_confirmed,
    m.window_label,
    m.start_date,
    m.end_date,
    m.cagr,
    m.vol_ann,
    m.sharpe,
    m.sortino,
    m.max_dd,
    m.max_dd_start,
    m.max_dd_end,
    m.te_ann,
    m.info_ratio,
    m.up_capture,
    m.down_capture,
    m.n_obs
FROM res_metrics m
JOIN dim_scheme s USING (scheme_code)
ORDER BY s.category, s.scheme_code,
    CASE m.window_label
        WHEN 'FULL' THEN 1
        WHEN '3Y' THEN 2
        WHEN '1Y' THEN 3
    END
"""

df = pd.read_sql(query, engine)

float_cols = [
    "cagr", "vol_ann", "sharpe", "sortino", "max_dd",
    "te_ann", "info_ratio", "up_capture", "down_capture"
]

for col in float_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce").round(6)

df["start_date"] = pd.to_datetime(df["start_date"]).dt.strftime("%Y-%m-%d")
df["end_date"] = pd.to_datetime(df["end_date"]).dt.strftime("%Y-%m-%d")

for col in ["max_dd_start", "max_dd_end"]:
    df[col] = pd.to_datetime(df[col]).dt.strftime("%Y-%m-%d")

df.to_csv("results/metrics_by_window.csv", index=False, na_rep="")

full = df[df["window_label"] == "FULL"].drop(columns="window_label")
full.to_csv("results/metrics.csv", index=False, na_rep="")

print("A2.8 export complete")
print("All-window records:", len(df))
print("Full-window records:", len(full))
print("Files: results/metrics.csv, results/metrics_by_window.csv")
