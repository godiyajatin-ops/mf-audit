"""Environment diagnostics for the mf-audit project."""

from __future__ import annotations

import argparse
import importlib.util
import shutil
import subprocess
import sys
import time
from pathlib import Path

import requests

REQUIRED = {
    "pandas": "pandas",
    "numpy": "numpy",
    "scipy": "scipy",
    "statsmodels": "statsmodels",
    "sqlalchemy": "sqlalchemy",
    "psycopg": "psycopg",
    "requests": "requests",
    "yaml": "PyYAML",
    "pdfplumber": "pdfplumber",
    "fitz": "PyMuPDF",
    "rapidfuzz": "rapidfuzz",
    "pytest": "pytest",
}

OPTIONAL = {
    "sentence_transformers": "sentence-transformers",
    "faiss": "faiss-cpu",
    "rank_bm25": "rank-bm25",
}

URLS = [
    "https://www.amfiindia.com",
    "https://portal.amfiindia.com",
    "https://www.niftyindices.com",
    "https://data.rbi.org.in",
]


def package_checks():
    results = []

    for module, package in REQUIRED.items():
        try:
            available = importlib.util.find_spec(module) is not None
        except (ImportError, ValueError):
            available = False

        results.append((
            package,
            "PASS" if available else "FAIL",
            "Required package",
        ))

    for module, package in OPTIONAL.items():
        try:
            available = importlib.util.find_spec(module) is not None
        except (ImportError, ValueError):
            available = False

        results.append((
            package,
            "PASS" if available else "WARN",
            "Optional Stage B package",
        ))

    return results


def command_available(command):
    executable = shutil.which(command)

    if not executable:
        return False

    try:
        result = subprocess.run(
            [executable, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def website_checks():
    results = []
    headers = {"User-Agent": "mf-audit-feasibility-check/1.0"}

    with requests.Session() as session:
        session.headers.update(headers)

        for index, url in enumerate(URLS):
            if index:
                time.sleep(1)

            try:
                response = session.head(
                    url,
                    timeout=10,
                    allow_redirects=True,
                )

                if response.status_code >= 400 or response.status_code == 405:
                    response.close()
                    response = session.get(
                        url,
                        timeout=10,
                        allow_redirects=True,
                        stream=True,
                    )

                status = (
                    "PASS"
                    if response.status_code < 400
                    else "WARN"
                )
                detail = f"HTTP {response.status_code}"
                response.close()

            except requests.RequestException as exc:
                status = "WARN"
                detail = str(exc)[:120]

            results.append((url, status, detail))

    return results


def database_check():
    try:
        from dotenv import load_dotenv
        from sqlalchemy import create_engine, text
        import os

        load_dotenv()

        database_url = os.getenv("DATABASE_URL")

        if not database_url:
            return "FAIL", "DATABASE_URL missing from .env"

        engine = create_engine(database_url)

        try:
            with engine.connect() as connection:
                value = connection.execute(
                    text("SELECT 1")
                ).scalar_one()

            return (
                ("PASS", "SELECT 1 returned 1")
                if value == 1
                else ("FAIL", "Unexpected database response")
            )
        finally:
            engine.dispose()

    except Exception as exc:
        return "FAIL", str(exc)[:150]


def main():
    parser = argparse.ArgumentParser(
        description="Check mf-audit development environment."
    )
    parser.add_argument(
        "--db",
        action="store_true",
        help="Test PostgreSQL connectivity.",
    )
    args = parser.parse_args()

    results = []

    version = sys.version_info
    python_ok = version.major == 3 and version.minor == 11

    results.append((
        "Python version",
        "PASS" if python_ok else "FAIL",
        sys.version.split()[0],
    ))

    venv_active = sys.prefix != sys.base_prefix

    results.append((
        "Virtual environment",
        "PASS" if venv_active else "WARN",
        str(sys.prefix),
    ))

    results.extend(package_checks())

    docker = command_available("docker")
    psql = command_available("psql")

    results.append((
        "Docker / PostgreSQL CLI",
        "PASS" if docker or psql else "WARN",
        f"Docker={docker}; psql={psql}",
    ))

    results.extend(website_checks())

    disk = shutil.disk_usage(Path.cwd())
    free_gb = disk.free / (1024 ** 3)

    results.append((
        "Free disk space",
        "PASS" if free_gb > 2 else "FAIL",
        f"{free_gb:.2f} GB",
    ))

    if args.db:
        status, detail = database_check()
        results.append(("PostgreSQL connection", status, detail))

    print("\n=== MF-AUDIT ENVIRONMENT CHECK ===\n")
    print(f"{'CHECK':35} {'STATUS':10} DETAILS")
    print("-" * 110)

    for name, status, detail in results:
        print(f"{name:35} {status:10} {detail}")

    failures = sum(
        status == "FAIL"
        for _, status, _ in results
    )

    warnings = sum(
        status == "WARN"
        for _, status, _ in results
    )

    print("\n" + "-" * 110)
    print(
        f"Total: {len(results)} | "
        f"Failures: {failures} | Warnings: {warnings}"
    )

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
