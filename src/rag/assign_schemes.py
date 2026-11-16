from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
UNIVERSE_PATH = ROOT / "config" / "universe.csv"
MANIFEST_PATH = ROOT / "data" / "docs_manifest.csv"
PAGES_PATH = ROOT / "data" / "processed" / "pages.parquet"
OUTPUT_PATH = ROOT / "data" / "processed" / "pages_assigned.parquet"


# Monthly factsheet assignments.
# Keys are document IDs, not AMC names. Page numbers are 1-based.
FACTSHEET_PAGES = {
    2: {
        "amc": "SBI",
        "schemes": {
            "119598": [8, 9],
            "119718": [18, 19],
            "119716": [26, 27],
        },
    },
    3: {
        "amc": "HDFC",
        "schemes": {
            "119018": [11, 12],
            "118955": [7, 8],
            "118989": [13, 14],
        },
    },
    4: {
        "amc": "ICICI",
        "schemes": {
            "120586": [14],
            "148990": [15],
            "120381": [26],
        },
    },
    12: {
        "amc": "KOTAK",
        "schemes": {
            "148978": [114],
        },
    },
    13: {
        "amc": "NIPPON",
        "schemes": {
            "118632": [6, 7],
            "149094": [30, 31],
            "118668": [15, 16],
            "118741": [129, 130],
        },
    },
}

# Additional factsheet pages verified directly from page contents.
# Page numbers are 1-based. These are not TOC-derived assignments.
CONTENT_VERIFIED_PAGES = {
    13: {
        "amc": "NIPPON",
        "schemes": {
            "149094": [323],
            "118741": [331],
        },
    },
}

# Standalone SID/KIM documents.
# All pages belong to the identified scheme family.
# scheme_code deliberately remains NULL because the documents
# are not restricted to one plan.
STANDALONE_DOCUMENTS = {
    5: {"amc": "ICICI", "pair_id": 10, "name": "ICICI Prudential Mid Cap Fund"},
    6: {"amc": "ICICI", "pair_id": 10, "name": "ICICI Prudential Mid Cap Fund"},
    7: {"amc": "ICICI", "pair_id": 16, "name": "ICICI Prudential Nifty Next 50 Index Fund"},
    8: {"amc": "ICICI", "pair_id": 16, "name": "ICICI Prudential Nifty Next 50 Index Fund"},
    9: {"amc": "HDFC", "pair_id": 1, "name": "HDFC Large Cap Fund"},
    10: {"amc": "HDFC", "pair_id": 13, "name": "HDFC Nifty 50 Index Fund"},
    11: {"amc": "SBI", "pair_id": 3, "name": "SBI Large Cap Fund"},
    14: {"amc": "NIPPON", "pair_id": 8, "name": "Nippon India Flexi Cap Fund"},
    15: {"amc": "NIPPON", "pair_id": 14, "name": "Nippon India Index Fund - Nifty 50 Plan"},
    16: {"amc": "HDFC", "pair_id": 13, "name": "HDFC Nifty 50 Index Fund"},
    17: {"amc": "SBI", "pair_id": 3, "name": "SBI Large Cap Fund"},
}


# Disclosure-only pages remain AMC-level, but retain scheme-family metadata.
DISCLOSURE_PAGES = {
    13: {
        "118632": [8],
        "149094": [32],
        "118668": [17],
        "118741": [131],
    }
}


AMC_KEYS = {
    "SBI Mutual Fund": "SBI",
    "HDFC Mutual Fund": "HDFC",
    "ICICI Prudential Mutual Fund": "ICICI",
    "Kotak Mahindra Mutual Fund": "KOTAK",
    "Nippon India Mutual Fund": "NIPPON",
}


def clean_code(value):
    if pd.isna(value):
        return None
    return str(value).strip().removesuffix(".0")


def main():
    universe = pd.read_csv(UNIVERSE_PATH, dtype={"scheme_code": str})
    manifest = pd.read_csv(MANIFEST_PATH)
    pages = pd.read_parquet(PAGES_PATH)

    required_universe = {
        "scheme_code", "pair_id", "scheme_name", "amc", "plan"
    }
    required_manifest = {"doc_id", "amc"}
    required_pages = {"doc_id", "page", "text"}

    for label, frame, required in [
        ("universe", universe, required_universe),
        ("manifest", manifest, required_manifest),
        ("pages", pages, required_pages),
    ]:
        missing = required - set(frame.columns)
        if missing:
            raise ValueError(
                f"{label} is missing columns: {sorted(missing)}"
            )

    universe["scheme_code"] = universe["scheme_code"].map(clean_code)

    if universe["scheme_code"].duplicated().any():
        raise ValueError("Duplicate scheme_code values in universe.csv")

    family_counts = universe.groupby("pair_id")["plan"].nunique()
    if not family_counts.eq(2).all():
        raise ValueError("Every pair_id must contain exactly two plans")

    family_lookup = (
        universe.drop_duplicates("pair_id")
        .set_index("pair_id")[["scheme_name", "amc"]]
        .to_dict("index")
    )

    code_lookup = (
        universe.set_index("scheme_code")[["pair_id", "scheme_name", "amc"]]
        .to_dict("index")
    )

    manifest["amc_key"] = manifest["amc"].map(AMC_KEYS)

    if manifest["amc_key"].isna().any():
        bad = manifest.loc[
            manifest["amc_key"].isna(), "amc"
        ].unique()
        raise ValueError(f"Unmapped AMC labels: {bad.tolist()}")

    if manifest["doc_id"].duplicated().any():
        raise ValueError("Duplicate doc_id values in docs_manifest.csv")

    pages = pages.merge(
        manifest[["doc_id", "amc", "amc_key"]],
        on="doc_id",
        how="left",
        validate="many_to_one",
    )

    if pages["amc_key"].isna().any():
        raise ValueError("Extracted pages have no matching manifest document")

    if pages.duplicated(["doc_id", "page"]).any():
        raise ValueError("Duplicate document-page rows detected")

    pages["pair_id"] = pd.NA
    pages["scheme_code"] = pd.NA
    pages["scheme_name"] = pd.NA
    pages["related_pair_id"] = pd.NA
    pages["related_scheme_code"] = pd.NA
    pages["assignment_status"] = "amc_level"
    pages["page_role"] = "amc_general_or_unclassified"
    pages["assignment_basis"] = "not_scheme_specific"

    available_docs = set(pages["doc_id"].unique())

    # Apply document-specific monthly factsheet assignments.
    for doc_id, document in FACTSHEET_PAGES.items():
        if doc_id not in available_docs:
            raise ValueError(f"Expected factsheet doc_id {doc_id} is missing")

        doc_mask = pages["doc_id"].eq(doc_id)

        actual_amc = pages.loc[doc_mask, "amc_key"].iloc[0]
        if actual_amc != document["amc"]:
            raise ValueError(
                f"AMC mismatch for factsheet doc {doc_id}: "
                f"expected={document['amc']}, actual={actual_amc}"
            )

        for code, page_numbers in document["schemes"].items():
            if code not in code_lookup:
                raise ValueError(f"Scheme code {code} absent from universe")

            family = code_lookup[code]
            expected_amc = AMC_KEYS.get(family["amc"])

            if expected_amc != document["amc"]:
                raise ValueError(
                    f"Universe AMC mismatch for scheme code {code}"
                )

            for page_number in page_numbers:
                mask = doc_mask & pages["page"].eq(page_number)

                if mask.sum() != 1:
                    raise ValueError(
                        f"Expected exactly one page {page_number} "
                        f"in document {doc_id}; found {int(mask.sum())}"
                    )

                if pages.loc[mask, "pair_id"].notna().any():
                    raise ValueError(
                        f"Overlapping assignment: doc {doc_id}, "
                        f"page {page_number}"
                    )

                pages.loc[mask, "pair_id"] = family["pair_id"]
                pages.loc[mask, "scheme_name"] = family["scheme_name"]
                pages.loc[mask, "assignment_status"] = "toc_verified"
                pages.loc[mask, "page_role"] = "scheme_section"
                pages.loc[
                    mask, "assignment_basis"
                ] = "verified_document_specific_contents_and_section"

                if page_number == min(page_numbers):
                    pages.loc[
                        mask, "page_role"
                    ] = "scheme_section_primary"
                else:
                    pages.loc[
                        mask, "page_role"
                    ] = "scheme_section_continuation"

    # Apply additional factsheet assignments verified from page contents.
    for doc_id, document in CONTENT_VERIFIED_PAGES.items():
        if doc_id not in available_docs:
            raise ValueError(
                f"Expected content-verified factsheet doc_id {doc_id} is missing"
            )

        doc_mask = pages["doc_id"].eq(doc_id)

        actual_amc = pages.loc[doc_mask, "amc_key"].iloc[0]
        if actual_amc != document["amc"]:
            raise ValueError(
                f"AMC mismatch for content-verified factsheet doc {doc_id}"
            )

        for code, page_numbers in document["schemes"].items():
            if code not in code_lookup:
                raise ValueError(
                    f"Scheme code {code} absent from universe"
                )

            family = code_lookup[code]

            if AMC_KEYS.get(family["amc"]) != document["amc"]:
                raise ValueError(
                    f"Universe AMC mismatch for scheme code {code}"
                )

            for page_number in page_numbers:
                mask = doc_mask & pages["page"].eq(page_number)

                if mask.sum() != 1:
                    raise ValueError(
                        f"Expected exactly one page {page_number} "
                        f"in document {doc_id}; found {int(mask.sum())}"
                    )

                if pages.loc[mask, "pair_id"].notna().any():
                    raise ValueError(
                        f"Overlapping content assignment: "
                        f"doc {doc_id}, page {page_number}"
                    )

                page_text = str(pages.loc[mask, "text"].iloc[0])

                if family["scheme_name"].casefold() not in page_text.casefold():
                    raise ValueError(
                        f"Scheme name not found on doc {doc_id}, "
                        f"page {page_number}: {family['scheme_name']}"
                    )

                pages.loc[mask, "pair_id"] = family["pair_id"]
                pages.loc[mask, "scheme_name"] = family["scheme_name"]
                pages.loc[mask, "assignment_status"] = "content_verified"
                pages.loc[mask, "page_role"] = "scheme_section_primary"
                pages.loc[
                    mask, "assignment_basis"
                ] = "verified_page_content_scheme_identity"

    # Assign standalone SID/KIM documents to scheme families.
    for doc_id, document in STANDALONE_DOCUMENTS.items():
        if doc_id not in available_docs:
            raise ValueError(f"Expected standalone doc_id {doc_id} is missing")

        mask = pages["doc_id"].eq(doc_id)

        if not mask.any():
            raise ValueError(f"No extracted pages for standalone doc {doc_id}")

        actual_amc = pages.loc[mask, "amc_key"].iloc[0]
        if actual_amc != document["amc"]:
            raise ValueError(
                f"AMC mismatch for standalone doc {doc_id}: "
                f"expected={document['amc']}, actual={actual_amc}"
            )

        pair_id = document["pair_id"]
        if pair_id not in family_lookup:
            raise ValueError(f"pair_id {pair_id} absent from universe")

        family = family_lookup[pair_id]

        if AMC_KEYS.get(family["amc"]) != document["amc"]:
            raise ValueError(
                f"Universe AMC mismatch for standalone doc {doc_id}"
            )

        if pages.loc[mask, "pair_id"].notna().any():
            raise ValueError(
                f"Standalone document {doc_id} overlaps another assignment"
            )

        pages.loc[mask, "pair_id"] = pair_id
        pages.loc[mask, "scheme_name"] = family["scheme_name"]
        pages.loc[mask, "assignment_status"] = "scheme_family_verified"
        pages.loc[mask, "page_role"] = "scheme_document_page"
        pages.loc[
            mask, "assignment_basis"
        ] = "standalone_sid_kim_document_identity_verified"

        first_page = pages.loc[mask, "page"].min()
        pages.loc[
            mask & pages["page"].eq(first_page), "page_role"
        ] = "scheme_document_primary"

    # Disclosure pages remain AMC-level but carry related scheme metadata.
    for doc_id, schemes in DISCLOSURE_PAGES.items():
        if doc_id not in available_docs:
            raise ValueError(f"Disclosure document {doc_id} is missing")

        for code, page_numbers in schemes.items():
            if code not in code_lookup:
                raise ValueError(f"Disclosure scheme code {code} absent")

            family = code_lookup[code]

            for page_number in page_numbers:
                mask = (
                    pages["doc_id"].eq(doc_id)
                    & pages["page"].eq(page_number)
                )

                if mask.sum() != 1:
                    raise ValueError(
                        f"Expected exactly one disclosure page "
                        f"{page_number} in doc {doc_id}"
                    )

                if pages.loc[mask, "pair_id"].notna().any():
                    raise ValueError(
                        f"Disclosure page {doc_id}:{page_number} "
                        f"already has a family assignment"
                    )

                pages.loc[mask, "related_pair_id"] = family["pair_id"]
                pages.loc[mask, "related_scheme_code"] = code
                pages.loc[mask, "assignment_status"] = "amc_level_related"
                pages.loc[mask, "page_role"] = "scheme_disclosure"
                pages.loc[
                    mask, "assignment_basis"
                ] = "verified_disclosure_heading"

    # Explicitly ensure the August SBI factsheet remains unassigned
    # until its scheme sections are independently verified.
    if pages.loc[pages["doc_id"].eq(1), "pair_id"].notna().any():
        raise ValueError(
            "SBI August factsheet has an unverified scheme assignment"
        )

    # Standalone documents must never be assigned to a single plan.
    for doc_id in STANDALONE_DOCUMENTS:
        mask = pages["doc_id"].eq(doc_id)
        if pages.loc[mask, "scheme_code"].notna().any():
            raise ValueError(
                f"Standalone document {doc_id} incorrectly has scheme_code"
            )

    # All assigned pair IDs must exist in the frozen universe.
    valid_pair_ids = set(universe["pair_id"].dropna().unique())
    assigned_pair_ids = set(pages["pair_id"].dropna().unique())

    if not assigned_pair_ids.issubset(valid_pair_ids):
        raise ValueError("Unknown pair_id found in page assignments")

    # Verify every expected standalone document was assigned.
    for doc_id in STANDALONE_DOCUMENTS:
        if not pages.loc[
            pages["doc_id"].eq(doc_id), "pair_id"
        ].notna().all():
            raise ValueError(
                f"Some pages in standalone document {doc_id} "
                f"were not assigned to its scheme family"
            )

    pages = pages.drop(columns=["amc_key"])
    pages.to_parquet(OUTPUT_PATH, index=False)

    print("\n=== DETERMINISTIC SCHEME-FAMILY ASSIGNMENT ===")
    print(f"Total pages: {len(pages)}")
    print(f"Scheme-family pages: {pages['pair_id'].notna().sum()}")
    print(
        "Standalone SID/KIM pages:",
        pages["assignment_status"].eq("scheme_family_verified").sum(),
    )
    print(
        "Factsheet scheme pages:",
        pages["assignment_status"].eq("toc_verified").sum(),
    )
    print(
    "Factsheet content-verified pages:",
    pages["assignment_status"].eq("content_verified").sum(),
    )
    print(
        "AMC-level related disclosure pages:",
        pages["assignment_status"].eq("amc_level_related").sum(),
    )
    print(
        "AMC-level general/unclassified pages:",
        pages["assignment_status"].eq("amc_level").sum(),
    )

    print("\nScheme-family coverage:")
    print(
        pages.dropna(subset=["pair_id"])
        .groupby(["pair_id", "scheme_name", "assignment_status"])
        .size()
        .to_string()
    )

    print("\nStandalone document coverage:")
    for doc_id, document in STANDALONE_DOCUMENTS.items():
        count = pages.loc[pages["doc_id"].eq(doc_id), "pair_id"].notna().sum()
        print(
            f"Doc {doc_id}: {document['name']} "
            f"(pair_id={document['pair_id']}): {count} pages"
        )

    print("\nSBI August factsheet: retained as AMC-level, not scheme-assigned.")
    print(f"\nSaved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
