import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.footnote_legend import parse_footnote_legend


def run():
    distractor_region = (
        "(2) Common units 09/2021 6,833,284 6.8 14.1 (3) Some description text here "
        "(4) Another company entry appears (5) Yet more schedule content follows "
        "(6) Unicorn Holdco Intermediate II LLC (7) Spread reference appears here "
    ) * 20
    filler = "x" * 10000
    legend_block = (
        "(8) Loan was on non-accrual status as of March 31, 2026. "
        "(9) Loan includes interest rate floor feature. "
        "(10) In addition to the interest earned by the Company on its investment. "
        "(11) Denotes an investment on which the Company receives a fee. "
        "(12) Position or portion thereof is held through a taxable subsidiary."
    )
    text = distractor_region + filler + legend_block

    legend = parse_footnote_legend(text)

    assert 2 not in legend, "SOI table footnote references should not be picked up as the legend"
    assert set(legend.keys()) == {8, 9, 10, 11, 12}
    assert legend[8].startswith("Loan was on non-accrual status")
    assert legend[9].startswith("Loan includes interest rate floor feature")
    assert legend[11].startswith("Denotes an investment on which the Company receives a fee")

    print("PASS")
    for k, v in sorted(legend.items()):
        print(k, ":", v)


if __name__ == "__main__":
    run()
