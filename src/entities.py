
from sqlalchemy import text
from pathlib import Path
import re
import pandas as pd
from rapidfuzz import process, fuzz


class EntityNotFoundError(ValueError):
    pass


class AmbiguousEntityError(ValueError):
    pass


def normalize_text(value: str) -> str:
    return " ".join(str(value).strip().lower().split())


def _resolve_exact(conn, table: str, column: str, value: str):
    # Table and column names are fixed internal identifiers.
    # User input is always passed as a bound parameter.
    allowed = {
        ("dim_scheme", "scheme_name"),
        ("dim_scheme", "category"),
        ("dim_scheme", "amc"),
        ("dim_scheme", "plan"),
        ("dim_benchmark", "name"),
    }

    if (table, column) not in allowed:
        raise ValueError("Unsupported entity lookup")

    query = text(f"""
        SELECT DISTINCT {column} AS value
        FROM public.{table}
        WHERE LOWER(TRIM({column})) = :value
        ORDER BY value
    """)

    rows = conn.execute(
        query,
        {"value": normalize_text(value)}
    ).fetchall()

    values = [row.value for row in rows]

    if not values:
        raise EntityNotFoundError(
            f"No matching {column}: {value}"
        )

    if len(values) > 1:
        raise AmbiguousEntityError(
            f"Multiple matches for {column}: {value}"
        )

    return values[0]



def resolve_scheme(conn, name: str, plan: str | None = None):
    query = text("""
        SELECT
            scheme_code,
            scheme_name,
            amc,
            category,
            plan,
            option,
            pair_id,
            is_passive,
            benchmark_id
        FROM public.dim_scheme
        WHERE LOWER(TRIM(scheme_name)) = :name
          AND (
              CAST(:plan AS TEXT) IS NULL
              OR LOWER(TRIM(plan)) = :plan
          )
        ORDER BY scheme_code
    """)

    rows = conn.execute(
        query,
        {
            "name": normalize_text(name),
            "plan": normalize_text(plan) if plan else None,
        }
    ).mappings().all()

    if not rows:
        raise EntityNotFoundError(
            f"No matching scheme: {name}"
            + (f" ({plan})" if plan else "")
        )

    if len(rows) > 1:
        raise AmbiguousEntityError(
            f"Scheme name matches multiple records: {name}. "
            "Specify the plan or option."
        )

    return dict(rows[0])



def resolve_category(conn, category: str):
    return _resolve_exact(
        conn, "dim_scheme", "category", category
    )


def resolve_amc(conn, amc: str):
    return _resolve_exact(
        conn, "dim_scheme", "amc", amc
    )


def resolve_plan(conn, plan: str):
    return _resolve_exact(
        conn, "dim_scheme", "plan", plan
    )


def resolve_benchmark(conn, benchmark: str):
    return _resolve_exact(
        conn, "dim_benchmark", "name", benchmark
    )


# Lexicons are deterministic and shared by the B2 router.
METRIC_TERMS = {
    "max_dd": ("max drawdown", "drawdown"), "sharpe": ("sharpe",),
    "sortino": ("sortino",), "vol_ann": ("volatility", "std"),
    "cagr": ("cagr", "return", "annualised return", "annualized return"),
    "te_ann": ("tracking error",), "info_ratio": ("information ratio",),
    "up_capture": ("up capture",), "down_capture": ("down capture",),
    "alpha_ann": ("alpha",), "beta": ("beta",), "gap_pp": ("fee gap", "direct vs regular"),
}
DOCUMENT_TERMS = ("benchmark", "objective", "exit load", "expense ratio", "ter", "aum", "category", "risk factor", "riskometer")

def detect_metric(question):
    q = normalize_text(question)
    matches = [(key, term) for key, terms in METRIC_TERMS.items() for term in terms if term in q]
    return max(matches, key=lambda pair: len(pair[1]))[0] if matches else None

def detect_window(question):
    q = normalize_text(question)
    if "1y" in q or "one year" in q or "1 year" in q: return "1y"
    if "3y" in q or "three year" in q or "3 year" in q: return "3y"
    return "full"

def detect_scheme(question, universe_path=None, threshold=88):
    path = Path(universe_path) if universe_path else Path(__file__).resolve().parents[1] / "config" / "universe.csv"
    frame = pd.read_csv(path, dtype={"scheme_code": str})
    names = frame["scheme_name"].dropna().unique().tolist()
    match = process.extractOne(str(question), names, scorer=fuzz.WRatio)
    if not match or match[1] < threshold:
        return None
    rows = frame[frame["scheme_name"].eq(match[0])]
    plan = "Regular" if "regular" in normalize_text(question) else "Direct"
    selected = rows[rows["plan"].str.lower().eq(plan.lower())]
    if selected.empty:
        selected = rows
    return str(selected.iloc[0]["scheme_code"])

def detect_scheme_codes(question, universe_path=None):
    """Return explicitly mentioned unique scheme codes in question order."""
    path = Path(universe_path) if universe_path else Path(__file__).resolve().parents[1] / "config" / "universe.csv"
    frame = pd.read_csv(path, dtype={"scheme_code": str})
    q = normalize_text(question)
    names = sorted(frame["scheme_name"].dropna().unique(), key=len, reverse=True)
    mentions = []
    for name in names:
        normalized = normalize_text(name)
        if re.search(rf"(?<!\w){re.escape(normalized)}(?!\w)", q):
            row = frame[frame["scheme_name"].eq(name)]
            plan = "Regular" if re.search(r"\bregular\b", q) else "Direct"
            row = row[row["plan"].str.lower().eq(plan.lower())]
            if row.empty:
                row = frame[frame["scheme_name"].eq(name)]
            code = str(row.iloc[0]["scheme_code"])
            if code not in mentions:
                mentions.append(code)
    return mentions
