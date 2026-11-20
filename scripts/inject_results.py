from __future__ import annotations

import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"

FILES = {
    "metrics": ROOT / "results" / "metrics.csv",
    "fees": ROOT / "results" / "fee_gap.csv",
    "mandate": ROOT / "results" / "mandate_audit.csv",
    "evaluation": ROOT / "results" / "eval_summary.csv",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Required file is missing: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def number(row: dict[str, str], field: str) -> float:
    value = row.get(field, "")
    if value is None or value.strip() == "":
        raise ValueError(f"Missing numeric value for {field}")
    return float(value)


def percentage(value: float) -> str:
    return f"{value * 100:.1f}%"


def build_results_block() -> str:
    metrics = read_csv(FILES["metrics"])
    fees = read_csv(FILES["fees"])
    mandate = read_csv(FILES["mandate"])
    evaluations = read_csv(FILES["evaluation"])

    if not metrics or not fees or not mandate:
        raise ValueError("One or more analytical result files are empty.")

    scheme_codes = {
        row["scheme_code"].strip()
        for row in mandate
        if row.get("scheme_code", "").strip()
    }

    if len(scheme_codes) != len(mandate):
        raise ValueError(
            "Mandate audit rows contain missing or duplicate scheme codes."
        )

    eval_by_split = {
        row["split"].strip().lower(): row
        for row in evaluations
    }

    if set(eval_by_split) != {"dev", "heldout"}:
        raise ValueError(
            f"Expected dev and heldout evaluation splits; found "
            f"{sorted(eval_by_split)}"
        )

    lines = [
        "<!-- Generated from results/*.csv by scripts/inject_results.py. Do not edit this block manually. -->",
        "",
        "### Quantitative outputs",
        "",
        "| Measure | Result |",
        "|---|---:|",
        f"| Scheme-plan metric records | {len(metrics)} |",
        f"| Matched Direct-Regular plan pairs | {len(fees)} |",
        f"| Scheme-level mandate audit records | {len(mandate)} |",
        "",
        "The mandate audit count is scheme-level. Supporting Direct and Regular plan records are not counted as additional schemes.",
        "",
        "### B2 question-answer evaluation",
        "",
        "| Evaluation split | Questions completed | Hit@5 | MRR | Exact gold-page citations | Numeric exactness | False-refusal rate |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]

    for split in ("dev", "heldout"):
        row = eval_by_split[split]

        completed = int(number(row, "completed_questions"))
        gold = int(number(row, "gold_questions"))

        if completed > gold:
            raise ValueError(
                f"{split}: completed question count exceeds gold question count."
            )

        lines.append(
            f"| {split.title()} ({gold} questions) "
            f"| {completed}/{gold} "
            f"| {percentage(number(row, 'doc_mix_retrieval_hit_at_5'))} "
            f"| {number(row, 'doc_mix_retrieval_mrr'):.4f} "
            f"| {percentage(number(row, 'doc_mix_gold_page_citation_rate'))} "
            f"| {percentage(number(row, 'numeric_exact_within_1e-6_rate'))} "
            f"| {percentage(number(row, 'false_refusal_rate'))} |"
        )

    lines.extend([
        "",
        "Evaluation figures are reported separately for development and heldout questions. Heldout results were measured after the retrieval configuration was frozen.",
    ])

    return "\n".join(lines)


def main() -> None:
    if not README.exists():
        raise FileNotFoundError(f"README not found: {README}")

    content = README.read_text(encoding="utf-8-sig")

    pattern = re.compile(
        r"(<!-- RESULTS:START -->).*?(<!-- RESULTS:END -->)",
        flags=re.DOTALL,
    )

    matches = list(pattern.finditer(content))

    if len(matches) != 1:
        raise ValueError(
            f"Expected exactly one results marker pair; found {len(matches)}."
        )

    generated = build_results_block()

    updated = pattern.sub(
        lambda match: (
            match.group(1)
            + "\n"
            + generated
            + "\n"
            + match.group(2)
        ),
        content,
        count=1,
    )

    README.write_text(updated, encoding="utf-8")

    print("README results block updated successfully.")
    print(f"Source files: {len(FILES)}")
    print(f"README: {README}")


if __name__ == "__main__":
    main()
