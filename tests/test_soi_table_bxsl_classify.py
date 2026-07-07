import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.soi_table_bxsl import classify_and_assign_bxsl


def build_sample():
    rows = [
        {"Investments": None, "Cost": None},
        {"Investments": "First Lien Debt", "Cost": "First Lien Debt"},
        {"Investments": "First Lien Debt - non-controlled/non-affiliated",
         "Cost": "First Lien Debt - non-controlled/non-affiliated"},
        {"Investments": "Aerospace & Defense", "Cost": "Aerospace & Defense"},
        {"Investments": "Aevex Holdings, LLC", "Cost": "46713"},
        {"Investments": "Aevex Holdings, LLC", "Cost": "107661"},
        {"Investments": "Corfin Holdings, Inc.", "Cost": "259721"},
        {"Investments": None, "Cost": "567184"},
        {"Investments": "Air Freight & Logistics", "Cost": "Air Freight & Logistics"},
        {"Investments": "ENV Bidco, AB", "Cost": "1103"},
        {"Investments": "Total First Lien Debt - non-controlled/affiliated", "Cost": "9999999"},
        {"Investments": "Total First Lien Debt", "Cost": "10999999"},
        {"Investments": "Total Portfolio Investments, Cash and Cash Equivalents", "Cost": "13942140"},
    ]
    return pd.DataFrame(rows)


def run():
    df = build_sample()
    result = classify_and_assign_bxsl(df)
    print(result[["Investments", "AssetClass", "Sector", "RowType"]])

    assert result.loc[0, "RowType"] == "blank"
    assert result.loc[1, "RowType"] == "banner"
    assert result.loc[3, "RowType"] == "banner"
    assert result.loc[3, "Sector"] == "Aerospace & Defense"

    assert result.loc[4, "RowType"] == "company_row"
    assert result.loc[4, "AssetClass"] == "First Lien Debt"
    assert result.loc[4, "Sector"] == "Aerospace & Defense"
    assert result.loc[5, "Sector"] == "Aerospace & Defense"

    assert result.loc[7, "RowType"] == "sector_subtotal"

    assert result.loc[8, "RowType"] == "banner"
    assert result.loc[9, "RowType"] == "company_row"
    assert result.loc[9, "Sector"] == "Air Freight & Logistics"

    assert result.loc[10, "RowType"] == "asset_class_subtotal"
    assert result.loc[11, "RowType"] == "asset_class_subtotal"
    assert result.loc[12, "RowType"] == "grand_total"

    print("PASS")


if __name__ == "__main__":
    run()
