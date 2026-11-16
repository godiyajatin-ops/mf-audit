from pathlib import Path
import re

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

PAGES_PATH = ROOT / "data" / "processed" / "pages_assigned.parquet"
MANIFEST_PATH = ROOT / "data" / "docs_manifest.csv"
OUTPUT_DIR = ROOT / "data" / "index"

# B1.5 parameters: approximately 4 characters per token.
CHARS_PER_TOKEN = 4
A_TARGET = 400 * CHARS_PER_TOKEN
A_OVERLAP = 50 * CHARS_PER_TOKEN
B_MAX = 600 * CHARS_PER_TOKEN
B_MIN = 40 * CHARS_PER_TOKEN


SECTION_PATTERNS = [
    ("Investment Objective", r"investment\s+objective"),
    ("Benchmark", r"(?:benchmark|primary\s+benchmark|additional\s+benchmark)"),
    ("Exit Load", r"exit\s+load"),
    ("Expense Ratio", r"(?:total\s+)?expense\s+ratio|ter\b"),
    ("Asset Allocation", r"asset\s+allocation"),
    ("Risk", r"(?:riskometer|risk\s+profile|risk\s+factors?)"),
    ("Fund Manager", r"fund\s+manager"),
    ("Portfolio", r"(?:portfolio|top\s+\d+\s+holdings|sector\s+allocation)"),
    ("Performance", r"(?:performance|absolute\s+returns?|annualised?\s+returns?)"),
]

HEADING_REGEXES = [
    (name, re.compile(r"^\s*" + pattern + r"\s*[:\-]?\s*$", re.I))
    for name, pattern in SECTION_PATTERNS
]


def normalize_text(value):
    if pd.isna(value):
        return ""
    text = str(value).replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_fixed(text, target=A_TARGET, overlap=A_OVERLAP):
    """Split text by approximate character count, preferring word boundaries."""
    text = normalize_text(text)
    if not text:
        return []

    chunks = []
    start = 0
    length = len(text)

    while start < length:
        end = min(start + target, length)

        if end < length:
            boundary = text.rfind(" ", start, end)
            newline_boundary = text.rfind("\n", start, end)
            boundary = max(boundary, newline_boundary)

            if boundary > start + target // 2:
                end = boundary

        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)

        if end >= length:
            break

        next_start = max(start + 1, end - overlap)

        # Avoid beginning the next chunk in the middle of a word.
        while next_start < length and not text[next_start - 1].isspace():
            next_start += 1

        start = next_start

    return chunks



def classify_heading(line):
    """
    Recognize headings only at the beginning of a line.
    Inline headings must use a colon, avoiding ordinary prose matches.
    """
    line = line.strip()
    if not line or len(line) > 140:
        return None

    rules = [
        ("Investment Objective",
         r"investment\s+objective"),
        ("Benchmark",
         r"(?:primary\s+|additional\s+)?benchmark"),
        ("Exit Load",
         r"exit\s+load"),
        ("Expense Ratio",
         r"expense\s+ratio\d*"),
        ("Asset Allocation",
         r"asset\s+allocation"),
        ("Risk",
         r"(?:scheme\s+|benchmark\s+)?riskometer|"
         r"major\s+risk\s+factors?|risk\s+profile"),
        ("Fund Manager",
         r"fund\s+manager(?:\s+details)?"),
        ("Portfolio",
         r"portfolio(?:\s+as\s+on|\s+details)?"),
        ("Performance",
         r"absolute\s+returns?(?:\s+for\s+each\s+f\.?y\.?)?|"
         r"annualised?\s+returns?|past\s+performance"),
    ]

    for section, heading in rules:
        match = re.match(
            rf"^\s*({heading})(?:\s*:\s*(.*)|\s*)$",
            line,
            flags=re.I,
        )
        if match:
            # A heading followed by inline content must have a colon.
            remainder = match.group(2)
            if remainder is not None:
                return section, remainder.strip()
            return section, ""

    return None


def detect_sections(text):
    """
    Split one page into heading-led sections.
    Recognizes standalone headings and colon-delimited inline headings.
    Never combines pages.
    """
    lines = normalize_text(text).splitlines()
    sections = []
    current_name = "General"
    current_lines = []

    for line in lines:
        stripped = line.strip()
        heading = classify_heading(stripped)

        if heading:
            content = "\n".join(current_lines).strip()
            if content:
                sections.append((current_name, content))

            current_name, remainder = heading
            current_lines = [remainder] if remainder else [stripped]
        else:
            current_lines.append(stripped)

    content = "\n".join(current_lines).strip()
    if content:
        sections.append((current_name, content))

    return sections or [("General", normalize_text(text))]

def merge_short_sections(sections):
    """Merge short sections with the preceding section while preserving labels."""
    merged = []

    for name, text in sections:
        if not text.strip():
            continue

        estimated_tokens = max(1, len(text) // CHARS_PER_TOKEN)

        if merged and estimated_tokens < B_MIN:
            previous_name, previous_text = merged[-1]

            labels = previous_name.split(" + ")
            if name not in labels:
                combined_name = previous_name + " + " + name
            else:
                combined_name = previous_name

            merged[-1] = (
                combined_name,
                previous_text + "\n\n" + text,
            )
        else:
            merged.append((name, text))

    return merged


def make_base_record(page, doc_date, strategy, section, text, part):
    return {
        "doc_id": int(page["doc_id"]),
        "amc": page["amc"],
        "pair_id": page["pair_id"],
        "scheme_code": page["scheme_code"],
        "scheme_name": page["scheme_name"],
        "related_pair_id": page["related_pair_id"],
        "related_scheme_code": page["related_scheme_code"],
        "page": int(page["page"]),
        "section": section,
        "doc_date": doc_date,
        "strategy": strategy,
        "text": text,
        "method": page["method"],
        "assignment_status": page["assignment_status"],
        "page_role": page["page_role"],
        "assignment_basis": page["assignment_basis"],
        "part": part,
    }


def build_strategy_a(pages, manifest_lookup):
    records = []

    for _, page in pages.sort_values(["doc_id", "page"]).iterrows():
        doc_date = manifest_lookup[page["doc_id"]]
        pieces = split_fixed(page["text"])

        for part, piece in enumerate(pieces, start=1):
            records.append(
                make_base_record(
                    page, doc_date, "A", "Page text", piece, part
                )
            )

    return records


def build_strategy_b(pages, manifest_lookup):
    records = []

    for _, page in pages.sort_values(["doc_id", "page"]).iterrows():
        doc_date = manifest_lookup[page["doc_id"]]
        sections = merge_short_sections(detect_sections(page["text"]))

        for section_name, section_text in sections:
            if len(section_text) > B_MAX:
                pieces = split_fixed(
                    section_text,
                    target=B_MAX,
                    overlap=A_OVERLAP,
                )
            else:
                pieces = [section_text]

            for part, piece in enumerate(pieces, start=1):
                records.append(
                    make_base_record(
                        page,
                        doc_date,
                        "B",
                        section_name,
                        piece,
                        part,
                    )
                )

    return records


def finalize(records, strategy):
    frame = pd.DataFrame(records)

    if frame.empty:
        raise ValueError(f"Strategy {strategy} produced zero chunks.")

    frame.insert(
        0,
        "chunk_id",
        [f"{strategy}-{i:07d}" for i in range(1, len(frame) + 1)],
    )

    # Preserve family IDs as nullable integers and scheme codes as strings.
    frame["pair_id"] = pd.to_numeric(
        frame["pair_id"], errors="raise"
    ).astype("Int64")
    frame["related_pair_id"] = pd.to_numeric(
        frame["related_pair_id"], errors="raise"
    ).astype("Int64")
    frame["scheme_code"] = frame["scheme_code"].astype("string")
    frame["related_scheme_code"] = frame["related_scheme_code"].astype("string")

    return frame


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--strategy",
        choices=["A", "B", "both"],
        default="both",
        help="Strategy to rebuild (default: both).",
    )
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    pages = pd.read_parquet(PAGES_PATH)
    manifest = pd.read_csv(MANIFEST_PATH)

    required_pages = {
        "doc_id", "page", "text", "method", "amc",
        "pair_id", "scheme_code", "scheme_name",
        "related_pair_id", "related_scheme_code",
        "assignment_status", "page_role", "assignment_basis",
    }
    required_manifest = {"doc_id", "doc_date"}

    if missing := required_pages - set(pages.columns):
        raise ValueError(f"Pages file missing columns: {sorted(missing)}")

    if missing := required_manifest - set(manifest.columns):
        raise ValueError(f"Manifest file missing columns: {sorted(missing)}")

    if pages.duplicated(["doc_id", "page"]).any():
        raise ValueError("Duplicate document-page rows in input.")

    manifest_lookup = manifest.set_index("doc_id")["doc_date"].to_dict()

    missing_docs = set(pages["doc_id"]) - set(manifest_lookup)
    if missing_docs:
        raise ValueError(f"Pages reference missing manifest IDs: {missing_docs}")

    strategies = []

    if args.strategy in ("A", "both"):
        strategies.append((
            "A",
            finalize(build_strategy_a(pages, manifest_lookup), "A"),
        ))

    if args.strategy in ("B", "both"):
        strategies.append((
            "B",
            finalize(build_strategy_b(pages, manifest_lookup), "B"),
        ))

    source_pages = set(zip(pages["doc_id"], pages["page"]))

    for label, frame in strategies:
        if frame["text"].isna().any() or frame["text"].str.strip().eq("").any():
            raise ValueError(f"Strategy {label} contains empty chunks.")

        if frame.duplicated(["chunk_id"]).any():
            raise ValueError(f"Strategy {label} has duplicate chunk IDs.")

        chunk_pages = set(zip(frame["doc_id"], frame["page"]))
        if not chunk_pages.issubset(source_pages):
            raise ValueError(f"Strategy {label} references unknown source pages.")

        path = OUTPUT_DIR / f"chunks{label}.parquet"
        frame.to_parquet(path, index=False)

        lengths = frame["text"].str.len()
        print(f"\\nStrategy {label}:")
        print(f"  Chunks: {len(frame)}")
        print(f"  Mean characters: {lengths.mean():.1f}")
        print(f"  Median characters: {lengths.median():.1f}")
        print(f"  Maximum characters: {lengths.max()}")
        print(
            "  Unique source pages: "
            f"{frame[['doc_id', 'page']].drop_duplicates().shape[0]}"
        )
        print(f"  Output: {path}")

        if label == "B":
            print("\\nStrategy B section distribution:")
            print(frame["section"].value_counts().to_string())


if __name__ == "__main__":
    main()
