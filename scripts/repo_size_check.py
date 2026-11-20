from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

GENERAL_LIMIT = 5 * 1024 * 1024
LARGE_ARTIFACT_LIMIT = 50 * 1024 * 1024

LARGE_ARTIFACT_EXTENSIONS = {
    ".pdf",
    ".parquet",
    ".index",
    ".pkl",
    ".pbix",
}


def tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    )

    names = result.stdout.decode("utf-8", errors="surrogateescape").split("\0")

    return [
        ROOT / name
        for name in names
        if name
    ]


def main() -> int:
    failures = []
    checked = 0
    missing = []

    for path in tracked_files():
        if not path.is_file():
            missing.append(path.relative_to(ROOT))
            continue

        checked += 1
        size = path.stat().st_size
        extension = path.suffix.lower()

        limit = (
            LARGE_ARTIFACT_LIMIT
            if extension in LARGE_ARTIFACT_EXTENSIONS
            else GENERAL_LIMIT
        )

        if size > limit:
            relative = path.relative_to(ROOT)
            size_mb = size / (1024 * 1024)
            limit_mb = limit / (1024 * 1024)

            failures.append(
                f"{relative}: {size_mb:.2f} MB "
                f"(limit: {limit_mb:.0f} MB)"
            )

    if missing:
        print("WARNING: Tracked files missing from working tree:")
        for path in missing:
            print(f"  {path}")

    print(f"Tracked files checked: {checked}")

    if failures:
        print("\nREPOSITORY SIZE CHECK FAILED")
        for failure in failures:
            print("FAIL:", failure)
        return 1

    print("REPOSITORY SIZE CHECK PASS")
    print("No tracked files exceed their applicable size limits.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
