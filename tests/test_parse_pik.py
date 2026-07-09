import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.pipeline_phase4 import parse_pik, parse_pct


def run():
    assert parse_pik("9.45% (2.88% PIK)") == 2.88
    assert parse_pik("10.60% (incl. 2.65% PIK)") == 2.65
    assert parse_pik("8.66%") is None
    assert parse_pik(None) is None

    assert parse_pct("9.45% (2.88% PIK)") == 9.45
    assert parse_pct("10.60% (incl. 2.65% PIK)") == 10.60

    print("PASS")


if __name__ == "__main__":
    run()
