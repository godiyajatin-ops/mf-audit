
import pytest
from sqlalchemy import create_engine

from src.entities import (
    resolve_scheme,
    resolve_category,
    resolve_plan,
    EntityNotFoundError,
    AmbiguousEntityError,
)


@pytest.fixture
def conn():
    # Uses the read-only database role.
    from dotenv import load_dotenv
    from pathlib import Path
    import os

    load_dotenv(Path(".env"))
    engine = create_engine(os.environ["READONLY_DATABASE_URL"])

    with engine.connect() as connection:
        yield connection

    engine.dispose()


def test_resolve_exact_scheme(conn):
    result = resolve_scheme(
        conn, "HDFC Large Cap Fund", plan="Direct"
    )
    assert result["scheme_name"] == "HDFC Large Cap Fund"
    assert result["plan"] == "Direct"
    assert result["scheme_code"] > 0

def test_resolve_category(conn):
    assert resolve_category(conn, "Large Cap") == "Large Cap"


def test_resolve_plan(conn):
    assert resolve_plan(conn, "Direct") == "Direct"


def test_unknown_scheme(conn):
    with pytest.raises(EntityNotFoundError):
        resolve_scheme(conn, "Imaginary Mutual Fund")


def test_ambiguous_scheme(conn):
    # Same base name may exist under Direct and Regular plans.
    with pytest.raises(AmbiguousEntityError):
        resolve_scheme(conn, "HDFC Large Cap Fund")
