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
if [[ "${OS:-}" == "Windows_NT" || -n "${WINDIR:-}" ]]; then
    python -m venv .venv
    VENV_PYTHON=".venv/Scripts/python.exe"
else
    python3 -m venv .venv
    VENV_PYTHON=".venv/bin/python"
fi

echo "[3/6] Installing requirements.txt..."
"$VENV_PYTHON" -m pip install --upgrade pip
"$VENV_PYTHON" -m pip install -r requirements.txt

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
