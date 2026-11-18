
from pathlib import Path
import pdfplumber

folder = Path("data/raw_docs/probe")

targets = [
    "SBI FLEXICAP",
    "ICICI PRUDENTIAL FLEXI CAP",
    "NIPPON INDIA GROWTH MID CAP",
]

for pdf_path in folder.glob("*.pdf"):
    print(f"\n{'='*90}\nFILE: {pdf_path.name}\n{'='*90}")

    with pdfplumber.open(pdf_path) as pdf:
        for page_no, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            upper = text.upper()

            if any(target in upper for target in targets):
                print(f"\n--- PAGE {page_no} ---")
                print(text[:10000])
