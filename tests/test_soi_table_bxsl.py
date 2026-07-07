import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.soi_table import find_header_row_generic, collapse_grouped_columns


def build_bxsl_sample():
    header = ["Investments (1)(19)"] * 3 + [None] * 3 + ["Footnotes"] * 3 + [None] * 3 \
        + ["Reference Rate and Spread (2)"] * 6 + [None] * 3 \
        + ["Fair Value"] * 3
    row1 = ["Aevex Holdings, LLC"] * 3 + [None] * 3 + ["(4)(11)"] * 3 + [None] * 3 \
        + ["SOFR +"] * 3 + ["6.00%"] * 3 + [None] * 3 \
        + ["$", "46713", "46713"]
    return pd.DataFrame([[None] * len(header), header, row1])


def run():
    df = build_bxsl_sample()
    hr = find_header_row_generic(df, ["Investments", "Fair Value"])
    assert hr == 1

    clean = collapse_grouped_columns(df, hr)
    print(clean)

    assert clean.loc[0, "Investments"] == "Aevex Holdings, LLC"
    assert clean.loc[0, "Footnotes"] == "(4)(11)"
    assert clean.loc[0, "Reference Rate and Spread"] == "SOFR + 6.00%"
    assert clean.loc[0, "Fair Value"] == "46713"

    print("PASS")


if __name__ == "__main__":
    run()
