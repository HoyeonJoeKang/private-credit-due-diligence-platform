import re
from xml.etree import ElementTree as ET

SOI_PATTERN = re.compile(r"schedule of investments", re.IGNORECASE)
BALANCE_SHEET_PATTERN = re.compile(r"balance sheet|statements? of assets and liabilities", re.IGNORECASE)
PARENTHETICAL_PATTERN = re.compile(r"parenthetical", re.IGNORECASE)
STATEMENT_PATTERN = re.compile(r"-\s*statement\s*-", re.IGNORECASE)


def parse_filing_summary(xml_text: str) -> list[dict]:
    root = ET.fromstring(xml_text)
    reports = []
    for report in root.findall(".//Report"):
        html_file = report.findtext("HtmlFileName")
        short_name = report.findtext("ShortName") or ""
        long_name = report.findtext("LongName") or ""
        position = report.findtext("Position")
        reports.append({
            "html_file": html_file,
            "short_name": short_name.strip(),
            "long_name": long_name.strip(),
            "position": int(position) if position else None,
        })
    return reports


def _find_by_pattern(reports, pattern, include_parenthetical=False, statements_only=True):
    matches = []
    for r in reports:
        text = f"{r['short_name']} {r['long_name']}"
        if not pattern.search(text):
            continue
        if not include_parenthetical and PARENTHETICAL_PATTERN.search(text):
            continue
        if statements_only and not STATEMENT_PATTERN.search(r["long_name"]):
            continue
        matches.append(r)
    matches.sort(key=lambda r: r["position"] or 0)
    return matches


def find_schedule_of_investments_reports(reports, include_parenthetical=False, statements_only=True):
    return _find_by_pattern(reports, SOI_PATTERN, include_parenthetical, statements_only)


def find_balance_sheet_reports(reports, include_parenthetical=False, statements_only=True):
    return _find_by_pattern(reports, BALANCE_SHEET_PATTERN, include_parenthetical, statements_only)
