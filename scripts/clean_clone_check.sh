#!/usr/bin/env bash
set -euo pipefail

SOURCE_REPO="$(git rev-parse --show-toplevel)"
BRANCH="$(git -C "$SOURCE_REPO" branch --show-current)"
TEMP_DIR="$(mktemp -d)"
CLONE_DIR="$TEMP_DIR/repo"

cleanup() {
    rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

echo "=== MF-Audit clean-clone verification ==="
echo "Source branch: $BRANCH"

echo "[1/6] Cloning committed repository..."
git clone --no-hardlinks --branch "$BRANCH" "$SOURCE_REPO" "$CLONE_DIR"

cd "$CLONE_DIR"

echo "[2/6] Creating fresh virtual environment..."
if [[ -n "${PYTHON_BIN:-}" ]]; then
    "$PYTHON_BIN" -m venv .venv
elif command -v python3.11 >/dev/null 2>&1; then
    python3.11 -m venv .venv
elif command -v python >/dev/null 2>&1 && python -c 'import sys; raise SystemExit(sys.version_info[:2] != (3, 11))'; then
    python -m venv .venv
else
    echo "ERROR: Python 3.11 is required. Set PYTHON_BIN to its executable."
    exit 1
fi

if [[ -x ".venv/Scripts/python.exe" ]]; then
    VENV_PYTHON=".venv/Scripts/python.exe"
elif [[ -x ".venv/bin/python.exe" ]]; then
    VENV_PYTHON=".venv/bin/python.exe"
elif [[ -x ".venv/bin/python" ]]; then
    VENV_PYTHON=".venv/bin/python"
else
    echo "ERROR: Python virtual environment executable was not found."
    exit 1
fi

echo "[3/6] Installing locked dependencies..."
"$VENV_PYTHON" -m pip install --upgrade pip
"$VENV_PYTHON" -m pip install -r requirements.lock.txt

echo "[4/6] Running non-DB tests..."
if command -v make >/dev/null 2>&1; then
    MAKE_BIN="make"
elif command -v mingw32-make >/dev/null 2>&1; then
    MAKE_BIN="mingw32-make"
else
    echo "ERROR: GNU Make was not found."
    exit 1
fi

"$MAKE_BIN" PYTHON="$VENV_PYTHON" test

echo "[5/6] Running packaging checks..."
"$VENV_PYTHON" scripts/verify_readme_numbers.py
"$VENV_PYTHON" scripts/secrets_scan.py
"$VENV_PYTHON" scripts/repo_size_check.py

echo "[6/6] Checking README run instructions..."
"$MAKE_BIN" PYTHON="$VENV_PYTHON" -n setup data metrics inference figures index eval test

echo
echo "CLEAN CLONE CHECK PASS"
