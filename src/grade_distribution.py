import re

NUM = r"([\d,]+\.?\d*)"

GRADE_ROW_PATTERN = re.compile(
    rf"Grade\s*(\d)\s+\$?\s*{NUM}\s+{NUM}\s*%?\s+{NUM}\s+{NUM}\s*%?\s*"
    rf"\$?\s*{NUM}\s+{NUM}\s*%?\s+{NUM}\s+{NUM}\s*%?"
)

WEIGHTED_AVG_PATTERN = re.compile(
    r"weighted average grade of the investments in our portfolio at fair value was\s*"
    r"([\d.]+)\s*and\s*([\d.]+)"
)

NON_ACCRUAL_DISCLOSED_PATTERN = re.compile(
    r"loans on non-accrual status represented\s*([\d.]+)%\s*of the total investments at amortized cost"
    r"\s*\(or\s*([\d.]+)%\s*at fair value\)\s*and\s*([\d.]+)%\s*at amortized cost"
    r"\s*\(or\s*([\d.]+)%\s*at fair value\)"
)


def _to_float(s: str) -> float:
    return float(s.replace(",", ""))


def parse_grade_distribution(text: str) -> dict:
    result = {"current": {}, "prior": {}}

    for m in GRADE_ROW_PATTERN.finditer(text):
        grade = m.group(1)
        result["current"][grade] = {
            "fair_value": _to_float(m.group(2)),
            "pct_fair_value": _to_float(m.group(3)),
            "n_companies": int(_to_float(m.group(4))),
            "pct_companies": _to_float(m.group(5)),
        }
        result["prior"][grade] = {
            "fair_value": _to_float(m.group(6)),
            "pct_fair_value": _to_float(m.group(7)),
            "n_companies": int(_to_float(m.group(8))),
            "pct_companies": _to_float(m.group(9)),
        }

    wavg = WEIGHTED_AVG_PATTERN.search(text)
    if wavg:
        result["weighted_avg_grade_current"] = float(wavg.group(1))
        result["weighted_avg_grade_prior"] = float(wavg.group(2))

    na = NON_ACCRUAL_DISCLOSED_PATTERN.search(text)
    if na:
        result["non_accrual_pct_cost_current"] = float(na.group(1))
        result["non_accrual_pct_fair_value_current"] = float(na.group(2))
        result["non_accrual_pct_cost_prior"] = float(na.group(3))
        result["non_accrual_pct_fair_value_prior"] = float(na.group(4))

    return result
