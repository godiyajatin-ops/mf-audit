from pathlib import Path
from hashlib import sha256
from datetime import date
import re

import pandas as pd
import pymupdf
import pdfplumber

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw_docs" / "probe"
PROCESSED_DIR = ROOT / "data" / "processed"

MANIFEST_PATH = ROOT / "data" / "docs_manifest.csv"
PAGES_PATH = PROCESSED_DIR / "pages.parquet"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def file_sha256(path):
    digest = sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def infer_amc(filename):
    name = filename.lower()
    if "sbimf" in name or "sbi" in name:
        return "SBI Mutual Fund"
    if "hdfc" in name:
        return "HDFC Mutual Fund"
    if "icici" in name:
        return "ICICI Prudential Mutual Fund"
    if "kotak" in name:
        return "Kotak Mahindra Mutual Fund"
    if "nippon" in name:
        return "Nippon India Mutual Fund"
    return "UNKNOWN"

def infer_doc_date(filename):
    match = re.search(
        r"(september|sep)[-_ ]?(\d{4})",
        filename,
        flags=re.IGNORECASE
    )
    if match:
        return date(int(match.group(2)), 9, 30)
    return None

def extract_document(path, doc_id):
    pages_output = []
    pdf = pymupdf.open(path)

    with pdfplumber.open(path) as fallback_pdf:
        for page_index, page in enumerate(pdf):
            page_number = page_index + 1
            text = page.get_text("text").strip()
            method = "pymupdf"

            if len(text) < 200:
                fallback_text = (
                    fallback_pdf.pages[page_index].extract_text() or ""
                ).strip()

                if len(fallback_text) > len(text):
                    text = fallback_text
                    method = "pdfplumber"

                if len(text) < 200:
                    method = "low_text_exception"

            # Normalize whitespace while retaining paragraph boundaries.
            text = text.replace("\r\n", "\n").replace("\r", "\n")
            text = re.sub(r"[ \t]+", " ", text)
            text = re.sub(r"\n{3,}", "\n\n", text).strip()

            pages_output.append({
                "doc_id": doc_id,
                "page": page_number,
                "text": text,
                "method": method
            })

    pdf.close()
    return pages_output

def main():
    if not RAW_DIR.exists():
        raise FileNotFoundError(f"Raw document directory not found: {RAW_DIR}")

    pdf_files = sorted(
        RAW_DIR.rglob("*.pdf"),
        key=lambda p: p.relative_to(ROOT).as_posix().lower()
    )

    if not pdf_files:
        raise RuntimeError("No PDF files found.")

    # Preserve manually curated metadata when ingestion is rerun.
    existing_metadata = {}

    if MANIFEST_PATH.exists():
        old_manifest = pd.read_csv(
            MANIFEST_PATH,
            keep_default_na=False
        )
        for _, row in old_manifest.iterrows():
            existing_metadata[row["local_path"]] = {
                field: row.get(field, "")
                for field in ("doc_type", "doc_date", "source_url")
            }

    manifest = []
    all_pages = []

    for doc_id, path in enumerate(pdf_files, start=1):
        print(f"\nProcessing [{doc_id}/{len(pdf_files)}]: {path.name}")

        extracted_pages = extract_document(path, doc_id)
        all_pages.extend(extracted_pages)

        char_count = sum(len(p["text"]) for p in extracted_pages)
        low_text_pages = sum(
            len(p["text"]) < 200 for p in extracted_pages
        )

        methods = sorted(set(p["method"] for p in extracted_pages))
        relative_path = path.relative_to(ROOT).as_posix()

        manifest.append({
            "doc_id": doc_id,
            "amc": infer_amc(path.name),
            "doc_type": "factsheet",
            "doc_date": infer_doc_date(path.name),
            "source_url": existing_metadata.get(relative_path, {}).get("source_url", ""),
            "local_path": relative_path,
            "sha256": file_sha256(path),
            "pages": len(extracted_pages),
            "extracted_chars": char_count,
            "extraction_method": ";".join(methods)
        })

        print(f"  Pages: {len(extracted_pages)}")
        print(f"  Characters: {char_count:,}")
        print(f"  Low-text pages: {low_text_pages}")
        print(f"  Methods: {', '.join(methods)}")

    manifest_df = pd.DataFrame(manifest)

    # Retain curated document type, date and source URL by file path.
    for field in ("doc_type", "doc_date", "source_url"):
        manifest_df[field] = manifest_df["local_path"].map(
            lambda path: existing_metadata.get(path, {}).get(field, "")
        )

    # Infer a date only for documents not previously present in the manifest.
    for index, row in manifest_df.iterrows():
        if row["local_path"] not in existing_metadata:
            inferred = infer_doc_date(Path(row["local_path"]).name)
            manifest_df.at[index, "doc_date"] = (
                inferred.isoformat() if inferred else ""
            )
    manifest_df.to_csv(MANIFEST_PATH, index=False)
    pages_df = pd.DataFrame(
        all_pages,
        columns=["doc_id", "page", "text", "method"]
    )
    pages_df.to_parquet(PAGES_PATH, index=False, engine="pyarrow")

    print("\n=== INGESTION SUMMARY ===")
    print(f"Documents: {len(manifest_df)}")
    print(f"Pages: {len(pages_df)}")
    print(f"Total extracted characters: {pages_df['text'].str.len().sum():,}")
    print(
        "Pages below 200 characters:",
        int((pages_df["text"].str.len() < 200).sum())
    )
    print(f"Manifest: {MANIFEST_PATH}")
    print(f"Pages dataset: {PAGES_PATH}")

if __name__ == "__main__":
    main()
