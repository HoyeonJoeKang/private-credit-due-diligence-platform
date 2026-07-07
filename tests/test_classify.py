import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.soi_table import classify_and_assign


def build_real_sample() -> pd.DataFrame:
    data = [
        ("Software and Services", None, None, None),
        ("ACP Avenu Midco LLC (13)", "First lien senior secured loan", 13.0, 13.1),
        (None, "First lien senior secured loan", 3.5, 3.6),
        (None, None, 16.5, 16.7),
        ("Actfy Buyer, Inc. (13)", "First lien senior secured loan", 20.9, 20.9),
        ("Activate Holdings (US) Corp.", "First lien senior secured loan", 42.0, 42.0),
        (None, "First lien senior secured loan", 6.8, 6.8),
        (None, "Limited partnership interest", 10.2, 12.8),
        (None, None, 59.0, 61.6),
        ("Adonis Bidco Inc. (13)", "First lien senior secured loan", 11.1, 10.8),
        (None, "First lien senior secured loan", 237.3, 232.5),
        (None, None, 248.4, 243.3),
        ("AI Titan Parent, Inc. (13)", "First lien senior secured loan", 7.3, 7.2),
        ("Total Investments", None, 29647.5, 29499.3),
    ]
    return pd.DataFrame(data, columns=["Company", "Investment", "Amortized Cost", "Fair Value"])


def run():
    df = build_real_sample()
    result = classify_and_assign(df)
    print(result[["Company", "Sector", "Company_Filled", "RowType"]])

    assert result.loc[0, "RowType"] == "sector_header"
    assert result.loc[0, "Sector"] == "Software and Services"

    assert result.loc[1, "RowType"] == "company_row"
    assert result.loc[1, "Company_Filled"] == "ACP Avenu Midco LLC (13)"
    assert result.loc[1, "Sector"] == "Software and Services"

    assert result.loc[2, "RowType"] == "tranche_continuation"
    assert result.loc[2, "Company_Filled"] == "ACP Avenu Midco LLC (13)"

    assert result.loc[3, "RowType"] == "company_subtotal"
    assert result.loc[3, "Company_Filled"] == "ACP Avenu Midco LLC (13)"

    assert result.loc[7, "RowType"] == "tranche_continuation"
    assert result.loc[7, "Company_Filled"] == "Activate Holdings (US) Corp."

    assert result.loc[8, "RowType"] == "company_subtotal"

    last_idx = result.index[-1]
    assert result.loc[last_idx, "RowType"] == "grand_total"
    assert pd.isna(result.loc[last_idx, "Company_Filled"])

    print("PASS")


if __name__ == "__main__":
    run()
