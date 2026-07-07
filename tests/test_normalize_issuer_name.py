import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.pipeline_phase4 import normalize_issuer_name


def run():
    assert normalize_issuer_name("Avalign Holdings, Inc. and Avalign Technologies, Inc.") \
        == "Avalign Holdings, Inc. and Avalign Technologies, Inc"
    assert normalize_issuer_name("Avalign Holdings, Inc. and Avalign Technologies, Inc. (13)") \
        == "Avalign Holdings, Inc. and Avalign Technologies, Inc"
    assert normalize_issuer_name("Absolute Dental Group LLC and Absolute Dental Equity, LLC (5)(13)") \
        == "Absolute Dental Group LLC and Absolute Dental Equity, LLC"
    assert normalize_issuer_name("ACP Avenu Midco LLC (13)") == "ACP Avenu Midco LLC"
    assert normalize_issuer_name("Team Acquisition Corporation") == "Team Acquisition Corporation"

    assert normalize_issuer_name("FEH Group, LLC.") == "FEH Group, LLC"
    assert normalize_issuer_name("FEH Group, LLC") == "FEH Group, LLC"

    assert normalize_issuer_name("Primo Water Holdings Inc / Triton Water Holdings Inc") \
        == "Primo Water Holdings Inc and Triton Water Holdings Inc"
    assert normalize_issuer_name("Elemica Parent, Inc. & EZ Elemica Holdings, Inc.") \
        == "Elemica Parent, Inc. and EZ Elemica Holdings, Inc"

    assert normalize_issuer_name("KBHS Acquisition, LLC (d/b/a Alita Care, LLC)") \
        == "KBHS Acquisition, LLC (d/b/a Alita Care, LLC)"
    assert normalize_issuer_name("AT&T Test Holdco") == "AT&T Test Holdco"

    print("PASS")


if __name__ == "__main__":
    run()
