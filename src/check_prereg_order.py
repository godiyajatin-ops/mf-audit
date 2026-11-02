import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone

def git(*args):
    return subprocess.check_output(
        ["git", *args], text=True
    ).strip()

state = json.loads(Path("PROJECT_STATE.json").read_text(encoding="utf-8"))
assert state["decisions"]["prereg_approved"] is True, "Preregistration not approved"

approved_at = datetime.fromisoformat(
    state["decisions"]["prereg_approved_at"].replace("Z", "+00:00")
)

tag_commit = git("rev-parse", "prereg-approved^{commit}")
tag_time = datetime.fromisoformat(
    git("show", "-s", "--format=%cI", tag_commit)
)

history_dir = Path("data/raw/amfi/history")
files = list(history_dir.rglob("*")) if history_dir.exists() else []
files = [f for f in files if f.is_file()]

print("Approval timestamp:", approved_at)
print("Approval tag commit:", tag_commit)
print("Approval commit time:", tag_time)
print("AMFI history files:", len(files))

failures = []
for f in files:
    modified = datetime.fromtimestamp(f.stat().st_mtime, timezone.utc)
    if approved_at >= modified or tag_time >= modified:
        failures.append((str(f), modified))

if failures:
    print("\nFAIL: History files do not all postdate approval:")
    for name, modified in failures:
        print(name, modified)
    raise SystemExit(1)

print("\nPASS: All AMFI history files postdate preregistration approval.")
