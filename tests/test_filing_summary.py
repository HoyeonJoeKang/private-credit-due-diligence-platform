import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.filing_summary import (
    parse_filing_summary,
    find_schedule_of_investments_reports,
    find_balance_sheet_reports,
)

FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "sample_filing_summary.xml"


def run():
    xml_text = FIXTURE_PATH.read_text()
    reports = parse_filing_summary(xml_text)
    assert len(reports) == 6

    soi = find_schedule_of_investments_reports(reports)
    assert len(soi) == 1
    assert soi[0]["html_file"] == "R5.htm"
    assert soi[0]["short_name"] == "Consolidated Schedule of Investments"

    soi_with_parenthetical = find_schedule_of_investments_reports(reports, include_parenthetical=True)
    assert len(soi_with_parenthetical) == 2
    assert {r["html_file"] for r in soi_with_parenthetical} == {"R5.htm", "R6.htm"}

    soi_including_disclosure = find_schedule_of_investments_reports(reports, statements_only=False)
    assert len(soi_including_disclosure) == 2
    assert {r["html_file"] for r in soi_including_disclosure} == {"R5.htm", "R43.htm"}

    alt_name_reports = [{
        "html_file": "R7.htm",
        "short_name": "Condensed Consolidated Statements of Assets and Liabilities",
        "long_name": "0002007 - Statement - Condensed Consolidated Statements of Assets and Liabilities",
        "position": 7,
    }]
    bs_alt = find_balance_sheet_reports(reports + alt_name_reports)
    assert len(bs_alt) == 2
    assert {r["html_file"] for r in bs_alt} == {"R2.htm", "R7.htm"}

    print("PASS")
    for r in soi:
        print(r["html_file"], "-", r["short_name"])


if __name__ == "__main__":
    run()
