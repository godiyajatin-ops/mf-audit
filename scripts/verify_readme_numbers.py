from __future__ import annotations

import csv
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"

FILES = {
    "metrics": ROOT / "results" / "metrics.csv",
    "fees": ROOT / "results" / "fee_gap.csv",
    "mandate": ROOT / "results" / "mandate_audit.csv",
    "evaluation": ROOT / "results" / "eval_summary.csv",
}


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def fmt_pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def main() -> int:
    failures = []

    content = README.read_text(encoding="utf-8-sig")

    matches = list(re.finditer(
        r"<!-- RESULTS:START -->(.*?)<!-- RESULTS:END -->",
        content,
        flags=re.DOTALL,
    ))

    if len(matches) != 1:
        print(f"FAIL: Expected one results block, found {len(matches)}")
        return 1

    block = matches[0].group(1)

    metrics = load_csv(FILES["metrics"])
    fees = load_csv(FILES["fees"])
    mandate = load_csv(FILES["mandate"])
    evaluations = load_csv(FILES["evaluation"])

    checks = {
        "Scheme-plan metric records": str(len(metrics)),
        "Matched Direct-Regular plan pairs": str(len(fees)),
        "Scheme-level mandate audit records": str(len(mandate)),
    }

    for label, expected in checks.items():
        pattern = rf"\|\s*{re.escape(label)}\s*\|\s*{re.escape(expected)}\s*\|"
        if not re.search(pattern, block):
            failures.append(f"{label}: expected {expected}")
        else:
            print(f"PASS: {label} = {expected}")

    eval_by_split = {
        row["split"].strip().lower(): row
        for row in evaluations
    }

    if set(eval_by_split) != {"dev", "heldout"}:
        failures.append("Evaluation split labels are not exactly dev and heldout")
    else:
        for split in ("dev", "heldout"):
            row = eval_by_split[split]

            gold = int(float(row["gold_questions"]))
            completed = int(float(row["completed_questions"]))

            expected_values = [
                f"{completed}/{gold}",
                fmt_pct(float(row["doc_mix_retrieval_hit_at_5"])),
                f"{float(row['doc_mix_retrieval_mrr']):.4f}",
                fmt_pct(float(row["doc_mix_gold_page_citation_rate"])),
                fmt_pct(float(row["numeric_exact_within_1e-6_rate"])),
                fmt_pct(float(row["false_refusal_rate"])),
            ]

            row_pattern = (
                rf"\|\s*{split.title()}\s*\({gold}\s*questions\)\s*\|"
                + "".join(
                    rf"\s*{re.escape(value)}\s*\|"
                    for value in expected_values
                )
            )

            if not re.search(row_pattern, block):
                failures.append(
                    f"{split}: README evaluation values do not match CSV"
                )
            else:
                print(f"PASS: {split} evaluation values match CSV")

    if failures:
        print("\nREADME NUMBER VERIFICATION FAILED")
        for failure in failures:
            print("FAIL:", failure)
        return 1

    print("\nREADME NUMBER VERIFICATION PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
