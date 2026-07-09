import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.balance_sheet import extract_line_item


def run():
    arcc_df = pd.DataFrame(
        [
            ["Total assets", "30679.0", "31235.0"],
            ["Debt", "15848.0", "15991.0"],
            ["Cash and cash equivalents", "505.0", "638.0"],
        ],
        columns=["CONSOLIDATED BALANCE SHEETS - USD ($) $ in Millions", "Mar. 31, 2026", "Dec. 31, 2025"],
    )
    debt = extract_line_item(arcc_df, label_prefixes=("debt",))
    assert debt["Mar. 31, 2026"] == 15848.0

    bxsl_df = pd.DataFrame(
        [
            ["Total assets", "14436610000", "14656463000"],
            ["Debt (net of unamortized debt issuance costs of $41,840 and $39,900, respectively)",
             "8033886000", "8080129000"],
            ["Cash and Cash Equivalent", "351276000", "289605000"],
        ],
        columns=["Condensed Consolidated Statements of Assets and Liabilities - USD ($)",
                 "Mar. 31, 2026", "Dec. 31, 2025"],
    )
    debt_bxsl = extract_line_item(bxsl_df, label_prefixes=("debt",))
    assert debt_bxsl["Mar. 31, 2026"] == 8033886000.0

    total_assets_arcc = extract_line_item(arcc_df, label_prefixes=("total assets",))
    assert total_assets_arcc["Mar. 31, 2026"] == 30679.0

    df_with_nan = pd.DataFrame(
        [
            ["Total assets", "30679.0", "31235.0"],
            ["Debt", "15848.0", "15991.0"],
            ["Cash and cash equivalents", "505.0", "638.0"],
            ["Interest receivable", "120.0", "115.0"],
            ["Total liabilities", "16500.0", "16700.0"],
            [np.nan, np.nan, np.nan],
            ["[1] Some footnote text unrelated to any line item", np.nan, np.nan],
        ],
        columns=["CONSOLIDATED BALANCE SHEETS - USD ($) $ in Millions", "Mar. 31, 2026", "Dec. 31, 2025"],
    )
    debt_with_nan = extract_line_item(df_with_nan, label_prefixes=("debt",))
    assert debt_with_nan["Mar. 31, 2026"] == 15848.0

    print("PASS")
    print("ARCC debt:", debt)
    print("BXSL debt:", debt_bxsl)
    print("With NaN row present:", debt_with_nan)


if __name__ == "__main__":
    run()
