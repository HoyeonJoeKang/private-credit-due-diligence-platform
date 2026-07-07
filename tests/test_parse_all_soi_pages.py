import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.fetch_soi_full import parse_all_soi_pages


def build_page(company_names, header_extra_row=True):
    rows = []
    if header_extra_row:
        rows.append([None] * 5)
    rows.append(["Company", "Business Description", "Investment", "Amortized Cost", "Fair Value"])
    for name in company_names:
        rows.append([name, "desc", "First lien senior secured loan", "9.0", "10.0"])
    return pd.DataFrame(rows)


def build_total_page():
    return pd.DataFrame([
        [None] * 5,
        ["Company", "Business Description", "Investment", "Amortized Cost", "Fair Value"],
        ["Total Investments", None, None, "95.0", "100.0"],
    ])


def run():
    page1 = build_page(["Alpha Corp"])
    page2 = build_total_page()
    page3 = build_page(["Alpha Corp"])
    page4 = build_total_page()

    all_tables = [page1, page2, page3, page4]
    page_indices = [0, 1, 2, 3]

    result = parse_all_soi_pages(all_tables, page_indices)
    source_tables_used = sorted(result["source_table"].unique().tolist())

    assert source_tables_used == [0, 1], f"second schedule incorrectly included: {source_tables_used}"
    assert (result["RowType"] == "grand_total").sum() == 1

    print("PASS")
    print(result[["Company", "RowType", "source_table"]])


if __name__ == "__main__":
    run()
