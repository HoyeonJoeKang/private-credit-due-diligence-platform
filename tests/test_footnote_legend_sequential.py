import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.footnote_legend import parse_footnote_legend


def build_noisy_soi_like_text(repeats: int) -> str:
    chunk = (
        "(2) Common units 09/2021 6,833,284 6.8 14.1 (9) Some description text here "
        "(5) Another company entry appears (2) Yet more schedule content follows "
        "(9) Unicorn Holdco Intermediate II LLC (2) Spread reference appears here "
    )
    return chunk * repeats


def run():
    before_noise = build_noisy_soi_like_text(30)
    after_noise = build_noisy_soi_like_text(30)

    legend_block = (
        "(8) Loan was on non-accrual status as of March 31, 2026. "
        "(9) Loan includes interest rate floor feature. "
        "(10) In addition to the interest earned by the Company on its investment in a "
        "broadly syndicated loan, the Company may also receive fees related to that "
        "investment which are not reflected in the stated interest rate. "
        "(11) Denotes an investment on which the Company receives a fee. "
        "(12) Position or portion thereof is held through a taxable subsidiary. "
        "(13) As of March 31, 2026, the Company had the following unfunded commitments "
        "outstanding to various portfolio companies which, if drawn, would be funded "
        "with cash on hand and borrowings under credit facilities. "
        "(14) Denotes a security which is not indebtedness under the 1940 Act. "
        "(15) Denotes an equity security without a stated interest rate."
    )

    text = before_noise + legend_block + after_noise

    legend = parse_footnote_legend(text)

    assert set(legend.keys()) == {8, 9, 10, 11, 12, 13, 14, 15}, f"got {sorted(legend.keys())}"
    assert legend[8].startswith("Loan was on non-accrual status")
    assert legend[13].startswith("As of March 31, 2026, the Company had the following")
    assert legend[15].startswith("Denotes an equity security")

    print("PASS")
    for k, v in sorted(legend.items()):
        print(k, ":", v[:70])


if __name__ == "__main__":
    run()
