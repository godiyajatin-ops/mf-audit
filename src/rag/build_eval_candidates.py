from pathlib import Path
import re

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CHUNKS_PATH = ROOT / "data/index/chunksB.parquet"
UNIVERSE_PATH = ROOT / "config/universe.csv"
OUTPUT_PATH = ROOT / "results/b1_eval_candidates.csv"

PATTERNS = {
    "benchmark": r"\bbenchmark\b|\bTRI\b|total returns index",
    "exit_load": r"exit load|load structure|redemption|switch.?out",
    "expense_ratio": r"expense ratio|total expense|TER\b|direct plan",
    "objective": r"investment objective|objective of the scheme|"
                 r"long.term capital appreciation|investment strategy",
}

def main():
    chunks = pd.read_parquet(CHUNKS_PATH)
    universe = pd.read_csv(UNIVERSE_PATH)

    rows = []

    for _, scheme in universe.drop_duplicates("pair_id").iterrows():
        pair_id = int(scheme["pair_id"])
        amc = scheme["amc"]
        name = str(scheme["scheme_name"])

        family = chunks["pair_id"].eq(pair_id).fillna(False)
        related = chunks["related_pair_id"].eq(pair_id).fillna(False)
        general = (
            chunks["pair_id"].isna()
            & chunks["related_pair_id"].isna()
            & chunks["amc"].eq(amc)
        )

        eligible = chunks[family | related | general].copy()

        for category, pattern in PATTERNS.items():
            keyword_match = eligible["text"].str.contains(
                pattern, case=False, regex=True, na=False
            )
            name_match = eligible["text"].str.contains(
                re.escape(name), case=False, regex=True, na=False
            )

            candidates = eligible[keyword_match & (family[eligible.index] | related[eligible.index] | name_match)].copy()

            if candidates.empty:
                continue

            candidates["name_match"] = name_match.loc[candidates.index].astype(int)
            candidates["keyword_count"] = candidates["text"].str.count(
                pattern, flags=re.IGNORECASE
            )
            candidates = candidates.sort_values(
                ["name_match", "keyword_count"],
                ascending=False,
            ).head(5)

            for _, chunk in candidates.iterrows():
                text = str(chunk["text"]).replace("\n", " ")
                rows.append({
                    "pair_id": pair_id,
                    "scheme_name": name,
                    "scheme_code_direct": str(
                        universe[
                            (universe["pair_id"] == pair_id)
                            & (universe["plan"] == "Direct")
                        ]["scheme_code"].iloc[0]
                    ),
                    "amc": amc,
                    "category": category,
                    "chunk_id": chunk["chunk_id"],
                    "doc_id": chunk["doc_id"],
                    "page": chunk["page"],
                    "section": chunk["section"],
                    "assignment_status": chunk["assignment_status"],
                    "name_match": int(name_match.loc[chunk.name]),
                    "keyword_count": int(chunk["keyword_count"]),
                    "candidate_text": text[:1600],
                    "expected": "VERIFY",
                })

    output = pd.DataFrame(rows)

    if output.empty:
        raise RuntimeError("No candidate pages found")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(OUTPUT_PATH, index=False)

    print("Candidate extraction complete")
    print(f"Rows: {len(output)}")
    print(f"Output: {OUTPUT_PATH}")
    print("\nCandidates by category:")
    print(output.groupby("category").size().to_string())
    print("\nCandidates by assignment status:")
    print(output.groupby("assignment_status").size().to_string())


if __name__ == "__main__":
    main()
