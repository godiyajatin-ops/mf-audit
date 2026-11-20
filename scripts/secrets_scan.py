from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

TEXT_EXTENSIONS = {
    ".py", ".md", ".txt", ".yaml", ".yml", ".json",
    ".toml", ".ini", ".cfg", ".ps1", ".bat", ".sh",
    ".sql", ".html", ".js", ".ts", ".csv", ".example",
}

EXCLUDED_DIRS = {
    ".git", ".venv", "__pycache__", ".pytest_cache",
    ".ruff_cache", "node_modules",
}

PLACEHOLDER_VALUES = {
    "", "none", "null", "changeme", "change_me",
    "your_api_key", "your_key_here", "your_secret_here",
    "replace_me", "placeholder", "example", "xxx",
    "your_password", "password_here",
}

# Known credential formats. These are targeted patterns, not
# generic high-entropy strings that mistake filenames for secrets.
TOKEN_PATTERNS = [
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{30,}\b")),
    ("GitHub token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})\b")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("Slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b")),
    ("JWT-like token", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b")),
]

PRIVATE_KEY_PATTERN = re.compile(
    r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"
)

POSTGRES_URI_PATTERN = re.compile(
    r"(?i)postgres(?:ql)?(?:\+[a-z0-9_]+)?://([^:/\s]+):([^@\s]+)@"
)

SENSITIVE_ASSIGNMENT_PATTERN = re.compile(
    r"""(?i)\b(api[_-]?key|secret|access[_-]?token|client[_-]?secret|password)\b\s*[:=]\s*(.+)"""
)

SAFE_EXPRESSION_PREFIXES = (
    "os.getenv(",
    "os.environ[",
    "os.environ.get(",
    "config.get(",
    "llm_config.get(",
    "settings.",
    "api_key",
    "secret",
    "None",
    "null",
    "${",
    "env(",
)


def git_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    )
    names = result.stdout.decode(
        "utf-8", errors="surrogateescape"
    ).split("\0")
    return [ROOT / name for name in names if name]


def is_placeholder(value: str) -> bool:
    cleaned = value.strip().strip("'\"").strip()
    lower = cleaned.lower()

    return (
        lower in PLACEHOLDER_VALUES
        or lower.startswith(("your_", "replace_", "change_me"))
        or lower.startswith("<")
        or lower.startswith("${")
        or lower.startswith("change-this")
    )


def should_scan(path: Path) -> bool:
    relative = path.relative_to(ROOT)

    if any(part in EXCLUDED_DIRS for part in relative.parts):
        return False

    if path.name == ".env":
        return False

    return (
        path.suffix.lower() in TEXT_EXTENSIONS
        or path.name == ".env.example"
    )


def check_env_example(path: Path, failures: list[str]) -> None:
    if not path.exists():
        failures.append(".env.example does not exist")
        return

    for number, line in enumerate(
        path.read_text(encoding="utf-8", errors="replace").splitlines(),
        start=1,
    ):
        stripped = line.strip()

        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue

        key, value = stripped.split("=", 1)
        value = value.split("#", 1)[0].strip()

        if not value:
            continue

        # Check PostgreSQL URI credentials separately.
        uri_match = POSTGRES_URI_PATTERN.search(value)
        if uri_match:
            username, password = uri_match.groups()

            if not is_placeholder(username) or not is_placeholder(password):
                failures.append(
                    f".env.example may contain real database credentials at line {number} ({key.strip()})"
                )
            continue

        if not is_placeholder(value):
            failures.append(
                f".env.example may contain a real value at line {number} ({key.strip()})"
            )


def check_sensitive_assignment(line: str) -> str | None:
    match = SENSITIVE_ASSIGNMENT_PATTERN.search(line)

    if not match:
        return None

    value = match.group(2).strip().rstrip(",")
    lower = value.lower()

    if is_placeholder(value):
        return None

    if lower.startswith(SAFE_EXPRESSION_PREFIXES):
        return None

    # Quoted literal credentials are suspicious unless placeholders.
    quoted = re.match(r"""^(['"])(.*?)\1""", value)

    if quoted:
        return None if is_placeholder(quoted.group(2)) else match.group(1)

    # Bare literal-looking values are suspicious.
    if re.match(r"^[A-Za-z0-9_./+=-]{8,}$", value):
        return match.group(1)

    return None


def main() -> int:
    failures: list[str] = []
    tracked = git_files()

    tracked_names = {
        path.relative_to(ROOT).as_posix()
        for path in tracked
    }

    if ".env" in tracked_names:
        failures.append(".env is tracked by Git")
    else:
        print("PASS: .env is not tracked")

    if ".env.example" not in tracked_names:
        failures.append(".env.example is not tracked")
    else:
        print("PASS: .env.example is tracked")

    check_env_example(ROOT / ".env.example", failures)

    if not any(".env.example may contain" in item for item in failures):
        print("PASS: .env.example contains no detected real values")

    checked = 0

    for path in tracked:
        if not path.is_file() or not should_scan(path):
            continue

        checked += 1

        try:
            content = path.read_text(
                encoding="utf-8",
                errors="replace",
            )
        except OSError:
            continue

        for number, line in enumerate(content.splitlines(), start=1):
            relative = path.relative_to(ROOT).as_posix()

            if PRIVATE_KEY_PATTERN.search(line):
                failures.append(
                    f"Private key header detected: {relative}:{number}"
                )

            for label, pattern in TOKEN_PATTERNS:
                if pattern.search(line):
                    failures.append(
                        f"Potential {label}: {relative}:{number}"
                    )

            if POSTGRES_URI_PATTERN.search(line):
                match = POSTGRES_URI_PATTERN.search(line)
                if match:
                    username, password = match.groups()

                    if (
                        not is_placeholder(username)
                        and not is_placeholder(password)
                    ):
                        failures.append(
                            f"PostgreSQL URI may contain real credentials: {relative}:{number}"
                        )

            assignment = check_sensitive_assignment(line)
            if assignment:
                failures.append(
                    f"Potential hardcoded {assignment}: {relative}:{number}"
                )

    print(f"Tracked text files scanned: {checked}")

    if failures:
        print("\nSECRETS SCAN FAILED")
        for failure in sorted(set(failures)):
            print("FAIL:", failure)
        print("Potential secret values were not printed.")
        return 1

    print("\nSECRETS SCAN PASS")
    print("No detected credentials or private-key material in tracked text files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
