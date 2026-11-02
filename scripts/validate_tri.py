from pathlib import Path
import pandas as pd

folder = Path("data/raw/tri")

for file in sorted(folder.glob("*.csv")):
    df = pd.read_csv(file)
    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")

    tri = pd.to_numeric(df["Total Returns Index"], errors="coerce")

    print(f"\n{file.name}")
    print("Rows:", len(df))
    print("Index:", df["IndexName"].dropna().unique())
    print("Start:", df["Date"].min().date())
    print("End:", df["Date"].max().date())
    print("Invalid dates:", df["Date"].isna().sum())
    print("Missing TRI values:", tri.isna().sum())
    print("Duplicate dates:", df["Date"].duplicated().sum())