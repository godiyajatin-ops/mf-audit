from pathlib import Path
import pandas as pd


CONTROL_BAND_PP = 1.0


def main():
    alpha_path = Path("results/alpha.csv")
    facts_path = Path("data/manual/scheme_facts.csv")

    if not alpha_path.exists():
        raise FileNotFoundError("Run regression.py and fdr.py first.")

    alpha = pd.read_csv(alpha_path)
    facts = pd.read_csv(facts_path)

    passive = alpha[
        (alpha["is_passive"].astype(bool))
        & (alpha["plan"] == "Direct")
    ].copy()

    if len(passive) != 4:
        raise ValueError(
            f"Expected 4 passive Direct schemes, found {len(passive)}"
        )

    facts = facts[["pair_id", "ter_direct_pct"]].copy()
    facts["ter_direct_pct"] = pd.to_numeric(
        facts["ter_direct_pct"], errors="coerce"
    )

    result = passive.merge(
        facts,
        on="pair_id",
        how="left",
        validate="one_to_one"
    )

    result["expected_alpha_ann"] = -result["ter_direct_pct"] / 100
    result["deviation_pp"] = (
        result["alpha_ann"] - result["expected_alpha_ann"]
    ) * 100

    result["control_status"] = "PENDING"

    available = result["ter_direct_pct"].notna()
    result.loc[available, "control_status"] = "FAIL"

    passed = (
        available
        & (result["deviation_pp"].abs() <= CONTROL_BAND_PP)
    )
    result.loc[passed, "control_status"] = "PASS"

    result["control_band_pp"] = CONTROL_BAND_PP
    result["provisional"] = True

    columns = [
        "scheme_code", "scheme_name", "amc", "pair_id",
        "alpha_ann", "ter_direct_pct", "expected_alpha_ann",
        "deviation_pp", "control_band_pp",
        "control_status", "provisional"
    ]

    output = result[columns]
    Path("results").mkdir(exist_ok=True)
    output.to_csv("results/control_check.csv", index=False)

    print("PASSIVE CONTROL CHECK GENERATED")
    print(output["control_status"].value_counts().to_dict())
    print("Output: results/control_check.csv")


if __name__ == "__main__":
    main()
