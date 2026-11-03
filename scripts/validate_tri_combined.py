
from pathlib import Path
import pandas as pd

folder = Path("data/raw/tri")
all_data = []

for file in sorted(folder.glob("*.csv")):
    df = pd.read_csv(file)

    df["Date"] = pd.to_datetime(
        df["Date"], dayfirst=True, errors="coerce"
    )
    df["Total Returns Index"] = pd.to_numeric(
        df["Total Returns Index"], errors="coerce"
    )

    df["Source File"] = file.name
    all_data.append(df[[
        "IndexName", "Date", "Total Returns Index", "Source File"
    ]])

data = pd.concat(all_data, ignore_index=True)

for index_name, group in data.groupby("IndexName"):
    print(f"\n{'=' * 60}")
    print(index_name)

    # Identify overlapping dates
    overlaps = group[group.duplicated("Date", keep=False)]

    print("Total file observations:", len(group))
    print("Unique dates:", group["Date"].nunique())
    print("Start:", group["Date"].min().date())
    print("End:", group["Date"].max().date())
    print("Overlapping date records:", len(overlaps))

    # Check whether overlapping TRI values agree
    conflicts = (
        group.groupby("Date")["Total Returns Index"]
        .nunique()
        .loc[lambda x: x > 1]
    )

    print("Conflicting TRI dates:", len(conflicts))

    if len(conflicts):
        print(conflicts)

    # Report repeated dates and their source files
    if not overlaps.empty:
        print("\nOverlapping records:")
        print(
            overlaps.sort_values("Date")[
                ["Date", "Total Returns Index", "Source File"]
            ].to_string(index=False)
        )



print("\nFINAL TRI VALIDATION SUMMARY")
print("-" * 55)

for index_name, group in data.groupby("IndexName"):
    unique_dates = group.drop_duplicates("Date")

    print(
        f"{index_name}: "
        f"{unique_dates['Date'].min().date()} to "
        f"{unique_dates['Date'].max().date()} | "
        f"{len(unique_dates)} unique dates | "
        f"{group['Date'].duplicated().sum()} duplicate records"
    )

print("\nTotal indices:", data["IndexName"].nunique())
print("Total raw CSV files:", len(list(folder.glob("*.csv"))))
