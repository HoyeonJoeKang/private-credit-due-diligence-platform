import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.grade_distribution import parse_grade_distribution

SAMPLE_TEXT = (
    "grade distribution of our portfolio companies as of March 31, 2026 and December 31, 2025: "
    "As of March 31, 2026 December 31, 2025 (dollar amounts in millions) Fair Value % Number of "
    "Companies % Fair Value % Number of Companies % Grade 4 $ 5,295 17.9 % 66 10.9 % $ 5,040 17.1 % "
    "65 10.8 % Grade 3 22,849 77.5 480 79.1 23,322 79.1 486 80.6 Grade 2 919 3.1 31 5.1 675 2.3 27 4.5 "
    "Grade 1 436 1.5 30 4.9 448 1.5 25 4.1 Total $ 29,499 100.0 % 607 100.0 % $ 29,485 100.0 % 603 "
    "100.0 % As of March 31, 2026 and December 31, 2025, the weighted average grade of the "
    "investments in our portfolio at fair value was 3.1 and 3.1, respectively. As of March 31, 2026 "
    "and December 31, 2025, loans on non-accrual status represented 2.1% of the total investments at "
    "amortized cost (or 1.2% at fair value) and 1.8% at amortized cost (or 1.2% at fair value), "
    "respectively."
)


def run():
    result = parse_grade_distribution(SAMPLE_TEXT)

    assert result["current"]["4"]["fair_value"] == 5295.0
    assert result["current"]["4"]["pct_fair_value"] == 17.9
    assert result["current"]["4"]["n_companies"] == 66

    assert result["current"]["3"]["fair_value"] == 22849.0
    assert result["current"]["2"]["fair_value"] == 919.0
    assert result["current"]["1"]["fair_value"] == 436.0

    assert result["prior"]["4"]["fair_value"] == 5040.0
    assert result["prior"]["1"]["n_companies"] == 25

    assert result["weighted_avg_grade_current"] == 3.1
    assert result["weighted_avg_grade_prior"] == 3.1

    assert result["non_accrual_pct_cost_current"] == 2.1
    assert result["non_accrual_pct_fair_value_current"] == 1.2
    assert result["non_accrual_pct_cost_prior"] == 1.8
    assert result["non_accrual_pct_fair_value_prior"] == 1.2

    print("PASS")
    for k, v in result.items():
        print(k, v)


if __name__ == "__main__":
    run()
