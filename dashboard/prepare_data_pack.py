from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
DATA = ROOT / "data" / "processed"
OUT = Path(__file__).resolve().parent / "data"
OUT.mkdir(parents=True, exist_ok=True)

def read_csv(name):
    return pd.read_csv(RESULTS / name)

def save(df, name):
    df.to_csv(OUT / name, index=False, date_format="%Y-%m-%d")

# Dimension: approved universe plus the canonical metrics and benchmark mappings.
universe = pd.read_csv(ROOT / "config" / "universe.csv")
metrics = read_csv("metrics.csv")
alpha = read_csv("alpha.csv")
fee = read_csv("fee_gap.csv")
ter = pd.read_csv(ROOT / "data" / "manual" / "scheme_facts.csv")
dim = universe.merge(metrics[["scheme_code", "option", "benchmark_id", "benchmark_confirmed"]], on="scheme_code", how="left", validate="one_to_one")
dim = dim.merge(alpha[["scheme_code", "benchmark_name", "provisional"]], on="scheme_code", how="left", validate="one_to_one")
dim = dim.merge(fee[["pair_id", "ter_direct_pct", "ter_regular_pct"]].drop_duplicates("pair_id"), on="pair_id", how="left", validate="many_to_one")
dim["ter_as_of"] = "2026-09-30"
dim["benchmark_basis"] = dim["benchmark_id"].map({6: "Estimated hybrid BSE TRI", 7: "Estimated hybrid BSE TRI"}).fillna("Disclosed benchmark TRI")
dim["provisional"] = dim["provisional"].fillna(False)
save(dim, "dim_scheme.csv")

# A3 outputs are carried through without altering their values.
for source, target in [("metrics.csv", "metrics.csv"), ("alpha.csv", "alpha.csv"), ("fee_gap.csv", "fee_gap.csv"), ("control_check.csv", "control_check.csv")]:
    read_csv(source).to_csv(OUT / target, index=False)

# Daily 252-observation trailing NAV return series, restricted to the approved 32 schemes.
nav = pd.read_parquet(DATA / "nav_long.parquet")
nav["scheme_code"] = nav["scheme_code"].astype(int)
nav = nav[nav.scheme_code.isin(set(universe.scheme_code.astype(int)))].copy()
nav["nav_date"] = pd.to_datetime(nav["nav_date"])
nav = nav.sort_values(["scheme_code", "nav_date"])
nav["rolling_return_252d"] = nav.groupby("scheme_code").nav.transform(lambda s: s / s.shift(252) - 1)
rolling_returns = nav.dropna(subset=["rolling_return_252d"])[["scheme_code", "nav_date", "rolling_return_252d"]]
rolling_returns["provisional"] = rolling_returns.scheme_code.map(alpha.set_index("scheme_code").provisional).fillna(False).values
save(rolling_returns, "rolling_returns.csv")

# Point-in-time drawdown path computed from observed NAV levels within the research window.
nav["running_peak"] = nav.groupby("scheme_code").nav.cummax()
drawdown = nav.assign(drawdown=nav.nav / nav.running_peak - 1)[["scheme_code", "nav_date", "drawdown"]]
drawdown["provisional"] = drawdown.scheme_code.map(alpha.set_index("scheme_code").provisional).fillna(False).values
save(drawdown, "drawdown.csv")

# Capture estimates are the already-reviewed A2/A3 full-window metric exports.
capture = metrics[["scheme_code", "scheme_name", "benchmark_id", "up_capture", "down_capture", "start_date", "end_date", "benchmark_confirmed"]].copy()
capture["provisional"] = capture.scheme_code.map(alpha.set_index("scheme_code").provisional).fillna(False).values
save(capture, "capture.csv")

# Benchmark levels combine actual TRI series and the explicitly labeled estimated BSE hybrids.
benchmark = pd.read_parquet(DATA / "benchmark_tri_long.parquet")
benchmark = benchmark.rename(columns={"tri_date": "date", "tri": "benchmark_level"})
benchmark["series_basis"] = "actual TRI"
benchmark["provisional"] = False
hybrid_path = DATA / "bse_hybrid_tri_long.parquet"
if hybrid_path.exists():
    hybrid = pd.read_parquet(hybrid_path).rename(columns={"tri_date": "date", "tri": "benchmark_level"})
    benchmark = pd.concat([benchmark, hybrid[["benchmark_id", "benchmark_name", "date", "benchmark_level", "series_basis", "provisional"]]], ignore_index=True)
benchmark["date"] = pd.to_datetime(benchmark["date"])
benchmark = benchmark.sort_values(["benchmark_id", "date"])
save(benchmark, "benchmark_levels.csv")

glossary = pd.DataFrame([
    ("alpha_ann", "Annualized CAPM alpha", "Annualized regression intercept versus the assigned benchmark; estimated, not proof of skill."),
    ("beta", "CAPM beta", "Sensitivity to benchmark returns over the research window."),
    ("p_bh", "BH adjusted p-value", "Benjamini-Hochberg adjusted p-value for the defined multiple-testing family."),
    ("significant_bh", "BH significant", "Whether the adjusted p-value meets the preregistered q=0.10 threshold."),
    ("gap_pp", "Direct-Regular CAGR gap", "Direct plan CAGR minus Regular plan CAGR in percentage points."),
    ("residual_pp", "Fee-gap residual", "Realized Direct-Regular CAGR gap minus the disclosed TER gap, in percentage points."),
    ("rolling_return_252d", "252-observation rolling return", "NAV-based return across 252 observed scheme NAV records; not a calendar-year return."),
    ("drawdown", "Drawdown from running peak", "NAV divided by the running NAV peak minus one."),
    ("up_capture", "Upside capture", "Fund return participation during benchmark-up periods, as calculated in the project metrics."),
    ("down_capture", "Downside capture", "Fund return participation during benchmark-down periods, as calculated in the project metrics."),
    ("provisional", "Provisional result", "True where the assigned benchmark uses the approved estimated hybrid BSE series."),
    ("benchmark_confirmed", "Benchmark confirmed", "Whether the assigned benchmark is the confirmed source series; estimated hybrid BSE series are not actual BSE TRI."),
    ("ter_as_of", "TER snapshot date", "30-Sep-2026 snapshot; it is not a historical five-year TER series."),
], columns=["field", "label", "definition"])
save(glossary, "glossary.csv")

print(f"Wrote {len(list(OUT.glob('*.csv')))} CSV files to {OUT}")
for f in sorted(OUT.glob("*.csv")):
    d = pd.read_csv(f)
    print(f"{f.name}: {len(d)} rows, {len(d.columns)} columns")
