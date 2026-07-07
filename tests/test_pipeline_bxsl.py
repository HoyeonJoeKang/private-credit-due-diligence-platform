import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.pipeline_bxsl import parse_reference_and_spread


def run():
    assert parse_reference_and_spread("SOFR + 6.00%") == ("SOFR", 6.00)
    assert parse_reference_and_spread("E + 5.00%") == ("E", 5.00)
    assert parse_reference_and_spread(None) == (None, None)

    print("PASS")


if __name__ == "__main__":
    run()
