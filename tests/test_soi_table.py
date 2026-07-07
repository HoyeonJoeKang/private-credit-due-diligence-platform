import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.soi_table import find_header_row, collapse_grouped_columns


def build_sample_df() -> pd.DataFrame:
    rows = [
        [None] * 16,
        ["Company", "Company", "Company", "Business Description", "Business Description",
         "Investment", "Investment", "Coupon", "Coupon", "Fair Value", "Fair Value",
         None, "Amortized Cost", "Amortized Cost", None, "% of Net Assets"],
        ["ACP Avenu Midco LLC (13)", "ACP Avenu Midco LLC (13)", "ACP Avenu Midco LLC (13)",
         "Provider of tech solutions", "Provider of tech solutions",
         "First lien senior secured loan", "First lien senior secured loan",
         "8.66%", "8.66%", "$", "13.1", "(2)(9)", "$", "13.0", None, None],
        [None] * 8 + ["$", "3.6", "(2)(9)", "$", "3.5", None, None],
        [None, None, None, None, None, None, None, None, None,
         "16.7", "16.7", None, "16.5", "16.5", None, None],
    ]
    return pd.DataFrame(rows)


def run():
    df = build_sample_df()
    header_row = find_header_row(df)
    assert header_row == 1

    result = collapse_grouped_columns(df, header_row)
    print(result)
    print()
    print(result.columns.tolist())

    assert result.loc[0, "Company"] == "ACP Avenu Midco LLC (13)"
    assert result.loc[0, "Fair Value"] == "13.1"
    assert result.loc[0, "Footnotes"] == "(2)(9)"
    assert result.loc[1, "Fair Value"] == "3.6"
    assert result.loc[2, "Fair Value"] == "16.7"
    assert pd.isna(result.loc[2, "Company"])

    print("PASS")


if __name__ == "__main__":
    run()
