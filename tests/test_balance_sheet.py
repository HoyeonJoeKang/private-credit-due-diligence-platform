import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.balance_sheet import extract_total_investments_fair_value, detect_unit_multiplier


def run():
    arcc_df = pd.DataFrame(
        [
            ["Investments at fair value", None, None],
            ["Fair Value", "$ 29,499.3", "$ 29,484.8"],
            ["Cash and cash equivalents", "505.0", "638.0"],
        ],
        columns=["CONSOLIDATED BALANCE SHEETS - USD ($)  $ in Millions", "Mar. 31, 2026", "Dec. 31, 2025"],
    )
    arcc_multiplier = detect_unit_multiplier(str(arcc_df.columns[0]))
    assert arcc_multiplier == 1_000_000.0
    arcc_result = extract_total_investments_fair_value(arcc_df, unit_multiplier=arcc_multiplier)
    assert arcc_result["Mar. 31, 2026"] == 29499300000.0

    bxsl_df = pd.DataFrame(
        [
            ["ASSETS", None, None],
            ["Investments at fair value", "$ 13,942,140,000", "$ 14,207,294,000"],
            ["Cash and Cash Equivalent", "351276000", "289605000"],
        ],
        columns=["Condensed Consolidated Statements of Assets and Liabilities - USD ($)",
                 "Mar. 31, 2026", "Dec. 31, 2025"],
    )
    bxsl_multiplier = detect_unit_multiplier(str(bxsl_df.columns[0]))
    assert bxsl_multiplier == 1.0
    bxsl_result = extract_total_investments_fair_value(
        bxsl_df, unit_multiplier=bxsl_multiplier, label_candidates=("investments at fair value",)
    )
    assert bxsl_result["Mar. 31, 2026"] == 13942140000.0

    print("PASS")
    print("ARCC:", arcc_result)
    print("BXSL:", bxsl_result)


if __name__ == "__main__":
    run()
