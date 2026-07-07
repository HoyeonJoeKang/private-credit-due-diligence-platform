import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.footnote_legend import find_non_accrual_footnote_candidates, footnotes_contain_number


def run():
    sample_text = (
        "nted. SOFR based contracts may include a credit spread adjustment that is charged in addition "
        "to the base rate and the stated spread. (8) Loan was on non-accrual status as of March 31, 2026. "
        "(9) Loan includes interest rate floor feature. (10) In addi"
    )

    candidates = find_non_accrual_footnote_candidates(sample_text)
    assert candidates == [8]

    assert footnotes_contain_number("(2)(9)", 8) is False
    assert footnotes_contain_number("(2)(8)(9)", 8) is True
    assert footnotes_contain_number("(18)(19)", 8) is False
    assert footnotes_contain_number(None, 8) is False

    sdlp_confusion_text = (
        "rst lien senior secured loan. (4) We hold an equity investment in this company. "
        "(5) Loan was on non-accrual status as of December 31, 2024. 80 SDLP Loan Portfolio "
        "as of December 31, 2023 ... "
        "er 31, 2024, the interest rate in effect for the secured borrowing was 12.15 %. "
        "(10) Loan was on non-accrual status as of December 31, 2024. "
        "(11) Loan includes interest rate floor feature."
    )
    multi_candidates = find_non_accrual_footnote_candidates(sdlp_confusion_text)
    assert multi_candidates == [5, 10]

    print("PASS")
    print("single-schedule candidates:", candidates)
    print("multi-schedule candidates:", multi_candidates)


if __name__ == "__main__":
    run()
