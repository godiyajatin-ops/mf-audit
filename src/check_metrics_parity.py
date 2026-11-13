
from pathlib import Path
import os
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

engine = create_engine(os.environ["DATABASE_URL"])
out = Path("results")
out.mkdir(exist_ok=True)

sql = pd.read_sql("SELECT * FROM res_metrics", engine)
py = pd.read_csv(out / "metrics_pandas.csv")

keys = ["scheme_code", "window_label"]
metrics = [
    "cagr", "vol_ann", "sharpe", "sortino", "max_dd",
    "te_ann", "info_ratio", "up_capture", "down_capture"
]
other = ["n_obs", "start_date", "end_date",
         "max_dd_start", "max_dd_end"]

assert len(sql) == len(py) == 96, "Expected 96 rows in each source"
assert not sql.duplicated(keys).any()
assert not py.duplicated(keys).any()

df = sql.merge(py, on=keys, suffixes=("_sql", "_py"),
               how="outer", indicator=True, validate="one_to_one")

failures = []

for _, row in df.iterrows():
    key = (row["scheme_code"], row["window_label"])

    if row["_merge"] != "both":
        failures.append((*key, "row_presence", str(row["_merge"])))
        continue

    for col in metrics:
        a, b = row[f"{col}_sql"], row[f"{col}_py"]

        if pd.isna(a) and pd.isna(b):
            continue
        if pd.isna(a) or pd.isna(b):
            failures.append((*key, col, "NULL mismatch"))
            continue

        a, b = float(a), float(b)
        tol = (1e-6 if col in ("up_capture", "down_capture")
               else 1e-8 * max(1.0, abs(b)))

        if not np.isfinite(a) or not np.isfinite(b) or abs(a-b) > tol:
            failures.append((*key, col, f"SQL={a}, Pandas={b}, tol={tol}"))

    for col in other:
        a, b = row[f"{col}_sql"], row[f"{col}_py"]
        if pd.isna(a) and pd.isna(b):
            continue
        if col in ("start_date", "end_date", "max_dd_start", "max_dd_end"):
            a = pd.to_datetime(a).date()
            b = pd.to_datetime(b).date()
        if a != b:
            failures.append((*key, col, f"SQL={a}, Pandas={b}"))

report = pd.DataFrame(
    failures, columns=["scheme_code", "window_label", "field", "detail"]
)
report.to_csv(out / "metrics_parity_failures.csv", index=False)

print(f"SQL rows: {len(sql)} | Pandas rows: {len(py)}")
print(f"Parity failures: {len(report)}")
print("A2.5:", "PASS" if report.empty else "FAIL")
if not report.empty:
    print(report.head(20).to_string(index=False))
